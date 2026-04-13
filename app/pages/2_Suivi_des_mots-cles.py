# 2_kpi2_Mots_cles.py -- Version Dynamique (Compteur & Effets de Surbrillance)

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

# ── CSS GLOBAL (Ajout des effets Hover) ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; color: #94a3b8; }
.page-title { text-align:center; font-size:2.8rem; font-weight:700; color:#a855f7; margin-bottom:20px; line-height:1.2; }
.section-header-centered {
    text-align:center; font-family:'Roboto Mono',monospace; font-size:1.2rem;
    letter-spacing:.1em; text-transform:uppercase; color:#a855f7;
    border-bottom:1px solid rgba(168,85,247,0.3); width:fit-content;
    margin:40px auto 20px; padding-bottom:8px;
}
.metric-container { 
    background: rgba(15,20,34,0.6); 
    border: 1px solid rgba(168,85,247,0.2); 
    border-radius: 8px; 
    padding: 20px; 
    text-align: center; 
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}
.metric-label { font-size: 0.8rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 5px; }
.metric-value { font-family: 'Roboto Mono'; font-size: 2.2rem; font-weight: 700; color: #e2e8f0; transition: all 0.3s ease; }

/* Effet de surbrillance au survol */
.metric-container:hover { border-color: #a855f7; box-shadow: 0 0 15px rgba(168,85,247,0.2); }
.metric-container:hover .glow-purple { color: #d8b4fe !important; text-shadow: 0 0 10px #a855f7; }
.metric-container:hover .glow-green { color: #4ade80 !important; text-shadow: 0 0 10px #22c55e; }

.article-card { background: rgba(15,20,34,0.8); border: 1px solid #1e2a42; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

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

# ── EN-TÊTE ET MÉTRIQUES ANIMÉES ──────────────────────────────────────────────
st.markdown('<div class="page-title">Threat Keywords Intelligence</div>', unsafe_allow_html=True)

nb_mots_cles = len(drift_df)
top_v = drift_df.sort_values('occurrences', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
top_a = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"

# On utilise un composant HTML pour le compteur et les effets hover
components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Roboto+Mono:wght@700&display=swap');
.grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; font-family: 'Roboto', sans-serif; }}
.card {{ 
    background: rgba(15,20,34,0.6); border: 1px solid rgba(168,85,247,0.2); 
    border-radius: 8px; padding: 18px; text-align: center; color: #94a3b8;
    transition: all 0.3s ease; cursor: default;
}}
.card:hover {{ border-color: #a855f7; box-shadow: 0 0 15px rgba(168,85,247,0.2); }}
.label {{ font-size: 0.75rem; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.05em; }}
.value {{ font-family: 'Roboto Mono'; font-size: 2.1rem; font-weight: 700; color: #e2e8f0; transition: all 0.3s ease; }}
.card:hover .purple {{ color: #d8b4fe; text-shadow: 0 0 10px #a855f7; }}
.card:hover .green {{ color: #4ade80; text-shadow: 0 0 10px #22c55e; }}
.btn {{ 
    background: rgba(168,85,247,0.1); border: 1px solid #a855f7; color: #a855f7;
    border-radius: 4px; padding: 8px; cursor: pointer; font-size: 0.9rem; margin-top: 10px; width: 100%;
}}
</style>

<div class="grid">
  <div class="card">
    <div class="label">Mots-clés Actifs</div>
    <div class="value" id="count-k2">0</div>
  </div>
  <div class="card">
    <div class="label">Top Volume</div>
    <div class="value purple">{top_v}</div>
  </div>
  <div class="card">
    <div class="label">Top Vélocité</div>
    <div class="value green">{top_a}</div>
  </div>
  <div class="card" style="border:none; background:transparent; display:flex; align-items:center;">
    <button class="btn" onclick="window.parent.location.reload()">⟳ REFRESH DATA</button>
  </div>
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

# ── LE RESTE DES GRAPHIQUES (TREEMAP & BARRES) ───────────────────────────────
# (Le code suivant reste identique à la version précédente pour le Treemap et le graphique de barres)
st.markdown('<div class="section-header-centered">Analyse Hiérarchique</div>', unsafe_allow_html=True)

_, f_col, _ = st.columns([1, 2, 1])
with f_col:
    min_accel = st.slider("Seuil d'émergence (Indice d'accélération)", 0.5, 3.0, 1.0, step=0.1)

df_filtered = drift_df[drift_df['acceleration'] >= min_accel]

fig_tree = px.treemap(
    df_filtered,
    path=[px.Constant("Global Overview"), 'category', 'keyword'],
    values='occurrences',
    color='acceleration',
    color_continuous_scale='Purples',
    range_color=[0.5, 2.5]
)
fig_tree.update_traces(
    textinfo="label+value",
    hovertemplate="<b>%{label}</b><br>Volume : %{value} articles<extra></extra>"
)
fig_tree.update_layout(margin=dict(t=0, b=0, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_tree, use_container_width=True)

st.markdown('<div class="section-header-centered">Fiabilité du Signal</div>', unsafe_allow_html=True)
df_snr = df_filtered.nlargest(15, 'occurrences').sort_values('source_count')
fig_snr = go.Figure(go.Bar(
    y=df_snr['keyword'], x=df_snr['source_count'],
    orientation='h',
    marker=dict(color='#a855f7', line=dict(color='#f0abfc', width=1)),
    hovertemplate="<b>%{y}</b><br>Sources uniques : %{x}<extra></extra>"
))
fig_snr.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,20,34,0.4)", font=dict(family="Roboto Mono", color="#94a3b8"))
st.plotly_chart(fig_snr, use_container_width=True)