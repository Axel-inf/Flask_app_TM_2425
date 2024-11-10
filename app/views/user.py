from flask import (Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for)
from app.utils import *
from werkzeug.utils import secure_filename
import os
import sqlite3
from app.db.db import get_db, close_db

# Routes /user/...
user_bp = Blueprint('user', __name__, url_prefix='/user')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'supersecretkey'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_profile_image():
    db = get_db()
    curseur = db.cursor()
    curseur.execute("SELECT chemin_vers_image FROM Personnes ORDER BY id_personne DESC LIMIT 1")
    result = curseur.fetchone()
    db.commit()         
    # On ferme la connexion à la base de données pour éviter les fuites de mémoire
    close_db()
    return result[0] if result else None

@user_bp.route('/profile', methods=('GET', 'POST'))
@login_required 
def profile():
    profile_image = None

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Insérer le chemin du fichier dans la base de données
            db = get_db()
            curseur = db.cursor()
            curseur.execute("INSERT INTO Personnes (chemin_vers_image) VALUES (?)", (filepath,))
            db.commit()
            close_db()

            profile_image = filename  # Mise à jour du chemin de l'image de profil
            return redirect(url_for('user.profile'))

    profile_image = get_profile_image()
    return render_template('user/profile.html', profile_image=profile_image,role=g.role)

