import sys, os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuration chemins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k5, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 5 Alertes", layout="wide")

# ── HELPER TITRE ──────────────────────────────────────────────────────────
def _section_title(text: str, size: str = "1.4rem"):
    st.markdown(
        f"<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:{size};"
        "letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;"
        "border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;"
         f"margin:28px auto 16px'>{text}</div>",
        unsafe_allow_html=True,
    )

# ── CSS GLOBAL ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif; color: #ffffff !important;}
.stApp { background-color: #050a14 !important; }

[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3,
.stSelectbox label, .stCheckbox p, .stTable td, .stTable th {
    color: #ffffff !important;
}

.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #3b82f6;
    margin-bottom: 20px; text-shadow: 0 0 15px rgba(59,130,246,0.5);
}

.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.insight-box {
    background: rgba(10, 20, 40, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 8px; padding: 25px; margin: 15px auto;
    backdrop-filter: blur(10px); max-width: 95%;
    line-height: 1.6;
}

.graph-header {
    text-align: center;
    color: #84cc16;
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 15px;
    font-family: 'Roboto Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ MATRIX (CORRIGÉ) ───────────────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document;
  var body = p.body;
  
  function startCodeRain(){
    var old = p.getElementById('matrix-rain-k5');
    if(old) old.remove();
    
    var cv = p.createElement('canvas');
    cv.id = 'matrix-rain-k5';
    cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.2;';
    body.appendChild(cv);
    
    var ctx = cv.getContext('2d');
    var W = cv.width = window.parent.innerWidth;
    var H = cv.height = window.parent.innerHeight;
    
    var symbols = "01ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".split("");
    var fontSize = 14;
    var columns = W / fontSize;
    var drops = [];
    for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
    
    function draw(){
      ctx.fillStyle = 'rgba(5, 10, 20, 0.1)';
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#3b82f6';
      ctx.font = fontSize + 'px monospace';
      for (var i = 0; i < drops.length; i++) {
        var text = symbols[Math.floor(Math.random() * symbols.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        drops[i]++;
        if (drops[i] * fontSize > H && Math.random() > 0.975) { drops[i] = 0; }
      }
    }
    setInterval(draw, 35);
  }
  if (p.readyState === 'complete') { startCodeRain(); } 
  else { window.parent.addEventListener('load', startCodeRain); }
})();
</script>
""", height=0)

# ── LOGIQUE DONNÉES ──────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k5()
    if df_raw is None or df_raw.empty:
        st.warning("Base de données vide.")
        st.stop()
    df_raw['semaine'] = pd.to_datetime(df_raw['semaine'])
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# ── EN-TETE ──────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Threat Intelligence Matrix</div>', unsafe_allow_html=True)

_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Synchroniser", use_container_width=True):
        force_refresh()
        st.rerun()

load_ts = datetime.now().strftime('%H:%M:%S')
with col_b:
    st.markdown(
        f'<div class="badge-live"><span class="dot-live"></span>'
        f'LIVE - MaJ {load_ts} - {int(df_raw["nb_alertes"].sum()):,} alertes</div>',
        unsafe_allow_html=True,
    )

# ── FILTRES ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Analyse de Menaces")
    lookback = st.selectbox("Fenetre d'observation", options=[7, 14, 30, 90], index=2)
    cutoff_date = df_raw['semaine'].max() - timedelta(days=lookback)
    df = df_raw[df_raw['semaine'] >= cutoff_date].copy()
    cats_all = sorted(df['category'].unique())
    target_cat = st.multiselect("Vecteur cible", options=cats_all, default=cats_all)
    df = df[df['category'].isin(target_cat)]

# ── GRAPHIQUES ───────────────────────────────────────────────────────────────
_section_title("Analyse Décisionnelle et Densité")

col_l, col_r = st.columns([1, 1])

with col_l:
    st.markdown("<div class='graph-header'>Densité Temporelle (Heatmap)</div>", unsafe_allow_html=True)
    pivot_df = df.pivot_table(index='category', columns='semaine', values='nb_alertes', aggfunc='sum')
    fig_heat = px.imshow(pivot_df, color_continuous_scale='Blues', aspect="auto")
    
    # Nettoyage de l'axe X : Uniquement la date
    fig_heat.update_xaxes(tickformat="%d/%m/%y")
    
    fig_heat.update_traces(hovertemplate="Date: %{x|%d/%m/%Y}<br>Catégorie: %{y}<br>Alertes: %{z}<extra></extra>")
    fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(5,10,20,0.6)', 
                           font=dict(family='Roboto', color='#94a3b8'), margin=dict(t=10, b=20, l=10, r=10))
    st.plotly_chart(fig_heat, use_container_width=True)

with col_r:
    st.markdown("<div class='graph-header'>Profil de Menace (Radar)</div>", unsafe_allow_html=True)
    radar_data = df.groupby('category')['nb_alertes'].mean().reset_index()
    fig_radar = go.Figure(go.Scatterpolar(
        r=radar_data['nb_alertes'], theta=radar_data['category'], fill='toself', line_color='#3b82f6',
        hovertemplate="Vecteur: %{theta}<br>Moyenne: %{r:.1f}<extra></extra>"
    ))
    fig_radar.update_layout(
        polar=dict(bgcolor="rgba(15,20,34,0.6)", radialaxis=dict(visible=True, gridcolor="#1e2a42"), angularaxis=dict(gridcolor="#1e2a42")),
        paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Roboto', color='#94a3b8'), margin=dict(t=30, b=20, l=10, r=10), height=400
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── INSIGHTS DYNAMIQUES ──────────────────────────────────────────────────────
_section_title("Interprétation des Tendances")

if not df.empty:
    total_hits = int(df['nb_alertes'].sum())
    weekly_stats = df.groupby('semaine')['nb_alertes'].sum()
    avg_hits = weekly_stats.mean()
    ranking = df.groupby('category')['nb_alertes'].sum().sort_values(ascending=False)
    top_cat = ranking.index[0]
    top_pct = round(ranking.iloc[0] / total_hits * 100, 1)
    
    pic_semaine = weekly_stats.idxmax().strftime('%d/%m/%Y')
    pic_val = int(weekly_stats.max())
    deviation_pic = round(((pic_val - avg_hits) / avg_hits * 100), 1) if avg_hits > 0 else 0

    st.markdown(f"""
    <div class="insight-box">
        <div style="font-family:'Roboto Mono'; color:#3b82f6; margin-bottom:15px; font-weight:700;">
            > ANALYSE DECISIONNELLE DU FLUX CTI
        </div>
        Loi de Pareto : La catégorie <b>{top_cat}</b> concentre à elle seule <b>{top_pct}%</b> du flux total observé sur la période ({total_hits} alertes). 
        L'effort de remédiation doit être priorisé sur ce vecteur.
        <br><br>
        Analyse de Pic : Un maximum d'activité a été détecté la semaine du <b>{pic_semaine}</b> avec <b>{pic_val} alertes</b>, 
        soit une hausse de <b>{deviation_pic}%</b> par rapport à la charge habituelle sur la période observée.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")