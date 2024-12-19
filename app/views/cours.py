from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
from datetime import datetime


# Définir le blueprint
cours_bp = Blueprint('cours', __name__)


# Définir la fonction `load_logged_in_user` en haut
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

# Utiliser `before_request`
@cours_bp.before_request
def before_request():
    load_logged_in_user()

@cours_bp.route('/recherche', methods=['GET', 'POST'])
def recherche():
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
        params.extend([f'%{search_query}%', f'%{search_query}%',f'%{search_query}%', f'%{search_query}%'])

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
    close_db()

    return render_template('cours/recherche.html', coachs=coachs, profile_image=g.chemin_image, role=g.role)





@cours_bp.route('/en_savoir_plus/<int:coach_id>', methods=['GET'])
def en_savoir_plus(coach_id):
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

    # Requête pour récupérer les coachs similaires
    coachs_similaires = db.execute("""
        SELECT Personnes.*, Coachs.*, Cours.tarif
        FROM Personnes
        JOIN Coachs ON Personnes.id_personne = Coachs.id_personne
        JOIN Cours ON Coachs.FK_idcours = Cours.id_cours
        WHERE Personnes.langue = ? AND Personnes.id_personne != ?
    """, (coach['langue'], coach_id)).fetchall()

    close_db()

    if not coach:
        flash("Coach non trouvé.", "error")
        return redirect(url_for('cours.recherche'))

    # Passer les informations du cours au template
    return render_template('cours/en_savoir_plus.html', coach=coach, coachs=coachs_similaires, cours=coach)


@cours_bp.route('/donner_avis/<int:coach_id>/<nom>/<prenom>', methods=['GET', 'POST'])
def donner_avis(coach_id, nom, prenom):
    if request.method == 'GET':
        # Méthode GET : Affiche la page pour donner un avis
        return render_template('cours/donner_avis.html', coach_id=coach_id, nom=nom, prenom=prenom)
    
    if request.method == 'POST':
        # Méthode POST : Traite et insère l'avis dans la base de données
        commentaire = request.form.get('commentaire')
        note = int(request.form.get('note', 0))
        date_envoi = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Date au format AAAA-MM-JJ HH:MM:SS

        client_id = session.get('user_id')  # ID de l'utilisateur connecté

        # Validation des données
        if not commentaire or note < 0 or note > 5:
            flash("Veuillez fournir un commentaire valide et une note entre 0 et 5.", "error")
            return redirect(url_for('cours.donner_avis', coach_id=coach_id, nom=nom, prenom=prenom))

        # Connexion à la base de données
        db = get_db()
        cursor = db.cursor()

        # Insérer l'avis dans la base de données avec la date
        cursor.execute("""
        INSERT INTO Evaluer (FK_idpersonneclient, FK_idpersonnecoach, date, commentaire, note)
        VALUES (?, ?, ?, ?, ?)
        """, (client_id, coach_id, date_envoi, commentaire, note))

        db.commit()

        flash("Votre avis a été enregistré avec succès.", "success")
        return redirect(url_for('cours.en_savoir_plus', coach_id=coach_id))



