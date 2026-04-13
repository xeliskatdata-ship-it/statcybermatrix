"""
StatCyberMatrix -- KPI 3
Analyse de la répartition des menaces
Design : Sentinel Code Rain Blue Edition
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from db_connect import get_mart_k3, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 3 Menaces", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── Helper : titre de section centré ──────────────────────────────────────────
def _section_title(text: str, size: str = "1.4rem"):
    st.markdown(
        f"<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:{size};"
        "letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;"
        "border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;"
        f"margin:28px auto 16px'>{text}</div>",
        unsafe_allow_html=True,
    )


# ── CSS global (Style unifié avec KPI1) ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif;}

.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        radial-gradient(circle, rgba(59,130,246,0.15) 1px, transparent 1px),
        radial-gradient(circle, rgba(96,165,250,0.08) 1px, transparent 1px),
        radial-gradient(circle, rgba(147,197,253,0.06) 1px, transparent 1px);
    background-size: 80px 80px, 130px 130px, 200px 200px;
    background-position: 0 0, 40px 40px, 80px 80px;
    filter: blur(0.8px);
    z-index: 0;
    pointer-events: none;
}
[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }
[data-testid="stSidebar"] { z-index: 2 !important; background: #0a1628 !important; border-right: 1px solid rgba(30,111,255,0.2); }

.kpi-tag{display:inline-block;font-family:'Roboto Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#3b82f6;background:rgba(59,130,246,.1);
border:1px solid rgba(59,130,246,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}

.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #3b82f6;
    margin-bottom: 20px; text-shadow: 0 0 15px rgba(59,130,246,0.3);
}

.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.insight-box{background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#93c5fd;font-size:0.88rem;backdrop-filter:blur(8px);}
</style>
""", unsafe_allow_html=True)

