"""
CyberPulse -- app.py
Dashboard Streamlit -- Page d'accueil
"""

import streamlit as st
import pandas as pd
import os
import sys
import base64
import streamlit.components.v1 as components
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from db_connect import get_mart_k1, get_mart_k3, get_stg_articles, force_refresh
from utils_lang import t

st.set_page_config(page_title="CyberPulse", layout="wide", initial_sidebar_state="expanded")

# ── Fond animé ECG ────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background: #050a14 !important; }
#ecg-bg { position:fixed; top:0; left:0; width:100%; height:100%; z-index:0; pointer-events:none; }
[data-testid="stAppViewContainer"] > * { position:relative; z-index:1; }
[data-testid="stSidebar"] { z-index:2 !important; }
</style>
<canvas id="ecg-bg"></canvas>
<script>
(function() {
var cv = document.getElementById('ecg-bg');
if (!cv) return;
var ctx = cv.getContext('2d');
function resize() { cv.width=window.innerWidth; cv.height=window.innerHeight; }
resize();
window.addEventListener('resize', resize);
var t=0, ecgX=0;
var TRAIL=window.innerWidth*1.8;
var history=[];

function ecgValue(x) {
  var mod = x % 220;
  if(mod<70)  return Math.sin(mod*0.05)*5;
  if(mod<80)  return (mod-70)*13;
  if(mod<85)  return 130-(mod-80)*55;
  if(mod<90)  return -145+(mod-85)*32;
  if(mod<100) return -25+(mod-90)*3;
  if(mod<115) return Math.sin((mod-100)*0.4)*9;
  return Math.sin(mod*0.04)*3;
}

var dots=[];
for(var i=0;i<50;i++) dots.push({
  x:Math.random()*window.innerWidth, y:Math.random()*window.innerHeight,
  r:Math.random()*1.5+0.3,
  phase:Math.random()*Math.PI*2, speed:Math.random()*0.008+0.004,
  dx:(Math.random()-0.5)*0.15, dy:(Math.random()-0.5)*0.15,
  color:Math.random()>0.6?'59,130,246':(Math.random()>0.5?'168,85,247':'20,184,166')
});

var rings=[];
function addRing(){rings.push({r:0,a:0.45});}
addRing();

function draw() {
  var W=cv.width, H=cv.height;
  ctx.clearRect(0,0,W,H);
  t+=0.016;
  var grd=ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,W*0.6);
  grd.addColorStop(0,'rgba(14,30,60,0.35)');
  grd.addColorStop(1,'rgba(5,10,20,0)');
  ctx.fillStyle=grd; ctx.fillRect(0,0,W,H);

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
    var p=0.3+Math.abs(Math.sin(d.phase))*0.5;
    ctx.beginPath(); ctx.arc(d.x,d.y,d.r,0,Math.PI*2);
    ctx.fillStyle='rgba('+d.color+','+p+')'; ctx.fill();
  });

  history.push({x:ecgX%W, y:H/2-ecgValue(ecgX)});
  ecgX+=1.0;
  TRAIL=W*1.8;
  if(history.length>TRAIL) history.shift();

  if(history.length>1){
    for(var k=1;k<history.length;k++){
      var prog=k/history.length;
      var alpha=prog<0.2?(prog/0.2)*0.75:0.75;
      var isSpike=Math.abs(history[k].y-H/2)>25;
      ctx.beginPath();
      ctx.moveTo(history[k-1].x,history[k-1].y);
      ctx.lineTo(history[k].x,history[k].y);
      ctx.strokeStyle=isSpike?'rgba(168,85,247,'+alpha+')':'rgba(59,130,246,'+(alpha*0.6)+')';
      ctx.lineWidth=isSpike?2.5:1.2; ctx.stroke();
    }
    var head=history[history.length-1];
    ctx.beginPath(); ctx.arc(head.x,head.y,3.5,0,Math.PI*2);
    ctx.fillStyle='rgba(200,150,255,1)'; ctx.fill();
    var glow=ctx.createRadialGradient(head.x,head.y,0,head.x,head.y,14);
    glow.addColorStop(0,'rgba(168,85,247,0.5)');
    glow.addColorStop(1,'rgba(168,85,247,0)');
    ctx.fillStyle=glow; ctx.fillRect(head.x-14,head.y-14,28,28);
  }
  requestAnimationFrame(draw);
}
draw();
})();
</script>
""", unsafe_allow_html=True)


# ── Logo ──────────────────────────────────────────────────────────────────────
_logo_path = os.path.join(os.path.dirname(__file__), 'static', 'logo_cyberpulse.jpg')
if os.path.exists(_logo_path):
    with open(_logo_path, 'rb') as _f:
        LOGO_B64 = base64.b64encode(_f.read()).decode()
else:
    LOGO_B64 = ""

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
.stApp { background: #0a0e1a; }
[data-testid="stSidebar"] { background: #0f1422 !important; border-right: 0.5px solid #1e2a42; }
[data-testid="stSidebar"] * { color: #a8b8d0 !important; }
.live-dot {
    display: inline-block; width: 7px; height: 7px;
    background: #22c55e; border-radius: 50%; margin-right: 8px;
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
.section-tag {
    display: inline-block; font-family: 'Roboto Mono', monospace;
    font-size: 0.65rem; letter-spacing: 0.15em; text-transform: uppercase;
    color: #3b82f6; background: rgba(59,130,246,0.1);
    border: 0.5px solid rgba(59,130,246,0.2);
    border-radius: 4px; padding: 3px 10px; margin-bottom: 14px;
}
</style>
""", unsafe_allow_html=True)

