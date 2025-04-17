from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
import os
from app.email.email import send_email

password_bp = Blueprint('password', __name__, url_prefix='/password')

@password_bp.route('/reset1', methods=['GET', 'POST'])
def reset1():
    return render_template('password/reset1.html')

@password_bp.route('/mot_de_passe_oublie', methods=['GET', 'POST'])
def mot_de_passe_oublie():
    if request.method == 'POST':
        email = request.form['email']
        print("Email reçu depuis le formulaire :", email)

        sujet = "Réinitialisation de votre mot de passe"
        message = """
        <h2>Bonjour,</h2>
        <p>Voici un e-mail de test pour vérifier que tout fonctionne.</p>
        <p>Code à usage unique : </p>
        <p>Si vous n’êtes pas à l’origine de cette demande, ignorez ce message.</p>
        <p>– L’équipe ttcoach</p>
        """

        try:
            send_email(to_address=email, subject=sujet, message=message, cc_addresses=[])
            flash("Un e-mail vous a été envoyé avec les instructions.", "success")
            return redirect(url_for('password.mot_de_passe_oublie'))
        except Exception as e:
            print(f"Erreur d'envoi : {e}")
            flash("Échec de l'envoi de l'e-mail.", "error")

        return redirect(url_for('password.mot_de_passe_oublie'))

    return render_template('password/reset2.html')

    