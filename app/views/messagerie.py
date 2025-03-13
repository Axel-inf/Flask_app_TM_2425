from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
from datetime import datetime, timedelta

messagerie_bp = Blueprint('messagerie', __name__, url_prefix='/messagerie')

@messagerie_bp.route('/discussion/<int:coach_id>', methods=['POST'])
def envoyer_message(coach_id):
    user_id = session.get('user_id')
    contenu = request.form.get('envoie-message')

    print(f"DEBUG: user_id={user_id}, coach_id={coach_id}, contenu={contenu}")

    if not user_id or not contenu:
        return redirect(url_for('messagerie.discussion', coach_id=coach_id))

    db = get_db()
    cursor = db.cursor()

    # Récupérer le prochain id_message
    cursor.execute("""
        SELECT COALESCE(MAX(id_message), 0) + 1 
        FROM Messagerie 
        WHERE FK_idpersonneclient = ? AND FK_idpersonnecoach = ?
    """, (user_id, coach_id))
    id_message = cursor.fetchone()[0]

    try:
        cursor.execute("""
            INSERT INTO Messagerie (FK_idpersonneclient, FK_idpersonnecoach, id_message, date, message)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, coach_id, id_message, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), contenu))
        db.commit()

    except Exception as e:
        print(f"📩 ERROR: {e}")

    close_db()

    return redirect(url_for('messagerie.discussion', coach_id=coach_id))



@messagerie_bp.route('/discussion', methods=['GET', 'POST'])
@messagerie_bp.route('/discussion/<int:coach_id>', methods=['GET', 'POST'])
def discussion(coach_id=None):
    user_id = session.get('user_id')
    g.chemin_image = get_profile_image(user_id)

    if not user_id:
        return redirect(url_for('auth.login'))

    db = get_db()
    cursor = db.cursor()

    # ✅ Si c'est un POST, récupérer coach_id depuis le formulaire
    if request.method == 'POST':
        form_coach_id = request.form.get('coach_id')
        if form_coach_id:
            coach_id = int(form_coach_id)  # Remplace l'ID dans l'URL si nécessaire
        message_contenu = request.form.get('envoie-message')
        
        if message_contenu and coach_id:
            cursor.execute("""
                INSERT INTO Messagerie (FK_idpersonneclient, FK_idpersonnecoach, date, message)
                VALUES (?, ?, datetime('now'), ?)""", (user_id, coach_id, message_contenu))
            db.commit()

    # 🔹 Récupérer les messages de la discussion
    messages = []
    coach_nom = None
    coach_prenom = None
    coach_image = None

    if coach_id:
        cursor.execute("""SELECT p.prenom, p.nom, p.chemin_vers_image FROM Personnes p WHERE p.id_personne = ?""", (coach_id,))
        coach_details = cursor.fetchone()

        if coach_details:
            coach_prenom, coach_nom, coach_image = coach_details

            cursor.execute("""SELECT FK_idpersonneclient, FK_idpersonnecoach, id_message, date, message FROM Messagerie
                              WHERE (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?) OR 
                                    (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?) 
                              ORDER BY date""", (user_id, coach_id, coach_id, user_id))
            messages = cursor.fetchall()

    # ✅ Récupérer les discussions existantes
    cursor.execute("""
        SELECT DISTINCT FK_idpersonnecoach FROM Messagerie WHERE FK_idpersonneclient = ?
        UNION
        SELECT DISTINCT FK_idpersonneclient FROM Messagerie WHERE FK_idpersonnecoach = ?
    """, (user_id, user_id))

    coach_ids = cursor.fetchall()

    coaches = []
    for contact_tuple in coach_ids:
        contact_id = contact_tuple[0]

        cursor.execute("""
            SELECT p.prenom, p.nom, p.chemin_vers_image, 
                (SELECT message FROM Messagerie 
                    WHERE (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?) OR 
                        (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?) 
                    ORDER BY date DESC LIMIT 1) AS dernier_message,
                (SELECT date FROM Messagerie 
                    WHERE (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?) OR 
                        (FK_idpersonneclient = ? AND FK_idpersonnecoach = ?) 
                    ORDER BY date DESC LIMIT 1) AS derniere_date_message
            FROM Personnes p 
            WHERE p.id_personne = ?
        """, (user_id, contact_id, contact_id, user_id, contact_id, contact_id, user_id, contact_id, user_id))

        coach_details = cursor.fetchone()

        if coach_details:
            coaches.append({
                'coach_id': contact_id,
                'prenom': coach_details[0],
                'nom': coach_details[1],
                'chemin_vers_image': coach_details[2],
                'dernier_message': coach_details[3] if coach_details[3] else "Aucun message",
                'derniere_date_message': coach_details[4]  # Ajout de la date
            })
            print(coaches)



    db.commit()
    close_db()

    return render_template('messagerie/discussion.html', 
                       messages=messages, 
                       coach_nom=coach_nom, 
                       coach_id=coach_id, 
                       profile_image=g.chemin_image, 
                       coach_image=coach_image, 
                       coach_prenom=coach_prenom, 
                       current_date=datetime.now(), 
                       timedelta=timedelta, 
                       coaches=coaches,
                       user_id=user_id)
