from flask import Blueprint, render_template

from models import Sinav, Soru

exam_bp = Blueprint('exam_bp', __name__)

@exam_bp.route('/sinav/<int:sinav_id>/soru/<int:soru_no>')
def sinav(sinav_id, soru_no):
    sinav = Sinav.query.get_or_404(sinav_id)
    soru = Soru.query.filter_by(sinav_id=sinav_id, soru_no=soru_no).first()
    sonrakiSoruVarMi = Soru.query.filter_by(sinav_id=sinav_id, soru_no=soru_no + 1).first()
    sonrakiSoruID = 1 if sonrakiSoruVarMi is not None else 0
    sonrakiSoruID += soru.soru_no

    if sinav is None or soru is None:
        return render_template('error.html', message='Sınav ya da soru bulunamadı')

    return render_template('exam.html', sinav=sinav, soru=soru, sonrakiSoruID=sonrakiSoruID)

