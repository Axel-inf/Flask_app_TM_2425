from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image


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

# Définir la route `recherche`
@cours_bp.route('/recherche', methods=['GET', 'POST'])
def recherche():
    if g.user:
        db = get_db()
        cursor = db.cursor()

        # Récupérer les coachs ayant proposé des cours
        cursor.execute(
            """
            SELECT p.chemin_vers_image, p.nom, p.prenom, p.ville, c.tarif, p.langue
            FROM Coachs co
            JOIN Personnes p ON co.id_personne = p.id_personne
            JOIN Cours c ON co.FK_idcours = c.id_cours
            WHERE co.FK_idcours IS NOT NULL
            """
        )
        results = cursor.fetchall()
        close_db()

        return render_template('cours/recherche.html', coachs=results, profile_image=g.chemin_image, role=g.role)
            
    else:
        print("Redirection vers la page d'accueil")
        return render_template('home/index.html')
