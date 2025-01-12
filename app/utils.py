import functools
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, Blueprint
from werkzeug.utils import secure_filename
import os
import sqlite3
from app.db.db import get_db, close_db

# Ce décorateur est utilisé dans l'application Flask pour protéger certaines vues (routes)
# afin de s'assurer qu'un utilisateur est connecté avant d'accéder à une route 

def login_required(view):
    
    @functools.wraps(view)
    def wrapped_view(**kwargs):
    
        # Si l'utilisateur n'est pas connecté, il ne peut pas accéder à la route, alors il faut le rediriger vers la route auth.login
        if g.user is None:
            return redirect(url_for('auth.login'))
        
        return view(**kwargs)
    
    return wrapped_view

def get_profile_image(user_id):
    db = get_db()
    curseur = db.cursor()
    curseur.execute("SELECT chemin_vers_image FROM Personnes WHERE id_personne = ? ORDER BY id_personne DESC LIMIT 1", (user_id,))
    result = curseur.fetchone()
    db.commit()
    close_db()
    if result and result[0]:
        return os.path.basename(result[0])
    return None