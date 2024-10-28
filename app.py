from flask import Flask
from models import db
from routes import api

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///veritabani.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# API rotalarını kaydedin
app.register_blueprint(api)
app.secret_key = 'HACKATHON24WWW'

# Veritabanını başlatma
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
