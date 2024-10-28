from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Ders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), nullable=False)
    sinavlar = db.relationship('Sinav', backref='ders', lazy=True)

class Sinav(db.Model):
    sinavID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tarih = db.Column(db.DateTime, nullable=False)
    ders_id = db.Column(db.Integer, db.ForeignKey('ders.id'), nullable=False)
    sorular = db.relationship('Soru', backref='sinav', lazy=True)

class Soru(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    soru = db.Column(db.String(500), nullable=False)
    soru_no = db.Column(db.Integer, nullable=False)
    puan = db.Column(db.Integer, nullable=False)
    kisitlamalar = db.Column(db.String(500), nullable=True)
    sinav_id = db.Column(db.Integer, db.ForeignKey('sinav.sinavID'), nullable=False)
    cevaplar = db.relationship('Cevap', backref='soru', lazy=True)

class Cevap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cevap = db.Column(db.String(500), nullable=False)
    puan = db.Column(db.Integer, nullable=False)
    soru_id = db.Column(db.Integer, db.ForeignKey('soru.id'), nullable=False)
    analizler = db.relationship('Analiz', backref='cevap', lazy=True)
    ogrenciler = db.relationship('Ogrenci', backref='cevap', lazy=True)

class Ogrenci(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numara = db.Column(db.String(50), nullable=True)
    ad = db.Column(db.String(50), nullable=False)
    soyad = db.Column(db.String(50), nullable=True)
    cevap_id = db.Column(db.Integer, db.ForeignKey('cevap.id'), nullable=False)

class Analiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pozitif = db.Column(db.String(500), nullable=True)
    negatif = db.Column(db.String(500), nullable=True)
    cevap_id = db.Column(db.Integer, db.ForeignKey('cevap.id'), nullable=False)


class Ogretmen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)