import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd

# Configuration Streamlit
st.set_page_config(layout="wide", page_title="StatCyberMatrix")

def afficher_carte():
    st.title("🛰️ Radar de Menaces Cyber")

    # --- RÉCUPÉRATION DU CHEMIN ---
    # os.getcwd() pointe sur /app/ (racine) sur Streamlit Cloud
    base_path = os.getcwd()
    html_path = os.path.join(base_path, "carte_menaces.html")

    # --- DONNÉES ---
    # On récupère le DataFrame depuis le session_state
    if 'df' in st.session_state:
        df = st.session_state['df']
        # Nettoyage pour la carte
        df_map = df.dropna(subset=['latitude', 'longitude'])
        # Conversion JSON
        articles_json = df_map.to_json(orient='records')
    else:
        articles_json = json.dumps([])
        st.info("Chargement des articles...")

    # --- RENDU ---
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # Injection dans la variable EVENTS du HTML
        final_html = html_content.replace("const EVENTS = [];", f"const EVENTS = {articles_json};")
        
        # Composant Streamlit
        components.html(final_html, height=800, scrolling=False)
    else:
        st.error(f"Fichier HTML introuvable : {html_path}")

if __name__ == "__main__":
    afficher_carte()