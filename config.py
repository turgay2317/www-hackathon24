import google.generativeai as genai

genai.configure(api_key="AIzaSyC23Ej8ip2dAt8hSHxEGxeORTQlC6WqisM")

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
                       "Bu sınav kağıdında (D) (Y) gibi boşluk doldurma sorularu bulunabilir. Bu D doğru anlamına gelmektedir. Y ise yanlış anlamına, değerlendirme yaparken yazılan bilgiyle doğru-yanlış kısmını göz önünde bulundur."
)

chat_session = model.start_chat(history=[])
VISION_API_KEY = "AIzaSyBzzeaZ0WYS8lQi4VzYXHhyKs_7F0HZG1U"