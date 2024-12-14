from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from app.db.db import get_db, close_db
from app.utils import get_profile_image
import os

# Création d'un blueprint contenant les routes ayant le préfixe /auth/...
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Route /auth/register
@auth_bp.route('/register', methods=('GET', 'POST'))
def register():

    # Si des données de formulaire sont envoyées vers la route /register (ce qui est le cas lorsque le formulaire d'inscription est envoyé)
    if request.method == 'POST':

        # On récupère les champs 'prenom' , 'nom', 'email' et 'mot_de_passe' de la requête HTTP
        prenom = request.form['prenom']
        nom = request.form['nom']
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        role = request.form['role']
        print(request.form)
        print(role)

        # On récupère la base de donnée
        db = get_db()
        curseur = db.cursor()

        # Si l'email et le mot de passe ont bien une valeur
        # on essaie d'insérer l'utilisateur dans la base de données
        if prenom and nom and email and mot_de_passe:
            try:
                curseur.execute("INSERT INTO Personnes (prenom, nom, email, mot_de_passe) VALUES (?, ?, ?, ?)",(prenom, nom, email, generate_password_hash(mot_de_passe)))
                # db.commit() permet de valider une modification de la base de données
               
                
                if role == "coach":
                    db.execute("INSERT INTO Coachs (id_personne) VALUES (?)",(curseur.lastrowid,))
                else:
                    db.execute("INSERT INTO Clients (id_personne) VALUES (?)",(curseur.lastrowid,))
                    
                db.commit()
                 
                # On ferme la connexion à la base de données pour éviter les fuites de mémoire
                close_db()



            except db.IntegrityError:

                # La fonction flash dans Flask est utilisée pour stocker un message dans la session de l'utilisateur
                # dans le but de l'afficher ultérieurement, généralement sur la page suivante après une redirection
                error = f"Utilisateur avec l'adresse {email} déjà enregistré."
                flash(error)
                return redirect(url_for("auth.register"))

            return redirect(url_for("auth.login"))

        else:
            error = "Email ou mot de passe invalide"
            flash(error)
            return redirect(url_for("auth.login"))
    else:
        # Si aucune donnée de formulaire n'est envoyée, on affiche le formulaire d'inscription
        return render_template('auth/register.html')

# Route /auth/login
@auth_bp.route('/login', methods=('GET', 'POST'))
def login():
    # Si des données de formulaire sont envoyées vers la route /login (ce qui est le cas lorsque le formulaire de login est envoyé)
    if request.method == 'POST':

        # On récupère les champs 'email' et 'mot_de_passe' de la requête HTTP
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        

        # On récupère la base de données
        db = get_db()

        # On récupère l'utilisateur avec l'email spécifié (une contrainte dans la db indique que l'email est unique)
        # La virgule après username est utilisée pour créer un tuple contenant une valeur unique
        user = db.execute('SELECT * FROM Personnes WHERE email = (?)', (email,)).fetchone()

        # On ferme la connexion à la base de données pour éviter les fuites de mémoire
        close_db()

        # Si aucun utilisateur n'est trouve ou si le mot de passe est incorrect
        # on crée une variable error 
        error = None
        if user is None:
            error = "Email incorrect"
        elif not check_password_hash(user['mot_de_passe'], mot_de_passe):
            error = "Mot de passe incorrect"

        # S'il n'y pas d'erreur, on ajoute l'id de l'utilisateur dans une variable de session
        # De cette manière, à chaque requête de l'utilisateur, on pourra récupérer l'id dans le cookie session
        if error is None:
            session.clear()
            session['user_id'] = user['id_personne']
            # On redirige l'utilisateur vers la page de validation de connexion une fois qu'il s'est connecté
            return redirect(url_for('auth.validation_connexion'))

        else:
            # En cas d'erreur, on ajoute l'erreur dans la session et on redirige l'utilisateur vers le formulaire de login
            flash(error)
            return redirect(url_for("auth.login"))
    else:
        return render_template('auth/login.html')

# Route /auth/logout
@auth_bp.route('/logout')
def logout():
    # Se déconnecter consiste simplement à supprimer le cookie session
    session.clear()

    # On redirige l'utilisateur vers la page principale une fois qu'il s'est déconnecté
    return redirect("/")


# Fonction automatiquement appelée à chaque requête (avant d'entrer dans la route) sur une route appartenant au blueprint 'auth_bp'
# La fonction permet d'ajouter un attribut 'user' représentant l'utilisateur connecté dans l'objet 'g' 
@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
        g.chemin_image = None
    else:
        db = get_db()
        g.user = db.execute('SELECT * FROM Personnes WHERE id_personne = ?', (user_id,)).fetchone()

        userrole = db.execute('SELECT * FROM Coachs WHERE id_personne = ?', (user_id,)).fetchone()
        g.role = "Coach" if userrole else "Joueur"
        course = db.execute("""
            SELECT id_cours 
            FROM Coachs Co
            JOIN Cours C ON Co.FK_idcours = C.id_cours
            WHERE Co.id_personne = ?
        """, (user_id,)).fetchone()

        # Définir g.has_course en fonction de l'existence du cours
        g.has_course = True if course else None

        # Utiliser la fonction utilitaire pour obtenir le chemin de l'image
        g.chemin_image = get_profile_image(user_id)
        print(f"Chemin de l'image de profil: {g.chemin_image}")  # Log de débogage
        close_db()




@auth_bp.route('/validation_connexion')
def validation_connexion():
    return render_template('auth/validation_connexion.html')
