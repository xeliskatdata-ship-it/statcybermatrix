# 2_kpi2_Mots_cles.py -- Version Sentinel Rain Green Edition

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

# ── CSS GLOBAL (Design Vert Pomme) ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; color: #94a3b8; }
.page-title { text-align:center; font-size:2.8rem; font-weight:700; color:#32CD32; margin-bottom:20px; text-shadow: 0 0 15px rgba(50,205,50,0.3); }
.section-header-centered {
    text-align:center; font-family:'Roboto Mono',monospace; font-size:1.2rem;
    letter-spacing:.1em; text-transform:uppercase; color:#32CD32;
    border-bottom:1px solid rgba(50,205,50,0.3); width:fit-content;
    margin:40px auto 20px; padding-bottom:8px;
}
.article-card { background: rgba(15,20,34,0.8); border: 1px solid #1e2a42; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; }
.article-link { color: #e2e8f0; text-decoration: none; font-size: 0.95rem; font-weight: 500; }
.article-link:hover { color: #32CD32; }
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (VERT) ────────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  function startCodeRain(){
    var old=p.getElementById('sentinel-rain-bg'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='sentinel-rain-bg';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.1;';
    p.body.appendChild(cv);
    var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
    var codeSymbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
    var fontSize = 14; var columns = W / fontSize; var drops = [];
    for (var x = 0; x < columns; x++) { drops[x] = Math.random() * (H / fontSize); }
    function draw(){
      if(!p.getElementById('sentinel-rain-bg'))return;
      ctx.fillStyle = 'rgba(5, 10, 20, 0.05)'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#32CD32'; ctx.font = fontSize + 'px Roboto Mono';
      for (var i = 0; i < drops.length; i++) {
        var text = codeSymbols[Math.floor(Math.random() * codeSymbols.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        drops[i]++;
        if (drops[i] * fontSize > H && Math.random() > 0.975) { drops[i] = 0; }
      }
      requestAnimationFrame(draw);
    }
    draw(); 
    w.addEventListener('resize', function(){W=cv.width=w.innerWidth; H=cv.height=w.innerHeight;});
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

# ── MÉTRIQUES AVEC COMPTEUR ET SURBRILLANCE VERT POMME ───────────────────────
nb_mots_cles = len(drift_df)
top_v = drift_df.sort_values('occurrences', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
top_a = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Mono:wght@700&display=swap');
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; font-family: 'Roboto', sans-serif; }}
.card {{ 
    background: rgba(15,20,34,0.6); border: 1px solid rgba(50,205,50,0.2); 
    border-radius: 8px; padding: 18px; text-align: center; color: #94a3b8;
    transition: all 0.3s ease; cursor: default; backdrop-filter: blur(10px);
}}
.card:hover {{ border-color: #32CD32; box-shadow: 0 0 15px rgba(50,205,50,0.2); }}
.label {{ font-size: 0.75rem; text-transform: uppercase; margin-bottom: 8px; }}
.value {{ font-family: 'Roboto Mono'; font-size: 2rem; font-weight: 700; color: #e2e8f0; transition: all 0.3s ease; }}
.card:hover .glow-green {{ color: #32CD32; text-shadow: 0 0 10px #32CD32; }}
.btn {{ 
    background: rgba(50,205,50,0.1); border: 1px solid #32CD32; color: #32CD32;
    border-radius: 4px; padding: 10px; cursor: pointer; font-size: 0.8rem; width: 100%; font-weight: bold;
}}
.btn:hover {{ background: rgba(50,205,50,0.2); }}
</style>
<div class="grid">
  <div class="card"><div class="label">Mots-clés Actifs</div><div class="value" id="count-k2">0</div></div>
  <div class="card"><div class="label">Top Volume</div><div class="value glow-green">{top_v}</div></div>
  <div class="card"><div class="label">Top Vélocité</div><div class="value glow-green">{top_a}</div></div>
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
animateValue("count-k2", 0, {nb_mots_cles}, 1500);
</script>
""", height=130)

# ── TREEMAP ET GRAPHIQUE (VERT POMME) ─────────────────────────────────────────
st.markdown('<div class="section-header-centered">Analyse Hiérarchique</div>', unsafe_allow_html=True)

_, f_col, _ = st.columns([1, 2, 1])
with f_col:
    min_accel = st.slider("Seuil d'émergence (Accélération)", 0.5, 3.0, 1.0, step=0.1)

df_filtered = drift_df[drift_df['acceleration'] >= min_accel]

fig_tree = px.treemap(
    df_filtered,
    path=[px.Constant("Cyber Overview"), 'category', 'keyword'],
    values='occurrences',
    color='acceleration',
    color_continuous_scale=['#0a1a0a', '#32CD32', '#7fff00'], # Dégradé de noirs à verts vifs
    range_color=[0.5, 2.5]
)
fig_tree.update_traces(textinfo="label+value", hovertemplate="<b>%{label}</b><br>Volume : %{value}<extra></extra>")
fig_tree.update_layout(margin=dict(t=0, b=0, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown('<div class="section-header-centered">Fiabilité du Signal</div>', unsafe_allow_html=True)
df_snr = df_filtered.nlargest(15, 'occurrences').sort_values('source_count')
fig_snr = go.Figure(go.Bar(
    y=df_snr['keyword'], x=df_snr['source_count'],
    orientation='h',
    marker=dict(color='#32CD32', line=dict(color='#7fff00', width=1)),
    hovertemplate="<b>%{y}</b><br>Sources uniques : %{x}<extra></extra>"
))
fig_snr.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(15,20,34,0.4)", 
    font=dict(family="Roboto Mono", color="#94a3b8"),
    xaxis=dict(gridcolor="rgba(50,205,50,0.1)")
)
st.plotly_chart(fig_snr, use_container_width=True)

# ── DEEP DIVE ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header-centered">🔍 Deep Dive : Articles Relatés</div>', unsafe_allow_html=True)
_, d_col, _ = st.columns([1, 2, 1])
with d_col:
    selected_kw = st.selectbox("Sélectionner une menace", ["-- Choisir --"] + sorted(list(df_filtered['keyword'])))

if selected_kw != "-- Choisir --":
    all_articles = get_stg_articles(limit=1000)
    relevant = all_articles[all_articles['title'].str.contains(selected_kw, case=False, na=False)].head(10)
    for _, row in relevant.iterrows():
        st.markdown(f"""
        <div class="article-card">
            <a href="{row['url']}" target="_blank" class="article-link">{row['title']}</a><br>
            <small style="color:#32CD32">{row['source']} | {str(row['published_date'])[:10]}</small>
        </div>
        """, unsafe_allow_html=True)