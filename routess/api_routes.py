from flask import Blueprint, jsonify, session
from models import db, Sinav, Soru, Cevap, Ders, Ogrenci, Analiz
from datetime import datetime

api_bp = Blueprint('api_routes', __name__)

@api_bp.route('/add_data', methods=['POST'])
def add_data(json_data=None):
    try:
        print(json_data)
        ders_data = json_data.get('ders')
        ders = Ders(ad=ders_data['ad'])
        db.session.add(ders)
        db.session.commit()

        sinav = Sinav(tarih=datetime.now(), ders_id=ders.id, ogretmen_id=session.get('teacher_id'))
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
