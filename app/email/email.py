from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from app.config import EMAIL_HOST, EMAIL_PORT, EMAIL_PASSWORD, EMAIL_ADDRESS

def send_email(to_address, subject, message, cc_addresses=None):
    # Création de l'objet email
    email = MIMEMultipart('alternative')
    email['From'] = f"ttcoach.ch <{EMAIL_ADDRESS}>"
    email['To'] = to_address
    email['Subject'] = subject

    # Ajout des adresses en copie
    if cc_addresses:
        email['Cc'] = ', '.join(cc_addresses)


    # Ajout du corps de l'email en version HTML (cela permet d'utiliser des tags html dans le message)
    # Pour utiliser une simple chaîne de caractère, il suffit de remplacer par MIMEText(message,'plain')
    # Partie texte brute (alternative au HTML)
    texte_simple = "Bonjour,\nVoici un e-mail de test pour vérifier que tout fonctionne.\nCode à usage unique : ######"

    # Partie HTML
    message_html = message  # Ton paramètre HTML est déjà bon

    email.attach(MIMEText(texte_simple, 'plain'))  # version texte simple
    email.attach(MIMEText(message_html, 'html'))   # version HTML


    # Connexion au serveur SMTP et envoi de l'email
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.set_debuglevel(1)  # Activer les messages de débogage
        server.ehlo()
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        # Envoi de l'email à tous les destinataires (To, Cc)
        server.sendmail(email['From'], [to_address] + cc_addresses, email.as_string())
        server.quit()
        print("Email envoyé avec succès !")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")

# Exemple d'utilisation
# send_email("...@edufr.ch", "Objet de test", "Contenu du message", cc_addresses=["...@edufr.ch"])


