from flask import Blueprint, render_template

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/', methods=['GET'])
def homepage():
    return render_template('index.html')

@main_bp.route('/about', methods=['GET'])
def about():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')