# ── Données ───────────────────────────────────────────────────────────────────
df_k1       = get_mart_k1()
df_articles = get_stg_articles(limit=500)

total_articles = int(df_k1['nb_articles'].sum())                        if not df_k1.empty else 0
nb_sources     = df_k1['source'].nunique()                              if not df_k1.empty else 0
top_source     = df_k1.groupby('source')['nb_articles'].sum().idxmax() if not df_k1.empty else '—'
date_max       = df_k1['published_date'].max().strftime('%d/%m/%Y')     if not df_k1.empty else '—'
last_update    = datetime.now().strftime('%d/%m/%Y à %H:%M:%S')

if not df_articles.empty:
    sources_live = (df_articles.groupby('source').size()
                    .sort_values(ascending=False)
                    .reset_index(name='nb_articles'))
else:
    sources_live = pd.DataFrame(columns=['source', 'nb_articles'])

lang = st.session_state.get('lang', 'en')

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    if LOGO_B64:
        st.markdown(
            f"<div style='padding:12px 0 8px 0;text-align:center'>"
            f"<img src='data:image/jpeg;base64,{LOGO_B64}' "
            f"style='width:100%;max-width:600px;border-radius:10px;margin-bottom:6px'>"
            f"</div>",
            unsafe_allow_html=True
        )
    st.divider()

    lang_choice = st.selectbox(t("Language", "en"), options=["English", "Francais"], index=0, key="lang_select")
    lang = "fr" if lang_choice == "Francais" else "en"
    st.session_state['lang'] = lang

    st.divider()

    if st.button("Rafraichir les données", key="home_refresh"):
        force_refresh()
        st.rerun()

    st.divider()

    st.markdown(
        f"<div style='font-size:0.72rem;color:#64748b;text-transform:uppercase;"
        f"letter-spacing:.08em;margin-bottom:4px'>Sources actives"
        f"<span style='color:#3b82f6;float:right'>{len(sources_live)}</span></div>"
        f"<div style='font-size:0.65rem;color:#475569;margin-bottom:8px'>Mise à jour : {last_update}</div>",
        unsafe_allow_html=True
    )
    if not sources_live.empty:
        for _, row in sources_live.iterrows():
            st.markdown(
                f"<div style='font-size:0.75rem;color:#94a3b8;padding:2px 0'>"
                f"<span style='color:#3b82f6'>&#9679;</span>&nbsp;{row['source']}"
                f"<span style='color:#475569;float:right'>{row['nb_articles']}</span></div>",
                unsafe_allow_html=True
            )
    st.divider()
    st.markdown(
        "<div style='font-size:0.72rem;color:#475569'>"
        "Sprint 4 · Mars 2026<br>PostgreSQL · dbt · Airflow · Streamlit</div>",
        unsafe_allow_html=True
    )

