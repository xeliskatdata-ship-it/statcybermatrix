"""
CyberPulse -- KPI 1
Articles collectés par jour / par source
Design : fond bokeh, small multiples, heatmap
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from db_connect import get_mart_k1, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 1 - Articles", layout="wide")

# ── CSS global ────────────────────────────────────────────────────────────────
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
[data-testid="stSidebar"] * { color: #a8b8d0 !important; }

.kpi-tag{display:inline-block;font-family:'Roboto Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#3b82f6;background:rgba(59,130,246,.1);
border:1px solid rgba(59,130,246,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}

.page-title {
    text-align: center;
    font-size: 2.8rem;
    font-weight: 700;
    color: #3b82f6;
    margin-bottom: 20px;
    line-height: 1.2;
    font-family: 'Roboto', sans-serif;
}

.desc-box {
    background: rgba(15,20,34,0.8);
    border: 1px solid #1e2a42;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 20px;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
    backdrop-filter: blur(8px);
    text-align: center;
}
.desc-line { color: #94a3b8; font-size: 1rem; line-height: 1.8; }
.desc-line b { color: #cbd5e1; }

.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.metric-card{
    background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:10px;
    padding:28px 24px; position:relative; overflow:hidden; backdrop-filter:blur(8px);
    text-align:center; transition:border-color 0.2s,transform 0.2s,box-shadow 0.2s; cursor:default;
}
.metric-card:hover { border-color:#3b82f6; transform:translateY(-3px); box-shadow:0 8px 28px rgba(59,130,246,0.18); background:rgba(20,28,48,0.95); }
.metric-card::after{content:'';position:absolute;top:0;left:0;width:100%;height:3px;background:#3b82f6;border-radius:10px 10px 0 0;}
.metric-val{font-family:'Roboto Mono',monospace;font-size:3rem;font-weight:700;color:#e2e8f0;}
.metric-lbl{font-size:1rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-top:10px;}
.metric-sub{font-size:0.95rem;color:#22c55e;margin-top:8px;}

.insight-box{background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#93c5fd;font-size:0.88rem;backdrop-filter:blur(8px);}

.section-title{font-family:'Roboto Mono',monospace;font-size:0.7rem;letter-spacing:.18em;
text-transform:uppercase;color:#64748b;border-left:3px solid #3b82f6;padding-left:10px;margin:24px 0 12px;}
.section-title-center{font-family:'Roboto Mono',monospace;font-size:0.7rem;letter-spacing:.18em;
text-transform:uppercase;color:#64748b;border-bottom:1px solid #3b82f6;
padding-bottom:6px;margin:24px auto 16px;width:fit-content;display:block;text-align:center;}
</style>
""", unsafe_allow_html=True)

