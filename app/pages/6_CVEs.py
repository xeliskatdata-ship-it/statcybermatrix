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
from db_connect import get_mart_k6, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 6 CVE", layout="wide")

# ── Helper : titre de section centre ──────────────────────────────────────────
def _section_title(text: str, size: str = "1.4rem"):
    st.markdown(
        f"<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:{size};"
        "letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;"
        "border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;"
        f"margin:28px auto 16px'>{text}</div>",
        unsafe_allow_html=True,
    )

# ── CSS global (Style Matrix Noir & Bleu) ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif; color: #ffffff !important;}

.stApp { background-color: #050a14 !important; }

/* Titre Principal */
.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #3b82f6;
    margin-bottom: 20px; text-shadow: 0 0 15px rgba(59,130,246,0.5);
}

/* Boîte de description */
.desc-box {
    background: rgba(15,20,34,0.8);
    border: 1px solid #1e2a42;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 15px 20px;
    margin-bottom: 25px;
    backdrop-filter: blur(8px);
}
.desc-line { color: #94a3b8; font-size: 0.95rem; line-height: 1.6; }

/* Badge Live */
.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* Cartes CVE */
.cve-card{background:rgba(15,20,34,0.85);border:1px solid #1e2a42;border-radius:10px;
padding:20px 24px;margin-top:16px;backdrop-filter:blur(8px);}
.cve-card-title{font-family:'Roboto Mono',monospace;font-size:1.2rem;font-weight:700;color:#3b82f6;}

/* CVSS Badges */
.badge{display:inline-block;border-radius:4px;padding:2px 10px;font-size:0.75rem;font-weight:600;margin-right:6px;}
.badge-red{background:rgba(239,68,68,.15);color:#ef4444;border:1px solid rgba(239,68,68,.3);}
.badge-orange{background:rgba(249,115,22,.15);color:#f97316;border:1px solid rgba(249,115,22,.3);}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ PLUIE DE CODE (IDENTIQUE KPI 1) ────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  function startCodeRain(){
    var old=p.getElementById('matrix-rain-bg-k6'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='matrix-rain-bg-k6';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.15;';
    p.body.appendChild(cv);
    var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
    var codeSymbols = "01ABCDEFSRATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
    var fontSize = 14; var columns = W / fontSize; var drops = [];
    for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
    function draw(){
      if(!p.getElementById('matrix-rain-bg-k6'))return;
      ctx.fillStyle = 'rgba(5, 10, 20, 0.1)'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#3b82f6'; ctx.font = fontSize + 'px Roboto Mono';
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

# ── Chargement des données ────────────────────────────────────────────────────
df_raw = get_mart_k6()

# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">CVEs les plus mentionnées</div>', unsafe_allow_html=True)

_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Synchroniser", use_container_width=True):
        force_refresh()
        st.rerun()

if df_raw.empty:
    st.info("Aucune donnée disponible.")
    st.stop()

with col_b:
    st.markdown(
        f'<div class="badge-live"><span class="dot-live"></span>'
        f'LIVE - {len(df_raw)} CVEs analysées</div>',
        unsafe_allow_html=True,
    )

# ── Description ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="desc-box">
    <div class="desc-line">
        <b>Surveillance des vulnérabilités :</b> Ce KPI identifie les failles de sécurité les plus discutées sur le Web. 
        Un volume élevé de mentions est souvent le précurseur d'une exploitation massive (0-day) ou d'une campagne de Ransomware majeure.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Métriques Animées (Style KPI1) ──────────────────────────────────────────
top_n = st.sidebar.slider("Nombre de CVEs à analyser", 5, 20, 10)
agg = df_raw.head(top_n).copy()
agg.columns = ['CVE', 'Mentions']

total_uniques = len(df_raw)
top_cve_id = agg.iloc[0]['CVE']
top_cve_val = int(agg.iloc[0]['Mentions'])

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@700&display=swap');
body {{ background:transparent; margin:0; font-family:sans-serif; }}
.grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:15px; }}
.card {{
    background:rgba(15,20,34,0.9); border:1px solid #1e2a42; border-radius:10px;
    padding:20px; text-align:center; color:white; backdrop-filter:blur(8px);
    border-top: 3px solid #3b82f6;
}}
.val {{ font-family:'Roboto Mono',monospace; font-size:2.5rem; font-weight:700; color:#3b82f6; }}
.lbl {{ font-size:0.8rem; color:#94a3b8; text-transform:uppercase; margin-top:5px; }}
</style>
<div class="grid">
  <div class="card"><div class="val" id="v1">0</div><div class="lbl">CVE Uniques</div></div>
  <div class="card"><div class="val" style="font-size:1.8rem">{top_cve_id}</div><div class="lbl">Plus mentionnée</div></div>
  <div class="card"><div class="val" id="v3">0</div><div class="lbl">Mentions Record</div></div>
</div>
<script>
function anim(id, target) {{
  var el = document.getElementById(id);
  var current = 0; var step = target / 50;
  var timer = setInterval(function() {{
    current += step;
    if (current >= target) {{ current = target; clearInterval(timer); }}
    el.textContent = Math.floor(current);
  }}, 20);
}}
anim('v1', {total_uniques});
anim('v3', {top_cve_val});
</script>
""", height=130)

# ── Graphiques Optimisés ──────────────────────────────────────────────────────
_section_title("Visualisation du Risque")

col_left, col_right = st.columns([1, 1])

with col_left:
    # TreeMap pour voir la proportionnalité
    fig_tree = px.treemap(agg, path=['CVE'], values='Mentions',
                          color='Mentions', color_continuous_scale='Blues')
    fig_tree.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           margin=dict(t=10, l=10, r=10, b=10), font=dict(color="#fff"))
    st.plotly_chart(fig_tree, use_container_width=True)

with col_right:
    # Bar Chart Horizontal élégant
    fig_bar = go.Figure(go.Bar(
        x=agg['Mentions'], y=agg['CVE'], orientation='h',
        marker=dict(color=agg['Mentions'], colorscale='Blues'),
        text=agg['Mentions'], textposition='outside'
    ))
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(5,10,20,0.4)',
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(autorange="reversed", tickfont=dict(color='#cbd5e1')),
        margin=dict(t=10, l=10, r=40, b=10), height=400
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── Fiche détail CVE (NVD API) ────────────────────────────────────────────────
_section_title("Investigation NVD")

cve_id = st.selectbox("Sélectionner une CVE pour analyse profonde", agg['CVE'].tolist())

if st.button("Interroger la National Vulnerability Database"):
    # Note: On utilise la fonction _fetch_cve_details existante dans votre code
    from __main__ import _fetch_cve_details, _render_cve_card
    with st.spinner("Récupération des données NIST..."):
        details = _fetch_cve_details(cve_id)
        if details:
            _render_cve_card(details)
        else:
            st.error("Impossible de récupérer les détails NVD pour le moment.")

# ── Référence CVSS ────────────────────────────────────────────────────────────
with st.expander("Comprendre les scores de sévérité (CVSS)"):
    st.info("Le score CVSS v3.1 est le standard utilisé pour évaluer l'urgence d'un correctif.")
    st.markdown("""
    | Score | Sévérité | Action Requise |
    |---|---|---|
    | **9.0 - 10.0** | <span style="color:#ef4444">CRITICAL</span> | Patch immédiat (< 24h) |
    | **7.0 - 8.9** | <span style="color:#f97316">HIGH</span> | Patch urgent (< 72h) |
    | **4.0 - 6.9** | <span style="color:#f59e0b">MEDIUM</span> | Cycle de maintenance habituel |
    """)