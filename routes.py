import json
from datetime import datetime
import requests
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from models import db, Ders, Sinav, Soru, Cevap, Ogrenci, Analiz
import google.generativeai as genai
api = Blueprint('api', __name__)

# API anahtarını yapılandır
genai.configure(api_key="AIzaSyC23Ej8ip2dAt8hSHxEGxeORTQlC6WqisM")

# Model yapılandırması
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json"
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction="Sen, klasik olarak yapılan bir sınavın analiz aracısın. "
                      "Sana şu komutları verdiğimde şu işlemleri gerçekleştirmeni istiyorum;\n\n"
                      "1 - sinavKagitlariniOku : Bu komutta, sana sınav kağıtlarının text verisini vereceğim. "
                      "Eline geçen text verisini şu json formatında bana vermeni istiyorum. "
                      "Bu soruları cevaplara göre kısıtlamaları ve soru içeriğini göz önüne alarak; "
                      "sahip olduğun bilgilere göre puanlandır ve nasıl puanlandırdığını analiz kısmında "
                      "pozitif ve negatif olarak sebeplerini açıklayarak belirt. "
                      "Aynı cevabı veren öğrenciler olursa bunu 'ogrenciler' propertysinde belirt. "
                      "Ek bir cevapmış gibi algılama. Ayrıca bir kısıtlama belirtilmediyse soruda "
                      "sorulan her şeyin puan değeri birbirine eşittir. Eğer sorulan soruya alakasız bir cevap "
                      "verildiyse puan verme.\n\n"
                      "{ders: {ad (string)}, sinav: {tarih (timestamp)},sorular: [{soru (string), "
                      "puan(double), kisitlamalar[], cevaplar: [\ncevap: (string),\npuan: (double),\n"
                      "ogrenciler: [{numara, ad, soyad}]\nanaliz: [\npozitif: [],\nnegatif: [],\n]\n]}]}",
)

chat_session = model.start_chat(history=[])

@api.route('/', methods=['GET'])
def homepage():
    return render_template('index.html')

@api.route('/run', methods=['POST'])
def run():
    if request.method == 'POST':
        text = request.form.get('text')
        json_data = chat_session.send_message(text).text
        if not json_data:
            return "Hata: JSON verisi boş.", 400
        try:
            response = requests.post("http://127.0.0.1:5000/add_data", json=json.loads(json_data))
            if response.status_code == 201:
                return redirect(url_for('api.sinav', sinav_id=response.json().get("sinavID"), soru_id=1))
            else:
                print("Bir hata oluştu:", response.status_code)
                print(response.text)
        except json.JSONDecodeError as e:
            return f"Hata: Geçersiz JSON formatı. {str(e)}", 400
        except Exception as e:
            return f"Hata: {str(e)}", 400


@api.route('/sinav/<int:sinav_id>/soru/<int:soru_id>')
def sinav(sinav_id, soru_id):
    sinav = Sinav.query.get_or_404(sinav_id)
    soru = Soru.query.get_or_404(soru_id)
    return render_template('exam.html', sinav=sinav, soru=soru)

@api.route('/add_data', methods=['POST'])
def add_data():
    try:
        # JSON verisini almak
        json_data = request.get_json(force=True)  # force=True, eğer Content-Type belirtilmemişse bile JSON verisini alır.

        # Ders ekleme
        ders_data = json_data.get('ders')
        ders = Ders(ad=ders_data['ad'])
        db.session.add(ders)
        db.session.commit()
        # Sınav ekleme
        sinav_data = json_data.get('sinav')
        sinav_tarih = sinav_data['tarih']

        # Tarih alanı kontrolü
        if sinav_tarih is None:
            sinav_tarih = datetime.now()  # Geçerli tarihi al
        else:
            sinav_tarih = datetime.fromisoformat(sinav_tarih)  # Geçerli tarih string ise burada dönüştür

        # Sınav nesnesini oluştur
        sinav = Sinav(tarih=sinav_tarih, ders_id=ders.id)
        db.session.add(sinav)
        db.session.commit()

        # Soruları ekleme
        for soru_data in json_data.get('sorular', []):
            soru = Soru(
                soru=soru_data['soru'],
                puan=soru_data['puan'],
                kisitlamalar=", ".join(soru_data['kisitlamalar']),
                sinav_id=sinav.sinavID
            )
            db.session.add(soru)
            db.session.commit()

            # Cevapları ekleme
            for cevap_data in soru_data.get('cevaplar', []):
                cevap = Cevap(
                    cevap=cevap_data['cevap'],
                    puan=cevap_data['puan'],
                    soru_id=soru.id
                )
                db.session.add(cevap)
                db.session.commit()

                # Öğrencileri ekleme
                for ogrenci_data in cevap_data.get('ogrenciler', []):
                    ogrenci = Ogrenci(
                        numara=ogrenci_data.get('numara'),
                        ad=ogrenci_data['ad'],
                        soyad=ogrenci_data.get('soyad'),
                        cevap_id=cevap.id
                    )
                    db.session.add(ogrenci)

                # Analizleri ekleme
                analiz_data = cevap_data.get('analiz', {})
                analiz = Analiz(
                    pozitif=", ".join(analiz_data.get('pozitif', [])),
                    negatif=", ".join(analiz_data.get('negatif', [])),
                    cevap_id=cevap.id
                )
                db.session.add(analiz)

                db.session.commit()

        return jsonify({"message": "Veri başarıyla eklendi!", "sinavID": sinav.sinavID}), 201

    except Exception as e:
        db.session.rollback()  # Hata durumunda geri alma
        return jsonify({"error": str(e)}), 500
