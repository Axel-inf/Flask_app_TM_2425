from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
import os
# Routes /...
coach_bp = Blueprint('coach', __name__, url_prefix='/coach')



@coach_bp.route('/create_course', methods=['GET', 'POST'])
def create_course():
    # Débogage : vérifier g.user
    print(f"Valeur de g.user : {g.user}")

    # Si l'utilisateur n'est pas connecté, rediriger vers l'accueil
    if not g.user:
        return redirect(url_for('home.landing_page'))

    # Si des données sont envoyées via le formulaire (POST)
    if request.method == 'POST':
        # Récupération des données envoyées par le formulaire
        description = request.form.get('description', '').strip()  # Description du cours
        tarif = request.form.get('tarif', '').strip()  # Tarif du cours
        disponibilites = request.form.getlist('disponibilite')  # Disponibilités du cours
        disponibilites_str = ",".join(disponibilites) 
        canton = request.form.get('canton', '').strip()  # Canton du coach
        ville = request.form.get('ville', '').strip()  # Ville du coach
        langue = request.form.get('langue', '').strip()  # Langue du coach
        apropos = request.form.get('apropos', '').strip()  # À propos du coach
        user_id = session.get('user_id')  # ID de l'utilisateur connecté
        print(f"user_id dans session : {user_id}")

        # Vérification des données
        if not tarif or not tarif.isdigit():
            flash("Le tarif doit être un nombre valide.", "error")
            return redirect(url_for('coach.create_course'))

        tarif = int(tarif)

        print(f"Form data: {request.form}")
        
        # Connexion à la base de données
        db = get_db()
        cursor = db.cursor()

        # Validation des champs
        if description and tarif and disponibilites_str and canton and ville and langue and apropos:
            try:
                # Mise à jour de la table Personnes
                cursor.execute("""
                    UPDATE Personnes 
                    SET canton = ?, ville = ?, langue = ?
                    WHERE id_personne = ?
                """, (canton, ville, langue, user_id))
                print(f"Mis à jour Personnes avec canton={canton}, ville={ville}, langue={langue}, id_personne={user_id}")

                
                # Mise à jour de la table Coachs
                cursor.execute("""
                    UPDATE Coachs 
                    SET biographie = ?
                    WHERE id_personne = ?
                """, (apropos, user_id))
                print(f"Mis à jour Coachs avec biographie={apropos}, id_personne={user_id}")



                # Insertion dans la table Cours
                cursor.execute("""
                    INSERT INTO Cours (description, tarif, disponibilites) 
                    VALUES (?, ?, ?)
                """, (description, tarif, disponibilites_str))
                print(f"Ajouté Cours avec description={description}, tarif={tarif}, disponibilites={disponibilites_str}")

                
                # Récupération de l'id du cours nouvellement créé
                cours_id = cursor.lastrowid

                # Mise à jour de la table Coachs pour établir le lien avec le cours
                cursor.execute("""
                    UPDATE Coachs 
                    SET FK_idcours = ?
                    WHERE id_personne = ?
                """, (cours_id, user_id))
                print(f"Mis à jour Coachs avec FK_idcours={cours_id} pour id_personne={user_id}")


                db.commit()  # Sauvegarde dans la base de données
                close_db()

                flash("Cours créé avec succès!", "success")
                return redirect(url_for('auth.validation_connexion'))

            except Exception as e:
                print(f"Erreur lors de l'insertion dans la base de données: {e}")
                flash("Une erreur est survenue lors de la création du cours.", "error")
                return redirect(url_for('coach.create_course'))
        else:
            flash("Tous les champs doivent être remplis.", "error")
            return redirect(url_for('coach.create_course'))

    # Si la méthode est GET, afficher le formulaire
    return render_template('coach/create_course.html', chemin_image=g.chemin_image, role=g.role)


@coach_bp.route('/confirmation')
def validation_connexion():
    return render_template('coach/confirmation.html')