# ── Fond animé ECG ────────────────────────────────────────────────────────────
# components.html(height=0) est la seule méthode fiable pour exécuter du JS
# dans Streamlit. window.parent.document accède à la vraie page (même origine).
# Le point traverse toute la hauteur de l'écran — amplitude = H/2 - marge.
# Traîne courte : clearRect complet + historique limité à TRAIL_PX points.
components.html("""
<script>
(function() {
  var p = window.parent.document;
  var w = window.parent;

  // ── Réglages ─────────────────────────────────────────────────────────────
  var PT_SIZE  = 24;
  var TRAIL_PX = 270;
  var SPD      = 2;
  // ─────────────────────────────────────────────────────────────────────────

  function ecgValue(x, H) {
    var margin = PT_SIZE + 10;
    var maxAmp = H / 2 - margin;
    var mod = x % 220;
    var raw;
    if(mod<70)  raw = Math.sin(mod*0.05)*5;
    else if(mod<80)  raw = (mod-70)*13;
    else if(mod<85)  raw = 130-(mod-80)*55;
    else if(mod<90)  raw = -145+(mod-85)*32;
    else if(mod<100) raw = -25+(mod-90)*3;
    else if(mod<115) raw = Math.sin((mod-100)*0.4)*9;
    else raw = Math.sin(mod*0.04)*3;
    return (raw / 130) * maxAmp;
  }

  function startECG() {
    // Supprime l'ancien canvas si présent
    var old = p.getElementById('ecg-bg');
    if (old) old.parentNode.removeChild(old);

    var cv = p.createElement('canvas');
    cv.id = 'ecg-bg';
    cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
    p.body.appendChild(cv);

    var ctx = cv.getContext('2d');
    var t = 0, ecgX = 0, history = [];
    var alive = true;

    function resize() {
      cv.width  = p.documentElement.clientWidth;
      cv.height = p.documentElement.clientHeight;
    }
    resize();
    w.addEventListener('resize', resize);

    var dots = [];
    for(var i=0;i<50;i++) dots.push({
      x: Math.random()*cv.width, y: Math.random()*cv.height,
      r: Math.random()*1.5+0.3,
      phase: Math.random()*Math.PI*2, speed: Math.random()*0.008+0.004,
      dx: (Math.random()-0.5)*0.15, dy: (Math.random()-0.5)*0.15,
      color: Math.random()>0.6?'59,130,246':(Math.random()>0.5?'168,85,247':'20,184,166')
    });

    var rings = [];
    function addRing(){ rings.push({r:0, a:0.45}); }
    addRing();

    function draw() {
      // Vérifie que le canvas est toujours dans le DOM
      if (!p.getElementById('ecg-bg') || !alive) return;

      var W = cv.width, H = cv.height;
      ctx.clearRect(0,0,W,H);
      t += 0.016;

      var grd = ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,W*0.6);
      grd.addColorStop(0,'rgba(14,30,60,0.35)');
      grd.addColorStop(1,'rgba(5,10,20,0)');
      ctx.fillStyle = grd; ctx.fillRect(0,0,W,H);

      rings.forEach(function(r,i){
        r.r+=1.0; r.a-=0.005;
        if(r.a<=0){rings.splice(i,1);return;}
        ctx.beginPath(); ctx.arc(W/2,H/2,r.r,0,Math.PI*2);
        ctx.strokeStyle='rgba(59,130,246,'+r.a*0.35+')';
        ctx.lineWidth=1; ctx.stroke();
      });
      if(Math.floor(t*1.2)%3===0&&rings.length<6) addRing();

      dots.forEach(function(d){
        d.phase+=d.speed; d.x+=d.dx; d.y+=d.dy;
        if(d.x<0)d.x=W; if(d.x>W)d.x=0;
        if(d.y<0)d.y=H; if(d.y>H)d.y=0;
        var op=0.3+Math.abs(Math.sin(d.phase))*0.5;
        ctx.beginPath(); ctx.arc(d.x,d.y,d.r,0,Math.PI*2);
        ctx.fillStyle='rgba('+d.color+','+op+')'; ctx.fill();
      });

      history.push({x: ecgX % W, y: H/2 - ecgValue(ecgX, H)});
      ecgX += SPD;
      var maxPts = Math.round(TRAIL_PX / SPD);
      if(history.length > maxPts) history.shift();

      if(history.length > 1){
        for(var k=1; k<history.length; k++){
          var prog  = k / history.length;
          var alpha = prog * 0.85;
          var isSpike = Math.abs(history[k].y - H/2) > H * 0.08;
          ctx.beginPath();
          ctx.moveTo(history[k-1].x, history[k-1].y);
          ctx.lineTo(history[k].x,   history[k].y);
          ctx.strokeStyle = isSpike
            ? 'rgba(168,85,247,'+alpha+')'
            : 'rgba(59,130,246,'+(alpha*0.6)+')';
          ctx.lineWidth = isSpike ? 3.5 : 1.8;
          ctx.stroke();
        }
        var head = history[history.length-1];
        var glow = ctx.createRadialGradient(head.x,head.y,0,head.x,head.y,PT_SIZE*4);
        glow.addColorStop(0,'rgba(168,85,247,0.55)');
        glow.addColorStop(1,'rgba(168,85,247,0)');
        ctx.fillStyle = glow;
        ctx.fillRect(head.x-PT_SIZE*4, head.y-PT_SIZE*4, PT_SIZE*8, PT_SIZE*8);
        ctx.beginPath();
        ctx.arc(head.x, head.y, PT_SIZE, 0, Math.PI*2);
        ctx.fillStyle = 'rgba(220,170,255,1)';
        ctx.fill();
      }

      requestAnimationFrame(draw);
    }

    draw();
    return function() { alive = false; };
  }

  // Lance l'animation
  var stop = startECG();

  // Watchdog : vérifie toutes les 2s si le canvas est vivant, relance si besoin
  setInterval(function() {
    var cv = p.getElementById('ecg-bg');
    if (!cv) {
      stop && stop();
      stop = startECG();
    }
  }, 2000);

  // Relance si la page redevient visible (changement d'onglet)
  p.addEventListener('visibilitychange', function() {
    if (!p.hidden) {
      stop && stop();
      stop = startECG();
    }
  });

})();
</script>
""", height=0)


