"""
CyberPulse -- KPI 5
Threat Intelligence Matrix — Alertes par semaine et categorie
Design : fond bokeh, animation ECG, cartes animees (style KPI1)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from db_connect import get_mart_k5, get_stg_articles, force_refresh

st.set_page_config(page_title="CyberPulse - KPI 5 Alertes", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── Helper : titre de section centre ──────────────────────────────────────────
def _section_title(text: str, size: str = "1.4rem"):
    st.markdown(
        f"<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:{size};"
        "letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;"
        "border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;"
        f"margin:28px auto 16px'>{text}</div>",
        unsafe_allow_html=True,
    )


# ── CSS global (style KPI1) ───────────────────────────────────────────────────
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

# ── Fond anime ECG (identique KPI1) ──────────────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document;
  var w = window.parent;

  var PT_SIZE  = 24;
  var TRAIL_PX = 270;
  var SPD      = 2;

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

  var stop = startECG();
  setInterval(function() {
    var cv = p.getElementById('ecg-bg');
    if (!cv) { stop && stop(); stop = startECG(); }
  }, 2000);
  p.addEventListener('visibilitychange', function() {
    if (!p.hidden) { stop && stop(); stop = startECG(); }
  });
})();
</script>
""", height=0)

# ── Palette ───────────────────────────────────────────────────────────────────
COLORS_MAP = {
    'vulnerability': '#3b82f6', 'ransomware': '#ef4444', 'phishing': '#f59e0b',
    'malware': '#a855f7', 'apt': '#14b8a6', 'ddos': '#22c55e',
    'data_breach': '#6366f1', 'supply_chain': '#ec4899', 'cryptography': '#06b6d4',
    'defense': '#f97316', 'offensive': '#84cc16', 'compliance': '#0ea5e9',
    'identity': '#e879f9', 'general': '#64748b',
}

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(5,10,20,0.6)',
    font=dict(family='Roboto', color='#94a3b8'),
)

# ── En-tete ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 5</div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Threat Intelligence Matrix</div>', unsafe_allow_html=True)

# ── Refresh + badge ───────────────────────────────────────────────────────────
_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Synchroniser", use_container_width=True):
        force_refresh()
        st.rerun()

# ── Chargement ────────────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k5()
    if df_raw is None or df_raw.empty:
        st.warning("mart_k5 est vide. Lance `dbt run` depuis le dossier dbt/.")
        st.stop()
    df_raw['semaine'] = pd.to_datetime(df_raw['semaine'])
    load_ts = datetime.now().strftime('%H:%M:%S')
    with col_b:
        st.markdown(
            f'<div class="badge-live"><span class="dot-live"></span>'
            f'LIVE - MaJ {load_ts} - {int(df_raw["nb_alertes"].sum()):,} alertes</div>',
            unsafe_allow_html=True,
        )
except Exception as e:
    st.error(f"Connexion PostgreSQL impossible : {e}")
    st.stop()

# ── Filtres sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtres Analytiques")
    lookback = st.select_slider("Fenetre temporelle (jours)", options=[7, 14, 30, 90], value=30)
    cutoff_date = df_raw['semaine'].max() - timedelta(days=lookback)
    df = df_raw[df_raw['semaine'] >= cutoff_date].copy()

    viz_type = st.radio("Mode de visualisation", ["Flux Empile (Volume)", "Lignes (Tendances)"])

    st.markdown("---")
    cats_all = sorted(df['category'].unique())
    target_cat = st.multiselect("Vecteurs de menace", options=cats_all, default=cats_all)
    df = df[df['category'].isin(target_cat)]

# ── Metriques ─────────────────────────────────────────────────────────────────
_section_title("Vue d'ensemble")

