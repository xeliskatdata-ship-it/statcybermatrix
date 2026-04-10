# app.py -- CyberPulse Dashboard -- Page d'accueil
# Metriques globales + tableau articles + navigation KPI

import base64
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh
from utils_lang import t

st.set_page_config(page_title="CyberPulse", layout="wide", initial_sidebar_state="expanded")

# ── Sidebar CSS (module partage) -- badges dynamiques ─────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── CSS global + menu Option B ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
        radial-gradient(circle, rgba(59,130,246,0.15) 1px, transparent 1px),
        radial-gradient(circle, rgba(96,165,250,0.08) 1px, transparent 1px),
        radial-gradient(circle, rgba(147,197,253,0.06) 1px, transparent 1px);
    background-size: 80px 80px, 130px 130px, 200px 200px;
    background-position: 0 0, 40px 40px, 80px 80px;
    filter: blur(0.8px); z-index: 0; pointer-events: none;
}
[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }

/* ── SIDEBAR OPTION B : gradient bar + sections ─────────────────────────── */
[data-testid="stSidebar"] {
    z-index: 2 !important;
    background: #050a14 !important;
    border-right: 1px solid rgba(30,111,255,0.15);
}
[data-testid="stSidebar"]::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #3b82f6, #a855f7, #3b82f6);
    background-size: 200% 100%;
    animation: sidebar-gradient 4s linear infinite;
}
@keyframes sidebar-gradient {
    0% { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}
/* Sidebar : gere par sidebar_css.py */
.live-dot {
    display: inline-block; width: 7px; height: 7px;
    background: #22c55e; border-radius: 50%; margin-right: 8px;
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

div[data-testid="stVerticalBlock"] .stButton > button {
    background: rgba(15,20,34,0.7) !important; color: #94a3b8 !important;
    border: 1px solid #1e2a42 !important; border-radius: 8px !important;
    font-family: 'Roboto', sans-serif !important; font-size: 14px !important;
    padding: 10px !important; transition: border-color 0.2s, color 0.2s, background 0.2s !important;
}
div[data-testid="stVerticalBlock"] .stButton > button:hover {
    border-color: #3b82f6 !important; color: #3b82f6 !important;
    background: rgba(59,130,246,0.08) !important;
}

.kpi-btn-inner {
    background: rgba(13,18,32,0.85); border-radius: 12px;
    border-left: 5px solid var(--c); padding: 36px 28px;
    position: relative; overflow: hidden; cursor: pointer;
    transition: background 0.22s, transform 0.22s, box-shadow 0.22s;
    backdrop-filter: blur(8px);
}
.kpi-btn-inner:hover {
    background: rgba(17,24,39,0.95); transform: translateX(6px);
    box-shadow: 8px 0 40px rgba(0,0,0,0.55);
}
.kpi-bnum {
    position: absolute; top: -10px; right: 10px;
    font-size: 140px; font-weight: 800; color: var(--c);
    opacity: 0.05; line-height: 1; pointer-events: none; transition: opacity 0.25s;
}
.kpi-btn-inner:hover .kpi-bnum { opacity: 0.12; }
.kpi-btitle { font-size: 22px; font-weight: 700; color: #cbd5e1; margin-bottom: 12px; line-height: 1.3; text-align: center; }
.kpi-bdesc  { font-size: 15px; color: #7a8fa6; line-height: 1.75; text-align: center; }

.map-btn-inner {
    background: rgba(13,18,32,0.85); border-radius: 12px;
    border-left: 5px solid #6366f1; padding: 36px 28px;
    display: flex; align-items: center; gap: 28px;
    cursor: pointer; position: relative; overflow: hidden;
    backdrop-filter: blur(8px); transition: background 0.22s, transform 0.22s, box-shadow 0.22s;
}
.map-btn-inner:hover { background: rgba(17,24,39,0.95); transform: translateX(6px); box-shadow: 8px 0 40px rgba(0,0,0,0.55); }
.map-bnum { position: absolute; top: -10px; right: 20px; font-size: 140px; font-weight: 800; color: #6366f1; opacity: 0.05; line-height: 1; pointer-events: none; transition: opacity 0.25s; }
.map-btn-inner:hover .map-bnum { opacity: 0.12; }
.map-btitle { font-size: 22px; font-weight: 700; color: #cbd5e1; margin-bottom: 8px; }
.map-bdesc  { font-size: 15px; color: #7a8fa6; line-height: 1.75; }
.map-btags  { display: flex; gap: 10px; margin-top: 12px; }
.map-btag   { font-size: 13px; color: #6366f1; border: 1px solid rgba(99,102,241,0.35); border-radius: 5px; padding: 4px 14px; }
.map-barrow { margin-left: auto; font-size: 22px; color: #334155; flex-shrink: 0; transition: color 0.2s, transform 0.2s; }
.map-btn-inner:hover .map-barrow { color: #6366f1; transform: translateX(7px); }
</style>
""", unsafe_allow_html=True)

# ── Fond anime ECG ────────────────────────────────────────────────────────────
components.html("""
<script>
(function() {
  var p = window.parent.document;
  var w = window.parent;
  var PT_SIZE = 24, TRAIL_PX = 270, SPD = 2;

  function ecgValue(x, H) {
    var margin = PT_SIZE + 10, maxAmp = H / 2 - margin;
    var mod = x % 220, raw;
    if(mod<70) raw=Math.sin(mod*0.05)*5;
    else if(mod<80) raw=(mod-70)*13;
    else if(mod<85) raw=130-(mod-80)*55;
    else if(mod<90) raw=-145+(mod-85)*32;
    else if(mod<100) raw=-25+(mod-90)*3;
    else if(mod<115) raw=Math.sin((mod-100)*0.4)*9;
    else raw=Math.sin(mod*0.04)*3;
    return (raw/130)*maxAmp;
  }

  function startECG() {
    var old = p.getElementById('ecg-bg');
    if(old) old.parentNode.removeChild(old);
    var cv = p.createElement('canvas');
    cv.id = 'ecg-bg';
    cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
    p.body.appendChild(cv);
    var ctx = cv.getContext('2d'), t=0, ecgX=0, history=[], alive=true;
    function resize(){cv.width=p.documentElement.clientWidth;cv.height=p.documentElement.clientHeight;}
    resize(); w.addEventListener('resize',resize);

    var dots=[];
    for(var i=0;i<50;i++) dots.push({
      x:Math.random()*cv.width, y:Math.random()*cv.height,
      r:Math.random()*1.5+0.3, phase:Math.random()*Math.PI*2,
      speed:Math.random()*0.008+0.004,
      dx:(Math.random()-0.5)*0.15, dy:(Math.random()-0.5)*0.15,
      color:Math.random()>0.6?'59,130,246':(Math.random()>0.5?'168,85,247':'20,184,166')
    });
    var rings=[]; function addRing(){rings.push({r:0,a:0.45});} addRing();

    function draw(){
      if(!p.getElementById('ecg-bg')||!alive) return;
      var W=cv.width, H=cv.height; ctx.clearRect(0,0,W,H); t+=0.016;
      var grd=ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,W*0.6);
      grd.addColorStop(0,'rgba(14,30,60,0.35)'); grd.addColorStop(1,'rgba(5,10,20,0)');
      ctx.fillStyle=grd; ctx.fillRect(0,0,W,H);
      rings.forEach(function(r,i){r.r+=1.0;r.a-=0.005;if(r.a<=0){rings.splice(i,1);return;}
        ctx.beginPath();ctx.arc(W/2,H/2,r.r,0,Math.PI*2);
        ctx.strokeStyle='rgba(59,130,246,'+r.a*0.35+')';ctx.lineWidth=1;ctx.stroke();});
      if(Math.floor(t*1.2)%3===0&&rings.length<6) addRing();
      dots.forEach(function(d){d.phase+=d.speed;d.x+=d.dx;d.y+=d.dy;
        if(d.x<0)d.x=W;if(d.x>W)d.x=0;if(d.y<0)d.y=H;if(d.y>H)d.y=0;
        var op=0.3+Math.abs(Math.sin(d.phase))*0.5;
        ctx.beginPath();ctx.arc(d.x,d.y,d.r,0,Math.PI*2);
        ctx.fillStyle='rgba('+d.color+','+op+')';ctx.fill();});
      history.push({x:ecgX%W, y:H/2-ecgValue(ecgX,H)}); ecgX+=SPD;
      var maxPts=Math.round(TRAIL_PX/SPD); if(history.length>maxPts) history.shift();
      if(history.length>1){
        for(var k=1;k<history.length;k++){
          var prog=k/history.length, alpha=prog*0.85;
          var isSpike=Math.abs(history[k].y-H/2)>H*0.08;
          ctx.beginPath();ctx.moveTo(history[k-1].x,history[k-1].y);ctx.lineTo(history[k].x,history[k].y);
          ctx.strokeStyle=isSpike?'rgba(168,85,247,'+alpha+')':'rgba(59,130,246,'+(alpha*0.6)+')';
          ctx.lineWidth=isSpike?3.5:1.8;ctx.stroke();}
        var head=history[history.length-1];
        var glow=ctx.createRadialGradient(head.x,head.y,0,head.x,head.y,PT_SIZE*4);
        glow.addColorStop(0,'rgba(168,85,247,0.55)');glow.addColorStop(1,'rgba(168,85,247,0)');
        ctx.fillStyle=glow;ctx.fillRect(head.x-PT_SIZE*4,head.y-PT_SIZE*4,PT_SIZE*8,PT_SIZE*8);
        ctx.beginPath();ctx.arc(head.x,head.y,PT_SIZE,0,Math.PI*2);
        ctx.fillStyle='rgba(220,170,255,1)';ctx.fill();}
      requestAnimationFrame(draw);}
    draw(); return function(){alive=false;};}

  var stop=startECG();
  setInterval(function(){if(!p.getElementById('ecg-bg')){stop&&stop();stop=startECG();}},2000);
  p.addEventListener('visibilitychange',function(){if(!p.hidden){stop&&stop();stop=startECG();}});
})();
</script>
""", height=0)

# ── Logo ──────────────────────────────────────────────────────────────────────
_logo_path = os.path.join(os.path.dirname(__file__), "static", "logo_cyberpulse.jpg")
LOGO_B64 = ""
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as f:
        LOGO_B64 = base64.b64encode(f.read()).decode()

# ── Donnees ───────────────────────────────────────────────────────────────────
df_k1       = get_mart_k1()
df_articles = get_stg_articles(limit=500)

total_articles = int(df_k1["nb_articles"].sum())                         if not df_k1.empty else 0
nb_sources     = df_k1["source"].nunique()                               if not df_k1.empty else 0
date_max       = df_k1["published_date"].max().strftime("%d/%m/%Y")      if not df_k1.empty else "--"
last_update    = datetime.now().strftime("%d/%m/%Y a %H:%M:%S")

sources_live = (
    df_articles.groupby("source").size()
    .sort_values(ascending=False)
    .reset_index(name="nb_articles")
    if not df_articles.empty
    else pd.DataFrame(columns=["source", "nb_articles"])
)

lang = st.session_state.get("lang", "en")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f"<div style='padding:12px 0 8px 0;text-align:center'>"
            f"<img src='data:image/jpeg;base64,{LOGO_B64}' "
            f"style='width:100%;max-width:600px;border-radius:10px;margin-bottom:6px'>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.divider()
    lang_choice = st.selectbox(t("Language", "en"), options=["English", "Francais"], index=0, key="lang_select")
    lang = "fr" if lang_choice == "Francais" else "en"
    st.session_state["lang"] = lang
    st.divider()
    if st.button("Rafraichir les donnees", key="home_refresh"):
        force_refresh()
        st.rerun()
    st.divider()
    st.markdown(
        f"<div style='font-size:0.72rem;color:#64748b;text-transform:uppercase;"
        f"letter-spacing:.08em;margin-bottom:4px'>Sources actives"
        f"<span style='color:#3b82f6;float:right'>{len(sources_live)}</span></div>"
        f"<div style='font-size:0.65rem;color:#475569;margin-bottom:8px'>Mise a jour : {last_update}</div>",
        unsafe_allow_html=True,
    )
    if not sources_live.empty:
        for _, row in sources_live.iterrows():
            st.markdown(
                f"<div style='font-size:0.75rem;color:#94a3b8;padding:2px 0'>"
                f"<span style='color:#3b82f6'>&#9679;</span>&nbsp;{row['source']}"
                f"<span style='color:#475569;float:right'>{row['nb_articles']}</span></div>",
                unsafe_allow_html=True,
            )
    st.divider()
    st.markdown(
        "<div style='font-size:0.72rem;color:#475569'>"
        "Sprint 5 -- Avril 2026<br>PostgreSQL -- dbt -- Airflow -- Streamlit</div>",
        unsafe_allow_html=True,
    )

# ── Banner ────────────────────────────────────────────────────────────────────
logo_tag = (
    f'<img src="data:image/jpeg;base64,{LOGO_B64}" '
    f'style="max-width:900px;width:80%;border-radius:12px;margin-bottom:20px;'
    f'display:block;margin-left:auto;margin-right:auto">'
    if LOGO_B64
    else '<div style="font-family:Roboto Mono;font-size:2rem;font-weight:700;'
         'color:#e2e8f0;margin-bottom:20px">CyberPulse</div>'
)

st.markdown(f"""
<div style="background:rgba(15,20,34,0.85);backdrop-filter:blur(8px);
border:1px solid #1e2a42;border-radius:16px;padding:40px 36px;margin-bottom:28px;text-align:center">
    {logo_tag}
    <div style="font-size:0.95rem;color:#64748b">
        <span class="live-dot"></span>
        Veille automatique de l'actualite cyber pour l'identification des sujets emergents et suivre leur evolution
    </div>
</div>
""", unsafe_allow_html=True)

# ── Cartes metriques animees ──────────────────────────────────────────────────
components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:transparent; font-family:'Roboto',sans-serif; }}
.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px; }}
.card {{
    background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:12px;
    padding:28px 36px; position:relative; overflow:hidden; text-align:center;
    transition:border-color 0.2s, transform 0.2s, box-shadow 0.2s; cursor:default;
    backdrop-filter:blur(8px);
}}
.card:hover {{ transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.5); }}
.card-accent {{ position:absolute; top:0; left:0; width:100%; height:3px; border-radius:12px 12px 0 0; }}
.c-blue .card-accent  {{ background:#3b82f6; }} .c-blue:hover  {{ border-color:#3b82f6; }}
.c-green .card-accent {{ background:#22c55e; }} .c-green:hover {{ border-color:#22c55e; }}
.card-label {{ font-size:13px; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:12px; }}
.c-blue .card-label  {{ color:#3b82f6; }}
.c-green .card-label {{ color:#22c55e; }}
.card-value {{ font-size:3.8rem; font-weight:700; color:#e2e8f0; font-family:'Roboto Mono',monospace; letter-spacing:-2px; }}
.date-card {{
    background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:12px;
    padding:28px 36px; display:flex; align-items:center; justify-content:center;
    gap:36px; margin-bottom:14px; max-width:620px; margin-left:auto; margin-right:auto;
    backdrop-filter:blur(8px); transition:border-color 0.2s, transform 0.2s; cursor:default;
}}
.date-card:hover {{ border-color:#6366f1; transform:translateY(-2px); }}
.date-label {{ font-size:13px; letter-spacing:0.12em; text-transform:uppercase; color:#6366f1; margin-bottom:10px; }}
.date-value {{ font-size:3rem; font-weight:700; color:#e2e8f0; font-family:'Roboto Mono',monospace; }}
.date-sub {{ font-size:13px; color:#4f46e5; margin-top:6px; }}
.refresh-btn {{
    display:inline-flex; align-items:center; gap:8px;
    background:rgba(99,102,241,0.1); border:1px solid rgba(99,102,241,0.3);
    border-radius:999px; padding:12px 22px; font-size:14px; color:#a5b4fc;
    cursor:pointer; transition:background 0.2s, transform 0.15s;
    font-family:'Roboto',sans-serif; white-space:nowrap;
}}
.refresh-btn:hover {{ background:rgba(99,102,241,0.25); transform:scale(1.04); }}
.r-icon {{ display:inline-block; transition:transform 0.4s; }}
.refresh-btn:hover .r-icon {{ transform:rotate(180deg); }}
</style>
<div class="cards">
  <div class="card c-blue">
    <div class="card-accent"></div>
    <div class="card-label">Articles collectes</div>
    <div class="card-value" id="cnt-articles">0</div>
  </div>
  <div class="card c-green">
    <div class="card-accent"></div>
    <div class="card-label">Sources actives</div>
    <div class="card-value" id="cnt-sources">0</div>
  </div>
</div>
<div class="date-card">
  <div style="text-align:center">
    <div class="date-label">Derniere mise a jour</div>
    <div class="date-value" id="cnt-date">{date_max}</div>
    <div class="date-sub">Collecte toutes les heures</div>
  </div>
  <div class="refresh-btn" onclick="refreshDate()">
    <span class="r-icon">&#x21bb;</span>
    <span id="refresh-time">{last_update}</span>
  </div>
</div>
<script>
function animateCounter(id, target, duration) {{
  var el = document.getElementById(id); if (!el) return;
  var step = target / (duration / 16), current = 0;
  var timer = setInterval(function() {{
    current += step;
    if (current >= target) {{ current = target; clearInterval(timer); }}
    el.textContent = Math.floor(current).toLocaleString('fr-FR');
  }}, 16);
}}
function refreshDate() {{
  var el = document.getElementById('cnt-date');
  var sub = document.getElementById('refresh-time');
  var now = new Date();
  var pad = function(n) {{ return String(n).padStart(2,'0'); }};
  var d = pad(now.getDate())+'/'+pad(now.getMonth()+1)+'/'+now.getFullYear();
  var h = pad(now.getHours())+':'+pad(now.getMinutes())+':'+pad(now.getSeconds());
  el.textContent = d;
  if (sub) sub.textContent = d + ' a ' + h;
  el.style.color = '#4ade80';
  setTimeout(function() {{ el.style.color = '#e2e8f0'; }}, 800);
}}
animateCounter('cnt-articles', {total_articles}, 1200);
animateCounter('cnt-sources', {nb_sources}, 800);
</script>
""", height=380)

# ── Tableau articles ──────────────────────────────────────────────────────────
df_preview = get_stg_articles(limit=500).drop_duplicates(subset=["title", "source"])

if not df_preview.empty:
    st.markdown("<br>", unsafe_allow_html=True)

    df_show = df_preview[["source", "title", "published_date", "category", "url"]].copy()
    df_show = df_show.sort_values("published_date", ascending=False)
    df_show["published_date"] = pd.to_datetime(df_show["published_date"], errors="coerce").dt.strftime("%d/%m/%Y")
    df_show = df_show.rename(columns={
        "source": "Source name", "title": "News headlines",
        "published_date": "Publication date", "category": "Threat category",
        "url": "Lien",
    })

    row_h   = 45
    dyn_h   = min(38 + len(df_show) * row_h, 620)
    st.dataframe(
        df_show, use_container_width=True, hide_index=True, height=dyn_h,
        column_config={"Lien": st.column_config.LinkColumn("Lien", display_text="Ouvrir")},
    )
else:
    st.warning(t("No data", lang))

# ── Section KPI ───────────────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)

_KPIS = [
    ("kpi1", "#3b82f6", "01", "Articles collectes",
     "Volume de publication par source et evolution temporelle des collectes",
     "pages/1_Articles_collectes.py"),
    ("kpi2", "#a855f7", "02", "Suivi des mots-cles",
     "Frequence des termes cyber et identification des sujets dominants",
     "pages/2_Suivi_des_mots-cles.py"),
    ("kpi3", "#ef4444", "03", "Analyse des menaces",
     "Repartition des categories : ransomware, phishing, APT, data breach...",
     "pages/3_Analyse_des_menaces.py"),
    ("kpi4", "#f59e0b", "04", "Analyse des tendances",
     "Evolution hebdomadaire et mensuelle des vecteurs de menace",
     "pages/4_Analyse_des_tendances.py"),
    ("kpi5", "#22c55e", "05", "Analyse des alertes",
     "Nombre d'alertes critiques par semaine et volatilite",
     "pages/5_Analyse_des_alertes.py"),
    ("kpi6", "#14b8a6", "06", "CVEs",
     "Vulnerabilites officielles les plus citees avec detail NVD",
     "pages/6_CVEs.py"),
]

col1, col2, col3 = st.columns(3)
for i, (key, color, num, title, desc, page) in enumerate(_KPIS):
    col = [col1, col2, col3][i % 3]
    with col:
        st.markdown(f"""
        <div class="kpi-btn-inner" style="--c:{color}">
            <div class="kpi-bnum">{num}</div>
            <div class="kpi-btitle">{title}</div>
            <div class="kpi-bdesc">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Voir l'analyse", key=f"btn_{key}", use_container_width=True):
            st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)

col_map, _, _ = st.columns(3)
with col_map:
    st.markdown("""
    <div class="map-btn-inner">
      <div class="map-bnum">07</div>
      <div style="flex:1">
        <div class="map-btitle">Carte mondiale des menaces</div>
        <div class="map-bdesc">Visualisation geographique des cyberattaques -- Hotspots, origines et cibles par pays</div>
        <div class="map-btags"><span class="map-btag">Temps reel</span><span class="map-btag">Geolocalisation</span></div>
      </div>
      <div class="map-barrow">&rarr;</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Voir la carte", key="btn_map", use_container_width=True):
        st.switch_page("pages/7_Carte_Menaces.py")