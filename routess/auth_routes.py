from flask import Blueprint, render_template, session, flash, redirect, url_for, request

from models import Ogretmen, Sinav

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'teacher_id' in session:
        return redirect(url_for('auth_bp.dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        teacher = Ogretmen.query.filter_by(username=username).first()

        if teacher and teacher.password == password:
            session['teacher_id'] = teacher.id  # Oturum aç
            flash('Başarıyla giriş yaptınız!', 'success')
            return redirect(url_for('auth_bp.dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'danger')

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    # Oturumdaki teacher_id'yi temizle
    session.pop('teacher_id', None)
    flash('Başarıyla çıkış yaptınız.', 'success')
    return redirect(url_for('auth_bp.login'))


@auth_bp.route('/dashboard')
def dashboard():
    if 'teacher_id' not in session:
        flash('Lütfen önce giriş yapın.', 'warning')
        return redirect(url_for('auth_bp.login'))

    return render_template('dashboard.html')

@auth_bp.route('/upload', methods=['GET'])
def upload():
    if 'teacher_id' not in session:
        flash('Lütfen önce giriş yapın.', 'warning')
        return redirect(url_for('auth_bp.login'))

    return render_template('upload.html');

@auth_bp.route('/recent')
def recent():
    if 'teacher_id' not in session:
        flash('Lütfen önce giriş yapın.', 'warning')
        return redirect(url_for('auth_bp.login'))

    # Giriş yapılmışsa dashboard sayfasını render et
    exams = Sinav.query.filter_by(ogretmen_id=session.get('teacher_id')).all()
    return render_template('recent.html',exams=exams)
