# 2_kpi2_Mots_cles.py -- KPI 2 : Threat Keywords Intelligence
# Design : Velocity Matrix, Keyword Drift, Signal-to-Noise Ratio

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k2, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 2 - Threat Intelligence", layout="wide")

# ── CSS & Thème (Identique KPI 1 pour cohérence) ──────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; color: #94a3b8; }
.page-title { text-align:center; font-size:2.5rem; font-weight:700; color:#a855f7; margin-bottom:10px; }
.section-title { font-family:'Roboto Mono'; font-size:1rem; color:#a855f7; border-left:4px solid #a855f7; padding-left:15px; margin:40px 0 20px; }
.metric-card { background:rgba(168,85,247,0.05); border:1px solid rgba(168,85,247,0.2); border-radius:10px; padding:20px; text-align:center; }
.metric-val { font-size:2.2rem; font-weight:700; color:#e2e8f0; font-family:'Roboto Mono'; }
</style>
""", unsafe_allow_html=True)

# ── ECG Animé (Thème Violet pour KPI 2) ──────────────────────────────────────
components.html("""
<script>
(function(){var p=window.parent.document,w=window.parent,PT=4,SP=2.5;
function draw(){
    var cv=p.getElementById('ecg-bg-v2'); if(!cv){
        cv=p.createElement('canvas'); cv.id='ecg-bg-v2';
        cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
        p.body.appendChild(cv);
    }
    var ctx=cv.getContext('2d'),W=cv.width=w.innerWidth,H=cv.height=w.innerHeight;
    ctx.strokeStyle='rgba(168,85,247,0.15)'; ctx.lineWidth=1.5;
    ctx.beginPath(); ctx.moveTo(0, H/2);
    for(var x=0; x<W; x+=5){ ctx.lineTo(x, H/2 + Math.sin(x*0.02)*10); }
    ctx.stroke();
}
draw(); w.addEventListener('resize', draw);
})();
</script>
""", height=0)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Threat Keywords Intelligence</div>', unsafe_allow_html=True)

# ── Données ──────────────────────────────────────────────────────────────────
try:
    df = get_mart_k2()
except Exception as e:
    st.error(f"Erreur : {e}"); st.stop()

# ── Logique de Monitoring ────────────────────────────────────────────────────
# On calcule la vélocité des mots-clés (3j vs 15j)
def calculate_drift(df):
    v3 = df[df['period_days'] == 3][['keyword', 'occurrences', 'source_count']].rename(columns={'occurrences':'occ_3j', 'source_count':'src_3j'})
    v15 = df[df['period_days'] == 15][['keyword', 'occurrences']].rename(columns={'occurrences':'occ_15j'})
    drift = pd.merge(v3, v15, on='keyword', how='left').fillna(0)
    # Ratio d'accélération
    drift['acceleration'] = (drift['occ_3j'] + 1) / ((drift['occ_15j'] / 5) + 1)
    return drift

drift_df = calculate_drift(df)

# ── Dashboard Layout ─────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown('<div class="metric-card"><div class="metric-val">'+str(len(drift_df))+'</div>Mots-clés Actifs</div>', unsafe_allow_html=True)
with col2:
    top_k = drift_df.sort_values('occ_3j', ascending=False).iloc[0]['keyword']
    st.markdown('<div class="metric-card"><div class="metric-val" style="font-size:1.5rem">'+top_k+'</div>Top Volume</div>', unsafe_allow_html=True)
with col3:
    fast_k = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword']
    st.markdown('<div class="metric-card"><div class="metric-val" style="font-size:1.5rem; color:#f0abfc">'+fast_k+'</div>Top Vélocité</div>', unsafe_allow_html=True)
with col4:
    st.button("⟳ Force Refresh", on_click=force_refresh)

# ── Visual 1 : Keyword Drift (Le "Splunk Look") ──────────────────────────────
st.markdown('<div class="section-title">DRIFT DES MENACES : VOLUME VS ACCÉLÉRATION</div>', unsafe_allow_html=True)

fig_drift = px.scatter(
    drift_df,
    x="occ_3j",
    y="acceleration",
    size="src_3j",
    color="acceleration",
    text="keyword",
    labels={"occ_3j": "Volume de mentions (3j)", "acceleration": "Indice d'accélération"},
    color_continuous_scale="Purples",
    height=500
)
fig_drift.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='rgba(255,255,255,0.2)')))
fig_drift.add_hline(y=1.5, line_dash="dash", line_color="#a855f7", annotation_text="Tendance Émergente")
fig_drift.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,20,34,0.6)", font=dict(family="Roboto Mono", color="#94a3b8"))
st.plotly_chart(fig_drift, use_container_width=True)

# ── Visual 2 : Signal-to-Noise (Lollipop PRO) ────────────────────────────────
st.markdown('<div class="section-title">FIABILITÉ DU SIGNAL (SOURCES UNIQUES)</div>', unsafe_allow_html=True)

# On affiche le ratio Sources / Mentions pour voir si c'est du spam ou une vraie news
df_snr = drift_df.nlargest(20, 'occ_3j').sort_values('src_3j')

fig_snr = go.Figure()
fig_snr.add_trace(go.Bar(
    y=df_snr['keyword'], x=df_snr['src_3j'],
    orientation='h', name='Sources Uniques',
    marker_color='#a855f7', opacity=0.8,
    hovertemplate="Sources : %{x}"
))
fig_snr.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,20,34,0.6)",
    height=500, font=dict(family="Roboto Mono", color="#94a3b8"),
    barmode='stack', margin=dict(l=20, r=20, t=20, b=20)
)
st.plotly_chart(fig_snr, use_container_width=True)

# ── Visual 3 : Matrix Contextuelle ──────────────────────────────────────────
st.markdown('<div class="section-title">EXPLORATEUR DE FLUX</div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 2])
with c1:
    selected_k = st.selectbox("Inspecter un mot-clé", drift_df.sort_values('occ_3j', ascending=False)['keyword'])
with c2:
    # Simuler la récupération des articles liés au mot-clé (à adapter selon ta fonction get_stg)
    st.markdown(f"**Dernières alertes pour : {selected_k}**")
    # Simulation de liste épurée
    for i in range(3):
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:5px; margin-bottom:5px; border-left:2px solid #a855f7;">
            <small style="color:#a855f7">DÉTECTION #00{i+1}</small><br>
            <span style="font-size:0.9rem">Anomalie détectée sur la source BleepingComputer concernant {selected_k}...</span>
        </div>
        """, unsafe_allow_html=True)