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
        SELECT Personnes.*, Coachs.*, Cours.tarif
        FROM Personnes
        JOIN Coachs ON Personnes.id_personne = Coachs.id_personne
        JOIN Cours ON Coachs.FK_idcours = Cours.id_cours
        WHERE Personnes.langue = ? AND Personnes.id_personne != ?
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


@cours_bp.route('/cours/modifier_avis/<int:coach_id>', methods=['POST'])
def modifier_avis(coach_id):
    # Récupérer les données transmises depuis le formulaire
    commentaire = request.form.get('commentaire')
    note = request.form.get('note')
    date = request.form.get('date')  # Date de l'avis existant

    if not commentaire or not note or not date:
        flash("Tous les champs sont obligatoires pour modifier l'avis.", "error")
        return redirect(url_for('cours.en_savoir_plus', coach_id=coach_id))

    try:
        db = get_db()
        cursor = db.cursor()

        # On vérifie si l'avis existe et appartient à l'utilisateur connecté
        existing_review = cursor.execute("""
            SELECT * 
            FROM Evaluer 
            WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
        """, (g.user['id_personne'], coach_id, date)).fetchone()

        if existing_review:
            # Mise à jour de l'avis existant
            cursor.execute("""
                UPDATE Evaluer
                SET commentaire = ?, note = ?
                WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
            """, (commentaire, note, g.user['id_personne'], coach_id, date))
            flash("Avis modifié avec succès.", "success")
        else:
            flash("Avis introuvable ou non autorisé.", "error")

        db.commit()
    except Exception as e:
        flash(f"Une erreur s'est produite lors de la modification de l'avis : {e}", "error")
    finally:
        close_db()

    return redirect(url_for('cours.en_savoir_plus', coach_id=coach_id))


@cours_bp.route('/cours/supprimer_avis/<int:coach_id>', methods=['POST'])
def supprimer_avis(coach_id):
    # Récupérer la date de l'avis à supprimer
    date = request.form.get('date')

    if not date:
        flash("La date de l'avis est requise pour supprimer l'avis.", "error")
        return redirect(url_for('cours.en_savoir_plus', coach_id=coach_id))

    try:
        db = get_db()
        cursor = db.cursor()

        # On vérifife si l'avis existe et appartient à l'utilisateur connecté
        existing_review = cursor.execute("""
            SELECT * 
            FROM Evaluer 
            WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
        """, (g.user['id_personne'], coach_id, date)).fetchone()

        if existing_review:
            # Suppression de l'avis
            cursor.execute("""
                DELETE FROM Evaluer
                WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ? AND date = ?
            """, (g.user['id_personne'], coach_id, date))
            flash("Avis supprimé avec succès.", "success")
        else:
            flash("Avis introuvable ou non autorisé.", "error")

        db.commit()
    except Exception as e:
        flash(f"Une erreur s'est produite lors de la suppression de l'avis : {e}", "error")
    finally:
        close_db()

    return redirect(url_for('cours.en_savoir_plus', coach_id=coach_id))


@cours_bp.route('/donner_avis/<int:coach_id>', methods=['GET', 'POST'])
def donner_avis(coach_id):
    # Vérifier si l'utilisateur est connecté
    if not g.user:
        return redirect(url_for('home.landing_page'))

    # Connexion à la base de données
    db = get_db()
    cursor = db.cursor()

    # Vérifier si l'utilisateur a déjà donné un avis pour ce coach
    cursor.execute("""
        SELECT * 
        FROM Evaluer
        WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ?
    """, (g.user['id_personne'], coach_id))
    existing_review = cursor.fetchone()

    if request.method == 'POST':
        # Récupérer les données envoyées par le formulaire
        note = request.form.get('note')
        commentaire = request.form.get('commentaire')

        if not note or not commentaire:
            flash("La note et le commentaire sont obligatoires.", "error")
            return redirect(url_for('cours.donner_avis', coach_id=coach_id))

        try:
            if existing_review:
                # Mettre à jour l'avis existant
                cursor.execute("""
                    UPDATE Evaluer
                    SET note = ?, commentaire = ?
                    WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ?
                """, (note, commentaire, g.user['id_personne'], coach_id))
                flash("Avis modifié avec succès!", "success")
            else:
                # Créer un nouvel avis
                cursor.execute("""
                    INSERT INTO Evaluer (FK_idpersonneclient, FK_idpersonnecoach, note, commentaire)
                    VALUES (?, ?, ?, ?)
                """, (g.user['id_personne'], coach_id, note, commentaire))
                flash("Avis ajouté avec succès!", "success")

            db.commit()

        except Exception as e:
            flash(f"Erreur lors de l'enregistrement de l'avis : {e}", "error")
            db.rollback()
        finally:
            close_db()

        return redirect(url_for('cours.validation_avis', coach_id=coach_id))

    # Si un avis existe, transmettre ses détails au gabarit
    review_data = {
        'note': existing_review['note'] if existing_review else '',
        'commentaire': existing_review['commentaire'] if existing_review else ''
    }

    return render_template('cours/donner_avis.html', coach_id=coach_id, review_data=review_data)



@cours_bp.route('/validation_avis/<int:coach_id>')
def validation_avis(coach_id):
    return render_template('cours/validation_avis.html', coach_id=coach_id)
