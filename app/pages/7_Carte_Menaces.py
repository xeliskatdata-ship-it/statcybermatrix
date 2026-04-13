import streamlit as st
import streamlit.components.v1 as components
import json
import os

# Configuration de la page
st.set_page_config(layout="wide", page_title="StatCyberMatrix - Live Map")

def load_map():
    # 1. SIMULATION / CHARGEMENT DE TES DONNÉES
    # Ici, remplace par ton code qui récupère tes 3675 articles (df = ...)
    # IMPORTANT : Chaque article doit avoir 'lat', 'lon', 'severity', 'title', 'source'
    data_articles = [
        {
            "cat": "failles", 
            "lat": 48.8566, "lon": 2.3522, 
            "country": "France", 
            "title": "CVE-2026-20131: RCE critique",
            "severity": "critical", 
            "source": "ANSSI", 
            "conf_score": 9.8,
            "kw": ["RCE", "Exploit"],
            "summary": "Cette vulnérabilité est actuellement très citée dans les rapports d'incidents APT."
        },
        {
            "cat": "menaces", 
            "lat": 37.7749, "lon": -122.4194, 
            "country": "USA", 
            "title": "Activité APT37 détectée",
            "severity": "high", 
            "source": "The Hacker News", 
            "conf_score": 8.5,
            "kw": ["APT37", "Malware"],
            "summary": "Tentatives d'exfiltration de données via ingénierie sociale sur Facebook."
        }
    ]
    
    # Conversion en JSON pour le JavaScript
    json_data = json.dumps(data_articles)

    # 2. LECTURE DU FICHIER HTML
    # On lit le fichier carte_menace.html que tu as créé
    if os.path.exists("carte_menace.html"):
        with open("carte_menace.html", "r", encoding="utf-8") as f:
            html_template = f.read()
        
        # INJECTION DES DONNÉES : On remplace le placeholder dans le HTML
        # On va chercher la variable 'const EVENTS = [];' dans ton HTML et la remplir
        final_html = html_template.replace("const EVENTS = [];", f"const EVENTS = {json_data};")
        
        # Affichage du composant
        components.html(final_html, height=850, scrolling=False)
    else:
        st.error("Le fichier 'carte_menace.html' est introuvable dans le répertoire.")

# Lancement de l'affichage
load_map()