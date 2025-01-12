from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
import os

coach_bp = Blueprint('coach', __name__, url_prefix='/coach')


@coach_bp.route('/create_course', methods=['GET', 'POST'])
def create_course():
    # On vérifie si l'utilisateur est connecté
    if not g.user:
        return redirect(url_for('home.landing_page'))

    user_id = session.get('user_id')  # ID de l'utilisateur connecté

    # Connexion à la base de données
    db = get_db()
    cursor = db.cursor()

    # On vérifie si le coach a déjà un cours
    cursor.execute("""
        SELECT C.id_cours, C.description, C.tarif, C.disponibilites, P.canton, P.ville, P.langue, Co.biographie
        FROM Coachs Co
        JOIN Cours C ON Co.FK_idcours = C.id_cours
        JOIN Personnes P ON Co.id_personne = P.id_personne
        WHERE Co.id_personne = ?
    """, (user_id,))
    existing_course = cursor.fetchone()

    # Création ou modification du cours
    if request.method == 'POST':
        # Récupération des données envoyées par le formulaire
        description = request.form.get('description', '').strip()
        tarif = request.form.get('tarif', '').strip()
        disponibilites = request.form.getlist('disponibilite')
        disponibilites_str = ",".join(disponibilites)
        canton = request.form.get('canton', '').strip()
        ville = request.form.get('ville', '').strip()
        langue = request.form.get('langue', '').strip()
        apropos = request.form.get('apropos', '').strip()

        # Validation des données
        if not tarif or not tarif.isdigit():
            flash("Le tarif doit être un nombre valide.", "error")
            return redirect(url_for('coach.create_course'))

        tarif = int(tarif)

        try:
            if existing_course:
                # Mise à jour du cours existant
                cursor.execute("""
                    UPDATE Cours 
                    SET description = ?, tarif = ?, disponibilites = ? 
                    WHERE id_cours = ?
                """, (description, tarif, disponibilites_str, existing_course['id_cours']))

                # Mise à jour des informations du coach
                cursor.execute("""
                    UPDATE Personnes 
                    SET canton = ?, ville = ?, langue = ?
                    WHERE id_personne = ?
                """, (canton, ville, langue, user_id))

                cursor.execute("""
                    UPDATE Coachs 
                    SET biographie = ? 
                    WHERE id_personne = ?
                """, (apropos, user_id))
                flash("Cours modifié avec succès!", "success")
                action = 'modified'
            else:
                # Création d'un nouveau cours
                cursor.execute("""
                    INSERT INTO Cours (description, tarif, disponibilites) 
                    VALUES (?, ?, ?)
                """, (description, tarif, disponibilites_str))
                cours_id = cursor.lastrowid

                cursor.execute("""
                    UPDATE Coachs 
                    SET FK_idcours = ? 
                    WHERE id_personne = ?
                """, (cours_id, user_id))

                cursor.execute("""
                    UPDATE Personnes 
                    SET canton = ?, ville = ?, langue = ? 
                    WHERE id_personne = ?
                """, (canton, ville, langue, user_id))

                cursor.execute("""
                    UPDATE Coachs 
                    SET biographie = ? 
                    WHERE id_personne = ?
                """, (apropos, user_id))
                flash("Cours créé avec succès!", "success")
                action = 'created'

            db.commit()

            # Utilisation de g pour stocker l'information que le coach a un cours
            g.has_course = True  # Enregistre cette information dans g

        except Exception as e:
            print(f"Erreur : {e}")
            db.rollback()
            flash("Une erreur est survenue.", "error")
            close_db()
            return redirect(request.url)

        return redirect(url_for('coach.confirmation', action=action))

    # Si un cours existe, transmettre ses détails au gabarit
    data = {
        'description': existing_course['description'] if existing_course else '',
        'tarif': existing_course['tarif'] if existing_course else '',
        'disponibilites': existing_course['disponibilites'].split(',') if existing_course else [],
        'canton': existing_course['canton'] if existing_course else '',
        'ville': existing_course['ville'] if existing_course else '',
        'langue': existing_course['langue'] if existing_course else '',
        'apropos': existing_course['biographie'] if existing_course else ''
    }

    return render_template('coach/create_course.html', chemin_image=g.chemin_image, role=g.role, data=data, has_course= g.has_course)







@coach_bp.route('/confirmation')
def confirmation():
    return render_template('coach/confirmation.html')


