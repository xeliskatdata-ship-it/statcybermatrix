# 3_kpi3_Analyse_Menaces.py -- Version Threat Intelligence Edition (Matrix Optimized)
import sys, os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration chemins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k3, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - Intelligence Menaces", layout="wide")

# ── Styles CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Roboto:wght@300;400;700&display=swap');
.stApp { background-color: #050a14 !important; }
.page-title { text-align: center; font-size: 2.5rem; font-weight: 700; color: #3b82f6; text-shadow: 0 0 15px rgba(59,130,246,0.3); }
.section-title { font-family:'Roboto Mono',monospace; font-size:1.1rem; color:#3b82f6; margin-top:30px; border-left:4px solid #3b82f6; padding-left:15px; text-transform:uppercase; margin-bottom:20px;}
.insight-card { background: rgba(59,130,246,0.05); border: 1px solid rgba(59,130,246,0.2); border-radius: 8px; padding: 20px; color: #93c5fd; }
.matrix-analysis { 
    background: rgba(30, 41, 59, 0.5); 
    border-radius: 4px; 
    padding: 15px; 
    border-left: 4px solid #3b82f6;
    margin-bottom: 10px;
    font-family: 'Roboto', sans-serif;
    color: #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# ── Animation Code Rain (Blue) ──────────────────────────────────────────────
components.html("""
<script>
(function() {
    var p = window.parent.document, w = window.parent;
    function startCodeRain(){
        var old=p.getElementById('rain-k3'); if(old)old.parentNode.removeChild(old);
        var cv=p.createElement('canvas'); cv.id='rain-k3';
        cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.1;';
        p.body.appendChild(cv);
        var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
        var symbols = "01SYSTEMFAILUREVIRUSAPT34MALWARE10".split("");
        var fontSize = 14; var columns = W / fontSize; var drops = [];
        for (var i = 0; i < columns; i++) { drops[i] = 1; }
        function draw(){
            ctx.fillStyle = 'rgba(5, 10, 20, 0.1)'; ctx.fillRect(0, 0, W, H);
            ctx.fillStyle = '#3b82f6'; ctx.font = fontSize + 'px monospace';
            for (var i = 0; i < drops.length; i++) {
                var text = symbols[Math.floor(Math.random() * symbols.length)];
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                if (drops[i] * fontSize > H && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
            requestAnimationFrame(draw);
        }
        draw();
    }
    startCodeRain();
})();
</script>
""", height=0)

# ── Chargement des données ──────────────────────────────────────────────────
try:
    df = get_mart_k3()
except:
    st.error("Erreur de base de données"); st.stop()

st.markdown('<div class="page-title">Intelligence Vectorielle des Menaces</div>', unsafe_allow_html=True)

# ── Top Section (Treemap & Radar) ───────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-title">Dominance par Secteur (Treemap)</div>', unsafe_allow_html=True)
    if not df.empty:
        fig_tree = px.treemap(
            df, 
            path=[px.Constant("Menaces"), 'category', 'source'], 
            values='nb_articles',
            color='nb_articles',
            color_continuous_scale='Blues'
        )
        
        # Optimisation de la lecture du Treemap
        fig_tree.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font_color="white", 
            margin=dict(t=0, l=0, r=0, b=0),
            hoverlabel=dict(
                bgcolor="rgba(13, 25, 48, 0.9)", # Bleu très foncé transparent
                font_size=13,
                font_family="Roboto Mono",
                bordercolor="#3b82f6"
            )
        )
        # Épuration du texte affiché
        fig_tree.update_traces(
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>Articles: %{value}<extra></extra>"
        )
        st.plotly_chart(fig_tree, use_container_width=True)

with col2:
    st.markdown('<div class="section-title">Résumé Analyste</div>', unsafe_allow_html=True)
    if not df.empty:
        top_cat = df.groupby('category')['nb_articles'].sum().idxmax()
        st.markdown(f"""
        <div class="insight-card">
            <b>Vecteur Dominant :</b> {top_cat.upper()}<br><br>
            <b>Analyse :</b> On observe une concentration critique sur le vecteur <i>{top_cat}</i>. 
            Les consultants devraient prioriser les audits sur ce périmètre pour les prochaines 72h.
        </div>
        """, unsafe_allow_html=True)
    
        agg = df.groupby('category')['nb_articles'].sum().reset_index()
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=agg['nb_articles'],
            theta=agg['category'],
            fill='toself',
            line_color='#3b82f6'
        ))
        fig_radar.update_layout(
            polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=False)), 
            showlegend=False, 
            paper_bgcolor='rgba(0,0,0,0)', 
            height=300, 
            margin=dict(t=30, b=30)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ── MATRICE DE CORRÉLATION AGRANDIE ─────────────────────────────────────────
st.markdown('<div class="section-title">Matrice de Corrélation Sources vs Menaces</div>', unsafe_allow_html=True)

if not df.empty:
    pivot = df.pivot_table(index='source', columns='category', values='nb_articles', aggfunc='sum').fillna(0)
    
    # --- Analyse Dynamique de la Matrice ---
    max_val = pivot.values.max()
    max_pos = (pivot == max_val).stack().idxmax()
    source_max, cat_max = max_pos
    
    # Suppression de l'emoji loupe
    st.markdown(f"""
    <div class="matrix-analysis">
        <b>Analyse de couverture :</b> Actuellement, la source <b>{source_max}</b> est le principal émetteur d'alertes 
        sur le vecteur <b>{cat_max}</b> ({int(max_val)} articles). 
        <i>Cette matrice permet d'identifier les zones d'ombre ou les sur-représentations de certains flux.</i>
    </div>
    """, unsafe_allow_html=True)

    fig_heat = px.imshow(
        pivot,
        labels=dict(x="Catégories de Menaces", y="Sources de Veille", color="Volume"),
        color_continuous_scale='Blues',
        aspect="auto" 
    )
    
    fig_heat.update_layout(
        height=600, 
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Roboto Mono', color="#94a3b8", size=12),
        xaxis=dict(side="top"), 
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    if len(pivot.index) < 25: 
        fig_heat.update_traces(text=pivot.values, texttemplate="%{text}")

    st.plotly_chart(fig_heat, use_container_width=True)

# ── Deep Dive ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Deep Dive : Derniers indicateurs</div>', unsafe_allow_html=True)
unique_cats = df['category'].unique() if not df.empty else ["N/A"]
selected_cat = st.selectbox("Filtrer par vecteur", unique_cats)

df_raw_articles = get_stg_articles(limit=200)
filtered_articles = df_raw_articles[df_raw_articles['title'].str.contains(selected_cat, case=False, na=False)].head(10)

if not filtered_articles.empty:
    for _, row in filtered_articles.iterrows():
        st.markdown(f"🔹 **{row['source']}** : [{row['title']}]({row['url']})")
else:
    st.info("Sélectionnez un vecteur pour afficher les articles récents correspondants.")