# ── Banner ────────────────────────────────────────────────────────────────────
logo_tag = f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="max-width:900px;width:80%;border-radius:12px;margin-bottom:20px;display:block;margin-left:auto;margin-right:auto">' if LOGO_B64 else '<div style="font-family:Roboto Mono;font-size:2rem;font-weight:700;color:#e2e8f0;margin-bottom:20px">CyberPulse</div>'

st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f1422 0%,#111827 100%);
border:0.5px solid #1e2a42;border-radius:16px;padding:40px 36px;margin-bottom:28px;text-align:center">
    {logo_tag}
    <div style="font-size:0.95rem;color:#64748b">
        <span class="live-dot"></span>
        Veille automatique de l'actualité cyber pour l'identification des sujets émergents et suivre leur évolution
    </div>
</div>
""", unsafe_allow_html=True)

# ── Threat keywords ───────────────────────────────────────────────────────────
_THREAT_KEYWORDS = {
    "ransomware"   : ["ransomware","ransom","lockbit","blackcat","ryuk","conti","akira","alphv","clop","hive","revil","maze","darkside","encrypted","decryptor","double extortion","ransomed","play ransomware","medusa","8base","hunters"],
    "phishing"     : ["phishing","spear-phishing","spearphishing","credential","spoofing","smishing","vishing","whaling","pretexting","social engineering","fake login","credential harvesting","business email compromise","bec","email fraud","impersonation","lure","malicious email","phish","typosquatting"],
    "vulnerability": ["vulnerability","vulnerabilities","cve","patch","exploit","zero-day","zero day","0day","rce","remote code execution","sql injection","xss","cross-site","buffer overflow","privilege escalation","authentication bypass","arbitrary code","security flaw","security hole","unpatched","proof of concept","poc","nvd","mitre","cvss","critical flaw","security update","security advisory","disclosure","severity","attack surface","misconfiguration","exposed port","open redirect"],
    "malware"      : ["malware","trojan","backdoor","spyware","rootkit","botnet","worm","virus","keylogger","stealer","infostealer","dropper","loader","payload","rat","remote access trojan","adware","fileless","polymorphic","obfuscated","shellcode","stealthy","persistence","command and control","c2","c&c","redline","raccoon","agent tesla","formbook","asyncrat","emotet","trickbot","qakbot","cobalt strike"],
    "apt"          : ["apt","nation-state","nation state","threat actor","campaign","espionage","state-sponsored","state sponsored","cyber espionage","advanced persistent","lazarus","fancy bear","cozy bear","sandworm","charming kitten","volt typhoon","salt typhoon","turla","fin7","ta505","hafnium","scattered spider","intelligence gathering","attribution","geopolitical","military cyber","targeted attack","ttp","ttps"],
    "ddos"         : ["ddos","denial of service","dos attack","flood","amplification","distributed denial","botnet attack","traffic flood","killnet","anonymous sudan","hacktivist"],
    "data_breach"  : ["data breach","breach","leak","exposed","stolen data","exfiltration","data theft","data stolen","personal data","pii","gdpr","data dump","database exposed","records stolen","customer data","sensitive data","compromised data","information disclosure","data loss","insider threat","unauthorized access","data for sale","dark web"],
    "supply_chain" : ["supply chain","third-party","third party","dependency","open source attack","software supply chain","package","npm","pypi","malicious package","build system","ci/cd","solarwinds","xz utils","polyfill","compromised library","upstream attack"],
    "cloud"        : ["cloud","aws","azure","google cloud","gcp","s3 bucket","cloud storage","misconfigured","cloud security","saas","kubernetes","container security","docker","serverless","cloud breach","iam","cloud exposure","public bucket"],
    "iot"          : ["iot","internet of things","smart device","connected device","industrial control","ics","scada","operational technology","ot security","embedded device","firmware","router","ip camera","smart home","mirai","default credentials"],
    "cryptojacking": ["cryptojacking","cryptomining","crypto mining","monero","coinhive","mining malware","cpu hijacking","browser mining","xmrig","unauthorized mining","crypto stealer","cryptocurrency theft","wallet drainer"],
    "regulation"   : ["regulation","compliance","gdpr","hipaa","pci dss","nis2","dora","iso 27001","nist","sec disclosure","cyber law","legislation","data protection","privacy law","fine","penalty","audit","certification","framework"],
    "incident"     : ["incident response","breach response","forensics","investigation","post-mortem","remediation","containment","threat hunting","detection","siem","edr","xdr","soar","playbook","ioc","indicator of compromise","threat intelligence","cyber insurance","recovery","business continuity"],
}

def _detect_category(row):
    text = (str(row.get("title", "")) + " " + str(row.get("description", ""))).lower()
    for cat, kws in _THREAT_KEYWORDS.items():
        for kw in kws:
            if kw in text:
                return cat
    return "general"

# ── Préparer les données tableau ──────────────────────────────────────────────
df_preview = get_stg_articles(limit=500)
df_preview = df_preview.drop_duplicates(subset=["title", "source"])

if not df_preview.empty:
    df_tbl = df_preview[['source', 'title', 'published_date']].copy().sort_values('published_date', ascending=False)
    df_tbl['category'] = df_preview.apply(_detect_category, axis=1)
    df_tbl['published_date'] = pd.to_datetime(df_tbl['published_date'], errors='coerce').dt.strftime('%d/%m/%Y')
    rows_json = df_tbl.fillna('').to_json(orient='records', force_ascii=False)
else:
    rows_json = '[]'

# ── Cartes + date + tableau ───────────────────────────────────────────────────
table_height = min(38 + len(df_preview) * 42, 620) if not df_preview.empty else 100

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:transparent; font-family:'Roboto',sans-serif; }}

.cards {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:12px; }}
.card {{
    background:#0f1422; border:0.5px solid #1e2a42; border-radius:12px;
    padding:28px 36px; position:relative; overflow:hidden; text-align:center;
    transition:border-color 0.2s, transform 0.2s, box-shadow 0.2s; cursor:default;
}}
.card:hover {{ transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.5); }}
.card-accent {{ position:absolute; top:0; left:0; width:100%; height:3px; border-radius:12px 12px 0 0; }}
.c-blue .card-accent  {{ background:#3b82f6; }} .c-blue:hover  {{ border-color:#3b82f6; }}
.c-green .card-accent {{ background:#22c55e; }} .c-green:hover {{ border-color:#22c55e; }}
.card-label {{ font-size:13px; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:12px; }}
.c-blue .card-label  {{ color:#a855f7; }}
.c-green .card-label {{ color:#22c55e; }}
.card-value {{ font-size:3.8rem; font-weight:700; color:#e2e8f0; font-family:'Roboto Mono',monospace; letter-spacing:-2px; }}

.date-card {{
    background:#0f172a; border:0.5px solid #312e81; border-radius:12px;
    padding:28px 36px; display:flex; align-items:center; justify-content:center;
    gap:36px; margin-bottom:14px; max-width:620px; margin-left:auto; margin-right:auto;
    transition:border-color 0.2s, transform 0.2s; cursor:default;
}}
.date-card:hover {{ border-color:#6366f1; transform:translateY(-2px); }}
.date-label {{ font-size:13px; letter-spacing:0.12em; text-transform:uppercase; color:#6366f1; margin-bottom:10px; }}
.date-value {{ font-size:3rem; font-weight:700; color:#e2e8f0; font-family:'Roboto Mono',monospace; }}
.date-sub {{ font-size:13px; color:#4f46e5; margin-top:6px; }}
.refresh-btn {{
    display:inline-flex; align-items:center; gap:8px;
    background:rgba(99,102,241,0.1); border:0.5px solid rgba(99,102,241,0.3);
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
    <div class="card-label">Articles collect\u00e9s</div>
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
    <div class="date-label">Derni\u00e8re mise \u00e0 jour</div>
    <div class="date-value" id="cnt-date">{date_max}</div>
    <div class="date-sub">Collecte toutes les heures</div>
  </div>
  <div class="refresh-btn" onclick="refreshDate()">
    <span class="r-icon">\u21bb</span>
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
  if (sub) sub.textContent = d + ' \u00e0 ' + h;
  el.style.color = '#4ade80';
  setTimeout(function() {{ el.style.color = '#e2e8f0'; }}, 800);
}}
animateCounter('cnt-articles', {total_articles}, 1200);
animateCounter('cnt-sources', {nb_sources}, 800);
</script>
""", height=380)

