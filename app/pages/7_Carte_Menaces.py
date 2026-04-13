import streamlit as st
import streamlit.components.v1 as components
import json
import os

# Titre de la page
st.title("🛰️ Radar de Menaces Cyber")

def charger_carte():
    # 1. LOCALISATION DU FICHIER (Adapté pour Streamlit Cloud)
    # On cherche le fichier dans le même dossier que ce script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "carte_menace.html")

    # 2. DONNÉES RÉELLES (Tes articles)
    # Ici, tu dois passer ton DataFrame d'articles. 
    # Exemple si tu as un DataFrame nommé 'df' :
    # articles_json = df.to_json(orient='records')
    
    # Pour le test, voici une structure qui correspond à tes colonnes (source, title, date)
    data_test = [
        {
            "cat": "menaces", 
            "lat": 39.9, "lon": 116.4, 
            "country": "Chine", 
            "title": "North Korea's APT37 Uses Facebook Social Engineering",
            "severity": "high", 
            "source": "The Hacker News", 
            "conf_score": 8.5,
            "kw": ["APT37", "Social Engineering"],
            "summary": "Attaque ciblant les utilisateurs via des tactiques de manipulation sur les réseaux sociaux."
        }
    ]
    articles_json = json.dumps(data_test)

    # 3. LECTURE ET INJECTION
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # On injecte les données dans la variable JS 'EVENTS'
        final_html = html_content.replace("const EVENTS = [];", f"const EVENTS = {articles_json};")
        
        # Rendu du composant
        components.html(final_html, height=800)
    else:
        st.error(f"Fichier introuvable à l'adresse : {html_path}")
        st.info("Assurez-vous que 'carte_menace.html' est bien dans le dossier 'pages/' avec ce script.")

charger_carte()