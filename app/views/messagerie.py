from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
from datetime import datetime

messagerie_bp = Blueprint('messagerie', __name__, url_prefix='/messagerie')


from datetime import datetime

@messagerie_bp.route('/discussion', methods=['GET', 'POST'])
@messagerie_bp.route('/discussion/<int:coach_id>', methods=['GET', 'POST'])
def discussion(coach_id=None):
    user_id = session.get('user_id')
    g.chemin_image = get_profile_image(user_id)
    
    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    # Si coach_id est présent dans l'URL, cela signifie que l'on veut discuter avec ce coach spécifique
    if coach_id:
        # Vérifier si une discussion existe déjà avec ce coach
        cursor.execute("""
            SELECT p.prenom, p.nom, p.chemin_vers_image
            FROM Personnes p
            WHERE p.id_personne = ?
        """, (coach_id,))
        coach_details = cursor.fetchone()

        if coach_details is None:
            return render_template('error.html', message="Coach non trouvé")

        coach_prenom = coach_details[0]
        coach_nom = coach_details[1]
        coach_image = coach_details[2]  # Récupérer le chemin de l'image du coach
        
        # Récupérer tous les messages entre l'utilisateur et ce coach
        cursor.execute("""
            SELECT FK_idpersonneclient, FK_idpersonnecoach, id_message, date, message
            FROM Messagerie
            WHERE (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?)
               OR (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?)
            ORDER BY date
        """, (user_id, coach_id, coach_id, user_id))
        messages = cursor.fetchall()
        
        db.commit()
        close_db()

        return render_template('messagerie/discussion.html', 
                               messages=messages, 
                               coach_nom=coach_nom, 
                               coach_id=coach_id, 
                               profile_image=g.chemin_image, 
                               coach_image=coach_image, coach_prenom=coach_prenom)

    else:
        # Si coach_id n'est pas présent, on charge toutes les discussions de l'utilisateur
        cursor.execute("""
            SELECT DISTINCT FK_idpersonnecoach
            FROM Messagerie
            WHERE FK_idpersonneclient = ?
        """, (user_id,))
        coach_ids = cursor.fetchall()

        if not coach_ids:
            # Aucun coach trouvé dans les discussions, afficher un message spécial
            return render_template('messagerie/discussion.html', message="Aucune discussion en cours")

        # Récupérer les informations des coaches dans les discussions
        coaches = []
        for coach_id in coach_ids:
            cursor.execute("""
                SELECT p.nom, p.chemin_vers_image
                FROM Personnes p
                WHERE p.id_personne = ?
            """, (coach_id[0],))
            coach_details = cursor.fetchone()
            if coach_details:
                coaches.append({'coach_id': coach_id[0], 'nom': coach_details[0], 'chemin_vers_image': coach_details[1]})

        db.commit()
        close_db()

        return render_template('messagerie/discussion.html', coaches=coaches, profile_image=g.chemin_image)


@messagerie_bp.route('/discussion', methods=['POST'])
@messagerie_bp.route('/discussion/<int:coach_id>', methods=['POST'])
def envoyer_message(coach_id=None):
    user_id = session.get('user_id')
    contenu = request.form.get('envoie-message')
    g.chemin_image = get_profile_image(user_id)

    if not user_id or not contenu:
        return redirect(url_for('messagerie.discussion', coach_id=coach_id))

    # Connexion à la base de données
    db = get_db()
    cursor = db.cursor()

    # Récupérer le prochain id_message
    cursor.execute("""
        SELECT COALESCE(MAX(id_message), 0) + 1 
        FROM Messagerie 
        WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ?
    """, (user_id, coach_id))
    id_message = cursor.fetchone()[0]

    # Insérer le message dans la table Messagerie
    cursor.execute("""
        INSERT INTO Messagerie (FK_idpersonneclient, FK_idpersonnecoach, id_message, date, message)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, coach_id, id_message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), contenu))

    db.commit()
    close_db()


    return redirect(url_for('messagerie.discussion', coach_id=coach_id))


