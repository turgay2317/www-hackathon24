from flask import Flask
from models import db
from routes import api
from routess.api_routes import api_bp
from routess.auth_routes import auth_bp
from routess.exam_routes import exam_bp
from routess.main_routes import main_bp
from routess.post_routes import post_bp

app = Flask(__name__,static_url_path='/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///veritabani.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config.from_object('config.Config')

app.register_blueprint(api_bp, url_prefix='/')
app.register_blueprint(main_bp, url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/')
app.register_blueprint(post_bp, url_prefix='/')
app.register_blueprint(exam_bp, url_prefix='/')

db.init_app(app)

# API rotalarını kaydedin
app.register_blueprint(api)
app.secret_key = 'HACKATHON24WWW'

# Veritabanını başlatma
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