# ── Palette couleurs ──────────────────────────────────────────────────────────
COLORS = {
    "NewsAPI":"#3b82f6","The Hacker News":"#22c55e","BleepingComputer":"#f59e0b",
    "CISA Alerts":"#ef4444","Krebs on Security":"#06b6d4","Dark Reading":"#8b5cf6",
    "SecurityWeek":"#f97316","Cyber Scoop":"#10b981","Threatpost":"#ec4899",
    "Schneier on Security":"#14b8a6","The Record":"#6366f1","Infosecurity Magazine":"#84cc16",
    "Helpnet Security":"#fb923c","Graham Cluley":"#a78bfa","Zataz":"#a855f7",
    "ANSSI":"#0ea5e9","CERT-EU":"#2563eb","French Breaches":"#f43f5e",
    "Malwarebytes Labs":"#dc2626","Naked Security":"#7c3aed","We Live Security":"#059669",
    "Trend Micro":"#d97706","Recorded Future Blog":"#0891b2","Cybereason":"#9333ea",
    "Bellingcat":"#ca8a04","SANS ISC":"#1d4ed8","Mandiant Blog":"#c2410c",
    "CrowdStrike Blog":"#e11d48","Securelist":"#4f46e5","Proofpoint":"#0369a1",
    "CIRCL":"#047857","Abuse.ch":"#9f1239","Citizen Lab":"#0e7490",
    "GreyNoise Blog":"#1e3a5f","VulnCheck":"#166534","AttackerKB":"#7f1d1d",
}

SOURCE_GROUPS = {
    "Tous les groupes": None,
    "API REST":["NewsAPI"],
    "Cyber généraliste":["The Hacker News","BleepingComputer","CISA Alerts",
                         "Krebs on Security","Dark Reading","SecurityWeek",
                         "Cyber Scoop","Threatpost","Schneier on Security",
                         "The Record","Infosecurity Magazine","Helpnet Security",
                         "Graham Cluley","Zataz","ANSSI","CERT-EU","French Breaches"],
    "Cyber spécialisé":["Malwarebytes Labs","Naked Security","We Live Security",
                        "Trend Micro","Recorded Future Blog","Cybereason"],
    "OSINT":["Bellingcat"],
    "Threat Intelligence":["SANS ISC","Mandiant Blog","CrowdStrike Blog",
                           "Securelist","Proofpoint","CIRCL","Abuse.ch"],
    "Investigation":["Citizen Lab","GreyNoise Blog","VulnCheck","AttackerKB"],
}

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(5,10,20,0.6)',
    font=dict(family='Roboto', color='#94a3b8'),
)

# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 1</div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Articles collectés par jour & par source</div>', unsafe_allow_html=True)

# ── Refresh + badge ───────────────────────────────────────────────────────────
_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("⟳ Actualiser", use_container_width=True):
        force_refresh()
        st.rerun()

# ── Chargement ────────────────────────────────────────────────────────────────
try:
    df = get_mart_k1()
    with col_b:
        st.markdown(
            f'<div class="badge-live"><span class="dot-live"></span>'
            f'Dernière mise à jour : le {datetime.now().strftime("%d/%m/%Y")} à {datetime.now().strftime("%H:%M:%S")} · {len(df):,} articles</div>',
            unsafe_allow_html=True
        )