total_hits = int(df['nb_alertes'].sum())
weekly_stats = df.groupby('semaine')['nb_alertes'].sum()
avg_hits = round(weekly_stats.mean(), 1) if not weekly_stats.empty else 0
volatility = round(weekly_stats.std(), 1) if len(weekly_stats) > 1 else 0
is_stable = volatility < (avg_hits * 0.4)
v_color = "#22c55e" if is_stable else "#ef4444"
nb_vecteurs = df['category'].nunique()

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
.card::before {{ content:''; position:absolute; top:0; left:0; width:100%; height:3px; border-radius:10px 10px 0 0; }}
.card:nth-child(1)::before {{ background:#3b82f6; }}
.card:nth-child(2)::before {{ background:#14b8a6; }}
.card:nth-child(3)::before {{ background:{v_color}; }}
.card:nth-child(4)::before {{ background:#f59e0b; }}
.card:hover {{ border-color:#3b82f6; transform:translateY(-3px); box-shadow:0 8px 28px rgba(59,130,246,0.18); background:rgba(20,28,48,0.95); }}
.val {{ font-family:'Roboto Mono',monospace; font-size:3rem; font-weight:700; color:#e2e8f0; }}
.lbl {{ font-size:1rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.08em; margin-top:10px; }}
.sub {{ font-size:1.1rem; margin-top:8px; font-weight:500; }}
</style>
<div class="grid">
  <div class="card">
    <div class="val" id="v1">0</div>
    <div class="lbl">Total Alertes</div>
    <div class="sub" style="color:#3b82f6">{lookback} jours</div>
  </div>
  <div class="card">
    <div class="val" id="v2">0</div>
    <div class="lbl">Moyenne Hebdo</div>
    <div class="sub" style="color:#14b8a6">Par semaine</div>
  </div>
  <div class="card">
    <div class="val" id="v3" style="color:{v_color}">0</div>
    <div class="lbl">Volatilite</div>
    <div class="sub" style="color:{v_color}">{"Stable" if is_stable else "Elevee"}</div>
  </div>
  <div class="card">
    <div class="val" id="v4">0</div>
    <div class="lbl">Vecteurs Actifs</div>
    <div class="sub" style="color:#f59e0b">Categories detectees</div>
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
animCount('v1', {total_hits}, 1200, false);
animCount('v2', {avg_hits}, 1000, true);
animCount('v3', {volatility}, 800, true);
animCount('v4', {nb_vecteurs}, 600, false);
</script>
""", height=160)

# ── Graphique principal ───────────────────────────────────────────────────────
_section_title(f"Analyse de flux - {viz_type}")

if viz_type == "Flux Empile (Volume)":
    fig = px.area(
        df, x="semaine", y="nb_alertes", color="category",
        color_discrete_map=COLORS_MAP, line_shape="spline",
    )
else:
    fig = px.line(
        df, x="semaine", y="nb_alertes", color="category",
        color_discrete_map=COLORS_MAP, markers=True,
    )

fig.update_layout(
    **PLOTLY_BASE,
    height=450,
    hovermode="x unified",
    margin=dict(t=10, b=20, l=20, r=20),
    legend=dict(orientation="h", y=1.1, x=0, title=None, font=dict(size=13)),
    xaxis=dict(gridcolor='#1e2a42', title="", tickfont=dict(size=14, color='#94a3b8')),
    yaxis=dict(gridcolor='#1e2a42', title="Alertes", tickfont=dict(size=14, color='#94a3b8')),
)
st.plotly_chart(fig, use_container_width=True)

# ── Detail : Treemap + Bar chart ──────────────────────────────────────────────
_section_title("Distribution & classement")

col_l, col_r2 = st.columns([1, 1])

# Ranking calcule une seule fois, reutilise par les deux colonnes
ranking = (
    df.groupby('category', as_index=False)['nb_alertes']
    .sum()
    .sort_values('nb_alertes', ascending=False)
)

with col_l:
    st.markdown(
        "<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:12px'>"
        "Distribution relative (Treemap)</div>",
        unsafe_allow_html=True,
    )
    fig_tree = px.treemap(
        ranking, path=['category'], values='nb_alertes',
        color='nb_alertes',
        color_continuous_scale=[[0, '#0a1628'], [0.5, '#1d4ed8'], [1, '#93c5fd']],
    )
    fig_tree.update_layout(
        height=380, margin=dict(t=10, b=10, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Roboto', color='#94a3b8'),
    )
    st.plotly_chart(fig_tree, use_container_width=True)

with col_r2:
    st.markdown(
        "<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:12px'>"
        "Top menaces (Periode)</div>",
        unsafe_allow_html=True,
    )
    fig_rank = go.Figure(go.Bar(
        x=ranking['nb_alertes'],
        y=ranking['category'],
        orientation='h',
        marker_color=[COLORS_MAP.get(c, '#3b82f6') for c in ranking['category']],
        hovertemplate='<b>%{y}</b><br>%{x} alertes<extra></extra>',
    ))
    fig_rank.update_layout(
        **PLOTLY_BASE,
        height=380,
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(gridcolor='#1e2a42', tickfont=dict(size=14)),
        yaxis=dict(gridcolor='#1e2a42', tickfont=dict(size=14, color='#cbd5e1')),
    )
    st.plotly_chart(fig_rank, use_container_width=True)

# ── Interpretation & Insights ─────────────────────────────────────────────────
if total_hits > 0 and not ranking.empty:
    top_cat = ranking.iloc[0]['category']
    top_val = int(ranking.iloc[0]['nb_alertes'])
    top_pct = round(top_val / total_hits * 100, 1)
    second_cat = ranking.iloc[1]['category'] if len(ranking) > 1 else "--"
    second_pct = round(int(ranking.iloc[1]['nb_alertes']) / total_hits * 100, 1) if len(ranking) > 1 else 0

    # Semaine la plus chargee — pic a surveiller
    pic_semaine = weekly_stats.idxmax().strftime('%d/%m/%Y') if not weekly_stats.empty else "--"
    pic_val = int(weekly_stats.max()) if not weekly_stats.empty else 0

    # Coefficient de variation — mesure normalisee de la volatilite
    cv = round(volatility / avg_hits * 100, 1) if avg_hits > 0 else 0

    st.markdown(f"""
    <div class="insight-box">
        <b>Interpretation & Insights</b><br><br>
        - <b>Concentration :</b> {top_cat} ({top_pct}%) et {second_cat} ({second_pct}%)
          representent a eux deux {round(top_pct + second_pct, 1)}% des alertes.
          Verifier si cette repartition reflete les incidents reels ou un biais de collecte.<br>
        - <b>Volatilite :</b> coefficient de variation de {cv}%
          (seuil : 40%). {'Flux regulier, les regles de detection semblent stables.'
          if is_stable else 'Flux irregulier — investiguer les semaines avec des pics anormaux, notamment la semaine du ' + pic_semaine + ' (' + str(pic_val) + ' alertes).'}<br>
        - <b>Action :</b> croiser le top vecteur ({top_cat}) avec les tickets ITSM
          pour mesurer le taux de faux positifs et ajuster les seuils d'alerte si necessaire.
    </div>
    """, unsafe_allow_html=True)
    