import streamlit as st
import streamlit.components.v1 as components
import json
import os

# --- CONFIGURATION ---
st.set_page_config(layout="wide", page_title="StatCyberMatrix")

def load_and_display_map():
    # 1. On récupère le chemin absolu du dossier où se trouve ce script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(current_dir, "carte_menace.html")

    # 2. Tes données (NLP / DataFrame)
    # Remplace cette liste par tes 3675 articles réels
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
            "summary": "Analyse NLP : Tentative d'exploitation sur serveur critique."
        }
    ]
    json_data = json.dumps(data_articles)

    # 3. Lecture et injection
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # On remplace la variable vide dans ton HTML par les données réelles
        final_html = html_content.replace("const EVENTS = [];", f"const EVENTS = {json_data};")
        
        # Affichage
        components.html(final_html, height=800, scrolling=False)
    else:
        st.error(f"⚠️ Erreur : Le fichier '{html_path}' est introuvable.")
        st.info("Vérifiez que le fichier HTML est bien dans le même dossier que le script .py")

# Lancement
st.title("🛰️ Radar de Menaces Cyber")
load_and_display_map()