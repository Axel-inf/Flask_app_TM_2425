from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)

# Routes /...
coach_bp = Blueprint('coach', __name__, url_prefix='/coach')



@coach_bp.route('/', methods=['GET', 'POST'])
def landing_page():
    # Débogage : vérifier g.user
    print(f"Valeur de g.user : {g.user}")

    # Si l'utilisateur n'est pas connecté, rediriger vers l'accueil
    if not g.user:
        return redirect(url_for('home.landing_page'))

    # Sinon, afficher la page de création de cours
    return render_template('coach/create_course.html', chemin_image=g.chemin_image, role=g.role)