if not df_preview.empty:
    st.markdown("<br>", unsafe_allow_html=True)
    df_show = df_tbl.copy()
    df_show['url'] = df_preview['url'].values
    df_show = df_show.rename(columns={
        'source'        : 'Source name',
        'title'         : 'News headlines',
        'published_date': 'Publication date',
        'category'      : 'Threat category',
        'url'           : 'Lien',
    })
    row_height = 45
    header_height = 38
    dynamic_height = min(header_height + len(df_show) * row_height, 620)
    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        height=dynamic_height,
        column_config={
            "Lien": st.column_config.LinkColumn(
                "Lien",
                display_text="Ouvrir →",
            )
        }
    )

if df_preview.empty:
    st.warning(t("No data", lang))

st.markdown("<br>", unsafe_allow_html=True)

# ── Section KPI + Carte Menaces ───────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlock"] button {
    width:100% !important; height:auto !important;
    background:#0d1220 !important; color:#cbd5e1 !important;
    border:none !important; border-radius:0 !important;
    padding:0 !important; font-family:'Roboto',sans-serif !important;
}
.kpi-btn-wrap {
    background:#0d1220; border-radius:12px;
    border-left:5px solid var(--c);
    padding:36px 28px; position:relative; overflow:hidden; cursor:pointer;
    transition:background 0.22s, transform 0.22s, box-shadow 0.22s;
    margin-bottom:0;
}
.kpi-btn-wrap:hover {
    background:#111827; transform:translateX(6px);
    box-shadow:8px 0 40px rgba(0,0,0,0.55);
}
.kpi-bnum {
    position:absolute; top:-10px; right:10px;
    font-size:140px; font-weight:800; color:var(--c);
    opacity:0.05; line-height:1; pointer-events:none;
    transition:opacity 0.25s;
}
.kpi-btn-wrap:hover .kpi-bnum { opacity:0.12; }
.kpi-btitle { font-size:22px; font-weight:700; color:#cbd5e1; margin-bottom:12px; line-height:1.3; text-align:center; }
.kpi-bdesc  { font-size:15px; color:#7a8fa6; line-height:1.75; text-align:center; }
.kpi-blink  { display:inline-flex; align-items:center; gap:9px; margin-top:28px; font-size:15px; color:#334155; justify-content:center; width:100%; }
.kpi-bdot   { width:8px; height:8px; border-radius:50%; background:var(--c); opacity:0.35; display:inline-block; }
.kpi-btn-wrap:hover .kpi-blink { color:var(--c); }
.kpi-btn-wrap:hover .kpi-bdot  { opacity:1; }
.map-btn-wrap {
    background:#0d1220; border-radius:12px; border-left:5px solid #6366f1;
    padding:36px 28px; display:flex; align-items:center; gap:28px; cursor:pointer;
    position:relative; overflow:hidden;
    transition:background 0.22s, transform 0.22s, box-shadow 0.22s;
}
.map-btn-wrap:hover { background:#111827; transform:translateX(6px); box-shadow:8px 0 40px rgba(0,0,0,0.55); }
.map-bnum { position:absolute; top:-10px; right:20px; font-size:140px; font-weight:800; color:#6366f1; opacity:0.05; line-height:1; pointer-events:none; transition:opacity 0.25s; }
.map-btn-wrap:hover .map-bnum { opacity:0.12; }
.map-btitle { font-size:22px; font-weight:700; color:#cbd5e1; margin-bottom:8px; }
.map-bdesc  { font-size:15px; color:#7a8fa6; line-height:1.75; }
.map-btags  { display:flex; gap:10px; margin-top:12px; }
.map-btag   { font-size:13px; color:#6366f1; border:0.5px solid rgba(99,102,241,0.35); border-radius:5px; padding:4px 14px; }
.map-barrow { margin-left:auto; font-size:22px; color:#334155; flex-shrink:0; transition:color 0.2s, transform 0.2s; }
.map-btn-wrap:hover .map-barrow { color:#6366f1; transform:translateX(7px); }
</style>
""", unsafe_allow_html=True)

_kpis = [
    ("kpi1","#3b82f6","01","Articles par source et par jour",                 "Volume de publication par source et évolution temporelle des collectes",  "pages/1_kpi1_Articles.py"),
    ("kpi2","#a855f7","02","Top des Mots-clés fréquents",                     "Fréquence des termes cyber et identification des sujets dominants",        "pages/2_kpi2_Mots_cles.py"),
    ("kpi3","#ef4444","03","Répartition par type de menaces",                 "Répartition des catégories : ransomware, phishing, APT, data breach…",    "pages/3_KPI3_Menaces.py"),
    ("kpi4","#f59e0b","04","Évolution hebdomadaire et mensuelle des menaces", " ",                                                                        "pages/4_KPI4_Tendances.py"),
    ("kpi5","#22c55e","05","Nombre d'alertes critiques par semaine",          " ",                                                                        "pages/5_KPI5_Alertes.py"),
    ("kpi6","#14b8a6","06","Top CVE les plus fréquents",                      "Vulnérabilités officielles les plus citées",                               "pages/6_KPI6_CVE.py"),
]

col1, col2, col3 = st.columns(3)
for i, (key, color, num, title, desc, page) in enumerate(_kpis):
    col = [col1, col2, col3][i % 3]
    with col:
        st.markdown(f"""
        <div class="kpi-btn-wrap" style="--c:{color}">
            <div class="kpi-bnum">{num}</div>
            <div class="kpi-btitle">{title}</div>
            <div class="kpi-bdesc">{desc}</div>
            <div class="kpi-blink"><div class="kpi-bdot"></div>Voir l'analyse →</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("→", key=f"btn_{key}", help=title, use_container_width=True):
            st.switch_page(page)

st.markdown("<br>", unsafe_allow_html=True)

col_map, _, _ = st.columns(3)
with col_map:
    st.markdown("""
<div class="map-btn-wrap">
  <div class="map-bnum">07</div>
  <div style="flex:1">
    <div class="map-btitle">Carte mondiale des menaces</div>
    <div class="map-bdesc">Visualisation géographique des cyberattaques · Hotspots, origines et cibles par pays</div>
    <div class="map-btags"><span class="map-btag">Temps réel</span><span class="map-btag">Géolocalisation</span></div>
  </div>
  <div class="map-barrow">→</div>
</div>
""", unsafe_allow_html=True)
    if st.button("Ouvrir la Carte Menaces →", key="btn_map", use_container_width=True):
        st.switch_page("pages/7_Carte_Menaces.py")