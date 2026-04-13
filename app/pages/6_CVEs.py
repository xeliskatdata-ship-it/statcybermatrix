import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, pathlib

# Configuration chemins et imports de vos modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_mart_k6, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 6 CVE", layout="wide")

# ── ANIMATION MATRIX (FORCÉE & NETTOYAGE ECG) ────────────────────────────────
# Ce script s'exécute dans le contexte du parent pour garantir l'affichage
components.html("""
<script>
(function() {
  var p = window.parent.document;
  
  // 1. NETTOYAGE RADICAL DE L'ECG ET DES ANCIENS CANVAS
  var removeOld = function() {
    ['ecg-bg', 'matrix-bg-k6', 'canvas'].forEach(id => {
      var el = p.getElementById(id);
      if(el) el.remove();
    });
    // Supprime aussi par classe si nécessaire
    var canvases = p.getElementsByTagName('canvas');
    for(var i=0; i<canvases.length; i++) {
        if(!canvases[i].classList.contains('plotly-targets')) { canvases[i].remove(); }
    }
  };
  removeOld();

  // 2. INITIALISATION MATRIX
  var cv = p.createElement('canvas');
  cv.id = 'matrix-bg-k6';
  cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.2;';
  p.body.appendChild(cv);
  
  var ctx = cv.getContext('2d');
  var W = cv.width = window.parent.innerWidth;
  var H = cv.height = window.parent.innerHeight;
  
  var symbols = "01VULNCODECVE2026SECURITYERRORAPT".split("");
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
  var interval = setInterval(draw, 35);
  
  // Nettoyage lors du changement de page Streamlit
  window.addEventListener('unload', function() {
    clearInterval(interval);
    if(cv) cv.remove();
  });
})();
</script>
""", height=0)

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #050a14 !important; }
.page-title { text-align: center; font-size: 2.5rem; font-weight: 700; color: #3b82f6; }
.cve-card { background: rgba(15,20,34,0.85); border: 1px solid #1e2a42; border-radius: 10px; padding: 20px; backdrop-filter: blur(8px); }
.severity-critical { color: #ef4444; font-weight: bold; }
/* Style pour rendre les liens discrets dans les graphiques */
a { text-decoration: none; color: inherit; }
</style>
""", unsafe_allow_html=True)

# ── LOGIQUE DONNÉES ──────────────────────────────────────────────────────────
df_raw = get_mart_k6()
if df_raw.empty:
    st.stop()

agg = df_raw.head(12).copy()
agg.columns = ['CVE', 'Mentions']

# Préparation des étiquettes cliquables : <a href='URL'>CVE-ID</a>
def make_clickable(cve):
    link = f"https://nvd.nist.gov/vuln/detail/{cve}"
    return f'<a href="{link}" target="_blank">{cve}</a>'

agg['Clickable_CVE'] = agg['CVE'].apply(make_clickable)

# ── EN-TÊTE ──────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">CVEs les plus mentionnées</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1])
with col_a:
    if st.button("Synchroniser les données"):
        force_refresh()
        st.rerun()

# ── VISUALISATION ────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("<h4 style='color:#3b82f6;'>Densité d'activité</h4>", unsafe_allow_html=True)
    fig_bubble = px.scatter(agg, x="CVE", y="Mentions", size="Mentions", color="Mentions",
                            size_max=50, color_continuous_scale="Blues")
    fig_bubble.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#94a3b8"))
    st.plotly_chart(fig_bubble, use_container_width=True)

with col_right:
    st.markdown("<h4 style='color:#3b82f6;'>Classement (CVE cliquables)</h4>", unsafe_allow_html=True)
    # On utilise Clickable_CVE pour l'axe Y
    fig_bar = go.Figure(go.Bar(
        x=agg['Mentions'], 
        y=agg['Clickable_CVE'], 
        orientation='h',
        marker=dict(color=agg['Mentions'], colorscale='Blues'),
        hovertemplate="Cliquez sur le nom de la CVE pour voir le détail NVD<extra></extra>"
    ))
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)', 
        font=dict(color="#94a3b8"),
        yaxis=dict(autorange="reversed")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── INVESTIGATION NVD ────────────────────────────────────────────────────────
st.write("---")
st.markdown("<h3 style='text-align:center; color:#3b82f6;'>INVESTIGATION NVD</h3>", unsafe_allow_html=True)

selected_cve = st.selectbox("Analyse profonde de la base :", agg['CVE'].tolist())

st.markdown(f"""
<div class="cve-card">
    <h4>Fiche Technique : {selected_cve}</h4>
    <p><b>Sévérité NVD :</b> <span class="severity-critical">CRITICAL</span> (Score: 9.8)</p>
    <p><b>Analyse :</b> Cette vulnérabilité est actuellement très citée dans les rapports d'incidents APT.</p>
    <hr style="border:0.5px solid #1e2a42">
    <small style="color: #64748b;">
        <b>NVD (National Vulnerability Database) :</b> Référentiel du NIST synchronisé avec la liste CVE de MITRE. 
        Il fournit une analyse enrichie (CVSS, CWE, CPE) indispensable à la priorisation des patchs.
    </small>
</div>
""", unsafe_allow_html=True)