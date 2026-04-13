# 3_kpi3_Analyse_Menaces.py -- Version Threat Intelligence Edition
import sys, os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuration chemins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k3, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - Intelligence Menaces", layout="wide")

# ── Styles CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; }
.page-title { text-align: center; font-size: 2.5rem; font-weight: 700; color: #3b82f6; text-shadow: 0 0 15px rgba(59,130,246,0.3); }
.section-title { font-family:'Roboto Mono',monospace; font-size:1.1rem; color:#3b82f6; margin-top:30px; border-left:4px solid #3b82f6; padding-left:15px; text-transform:uppercase; }
.insight-card { background: rgba(59,130,246,0.05); border: 1px solid rgba(59,130,246,0.2); border-radius: 8px; padding: 20px; color: #93c5fd; }
</style>
""", unsafe_allow_html=True)

# ── Animation Code Rain ─────────────────────────────────────────────────────
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
    # Simulation de données temporelles si absentes pour l'exemple de dynamique
    df['published_date'] = pd.to_datetime(datetime.now()) 
except:
    st.error("Erreur de base de données"); st.stop()

st.markdown('<div class="page-title">Intelligence Vectorielle des Menaces</div>', unsafe_allow_html=True)

# ── Dashboard Layout ────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-title">Dominance par Secteur (Treemap)</div>', unsafe_allow_html=True)
    # Le Treemap est bien plus parlant qu'un donut pour un consultant (hiérarchie)
    fig_tree = px.treemap(
        df, 
        path=[px.Constant("Menaces"), 'category', 'source'], 
        values='nb_articles',
        color='nb_articles',
        color_continuous_scale='Blues'
    )
    fig_tree.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", margin=dict(t=0, l=0, r=0, b=0))
    st.plotly_chart(fig_tree, use_container_width=True)

with col2:
    st.markdown('<div class="section-title">Résumé Analyste</div>', unsafe_allow_html=True)
    top_cat = df.groupby('category')['nb_articles'].sum().idxmax()
    st.markdown(f"""
    <div class="insight-card">
        <b>Vecteur Dominant :</b> {top_cat.upper()}<br><br>
        <b>Analyse :</b> On observe une concentration critique sur le vecteur <i>{top_cat}</i>. 
        Les consultants devraient prioriser les audits sur ce périmètre pour les prochaines 72h.
    </div>
    """, unsafe_allow_html=True)
    
    # Graphique Radar pour l'équilibre des menaces
    agg = df.groupby('category')['nb_articles'].sum().reset_index()
    fig_radar = go.Figure(data=go.Scatterpolar(
        r=agg['nb_articles'],
        theta=agg['category'],
        fill='toself',
        line_color='#3b82f6'
    ))
    fig_radar.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(visible=False)), showlegend=False, paper_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(t=30, b=30))
    st.plotly_chart(fig_radar, use_container_width=True)

# ── Matrice de Corrélation ──────────────────────────────────────────────────
st.markdown('<div class="section-title">Matrice de Corrélation Sources vs Menaces</div>', unsafe_allow_html=True)
pivot = df.pivot_table(index='source', columns='category', values='nb_articles', aggfunc='sum').fillna(0)

fig_heat = px.imshow(
    pivot,
    labels=dict(x="Catégorie", y="Source", color="Volume"),
    color_continuous_scale='Blues'
)
fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
st.plotly_chart(fig_heat, use_container_width=True)

# ── Explorer le flux ────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Deep Dive : Derniers indicateurs</div>', unsafe_allow_html=True)
selected_cat = st.selectbox("Filtrer par vecteur", df['category'].unique())

df_raw_articles = get_stg_articles(limit=200)
# Note : Ici on filtre sur le titre car la catégorie dépend du tagage
filtered_articles = df_raw_articles[df_raw_articles['title'].str.contains(selected_cat, case=False)].head(10)

if not filtered_articles.empty:
    for _, row in filtered_articles.iterrows():
        st.markdown(f"🔹 **{row['source']}** : [{row['title']}]({row['url']})")
else:
    st.info("Aucun article récent spécifique trouvé pour ce vecteur.")