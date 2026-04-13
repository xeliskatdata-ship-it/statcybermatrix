import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import time
import sys, pathlib
import os

# Configuration chemins
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_mart_k6, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 6 CVE", layout="wide")

# ── ANIMATION MATRIX (FORCÉE) ────────────────────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document;
  var body = p.body;
  
  function startMatrix(){
    var old = p.getElementById('matrix-bg-k6');
    if(old) old.remove();
    
    var cv = p.createElement('canvas');
    cv.id = 'matrix-bg-k6';
    cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.15;';
    body.appendChild(cv);
    
    var ctx = cv.getContext('2d');
    var W = cv.width = window.parent.innerWidth;
    var H = cv.height = window.parent.innerHeight;
    
    var symbols = "01VULNCODECVE2026SECURITYERROR".split("");
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
  startMatrix();
})();
</script>
""", height=0)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; }
.page-title { text-align: center; font-size: 2.8rem; font-weight: 700; color: #3b82f6; text-shadow: 0 0 15px rgba(59,130,246,0.5); }
.badge-live { display:inline-flex; align-items:center; gap:6px; font-family:'Roboto Mono'; font-size:0.7rem; color:#22c55e; background:rgba(34,197,94,.08); border:1px solid rgba(34,197,94,.2); border-radius:20px; padding:4px 12px; }
.dot-live { width:7px; height:7px; border-radius:50%; background:#22c55e; animation:pulse 2s infinite; }
@keyframes pulse { 0%,100% {opacity:1} 50% {opacity:.4} }
.cve-card { background: rgba(15,20,34,0.85); border: 1px solid #1e2a42; border-radius: 10px; padding: 20px; backdrop-filter: blur(8px); }
.severity-critical { color: #ef4444; font-weight: bold; }
.severity-high { color: #f97316; font-weight: bold; }
.severity-medium { color: #f59e0b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── LOGIQUE DONNÉES ──────────────────────────────────────────────────────────
df_raw = get_mart_k6()
if df_raw.empty:
    st.warning("Aucune donnée CVE disponible.")
    st.stop()

# ── EN-TÊTE ──────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">CVEs les plus mentionnées</div>', unsafe_allow_html=True)

_, col_sync, col_stat, _ = st.columns([2, 1, 2, 2])
with col_sync:
    if st.button("Synchroniser", use_container_width=True):
        force_refresh()
        st.rerun()
with col_stat:
    st.markdown(f'<div class="badge-live"><span class="dot-live"></span>LIVE - {len(df_raw)} CVE ANALYSÉES</div>', unsafe_allow_html=True)

# ── VISUALISATION ────────────────────────────────────────────────────────────
st.write("## ")
agg = df_raw.head(15).copy()
agg.columns = ['CVE', 'Mentions']
# Ajout de sources fictives pour l'exemple (à remplacer par vos URLs réelles)
agg['Source'] = "https://nvd.nist.gov/vuln/detail/" + agg['CVE']

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("<h4 style='text-align:center; color:#3b82f6;'>Densité des Mentions</h4>", unsafe_allow_html=True)
    fig_bubble = px.scatter(agg, x="CVE", y="Mentions", size="Mentions", color="Mentions",
                            hover_name="CVE", size_max=60, color_continuous_scale="Blues")
    fig_bubble.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                             font=dict(color="#94a3b8"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    st.plotly_chart(fig_bubble, use_container_width=True)

with col_right:
    st.markdown("<h4 style='text-align:center; color:#3b82f6;'>Classement & Sources</h4>", unsafe_allow_html=True)
    fig_bar = go.Figure(go.Bar(
        x=agg['Mentions'], y=agg['CVE'], orientation='h',
        marker=dict(color=agg['Mentions'], colorscale='Blues'),
        text=agg['Source'], # On cache l'URL dans le texte pour le hover
        hovertemplate="<b>%{y}</b><br>Mentions: %{x}<br>Source: %{text}<extra></extra>"
    ))
    fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                          font=dict(color="#94a3b8"), yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bar, use_container_width=True)

# ── INVESTIGATION NVD ────────────────────────────────────────────────────────
st.write("---")
st.markdown("<h3 style='text-align:center; color:#3b82f6;'>INVESTIGATION NVD</h3>", unsafe_allow_html=True)

selected_cve = st.selectbox("Sélectionner une CVE pour analyse profonde", agg['CVE'].tolist())

# Simulation du retour de l'API NVD avec correction HTML
severity_html = {
    "CRITICAL": "<span class='severity-critical'>CRITICAL</span>",
    "HIGH": "<span class='severity-high'>HIGH</span>",
    "MEDIUM": "<span class='severity-medium'>MEDIUM</span>"
}

st.markdown(f"""
<div class="cve-card">
    <h4>Analyse détaillée : {selected_cve}</h4>
    <p><b>Sévérité NVD :</b> {severity_html.get("CRITICAL")} (Score: 9.8)</p>
    <p><b>Description :</b> Une vulnérabilité a été identifiée nécessitant une mise à jour immédiate des systèmes affectés.</p>
    <p><b>Statut :</b> Analysé par le NIST.</p>
</div>
""", unsafe_allow_html=True)

# ── FOOTER & ACRONYME ────────────────────────────────────────────────────────
st.write("## ")
st.markdown("""
<div style="background: rgba(59,130,246,0.05); padding: 15px; border-radius: 5px; border: 1px solid rgba(59,130,246,0.2);">
    <small style="color: #64748b;">
        <b>NVD :</b> National Vulnerability Database (Base de données nationale sur les vulnérabilités). 
        C'est le référentiel du gouvernement américain, synchronisé avec la liste CVE, qui fournit des analyses de sévérité et des scores CVSS.
    </small>
</div>
""", unsafe_allow_html=True)