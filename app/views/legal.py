from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from app.utils import get_profile_image

legal_bp = Blueprint('legal', __name__)


@legal_bp.route('/conditions_utilisation')
def conditions_utilisation():
    return render_template('legal/conditions_utilisation.html')

@legal_bp.route('/mentions_legales')
def mentions_legales():
    return render_template('legal/mentions_legales.html')

@legal_bp.route('/def politique_confidentialite')
def politique_confidentialite():
    return render_template('legal/politique_confidentialite.html')