except Exception as e:
    st.error(f"Connexion PostgreSQL impossible : {e}")
    st.stop()

if df.empty:
    st.warning("mart_k1 est vide. Lance `dbt run` depuis le dossier dbt/.")
    st.stop()

# ── Filtres ───────────────────────────────────────────────────────────────────
st.markdown("<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:1.4rem;letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;margin:28px auto 16px'>Filtres</div>", unsafe_allow_html=True)

_, col1, col2, _ = st.columns([1, 2, 2, 1])

with col1:
    groupe_sel = st.selectbox("Groupe de sources", list(SOURCE_GROUPS.keys()), key="k1_groupe")

with col2:
    periode_opts = {"7 derniers jours": 7, "14 derniers jours": 14, "30 derniers jours": 30}
    periode_sel = st.selectbox("Période", list(periode_opts.keys()), key="k1_periode")
    n_days = periode_opts[periode_sel]

sources_dispo = sorted(df['source'].dropna().unique().tolist())
if SOURCE_GROUPS[groupe_sel]:
    sources = [s for s in SOURCE_GROUPS[groupe_sel] if s in sources_dispo]
else:
    sources = sources_dispo

date_cut = pd.Timestamp.now() - pd.Timedelta(days=n_days)
mask = df['source'].isin(sources) & (df['published_date'] >= date_cut)
agg = df[mask].copy()

if agg.empty:
    agg = df[df['source'].isin(sources)].copy()
    st.info("Pas de données pour la fenêtre sélectionnée — affichage de toutes les données disponibles.")

agg['date'] = agg['published_date'].dt.strftime('%Y-%m-%d')
agg = agg[['date', 'source', 'nb_articles']].copy()
agg_total = agg.groupby('date')['nb_articles'].sum().reset_index()
agg_total.columns = ['date', 'total']

# ── Métriques résumées ────────────────────────────────────────────────────────
st.markdown("<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:1.4rem;letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;margin:28px auto 16px'>Vue d\'ensemble</div>", unsafe_allow_html=True)

