# 2_kpi2_Mots_cles.py -- Version Sentinel Rain Green (Style KPI 3 avec Insights)

import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# Import des fonctions de données
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k2, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 2 - Threat Keywords", layout="wide")

# ── CSS GLOBAL (Style KPI 3 + Ajustements Vert/Blanc/Rouge) ──────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}

[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }

.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #ffffff !important;
    margin-bottom: 20px; text-shadow: 0 0 15px rgba(50,205,50,0.4);
}

.section-header-centered {
    text-align:center; font-family:'Roboto Mono',monospace; font-size:1.1rem;
    letter-spacing:.1em; text-transform:uppercase; color:#32CD32;
    border-bottom:1px solid rgba(50,205,50,0.3); width:fit-content;
    margin:40px auto 20px; padding-bottom:8px;
}

/* Boîte d'analyse style KPI 3 */
.insight-box {
    background: rgba(50, 205, 50, 0.07);
    border: 1px solid rgba(50, 205, 50, 0.2);
    border-radius: 8px;
    padding: 15px 20px;
    margin: 10px auto 30px;
    color: #e2e8f0;
    font-size: 0.95rem;
    backdrop-filter: blur(8px);
    border-left: 4px solid #32CD32;
    max-width: 90%;
}

[data-testid="stMarkdownContainer"] p, .stSelectbox label, .stSlider label {
    color: #ffffff !important;
}

