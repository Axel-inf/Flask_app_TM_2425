console.log("Script bien chargé")
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('changement-visu').addEventListener('click', function() {
        const passwordInput = document.getElementById('mot_de_passe');
        const type = passwordInput.getAttribute('type') === 'mot_de_passe' ? 'text' : 'mot_de_passe';
        passwordInput.setAttribute('type', type);
        
        // Changer l'icône en fonction du type
        if (type === 'mot_de_passe') {
            this.src = "{{url_for('static', filename='imgs/cacher_mot_de_passe.svg')}}"; // Image pour cacher le mot de passe
        } else {
            this.src = "{{url_for('static', filename='imgs/voir_mot_de_passe.svg')}}"; // Image pour voir le mot de passe
        }
    });
});
    
    