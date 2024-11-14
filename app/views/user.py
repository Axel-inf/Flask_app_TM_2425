from flask import Flask, render_template, request, redirect, url_for, flash, g, session, Blueprint, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
from app.db.db import get_db, close_db

app = Flask(__name__)
# Routes /user/...
user_bp = Blueprint('user', __name__, url_prefix='/user')
app.config['UPLOAD_FOLDER'] = 'app/static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.secret_key = 'supersecretkey'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_profile_image(user_id):
    db = get_db()
    curseur = db.cursor()
    curseur.execute("SELECT chemin_vers_image FROM Personnes WHERE id_personne = ? ORDER BY id_personne DESC LIMIT 1", (user_id,))
    result = curseur.fetchone()
    db.commit()
    close_db()
    if result and result[0]:
        # Retourne uniquement le nom du fichier, sans le chemin complet
        return os.path.basename(result[0])
    return None

@user_bp.route('profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')  # Assuming user ID is stored in g.user.id
    profile_image = get_profile_image(user_id)  # Assurer que profile_image est défini après user_id

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            print('No file part')  # Log de débogage
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            print('No selected file')  # Log de débogage
            return redirect(request.url)
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                print(f"Saving file to {filepath}")  # Log de débogage
                file.save(filepath)

                # Insérer le chemin du fichier et l'id de l'utilisateur dans la base de données
                db = get_db()
                curseur = db.cursor()
                curseur.execute("UPDATE Personnes SET chemin_vers_image = ? WHERE id_personne = ?", (filename, user_id))
                db.commit()
                close_db()

                profile_image = filename  # Mise à jour du chemin de l'image de profil
                print(f"File saved to {filepath} and path updated in database")  # Log de débogage
                return redirect(url_for('user.profile'))
            
            except Exception as e: 
                print(f"An error occurred: {e}") 
                flash('An error occurred while saving the file.') 
                return redirect(request.url)

    profile_image = get_profile_image(user_id)  # Récupérer l'image de profil après les opérations
    return render_template('user/profile.html', profile_image=profile_image, role=g.role)


@user_bp.route('/user/delete_image', methods=['POST'])
def delete_image():
    user_id = session.get('user_id')
    profile_image = get_profile_image(user_id)

    if profile_image:
        # Supprime le fichier d'image du dossier static/uploads
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], profile_image)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Met à jour la base de données pour enlever le chemin de l'image
        db = get_db()
        db.execute("UPDATE Personnes SET chemin_vers_image = NULL WHERE id_personne = ?", (user_id,))
        db.commit()
        close_db()

        flash("L'image de profil a été supprimée.")

    return redirect(url_for('user.profile'))

@user_bp.route('/update_user', methods=['POST'])
def update_user():
    if g.user:
        if request.method == 'POST':
            # Récupérer les données envoyées par le formulaire
            prenom = request.form['prenom']
            nom = request.form['nom']
            email = request.form['email']

            # Vérifier que les champs sont valides
            if prenom and nom and email:
                # Connexion à la base de données
                db = get_db()

                # Mise à jour de l'utilisateur dans la table Personnes
                db.execute('''
                    UPDATE Personnes
                    SET prenom = ?, nom = ?, email = ?
                    WHERE id_personne = ?
                ''', (prenom, nom, email, g.user['id_personne']))

                # Commit des modifications
                db.commit()
                close_db()

                # Rediriger l'utilisateur vers sa page de profil
                return redirect(url_for('user.profile'))  # Redirection vers la page user/profil
            else:
                flash('Veuillez remplir tous les champs.')
                return redirect(url_for('user.profile'))  # Rediriger vers la page de profil si les champs ne sont pas valides
        else:
            # Si l'utilisateur n'est pas connecté, rediriger vers la page de connexion
            return redirect(url_for('auth.login'))




if __name__ == '__main__':
    app.run(debug=True)