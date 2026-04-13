import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="CyberMatrix KPI 5", layout="wide")

st.markdown("""
<style>
    /* Fond animé en arrière-plan */
    #sentinel-rain-bg {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        z-index: -1; opacity: 0.1; pointer-events: none;
    }
    .main { background-color: #050a14; }
    .stMetric { background: rgba(15, 20, 34, 0.8); border: 1px solid #1e2a42; border-radius: 10px; padding: 15px; }
</style>
""", unsafe_allow_html=True)

# Animation Rain (Arrière-plan)
st.components.v1.html("""
<canvas id="sentinel-rain-bg"></canvas>
<script>
    const canvas = document.getElementById('sentinel-rain-bg');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth; canvas.height = window.innerHeight;
    const letters = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops = Array(Math.floor(columns)).fill(1);
    function draw() {
        ctx.fillStyle = "rgba(5, 10, 20, 0.1)"; ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#3b82f6"; ctx.font = fontSize + "px monospace";
        for (let i = 0; i < drops.length; i++) {
            const text = letters.charAt(Math.floor(Math.random() * letters.length));
            ctx.fillText(text, i * fontSize, drops[i] * fontSize);
            if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
            drops[i]++;
        }
    }
    setInterval(draw, 33);
</script>
""", height=0)

# --- SIMULATION DE DONNÉES ---
@st.cache_data
def get_data():
    dates = pd.date_range(end=datetime.now(), periods=12, freq='W')
    categories = ['ransomware', 'phishing', 'data_breach', 'vulnerability', 'apt']
    data = []
    for d in dates:
        for c in categories:
            data.append({'semaine': d, 'category': c, 'nb_alertes': np.random.randint(5, 50)})
    return pd.DataFrame(data)

import numpy as np
df = get_data()

# --- SIDEBAR (FILTRES AMÉLIORÉS) ---
with st.sidebar:
    st.title("🛡️ Filtres Stratégiques")
    lookback = st.slider("Fenetre (jours)", 7, 90, 30)
    st.markdown("---")
    target_cats = st.multiselect("Vecteurs à surveiller", df['category'].unique(), default=df['category'].unique())

# Filtrage
cutoff = datetime.now() - timedelta(days=lookback)
df_filtered = df[(df['semaine'] >= cutoff) & (df['category'].isin(target_cats))]

# --- HEADER ---
st.title("Threat Intelligence Matrix")
st.markdown("---")

# --- GRAPHIQUES PERTINENTS ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Densité Temporelle (Heatmap)")
    # Une Heatmap est bien plus pertinente pour voir les "points chauds" par catégorie
    pivot_df = df_filtered.pivot_table(index='category', columns='semaine', values='nb_alertes', aggfunc='sum')
    fig_heat = px.imshow(pivot_df, color_continuous_scale='Blues', aspect="auto")
    fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_heat, use_container_width=True)

with col2:
    st.subheader("Profil de Menace (Radar)")
    # Le radar permet de comparer la force relative de chaque vecteur
    radar_data = df_filtered.groupby('category')['nb_alertes'].mean().reset_index()
    fig_radar = go.Figure(data=go.Scatterpolar(
        r=radar_data['nb_alertes'],
        theta=radar_data['category'],
        fill='toself',
        line_color='#3b82f6'
    ))
    fig_radar.update_layout(polar=dict(bgcolor="rgba(15,20,34,0.8)", radialaxis=dict(visible=True, gridcolor="#1e2a42")),
                            paper_bgcolor='rgba(0,0,0,0)', font_color="white")
    st.plotly_chart(fig_radar, use_container_width=True)

# --- ANALYSE DÉCISIONNELLE (TEXTE NETTOYÉ) ---
st.markdown("### > ANALYSE DECISIONNELLE DU FLUX")

# Calculs
total_alertes = df_filtered['nb_alertes'].sum()
top_cat = df_filtered.groupby('category')['nb_alertes'].sum().idxmax()
pic_val = df_filtered.groupby('semaine')['nb_alertes'].sum().max()
pic_date = df_filtered.groupby('semaine')['nb_alertes'].sum().idxmax().strftime('%d/%m/%Y')
avg_vol = df_filtered.groupby('semaine')['nb_alertes'].sum().mean()
hausse_pic = round(((pic_val - avg_vol) / avg_vol * 100), 1)

# Affichage propre sans HTML parasite
st.info(f"**Loi de Pareto :** La catégorie **{top_cat}** concentre la majorité du flux observé sur la période.")

col_a, col_b = st.columns(2)
with col_a:
    st.error(f"**Analyse de Pic :** Un maximum d'activité a été détecté la semaine du **{pic_date}** avec **{pic_val} alertes**, soit une hausse de **{hausse_pic}%** par rapport à l'activité habituelle.")

with col_b:
    volatilité = round(df_filtered.groupby('semaine')['nb_alertes'].sum().std(), 1)
    status_signal = "Signal bruyant/instable" if volatilité > 10 else "Signal stable"
    st.warning(f"**Stabilité du Signal :** Avec une volatilité de **{volatilité}** ({status_signal}), le consultant doit ajuster les politiques de corrélation pour optimiser le temps d'analyse.")

# --- TABLEAU DE DÉTAIL ---
with st.expander("Voir le détail brut des données"):
    st.dataframe(df_filtered, use_container_width=True)