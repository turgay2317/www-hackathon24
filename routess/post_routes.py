import base64
import json

import requests
from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, session

from config import chat_session, VISION_API_KEY
from models import db, Analiz, Cevap, Ogretmen
from routess.api_routes import add_data

post_bp = Blueprint('post_bp', __name__)


@post_bp.route('/run', methods=['POST'])
def run():
    teacher_id = session.get('teacher_id')
    if teacher_id is None:
        return render_template('error.html', message='Önce giriş yapmalısınız.')

    detected_texts = []

    if request.method == 'POST':
        images = request.files.getlist("images")

        if not images:
            return "Lütfen en az bir görüntü yükleyin", 400

        for image in images:
            # Görüntüyü base64 formatına çevir
            content = base64.b64encode(image.read()).decode("utf-8")

            # Google Vision API endpoint'i
            url = f"https://vision.googleapis.com/v1/images:annotate?key={VISION_API_KEY}"

            # İstek verisi
            data = {
                "requests": [
                    {
                        "image": {
                            "content": content
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION"
                            }
                        ]
                    }
                ]
            }

            # API'ye POST isteği gönder ve yanıtı al
            try:
                response = requests.post(url, json=data)
                response.raise_for_status()  # Yanıt 200 OK değilse hata fırlatır
                result = response.json()

                # Yanıtın "responses" ve "textAnnotations" anahtarını kontrol et
                if "responses" in result and result['responses'] and 'textAnnotations' in result['responses'][0]:
                    detected_text = result['responses'][0]['textAnnotations'][0].get('description', 'Metin bulunamadı.')
                else:
                    detected_text = "Yanıtta metin bulunamadı."

                detected_texts.append(detected_text)

            except requests.exceptions.RequestException as e:
                print(f"API isteğinde hata oluştu: {e}")
                detected_texts.append("API isteğinde bir hata oluştu.")

        text = '\n'.join(detected_texts)

        json_data = chat_session.send_message(text).text
        if not json_data:
            return "Hata: JSON verisi boş.", 400
        try:
            response = add_data(json.loads(json_data))

            if isinstance(response, tuple):
                status_code = response[1]
                if status_code != 201:
                    return jsonify({"error": "Hata oluştu"}), status_code

                response_data = response[0].get_json()  # JSON yanıtını al
                sinavID = response_data.get("sinavID")  # sinavID'yi al

                return redirect(url_for('exam_bp.sinav', sinav_id=sinavID, soru_no=1))

            else:
                print("Bir hata oluştu:", response.status_code)
                print(response.text)
                return "Veri eklenemedi, lütfen daha sonra tekrar deneyin.", 400
        except json.JSONDecodeError as e:
            print(json_data)
            return f"Hata: Geçersiz JSON formatı. {str(e)}", 400
        except Exception as e:
            return f"Hata: {str(e)}", 400



@post_bp.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        new_teacher = Ogretmen(username=username)
        new_teacher.password = password

        db.session.add(new_teacher)
        db.session.commit()

        flash('Öğretmen başarıyla eklendi!', 'success')
        return redirect(url_for('post_bp.add_teacher'))

    return render_template('add_teacher.html')


@post_bp.route('/kaydet_puanlar', methods=['POST'])
def kaydet_puanlar():
    data = request.json
    puanlar = data.get('puanlar', [])
    pozitif_analizler = data.get('pozitif', [])
    negatif_analizler = data.get('negatif', [])

    try:
        # Puanları güncelle
        for puan in puanlar:
            cevap_id = puan['cevap_id']
            yeni_puan = puan['puan']
            cevap_objesi = Cevap.query.get(cevap_id)
            if cevap_objesi:
                cevap_objesi.puan = yeni_puan
                db.session.commit()

        # Pozitif analizleri güncelle
        for analiz in pozitif_analizler:
            analiz_id = analiz['id']
            yeni_pozitif = analiz['pozitif']
            analiz_objesi = Analiz.query.get(analiz_id)
            if analiz_objesi:
                analiz_objesi.pozitif = yeni_pozitif
                db.session.commit()

        # Negatif analizleri güncelle
        for analiz in negatif_analizler:
            analiz_id = analiz['id']
            yeni_negatif = analiz['negatif']
            analiz_objesi = Analiz.query.get(analiz_id)
            if analiz_objesi:
                analiz_objesi.negatif = yeni_negatif
                db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()  # Hata olursa değişiklikleri geri al
        return jsonify({'success': False, 'message': str(e)}), 500