div[data-baseweb="slider"] > div > div { background: #ff0000 !important; }
div[role="slider"] { background-color: #ff0000 !important; border: 2px solid #ffffff !important; }

.article-card { background: rgba(15,20,34,0.8); border: 1px solid #1e2a42; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; }
.article-link { color: #ffffff !important; text-decoration: none; font-size: 0.95rem; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">Suivi des mots-clés</div>', unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN ──────────────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document;
  var w = window.parent;
  function startCodeRain() {
    var old = p.getElementById('sentinel-rain-bg-k2');
    if (old) old.parentNode.removeChild(old);
    var cv = p.createElement('canvas');
    cv.id = 'sentinel-rain-bg-k2';
    cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.12;';
    p.body.appendChild(cv);
    var ctx = cv.getContext('2d');
    var W = cv.width = w.innerWidth;
    var H = cv.height = w.innerHeight;
    var symbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
    var fontSize = 14;
    var columns = W / fontSize;
    var drops = [];
    for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
    function draw() {
      if (!p.getElementById('sentinel-rain-bg-k2')) return;
      ctx.fillStyle = 'rgba(5, 10, 20, 0.1)'; 
      ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#32CD32'; 
      ctx.font = fontSize + 'px Roboto Mono';
      for (var i = 0; i < drops.length; i++) {
        var text = symbols[Math.floor(Math.random() * symbols.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        drops[i]++;
        if (drops[i] * fontSize > H && Math.random() > 0.975) { drops[i] = 0; }
      }
      requestAnimationFrame(draw);
    }
    draw();
    w.addEventListener('resize', function() { W = cv.width = w.innerWidth; H = cv.height = w.innerHeight; });
  }
  startCodeRain();
})();
</script>
""", height=0)

# ── DATA PROCESSING ──────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k2()
    v3 = df_raw[df_raw['period_days'] == 3].copy()
    v15 = df_raw[df_raw['period_days'] == 15][['keyword', 'occurrences']].rename(columns={'occurrences':'occ_15j'})
    drift_df = pd.merge(v3, v15, on='keyword', how='left').fillna(0)
    drift_df['acceleration'] = (drift_df['occurrences'] + 1) / ((drift_df['occ_15j'] / 5) + 1)
    if 'category' not in drift_df.columns:
        drift_df['category'] = 'Threats'
except Exception as e:
    st.error(f"Erreur data : {e}"); st.stop()

# ── MÉTRIQUES ────────────────────────────────────────────────────────────────
nb_mots_cles = len(drift_df)
top_v = drift_df.sort_values('occurrences', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
top_a = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Mono:wght@700&display=swap');
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; font-family: 'Roboto', sans-serif; }}
.card {{ 
    background: rgba(15,20,34,0.8); border: 1px solid rgba(50,205,50,0.3); 
    border-radius: 8px; padding: 18px; text-align: center; color: #ffffff;
    backdrop-filter: blur(8px);
}}
.label {{ font-size: 0.75rem; text-transform: uppercase; margin-bottom: 8px; color: #ffffff; opacity: 0.7; }}
.value {{ font-family: 'Roboto Mono'; font-size: 2rem; font-weight: 700; color: #ffffff; }}
.btn {{ 
    background: rgba(50,205,50,0.1); border: 1px solid #32CD32; color: #32CD32;
    border-radius: 4px; padding: 10px; cursor: pointer; font-size: 0.8rem; width: 100%; font-weight: bold;
}}
</style>
<div class="grid">
  <div class="card"><div class="label">Mots-clés Actifs</div><div class="value" id="count-k2">0</div></div>
  <div class="card"><div class="label">Top Volume</div><div class="value" style="color:#32CD32">{top_v}</div></div>
  <div class="card"><div class="label">Top Vélocité</div><div class="value" style="color:#32CD32">{top_a}</div></div>
  <div class="card" style="border:none; background:transparent;"><button class="btn" onclick="window.parent.location.reload()">⟳ REFRESH DATA</button></div>
</div>
<script>
function animateValue(id, start, end, duration) {{
    let obj = document.getElementById(id);
    let startTimestamp = null;
    const step = (timestamp) => {{
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {{ window.requestAnimationFrame(step); }}
    }};
    window.requestAnimationFrame(step);
}}
animateValue("count-k2", 0, {nb_mots_cles}, 1200);
</script>
""", height=130)

# ── TREEMAP ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header-centered">Analyse Hiérarchique</div>', unsafe_allow_html=True)

_, f_col, _ = st.columns([1, 2, 1])
with f_col:
    min_accel = st.slider("Seuil d'émergence (Accélération)", 0.5, 3.0, 1.0, step=0.1)

df_filtered = drift_df[drift_df['acceleration'] >= min_accel]

PLOT_STYLE = dict(
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(15,20,34,0.6)",
    font=dict(family="Roboto Mono", color="#ffffff", size=13)
)

fig_tree = px.treemap(
    df_filtered,
    path=[px.Constant("Cyber Overview"), 'category', 'keyword'],
    values='occurrences',
    color='acceleration',
    color_continuous_scale=['#050a14', '#1b4d1b', '#32CD32', '#7fff00'],
    range_color=[0.5, 2.5]
)
fig_tree.update_traces(textinfo="label+value", textfont=dict(color="white"))
fig_tree.update_layout(margin=dict(t=0, b=0, l=10, r=10), **PLOT_STYLE)
st.plotly_chart(fig_tree, use_container_width=True)

# PHRASE D'ANALYSE DYNAMIQUE 1
if not df_filtered.empty:
    top_accel_row = df_filtered.sort_values('acceleration', ascending=False).iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse de vélocité :</b> Le mot-clé <b>{top_accel_row['keyword']}</b> présente la plus forte accélération 
        ({top_accel_row['acceleration']:.2f}x). Cela indique une tendance émergente ou une campagne active détectée sur les dernières 72h.
    </div>
    """, unsafe_allow_html=True)

# ── BAR CHART SNR ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-header-centered">Fiabilité du Signal (Sources Uniques)</div>', unsafe_allow_html=True)
df_snr = df_filtered.nlargest(15, 'occurrences').sort_values('source_count')
fig_snr = go.Figure(go.Bar(
    y=df_snr['keyword'], x=df_snr['source_count'],
    orientation='h',
    marker=dict(color='#32CD32', line=dict(color='#ffffff', width=0.5)),
    hovertemplate="<b>%{y}</b><br>Sources : %{x}<extra></extra>"
))
fig_snr.update_layout(
    **PLOT_STYLE,
    xaxis=dict(gridcolor="rgba(255,255,255,0.1)", tickfont=dict(color="#ffffff")),
    yaxis=dict(tickfont=dict(color="#ffffff"))
)
st.plotly_chart(fig_snr, use_container_width=True)

# PHRASE D'ANALYSE DYNAMIQUE 2
if not df_snr.empty:
    reliable_kw = df_snr.sort_values('source_count', ascending=False).iloc[0]
    st.markdown(f"""
    <div class="insight-box">
        <b>Fiabilité du signal :</b> Le terme <b>{reliable_kw['keyword']}</b> est corroboré par <b>{reliable_kw['source_count']} sources distinctes</b>. 
        Un score élevé ici réduit le risque de faux positif lié au bruit d'une source unique.
    </div>
    """, unsafe_allow_html=True)

# ── DEEP DIVE ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header-centered">🔍 Explorer les Articles</div>', unsafe_allow_html=True)
_, d_col, _ = st.columns([1, 2, 1])
with d_col:
    selected_kw = st.selectbox("Filtrer par mot-clé", ["-- Choisir --"] + sorted(list(df_filtered['keyword'])))

if selected_kw != "-- Choisir --":
    all_articles = get_stg_articles(limit=1000)
    relevant = all_articles[all_articles['title'].str.contains(selected_kw, case=False, na=False)].head(10)
    for _, row in relevant.iterrows():
        st.markdown(f"""
        <div class="article-card">
            <a href="{row['url']}" target="_blank" class="article-link">{row['title']}</a><br>
            <small style="color:#32CD32; font-weight:bold;">{row['source']} | {str(row['published_date'])[:10]}</small>
        </div>
        """, unsafe_allow_html=True)