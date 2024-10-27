import json
from datetime import datetime
import requests
import base64
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

json_string = '''{
    "ders": {
        "ad": "string"  # Ders adı
    },
    "sinav": {
        "tarih": None  # Sınav tarihi (timestamp)
    },
    "sorular": [
        {
            "soru": "string",  # Soru metni
            "soru_no": 1,  # Soru numarası (int, otomatik artan)
            "puan": 0.0,  # Soru puanı (float)
            "kisitlamalar": [],  # Kısıtlamalar listesi
            "cevaplar": [
                {
                    "cevap": "string",  # Cevap metni
                    "puan": 0.0,  # Cevap puanı (float)
                    "ogrenciler": [
                        {
                            "numara": "string",  # Öğrenci numarası
                            "ad": "string",  # Öğrenci adı
                            "soyad": "string"  # Öğrenci soyadı
                        }
                    ],
                    "analiz": {
                        "pozitif": [],  # Pozitif analiz listesi
                        "negatif": []   # Negatif analiz listesi
                    }
                }
            ]
        }
    ]
} '''

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
    system_instruction="Sen, klasik olarak yapılan bir sınavın analiz aracısın. "
                      "Sana şu komutları verdiğimde şu işlemleri gerçekleştirmeni istiyorum;\n\n"
                      "1 - sinavKagitlariniOku : Bu komutta, sana sınav kağıtlarının text verisini vereceğim. "
                      "Bu text verisindeki Türkçe kelimelerde bazı yazım yanlışları olabilir Onları doğru kelimelerle değiştirip değerlendirmeni istiyorum."
                      "Eline geçen text verisini şu json formatında bana vermeni istiyorum. "
                      "Bu soruları cevaplara göre kısıtlamaları ve soru içeriğini göz önüne alarak; "
                      "sahip olduğun bilgilere göre puanlandır ve nasıl puanlandırdığını analiz kısmında "
                      "pozitif ve negatif olarak sebeplerini açıklayarak belirt. "
                      "Aynı cevabı veren öğrenciler olursa bunu 'ogrenciler' propertysinde belirt. "
                      "Ek bir cevapmış gibi algılama. Ayrıca bir kısıtlama belirtilmediyse soruda "
                      "sorulan her şeyin puan değeri birbirine eşittir. Eğer sorulan soruya alakasız bir cevap "
                      f"verildiyse puan verme.\n {json_string}"
                      "Bana vereceğin JSON'da kesinlikle parantezler doğru olsun. Herhangi bir hata olmasın güzelce kontrol et."
)

chat_session = model.start_chat(history=[])

@api.route('/', methods=['GET'])
def homepage():
    return render_template('upload.html')

VISION_API_KEY = "AIzaSyBzzeaZ0WYS8lQi4VzYXHhyKs_7F0HZG1U"

@api.route('/run', methods=['POST'])
def run():
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
            response = requests.post("http://127.0.0.1:5000/add_data", json=json.loads(json_data))
            if response.status_code == 201:
                return redirect(url_for('api.sinav', sinav_id=response.json().get("sinavID"), soru_no=1))
            else:
                print("Bir hata oluştu:", response.status_code)
                print(response.text)
        except json.JSONDecodeError as e:
            print(json_data)
            return f"Hata: Geçersiz JSON formatı. {str(e)}", 400
        except Exception as e:
            return f"Hata: {str(e)}", 400


@api.route('/sinav/<int:sinav_id>/soru/<int:soru_no>')
def sinav(sinav_id, soru_no):
    sinav = Sinav.query.get_or_404(sinav_id)
    soru = Soru.query.filter_by(sinav_id=sinav_id, soru_no=soru_no).first()

    if sinav is None or soru is None:
        return render_template('error.html', message='Sınav ya da soru bulunamadı')

    return render_template('exam.html', sinav=sinav, soru=soru)

@api.route('/add_data', methods=['POST'])
def add_data():
    try:
        json_data = request.get_json(force=True)
        print(json_data)
        ders_data = json_data.get('ders')
        ders = Ders(ad=ders_data['ad'])
        db.session.add(ders)
        db.session.commit()
        sinav = Sinav(tarih=datetime.now(), ders_id=ders.id)
        db.session.add(sinav)
        db.session.commit()

        for soru_data in json_data.get('sorular', []):
            soru = Soru(
                soru=soru_data['soru'],
                soru_no=soru_data['soru_no'],
                puan=soru_data['puan'],
                kisitlamalar=", ".join(soru_data['kisitlamalar']),
                sinav_id=sinav.sinavID
            )
            db.session.add(soru)
            db.session.commit()

            for cevap_data in soru_data.get('cevaplar', []):
                cevap = Cevap(
                    cevap=cevap_data['cevap'],
                    puan=cevap_data['puan'],
                    soru_id=soru.id
                )
                db.session.add(cevap)
                db.session.commit()

                for ogrenci_data in cevap_data.get('ogrenciler', []):
                    ogrenci = Ogrenci(
                        numara=ogrenci_data.get('numara'),
                        ad=ogrenci_data['ad'],
                        soyad=ogrenci_data.get('soyad'),
                        cevap_id=cevap.id
                    )
                    db.session.add(ogrenci)

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