# ── FOND ANIMÉ : SENTINEL CODE RAIN (VERSION BLEUE) ───────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  function startCodeRain(){
    var old=p.getElementById('sentinel-rain-bg-k3'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='sentinel-rain-bg-k3';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.12;';
    p.body.appendChild(cv);
    var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
    var symbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
    var fontSize = 14; var columns = W / fontSize; var drops = [];
    for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
    function draw(){
      if(!p.getElementById('sentinel-rain-bg-k3'))return;
      ctx.fillStyle = 'rgba(5, 10, 20, 0.08)'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#3b82f6'; ctx.font = fontSize + 'px Roboto Mono';
      for (var i = 0; i < drops.length; i++) {
        var text = symbols[Math.floor(Math.random() * symbols.length)];
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

# ── Palette & config ──────────────────────────────────────────────────────────
COLORS_MAP = {
    'vulnerability': '#3b82f6', 'ransomware': '#ef4444', 'phishing': '#f59e0b',
    'malware': '#a855f7', 'apt': '#14b8a6', 'ddos': '#22c55e',
    'data_breach': '#6366f1', 'supply_chain': '#ec4899', 'cryptography': '#06b6d4',
    'defense': '#f97316', 'offensive': '#84cc16', 'compliance': '#0ea5e9',
    'identity': '#e879f9', 'general': '#64748b',
}

CAT_DESC = {
    'ransomware': 'Chiffrement et extorsion',
    'phishing': 'Ingénierie sociale et vol identifiants',
    'vulnerability': 'Exploitation de failles logicielles',
    'malware': 'Logiciels malveillants divers',
    'apt': 'Menaces persistantes avancées',
    'ddos': 'Déni de service distribué',
    'data_breach': 'Exfiltration de données',
    'supply_chain': 'Compromission chaîne logistique',
    'cryptography': 'Chiffrement et certificats',
    'defense': 'Opérations de sécurité',
    'offensive': 'Sécurité offensive et pentest',
    'compliance': 'Conformité et réglementation',
    'identity': 'Identité et gestion des accès',
    'general': 'Articles non catégorisés',
}

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(5,10,20,0.6)',
    font=dict(family='Roboto', color='#94a3b8'),
)

# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 3</div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Analyse Vectorielle des Menaces</div>', unsafe_allow_html=True)

# ── Refresh + badge ───────────────────────────────────────────────────────────
_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("⟳ Synchroniser", use_container_width=True):
        force_refresh()
        st.rerun()

# ── Chargement ────────────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k3()
    load_ok = not df_raw.empty
    load_ts = datetime.now().strftime('%H:%M:%S')
    with col_b:
        st.markdown(
            f'<div class="badge-live"><span class="dot-live"></span>'
            f'LIVE · MàJ {load_ts} · {int(df_raw["nb_articles"].sum()):,} articles</div>',
            unsafe_allow_html=True,
        )
except Exception as e:
    st.error(f"Connexion PostgreSQL impossible : {e}")
    st.stop()

if not load_ok:
    st.warning("Données indisponibles.")
    st.stop()

# ── Filtres sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtres")
    sources_all = sorted(df_raw['source'].dropna().unique().tolist())
    sel_sources = st.multiselect("Sources de données", sources_all, default=sources_all)

df = df_raw[df_raw['source'].isin(sel_sources)] if sel_sources else df_raw

agg = (
    df.groupby('category', as_index=False)['nb_articles']
    .sum()
    .sort_values('nb_articles', ascending=False)
)
total = int(agg['nb_articles'].sum())

# ── Métriques ─────────────────────────────────────────────────────────────────
top_cat = agg.iloc[0]['category'] if not agg.empty else "N/A"
top_val = int(agg.iloc[0]['nb_articles']) if not agg.empty else 0
top_pct = round(top_val / total * 100, 1) if total > 0 else 0
nb_cats = len(agg[agg['nb_articles'] > 0])

_section_title("Vue d'ensemble")

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:transparent; font-family:'Roboto',sans-serif; }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }}
.card {{
    background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:10px;
    padding:28px 20px; text-align:center; position:relative; overflow:hidden;
    backdrop-filter:blur(8px); transition: 0.2s;
}}
.card::before {{ content:''; position:absolute; top:0; left:0; width:100%; height:3px; }}
.card:nth-child(1)::before {{ background:#3b82f6; }}
.card:nth-child(2)::before {{ background:#ef4444; }}
.card:nth-child(3)::before {{ background:#f59e0b; }}
.card:nth-child(4)::before {{ background:#22c55e; }}
.val {{ font-family:'Roboto Mono',monospace; font-size:3rem; font-weight:700; color:#e2e8f0; }}
.lbl {{ font-size:1rem; color:#94a3b8; text-transform:uppercase; margin-top:10px; }}
</style>
<div class="grid">
  <div class="card"><div class="val" id="v1">0</div><div class="lbl">Volume Total</div></div>
  <div class="card"><div class="val" style="font-size:1.8rem">{top_cat.upper()}</div><div class="lbl">Vecteur Critique</div></div>
  <div class="card"><div class="val" id="v3">0</div><div class="lbl">Catégories actives</div></div>
  <div class="card"><div class="val">LIVE</div><div class="lbl">Status</div></div>
</div>
<script>
function animCount(id, target, duration) {{
  var el = document.getElementById(id);
  var step = target / (duration / 16), current = 0;
  var timer = setInterval(function() {{
    current += step;
    if (current >= target) {{ current = target; clearInterval(timer); }}
    el.textContent = Math.floor(current).toLocaleString('fr-FR');
  }}, 16);
}}
animCount('v1', {total}, 1200);
animCount('v3', {nb_cats}, 800);
</script>
""", height=160)

# ── Graphiques ──────────────────────────────────────────────────────────────
_section_title("Répartition des vecteurs de menace")
col_viz, col_side = st.columns([3, 1])

with col_side:
    viz_type = st.radio("Mode d'affichage", ["Radar Chart", "Donut Chart", "Bar Chart"])
    st.markdown(f"""<div class="insight-box"><b>Analyse :</b><br>La menace <b>{top_cat}</b> domine avec <b>{top_pct}%</b> du flux.</div>""", unsafe_allow_html=True)

with col_viz:
    if viz_type == "Radar Chart":
        fig = go.Figure(data=go.Scatterpolar(r=agg['nb_articles'], theta=agg['category'].str.upper(), fill='toself', line_color='#3b82f6'))
        fig.update_layout(polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(gridcolor='#1e2a42')), **PLOTLY_BASE, height=450)
    elif viz_type == "Donut Chart":
        fig = px.pie(agg, names='category', values='nb_articles', hole=0.6, color='category', color_discrete_map=COLORS_MAP)
        fig.update_layout(**PLOTLY_BASE, height=450, showlegend=False)
    else:
        agg_bar = agg.sort_values('nb_articles')
        fig = go.Figure(go.Bar(x=agg_bar['nb_articles'], y=agg_bar['category'], orientation='h', marker_color='#3b82f6'))
        fig.update_layout(**PLOTLY_BASE, height=450)
    st.plotly_chart(fig, use_container_width=True)

# ── Heatmap ─────────────────────────────────────────────────────────────────
_section_title("Matrice d'occurrence")
pivot = df.pivot_table(index='source', columns='category', values='nb_articles', aggfunc='sum', fill_value=0)
fig_heat = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorscale='Blues'))
fig_heat.update_layout(**PLOTLY_BASE, height=400)
st.plotly_chart(fig_heat, use_container_width=True)

with st.expander("Données brutes"):
    st.dataframe(agg, use_container_width=True, hide_index=True)