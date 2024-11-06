from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from app.utils import *

# Routes /user/...
user_bp = Blueprint('user', __name__, url_prefix='/user')

# Route /user/profile accessible uniquement à un utilisateur connecté grâce au décorateur @login_required
@user_bp.route('/profile', methods=('GET', 'POST'))
@login_required 
def show_profile():
    # Affichage de la page principale de l'application
    return render_template('user/profile.html', role=g.role)