total_global   = int(agg['nb_articles'].sum())
nb_src_actives = agg[agg['nb_articles'] > 0]['source'].nunique()
top_source     = agg.groupby('source')['nb_articles'].sum().idxmax() if total_global > 0 else "—"
top_total      = int(agg.groupby('source')['nb_articles'].sum().max()) if total_global > 0 else 0
moy_jour       = round(agg_total['total'].mean(), 1) if not agg_total.empty else 0
top_src_short  = top_source[:18] if len(top_source) > 18 else top_source

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:transparent; font-family:'Roboto',sans-serif; }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }}
.card {{
    background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:10px;
    padding:28px 20px; text-align:center; position:relative; overflow:hidden;
    transition:border-color 0.2s,transform 0.2s,box-shadow 0.2s; cursor:default;
    backdrop-filter:blur(8px);
}}
.card::before {{ content:''; position:absolute; top:0; left:0; width:100%; height:3px; background:#3b82f6; border-radius:10px 10px 0 0; }}
.card:hover {{ border-color:#3b82f6; transform:translateY(-3px); box-shadow:0 8px 28px rgba(59,130,246,0.18); background:rgba(20,28,48,0.95); }}
.val {{ font-family:'Roboto Mono',monospace; font-size:3rem; font-weight:700; color:#e2e8f0; }}
.lbl {{ font-size:1rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.08em; margin-top:10px; }}
.sub {{ font-size:1.1rem; color:#22c55e; margin-top:8px; font-weight:500; }}
</style>
<div class="grid">
  <div class="card">
    <div class="val" id="v1">0</div>
    <div class="lbl">Articles collectés</div>
    <div class="sub">{n_days} jours</div>
  </div>
  <div class="card">
    <div class="val" id="v2">0</div>
    <div class="lbl">Sources actives</div>
    <div class="sub">sur {len(sources)} sélectionnées</div>
  </div>
  <div class="card">
    <div class="val" style="font-size:1.8rem" id="v3">{top_src_short}</div>
    <div class="lbl">Source la + active</div>
    <div class="sub">{top_total} articles</div>
  </div>
  <div class="card">
    <div class="val" id="v4">0</div>
    <div class="lbl">Moy. articles/jour</div>
    <div class="sub">toutes sources</div>
  </div>
</div>
<script>
function animCount(id, target, duration, isFloat) {{
  var el = document.getElementById(id);
  if (!el || isNaN(target)) return;
  var step = target / (duration / 16), current = 0;
  var timer = setInterval(function() {{
    current += step;
    if (current >= target) {{ current = target; clearInterval(timer); }}
    el.textContent = isFloat ? current.toFixed(1).replace('.',',') : Math.floor(current).toLocaleString('fr-FR');
  }}, 16);
}}
animCount('v1', {total_global}, 1200, false);
animCount('v2', {nb_src_actives}, 800, false);
animCount('v4', {moy_jour}, 1000, true);
</script>
""", height=160)

# ── Small Multiples ───────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:1.4rem;"
    "letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;"
    "border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;"
    "margin:28px auto 16px'>Small multiples — activité par source</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:20px'>"
    "Chaque mini-graphique représente une source. "
    "La courbe montre le volume d'articles collectés par jour sur la période sélectionnée."
    "</div>", unsafe_allow_html=True
)

all_dates = sorted(agg['date'].unique())
sources_actives = sorted(agg[agg['nb_articles'] > 0]['source'].unique())

if sources_actives:
    n_cols = 4
    n_rows = -(-len(sources_actives) // n_cols)

    fig_sm = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=[s[:20] for s in sources_actives],
        vertical_spacing=0.08,
        horizontal_spacing=0.04,
    )

    for idx, src in enumerate(sources_actives):
        row = idx // n_cols + 1
        col = idx % n_cols + 1
        src_data = agg[agg['source'] == src].sort_values('date')
        color = COLORS.get(src, "#3b82f6")

        fig_sm.add_trace(
            go.Bar(
                x=src_data['date'],
                y=src_data['nb_articles'],
                name=src,
                marker_color=color,
                opacity=0.85,
                marker_line_color=color,
                marker_line_width=0.5,
                showlegend=False,
                hovertemplate=f"<b>{src}</b><br>%{{x}}<br>%{{y}} articles<extra></extra>",
            ),
            row=row, col=col
        )

    for i in range(1, n_rows * n_cols + 1):
        fig_sm.update_xaxes(
            showticklabels=False, showgrid=False, zeroline=False,
            row=(i - 1) // n_cols + 1, col=(i - 1) % n_cols + 1
        )
        fig_sm.update_yaxes(
            showgrid=True, gridcolor='rgba(30,42,66,0.5)',
            tickfont=dict(size=9, color='#64748b'),
            zeroline=False,
            row=(i - 1) // n_cols + 1, col=(i - 1) % n_cols + 1
        )

    fig_sm.update_layout(
        **PLOTLY_BASE,
        height=max(300, n_rows * 130),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    for ann in fig_sm['layout']['annotations']:
        ann['font'] = dict(size=16, color='#cbd5e1', family='Roboto')
        ann['xanchor'] = 'center'

    st.plotly_chart(fig_sm, use_container_width=True)

# ── Heatmap ───────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:1.4rem;"
    "letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;"
    "border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;"
    "margin:28px auto 16px'>Intensité par source & par jour</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:20px'>"
    "Plus la couleur est claire, plus la source a édité d'articles ce jour-là."
    "</div>", unsafe_allow_html=True
)

heatmap_data = agg.pivot_table(
    index='source', columns='date',
    values='nb_articles', aggfunc='sum', fill_value=0
)

if not heatmap_data.empty:
    fig_heat = go.Figure(go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns.tolist(),
        y=heatmap_data.index.tolist(),
        colorscale=[[0.0,'#0a1628'],[0.15,'#1e3a5f'],[0.4,'#1d4ed8'],[0.7,'#3b82f6'],[1.0,'#93c5fd']],
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>%{x}<br>%{z} articles<extra></extra>',
        text=heatmap_data.values,
        texttemplate='%{text}',
        textfont=dict(size=18, color='white'),
        showscale=True,
        colorbar=dict(title='Articles', tickfont=dict(color='#94a3b8', size=14)),
    ))
    fig_heat.update_layout(
        **PLOTLY_BASE,
        xaxis=dict(gridcolor='#1e2a42', tickangle=-30, tickfont=dict(size=16, color='#94a3b8')),
        yaxis=dict(gridcolor='#1e2a42', tickfont=dict(size=16, color='#cbd5e1')),
        margin=dict(l=20, r=20, t=10, b=40),
        height=max(200, 50 + len(heatmap_data) * 55),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Insight automatique ───────────────────────────────────────────────────────
if total_global > 0:
    top_day = agg.loc[agg['nb_articles'].idxmax()]
    st.markdown(f"""
    <div class="insight-box">
        <b>Insights :</b> {total_global:,} articles collectés sur {n_days} jours.
        Source la plus active : <b>{top_source}</b> ({top_total} articles, {round(top_total/total_global*100,1)}%).
        Pic de collecte : <b>{top_day['date']}</b> — <b>{int(top_day['nb_articles'])}</b> articles depuis <b>{top_day['source']}</b>.
    </div>
    """, unsafe_allow_html=True)

# ── Détail articles par source ────────────────────────────────────────────────
st.markdown('<div class="section-title">Articles récents par source</div>', unsafe_allow_html=True)

src_select = st.selectbox(
    "Choisir une source",
    options=["-- Sélectionner --"] + sorted(sources_actives),
    key="k1_src_detail"
)

if src_select != "-- Sélectionner --":
    try:
        df_articles = get_stg_articles(limit=2000)
        df_detail = df_articles[df_articles['source'] == src_select].sort_values('published_date', ascending=False)
    except Exception as e:
        st.error(f"Erreur : {e}")
        df_detail = pd.DataFrame()

    if df_detail.empty:
        st.info(f"Aucun article disponible pour {src_select}.")
    else:
        couleur = COLORS.get(src_select, "#3b82f6")
        st.markdown(f"""
        <div style='background:rgba(15,20,34,0.85);border:1px solid #1e2a42;
        border-left:3px solid {couleur};border-radius:8px;padding:12px 18px;margin-bottom:16px;backdrop-filter:blur(8px)'>
            <span style='font-family:Roboto Mono,monospace;font-size:0.8rem;color:{couleur}'>{src_select.upper()}</span>
            <span style='color:#64748b;font-size:0.8rem'> — {len(df_detail)} articles disponibles</span>
        </div>""", unsafe_allow_html=True)

        for _, row in df_detail.head(15).iterrows():
            titre = str(row.get('title', 'Sans titre'))
            url   = str(row.get('url', ''))
            date  = str(row.get('published_date', ''))[:10]
            cat   = str(row.get('category', 'général'))
            lien  = f'<a href="{url}" target="_blank" style="color:#e2e8f0;text-decoration:none">{titre}</a>' if url and url != 'nan' else titre
            st.markdown(
                f"<div style='background:rgba(15,20,34,0.8);border:1px solid #1e2a42;"
                f"border-radius:6px;padding:12px 16px;margin-bottom:8px;backdrop-filter:blur(6px)'>"
                f"<div style='font-size:0.9rem'>{lien}</div>"
                f"<div style='margin-top:6px;font-size:0.75rem;color:#475569'>"
                f"{date} &nbsp;·&nbsp;"
                f"<span style='background:rgba(59,130,246,.15);color:#93c5fd;border-radius:4px;padding:1px 8px'>{cat}</span>"
                f"</div></div>", unsafe_allow_html=True
            )
        if len(df_detail) > 15:
            st.caption(f"... et {len(df_detail) - 15} articles supplémentaires non affichés.")

# ── Export CSV ────────────────────────────────────────────────────────────────
st.markdown("---")
csv = agg.rename(columns={'nb_articles':'articles'}).to_csv(index=False).encode('utf-8')
st.download_button(
    "⬇ Télécharger les données (CSV)",
    data=csv,
    file_name=f"kpi1_articles_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)
