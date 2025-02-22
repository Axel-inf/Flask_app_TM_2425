from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
from datetime import datetime

messagerie_bp = Blueprint('messagerie', __name__, url_prefix='/messagerie')

@messagerie_bp.route('/discussion', methods=['GET', 'POST'])
def discussion():
    if not g.get('user'):
        return redirect(url_for('auth.login'))
    return render_template('messagerie/discussion.html', profile_image=g.chemin_image, role=g.role)
