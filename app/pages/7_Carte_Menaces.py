import streamlit as st
import streamlit.components.v1 as components
import json
import os
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(layout="wide", page_title="StatCyberMatrix | Radar de Menaces")

# --- TITRE ---
st.title("🛰️ Radar de Menaces Cyber")

def charger_et_afficher_carte():
    # 1. RÉCUPÉRATION DU CHEMIN DU FICHIER HTML
    # Ton image montre : pages/7_Carte_Menaces.py et carte_menaces.html à la racine (/app)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # On remonte d'un dossier pour atteindre le HTML
    html_path = os.path.join(current_dir, "..", "carte_menaces.html")

    # 2. PRÉPARATION DES DONNÉES (Tes 3675 articles)
    # Remplacer 'st.session_state.df' par le nom de ton DataFrame réel
    if 'df' in st.session_state:
        df = st.session_state.df
        
        # Filtrage des colonnes nécessaires pour ne pas alourdir le JS
        # On s'assure que les noms correspondent à ton script de nettoyage
        colonnes_requises = ['category', 'latitude', 'longitude', 'country', 'title', 'severity', 'source', 'confidence_score', 'keywords', 'summary']
        
        # On ne garde que les lignes qui ont des coordonnées GPS valides
        df_map = df.dropna(subset=['latitude', 'longitude'])
        
        # Conversion en JSON pour l'injection
        # On utilise 'records' pour avoir une liste d'objets [{...}, {...}]
        articles_json = df_map[df_map.columns.intersection(colonnes_requises)].to_json(orient='records')
    else:
        # Données de secours (Mock) si le DataFrame n'est pas encore chargé
        data_fallback = [
            {
                "cat": "menaces", 
                "lat": 48.8566, "lon": 2.3522, 
                "country": "France", 
                "title": "Initialisation du système...",
                "severity": "low", 
                "source": "Système", 
                "conf_score": 0,
                "kw": ["Info"],
                "summary": "Chargement des données en cours..."
            }
        ]
        articles_json = json.dumps(data_fallback)

    # 3. LECTURE DU HTML ET INJECTION
    if os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            
            # REMPLACEMENT CRITIQUE : on injecte le JSON dans la variable EVENTS du JS
            # Note : On s'assure que le nom du fichier est 'carte_menaces.html' (avec un 's')
            final_html = html_content.replace("const EVENTS = [];", f"const EVENTS = {articles_json};")
            
            # AFFICHAGE DU COMPOSANT
            components.html(final_html, height=800, scrolling=False)
            
            st.success(f"Affichage de {len(df_map) if 'df' in st.session_state else 0} points de menaces.")
            
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier HTML : {e}")
    else:
        # Affichage d'une aide au diagnostic si le fichier n'est toujours pas trouvé
        st.error(f"Fichier HTML introuvable.")
        st.warning(f"Chemin tenté : `{html_path}`")
        st.info("Vérifie que le fichier 'carte_menaces.html' est bien situé à la racine du dossier 'app'.")

# --- EXÉCUTION ---
if __name__ == "__main__":
    charger_et_afficher_carte()