from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
from datetime import datetime


cours_bp = Blueprint('cours', __name__)


def load_logged_in_user():
    user_id = session.get('user_id')
    print(f"user_id: {user_id}")
    if user_id is None:
        g.user = None
        g.chemin_image = None
        g.role = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM Personnes WHERE id_personne = ?', (user_id,)).fetchone()
        print(f"g.user: {g.user}")
        userrole = db.execute('SELECT * FROM Coachs WHERE id_personne = ?', (user_id,)).fetchone()
        g.role = "Coach" if userrole else "Joueur"
        g.chemin_image = get_profile_image(user_id)
        print(f"g.role: {g.role}, g.chemin_image: {g.chemin_image}")
        close_db()

@cours_bp.before_request
def before_request():
    load_logged_in_user()

@cours_bp.route('/recherche', methods=['GET', 'POST'])
def recherche():
    if not g.get('user'):
        return redirect(url_for('auth.login'))
    search_query = request.form.get('search_query', '').strip().lower()
    filtre_tarif_min = request.form.get('filtre_tarif_min', '').strip()
    filtre_tarif_max = request.form.get('filtre_tarif_max', '').strip()
    filtre_region = request.form.getlist('region')
    filtre_langue = request.form.getlist('langue')
    
    # Connexion à la base de données
    db = get_db()
    cursor = db.cursor()

    # Construction de la requête SQL avec les filtres
    query = """
        SELECT Personnes.*, Coachs.*, Cours.description, Cours.tarif, Cours.disponibilites
        FROM Personnes
        JOIN Coachs ON Personnes.id_personne = Coachs.id_personne
        JOIN Cours ON Coachs.FK_idcours = Cours.id_cours
        WHERE Coachs.FK_idcours IS NOT NULL
    """
    params = []

    if search_query:
        query += " AND (LOWER(Personnes.nom) LIKE ? OR LOWER(Personnes.prenom) LIKE ? OR LOWER(Personnes.ville) LIKE ? OR LOWER(Personnes.canton) LIKE ?)"
        params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])

    if filtre_tarif_min and filtre_tarif_max:
        query += " AND Cours.tarif BETWEEN ? AND ?"
        params.extend([filtre_tarif_min, filtre_tarif_max])

    if filtre_region:
        query += " AND Personnes.canton IN ({})".format(','.join('?' for _ in filtre_region))
        params.extend(filtre_region)

    if filtre_langue:
        query += " AND Personnes.langue IN ({})".format(','.join('?' for _ in filtre_langue))
        params.extend(filtre_langue)

    cursor.execute(query, params)
    coachs = cursor.fetchall()

    # Récupérer les moyennes des notes pour chaque coach
    coachs_with_ratings = []
    for coach in coachs:
        coach_id = coach['id_personne']
        moyenne_note = db.execute("""
            SELECT AVG(Evaluer.note) as moyenne
            FROM Evaluer
            WHERE Evaluer.FK_idpersonnecoach = ?
        """, (coach_id,)).fetchone()['moyenne']
        
        # Si aucune note n'est trouvée, on met la moyenne à 0
        if moyenne_note is None:
            moyenne_note = 0
        
        coachs_with_ratings.append({
            **coach,
            'moyenne_note': moyenne_note  # Ajout de la moyenne au coach
        })

    close_db()

    return render_template('cours/recherche.html', coachs=coachs_with_ratings, profile_image=g.chemin_image, role=g.role)




@cours_bp.route('/en_savoir_plus/<int:coach_id>', methods=['GET', 'POST'])
def en_savoir_plus(coach_id):
    # Redirige vers la page de connexion si l'utilisateur n'est pas connecté
    if not g.get('user'):
        return redirect(url_for('auth.login'))

    # Connexion à la base de données
    db = get_db()
    cursor = db.cursor()

    # Requête pour récupérer les détails du coach et du cours
    cursor.execute("""
        SELECT Personnes.*, Coachs.*, Cours.*
        FROM Personnes
        JOIN Coachs ON Personnes.id_personne = Coachs.id_personne
        JOIN Cours ON Coachs.FK_idcours = Cours.id_cours
        WHERE Personnes.id_personne = ?
    """, (coach_id,))
    coach = cursor.fetchone()

    # Si le coach n'est pas trouvé, rediriger avec un message d'erreur
    if not coach:
        flash("Coach non trouvé.", "error")
        return redirect(url_for('cours.recherche'))

    # Requête pour récupérer les coachs similaires
    coachs_similaires = db.execute("""
    SELECT 
        Personnes.*, 
        Coachs.*, 
        Cours.tarif,
        AVG(Evaluer.note) AS moyenne_note
        FROM Personnes
        JOIN Coachs ON Personnes.id_personne = Coachs.id_personne
        JOIN Cours ON Coachs.FK_idcours = Cours.id_cours
        LEFT JOIN Evaluer ON Evaluer.FK_idpersonnecoach = Coachs.id_personne
        WHERE Personnes.langue = ? AND Personnes.id_personne != ?
        GROUP BY Personnes.id_personne, Coachs.id_personne, Cours.tarif
    """, (coach['langue'], coach_id)).fetchall()


    # Requête pour récupérer les avis du coach
    commentaires = db.execute("""
        SELECT Evaluer.commentaire, Evaluer.note, Evaluer.date, 
               Personnes.nom, Personnes.prenom, Personnes.chemin_vers_image, 
               Evaluer.FK_idpersonneclient
        FROM Evaluer
        JOIN Personnes ON Evaluer.FK_idpersonneclient = Personnes.id_personne
        WHERE Evaluer.FK_idpersonnecoach = ?
        ORDER BY Evaluer.date DESC
    """, (coach_id,)).fetchall()

    # Requête pour calculer la moyenne des notes
    moyenne_note = db.execute("""
        SELECT AVG(Evaluer.note) as moyenne
        FROM Evaluer
        WHERE Evaluer.FK_idpersonnecoach = ?
    """, (coach_id,)).fetchone()['moyenne']

    # Si la méthode est POST, traiter une action (modifier ou supprimer)
    if request.method == 'POST':
        action = request.form.get('action')
        client_id = g.user['id_personne']
        date = request.form.get('date')

        # Modifier un avis
        if action == 'modifier':
            nouvelle_note = request.form.get('note')
            nouveau_commentaire = request.form.get('commentaire')
            db.execute("""
                UPDATE Evaluer
                SET note = ?, commentaire = ?
                WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
            """, (nouvelle_note, nouveau_commentaire, client_id, coach_id, date))
            db.commit()
            flash("Votre avis a été mis à jour.", "success")
        
        # Supprimer un avis
        elif action == 'supprimer':
            db.execute("""
                DELETE FROM Evaluer
                WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
            """, (client_id, coach_id, date))
            db.commit()
            flash("Votre avis a été supprimé.", "success")

        return redirect(url_for('cours.en_savoir_plus', coach_id=coach_id))

    close_db()

    # Rendu du template avec les données nécessaires
    return render_template(
        'cours/en_savoir_plus.html',
        coach=coach,
        coachs=coachs_similaires,
        cours=coach,
        commentaires=commentaires,
        moyenne_note=moyenne_note,
        user_id=g.user['id_personne']  # Passe l'ID de l'utilisateur connecté
    )


