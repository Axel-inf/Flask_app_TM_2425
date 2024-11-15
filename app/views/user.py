from flask import Flask, render_template, request, redirect, url_for, flash, g, session, Blueprint, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
from app.db.db import get_db, close_db

app = Flask(__name__)
user_bp = Blueprint('user', __name__, url_prefix='/user')
app.config['UPLOAD_FOLDER'] = 'app/static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'supersecretkey'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_profile_image(user_id):
    db = get_db()
    curseur = db.cursor()
    curseur.execute("SELECT chemin_vers_image FROM Personnes WHERE id_personne = ?", (user_id,))
    result = curseur.fetchone()
    db.commit()
    close_db()
    return os.path.basename(result[0]) if result and result[0] else None


@user_bp.route('profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')  # Identifiant de l'utilisateur en session
    if not user_id:
        return redirect(url_for('auth.login'))

    profile_image = get_profile_image(user_id)  # Récupérer l'image de profil actuelle

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier détecté.')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Aucun fichier sélectionné.')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)

                # Mettre à jour la base de données
                db = get_db()
                db.execute("UPDATE Personnes SET chemin_vers_image = ? WHERE id_personne = ?", (filename, user_id))
                db.commit()
                close_db()

                # Mettre à jour la session
                session['chemin_image'] = filename

                flash('Image de profil mise à jour avec succès.')
                return redirect(url_for('user.profile'))
            except Exception as e:
                flash(f"Erreur lors de l'enregistrement du fichier : {e}")
                return redirect(request.url)
        else:
            flash('Type de fichier non autorisé.')
            return redirect(request.url)

    return render_template('user/profile.html', profile_image=profile_image, role=g.get('role'))


@user_bp.route('/delete_image', methods=['POST'])
def delete_image():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    profile_image = get_profile_image(user_id)
    if profile_image:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], profile_image)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Mettre à jour la base de données pour supprimer le chemin
        db = get_db()
        db.execute("UPDATE Personnes SET chemin_vers_image = NULL WHERE id_personne = ?", (user_id,))
        db.commit()
        close_db()

        # Mettre à jour la session
        session['chemin_image'] = None
        flash("L'image de profil a été supprimée.")
    else:
        flash("Aucune image de profil à supprimer.")

    return redirect(url_for('user.profile'))


@user_bp.route('/update_user', methods=['POST'])
def update_user():
    if not g.get('user'):
        return redirect(url_for('auth.login'))

    prenom = request.form.get('prenom')
    nom = request.form.get('nom')
    email = request.form.get('email')

    if not prenom or not nom or not email:
        flash('Tous les champs sont requis.')
        return redirect(url_for('user.profile'))

    db = get_db()
    db.execute('''
        UPDATE Personnes
        SET prenom = ?, nom = ?, email = ?
        WHERE id_personne = ?
    ''', (prenom, nom, email, g.user['id_personne']))
    db.commit()
    close_db()

    flash("Profil mis à jour avec succès.")
    return redirect(url_for('user.profile'))


if __name__ == '__main__':
    app.run(debug=True)
