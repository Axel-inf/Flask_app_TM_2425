import os
from flask import Flask
from app.utils import *
from app.email.email import send_email

# Importation des blueprints de l'application
# Chaque blueprint contient des routes pour l'application
from app.views.home import home_bp
from app.views.auth import auth_bp
from app.views.user import user_bp
from app.views.coach import coach_bp
from app.views.cours import cours_bp
from app.views.messagerie import messagerie_bp
from app.views.password import password_bp
from app.views.legal import legal_bp
from app.views.sitemap import sitemap_bp

# Fonction automatiquement appelée par le framework Flask lors de l'exécution de la commande python -m flask run permettant de lancer le projet
# La fonction retourne une instance de l'application créée
def create_app():
    
    # Crée l'application Flask
    app = Flask(__name__)

    # Chargement des variables de configuration stockées dans le fichier config.py
    app.config.from_pyfile(os.path.join(os.path.dirname(__file__), "config.py"))

    # Enreigstrement des blueprints de l'application.
    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(cours_bp)
    app.register_blueprint(messagerie_bp)
    app.register_blueprint(password_bp)
    app.register_blueprint(legal_bp)
    app.register_blueprint(sitemap_bp)

    # Route spéciale pour la validation Google Search Console
    @app.route('/google4e21d2c8476bb15e.html')
    def google_verification():
        return app.send_static_file('google4e21d2c8476bb15e.html')


    

    # On retourne l'instance de l'application Flask
    return app