@cours_bp.route('/donner_avis/<int:coach_id>', methods=['GET', 'POST']) 
def donner_avis(coach_id):
    if not g.user:
        return redirect(url_for('home.landing_page'))

    db = get_db()
    cursor = db.cursor()

    # Récupérer les informations du coach
    cursor.execute("""
        SELECT * 
        FROM Personnes
        WHERE id_personne = ?
    """, (coach_id,))
    coach = cursor.fetchone()

    if not coach:
        flash("Coach introuvable.", "error")
        return redirect(url_for('cours.recherche'))

    # Récupérer l'avis existant (s'il existe)
    cursor.execute("""
        SELECT * 
        FROM Evaluer
        WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ?
        ORDER BY date DESC LIMIT 1
    """, (g.user['id_personne'], coach_id))
    existing_review = cursor.fetchone()

    # Pré-remplir les données uniquement si l'action est "modifier"
    if request.args.get('action') == 'modifier' and existing_review:
        review_data = {
            'note': existing_review['note'],
            'commentaire': existing_review['commentaire'],
            'date': existing_review['date']
        }
        is_edit = True
    else:
        # Sinon, le formulaire est vide pour un ajout
        review_data = {
            'note': '',
            'commentaire': '',
            'date': ''
        }
        is_edit = False

    if request.method == 'POST':
        action = request.form.get('action')
        note = request.form.get('note')
        commentaire = request.form.get('commentaire')

        # Suppression d'un avis
        if action == 'supprimer' and existing_review:
            try:
                cursor.execute("""
                    DELETE FROM Evaluer
                    WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
                """, (g.user['id_personne'], coach_id, existing_review['date']))
                db.commit()
                flash("Votre avis a été supprimé avec succès.", "success")
            except Exception as e:
                flash(f"Erreur lors de la suppression de l'avis : {e}", "error")
                db.rollback()
            finally:
                close_db()
            return redirect(url_for('cours.en_savoir_plus', coach_id=coach_id))

        # Modification d'un avis existant
        elif action == 'modifier' and existing_review:
            if not note or not commentaire:
                flash("La note et le commentaire sont obligatoires.", "error")
                return redirect(url_for('cours.donner_avis', coach_id=coach_id))

            try:
                cursor.execute("""
                    UPDATE Evaluer
                    SET note = ?, commentaire = ?, date = datetime('now')
                    WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
                """, (note, commentaire, g.user['id_personne'], coach_id, existing_review['date']))
                db.commit()
                flash("Votre avis a été modifié avec succès.", "success")
            except Exception as e:
                flash(f"Erreur lors de la modification de l'avis : {e}", "error")
                db.rollback()
            finally:
                close_db()
            return redirect(url_for('cours.validation_avis', coach_id=coach_id))

        # Ajout d'un nouvel avis
        elif action == 'ajouter':
            if not note or not commentaire:
                flash("La note et le commentaire sont obligatoires.", "error")
                return redirect(url_for('cours.donner_avis', coach_id=coach_id))

            try:
                # Ajouter un nouvel avis sans toucher aux précédents
                cursor.execute("""
                    INSERT INTO Evaluer (FK_idpersonneclient, FK_idpersonnecoach, note, commentaire, date)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (g.user['id_personne'], coach_id, note, commentaire))
                db.commit()
                flash("Votre avis a été ajouté avec succès.", "success")
            except Exception as e:
                flash(f"Erreur lors de l'ajout de l'avis : {e}", "error")
                db.rollback()
            finally:
                close_db()

            return redirect(url_for('cours.validation_avis', coach_id=coach_id))

    return render_template(
        'cours/donner_avis.html',
        coach_id=coach_id,
        review_data=review_data,  # Affichage des données de l'avis existant ou vide pour un ajout
        is_edit=is_edit,  # Indique si l'on est en mode modification ou ajout
        coach=coach
    )













@cours_bp.route('/validation_avis/<int:coach_id>')
def validation_avis(coach_id):
    return render_template('cours/validation_avis.html', coach_id=coach_id)