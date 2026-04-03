"""
CyberPulse — KPI 2
Suivi des mots-clés cyber
Chargement depuis PostgreSQL via get_mart_k2()
"""

import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k2, force_refresh, get_articles_by_keyword

st.set_page_config(page_title="KPI 2 - Mots-clés", layout="wide")

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif;}
.stApp{
    background-image: url("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/wAARCANcBgwDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL") !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    background: rgba(5, 10, 20, 0.75);
    z-index: 0;
    pointer-events: none;
}
[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }
[data-testid="stSidebar"]{background:#0f1422!important;border-right:1px solid #1e2a42;}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}

.kpi-tag{display:inline-block;font-family:'Roboto Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#22c55e;background:rgba(34,197,94,.1);
border:1px solid rgba(34,197,94,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}

.page-title {
    text-align: center;
    font-size: 3rem;
    font-weight: 700;
    color: #a855f7;
    margin-bottom: 20px;
    line-height: 1.2;
    font-family: 'Roboto', sans-serif;
}

.desc-box{
    background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #22c55e;
    border-radius:8px;padding:20px 24px;margin-bottom:24px;
    color:#94a3b8;font-size:1.5rem;line-height:1.8;
    text-align:center;
    max-width:900px;margin-left:auto;margin-right:auto;
}

.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:1rem;letter-spacing:.08em;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:8px 18px;}
.badge-err{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#ef4444;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

div[data-testid="stButton"] button {
    background: rgba(34,197,94,0.12) !important;
    border: 1px solid rgba(34,197,94,0.4) !important;
    color: #22c55e !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
}
div[data-testid="stButton"] button:hover {
    background: rgba(34,197,94,0.25) !important;
}
</style>
""", unsafe_allow_html=True)

# ── Fond animé ECG ────────────────────────────────────────────────────────────
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
    if (!p.getElementById('ecg-bg')) {
      stop && stop();
      stop = startECG();
    }
  }, 2000);

  p.addEventListener('visibilitychange', function() {
    if (!p.hidden) {
      stop && stop();
      stop = startECG();
    }
  });

})();
</script>
""", height=0)


# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<div style="text-align:center"><div class="kpi-tag">KPI 2</div></div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Suivi des mots-clés</div>', unsafe_allow_html=True)
st.markdown("""
<div class="desc-box">
    Cliquez sur une bulle du scatter pour afficher les articles associés avec leurs liens.<br>
    Cellule grise sur la heatmap : 0 occurrence sur la période sélectionnée.
</div>
""", unsafe_allow_html=True)

# ── Refresh + badge ───────────────────────────────────────────────────────────
_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Actualiser", use_container_width=True):
        force_refresh()
        st.rerun()

# ── Chargement ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_mart_k2():
    return get_mart_k2()

try:
    df_raw = load_mart_k2()
    load_ok = True
    load_ts = time.strftime("%H:%M:%S")
except Exception as e:
    load_ok = False
    load_err = str(e)

with col_b:
    if load_ok:
        st.markdown(
            f'<div class="badge-live"><span class="dot-live"></span>{load_ts}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="badge-err">Erreur de connexion</div>', unsafe_allow_html=True)

if not load_ok:
    st.error(f"Impossible de charger mart_k2 : {load_err}")
    st.stop()

if df_raw.empty:
    st.warning("mart_k2 est vide. Vérifiez votre pipeline dbt.")
    st.stop()

# ── Catégories ────────────────────────────────────────────────────────────────
CATEGORIES = {
    "failles": {
        "label": "Vulnerabilities & Exploits", "color": "#ef4444",
        "subcats": {
            "Vulnerabilities": ["zero-day", "0-day", "cve", "rce", "remote code execution", "lpe", "privilege escalation"],
            "Techniques": ["sql injection", "xss", "cross-site scripting", "buffer overflow", "man-in-the-middle", "mitm", "supply chain attack", "supply chain"],
            "Data Leaks": ["data breach", "database dump", "leaked credentials", "exfiltration", "data leak", "exposed credentials"],
        },
    },
    "infra": {
        "label": "Infrastructures", "color": "#3b82f6",
        "subcats": {
            "Cloud": ["aws", "s3 bucket", "azure", "azure ad", "google cloud", "gcp", "kubernetes", "docker"],
            "Systems": ["active directory", "windows server", "linux kernel", "macos", "tcc"],
            "Networks": ["vpn", "firewall", "sd-wan", "dns tunneling", "firewall bypass", "vpn gateway"],
        },
    },
    "editeurs": {
        "label": "Critical Vendors", "color": "#f59e0b",
        "subcats": {
            "Hardware": ["cisco", "fortinet", "palo alto", "check point", "juniper", "ubiquiti", "f5"],
            "Software": ["microsoft 365", "exchange", "vmware", "esxi", "citrix", "sap", "salesforce", "atlassian", "confluence", "jira"],
        },
    },
    "menaces": {
        "label": "Threats & APT", "color": "#a855f7",
        "subcats": {
            "Malware": ["ransomware", "infostealer", "trojan", "rat", "botnet", "wiper", "malware"],
            "APT Groups": ["apt28", "lazarus", "lockbit", "revil", "fancy bear", "scattered spider", "volt typhoon"],
            "Indicators": ["ioc", "indicator of compromise", "ttp", "threat intelligence", "threat actor"],
        },
    },
}

PERIODS    = {3: "3j", 7: "7j", 15: "15j", 30: "30j"}
CAT_COLORS = {"failles": "#ef4444", "infra": "#3b82f6", "editeurs": "#f59e0b", "menaces": "#a855f7"}

kw_cat_map = {
    kw: cat_key
    for cat_key, cat in CATEGORIES.items()
    for kws in cat["subcats"].values()
    for kw in kws
}

def get_counts(df, period):
    sub = df[df["period_days"] == period]
    return dict(zip(sub["keyword"], sub["occurrences"].fillna(0).astype(int)))

def get_article_counts(df, period):
    sub = df[df["period_days"] == period]
    return dict(zip(sub["keyword"], sub["article_count"].fillna(0).astype(int)))

def get_source_counts(df, period):
    sub = df[df["period_days"] == period]
    if "source_count" in sub.columns:
        return dict(zip(sub["keyword"], sub["source_count"].fillna(0).astype(int)))
    return {}

counts_all     = {p: get_counts(df_raw, p)         for p in PERIODS}
art_counts_all = {p: get_article_counts(df_raw, p)  for p in PERIODS}
src_counts_all = {p: get_source_counts(df_raw, p)   for p in PERIODS}

# ── Slider période ────────────────────────────────────────────────────────────
col_sl, _ = st.columns([1, 3])
with col_sl:
    n_days = st.slider("Période d'affichage (jours)", min_value=3, max_value=30, value=7, step=1, key="k2_days")

_avail     = sorted(PERIODS.keys())
period_sel = min(_avail, key=lambda p: abs(p - n_days))

counts     = counts_all[period_sel]
art_counts = art_counts_all[period_sel]
src_counts = src_counts_all[period_sel]

# ── Métriques résumées avec compteurs animés ──────────────────────────────────
top_kw            = max(counts, key=counts.get) if any(counts.values()) else "—"
total_occ         = sum(counts.values())
nb_detect         = sum(1 for v in counts.values() if v > 0)
nb_articles_total = int(df_raw[df_raw["period_days"] == period_sel]["article_count"].sum())
period_label      = PERIODS[period_sel]

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ background:transparent; font-family:'Roboto',sans-serif; }}
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }}
.card {{
    background:rgba(15,20,34,0.85); border:1px solid #1e2a42; border-radius:10px;
    padding:28px 20px; text-align:center; position:relative; overflow:hidden;
    transition:border-color 0.2s, transform 0.2s, box-shadow 0.2s; cursor:default;
}}
.card::before {{ content:''; position:absolute; top:0; left:0; width:100%; height:3px; background:#a855f7; border-radius:10px 10px 0 0; }}
.card:hover {{ border-color:#a855f7; transform:translateY(-3px); box-shadow:0 8px 28px rgba(168,85,247,0.18); }}
.val {{ font-family:'Roboto Mono',monospace; font-size:3rem; font-weight:700; color:#e2e8f0; }}
.lbl {{ font-size:0.9rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.08em; margin-top:10px; }}
</style>
<div class="grid">
  <div class="card">
    <div class="val" id="v1">0</div>
    <div class="lbl">Mots-clés détectés ({period_label})</div>
  </div>
  <div class="card">
    <div class="val" style="font-size:2rem">{top_kw}</div>
    <div class="lbl">Mot-clé le plus recherché ({period_label})</div>
  </div>
  <div class="card">
    <div class="val" id="v3">0</div>
    <div class="lbl">Total occurrences ({period_label})</div>
  </div>
  <div class="card">
    <div class="val" id="v4">0</div>
    <div class="lbl">Articles correspondants ({period_label})</div>
  </div>
</div>
<script>
function animCount(id, target, duration) {{
  var el = document.getElementById(id);
  if (!el || isNaN(target)) return;
  var step = target / (duration / 16), current = 0;
  var timer = setInterval(function() {{
    current += step;
    if (current >= target) {{ current = target; clearInterval(timer); }}
    el.textContent = Math.floor(current).toLocaleString('fr-FR');
  }}, 16);
}}
animCount('v1', {nb_detect}, 1000);
animCount('v3', {total_occ}, 1200);
animCount('v4', {nb_articles_total}, 1000);
</script>
""", height=150)

st.markdown("<br>", unsafe_allow_html=True)

# ── Graphique bar chart ───────────────────────────────────────────────────────
top_n = 20

col_title, col_cat = st.columns([3, 1])
with col_cat:
    cat_filter = st.selectbox(
        "Catégorie",
        ["Toutes", "Vulnerabilities", "Infra", "Vendors", "Menaces"],
        key="k2_cat"
    )

cat_filter_map = {
    "Toutes": None, "Vulnerabilities": "failles",
    "Infra": "infra", "Vendors": "editeurs", "Menaces": "menaces"
}

entries   = sorted(counts.items(), key=lambda x: x[1], reverse=True)
df_chart  = pd.DataFrame(entries, columns=["keyword", "occurrences"])
df_chart["category"] = df_chart["keyword"].map(kw_cat_map)

if cat_filter_map[cat_filter]:
    df_chart = df_chart[df_chart["category"] == cat_filter_map[cat_filter]]

df_chart = df_chart.head(top_n).sort_values("occurrences")

with col_title:
    st.markdown(
        f"<div style='text-align:center;font-size:2.2rem;color:#a855f7;font-weight:700;padding-top:24px'>"
        f"Top {top_n} mots-clés — {n_days}j</div>",
        unsafe_allow_html=True,
    )

with st.container():
    fig = px.bar(
        df_chart, x="occurrences", y="keyword",
        orientation="h", color="category",
        color_discrete_map=CAT_COLORS,
        labels={"occurrences": "Cas", "keyword": "", "category": "Catégorie"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,10,20,0.6)",
        font=dict(family="Roboto", color="#94a3b8", size=18),
        xaxis=dict(gridcolor="#1e2a42", tickfont=dict(size=18, color="#94a3b8"), title_font=dict(size=20)),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=18, color="#cbd5e1")),
        title_font=dict(size=22, color="#e2e8f0"),
        legend=dict(font=dict(size=18)),
        legend_title_font=dict(size=18),
        legend_title="Catégorie",
        margin=dict(l=20, r=20, t=60, b=20),
        height=max(500, top_n * 40),
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# HEATMAP — Intensité des menaces par catégorie × période
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;font-size:2.2rem;color:#a855f7;font-weight:700;padding-bottom:12px'>"
    "Intensité des menaces par catégorie</div>",
    unsafe_allow_html=True,
)

cat_keys    = list(CATEGORIES.keys())
cat_labels  = [CATEGORIES[k]["label"] for k in cat_keys]
period_keys = sorted(PERIODS.keys())
period_lbls = [PERIODS[p] for p in period_keys]

# Matrice occurrences catégorie × période
heat_z = []
for cat_key in cat_keys:
    kws_in_cat = [kw for kws in CATEGORIES[cat_key]["subcats"].values() for kw in kws]
    heat_z.append([
        sum(counts_all[p].get(kw, 0) for kw in kws_in_cat)
        for p in period_keys
    ])

# Delta d'accélération : rythme 3j vs moyenne 7j ramenée sur 3j
delta_col = []
for cat_key in cat_keys:
    kws_in_cat = [kw for kws in CATEGORIES[cat_key]["subcats"].values() for kw in kws]
    v3       = sum(counts_all[3].get(kw, 0) for kw in kws_in_cat)
    v7       = sum(counts_all[7].get(kw, 0) for kw in kws_in_cat)
    baseline = (v7 / 7) * 3
    ratio    = round((v3 / baseline) - 1, 2) if baseline > 0 else 0.0
    delta_col.append(ratio)

fig_heat = go.Figure(data=go.Heatmap(
    z=heat_z,
    x=period_lbls,
    y=cat_labels,
    colorscale=[
        [0.0,  "#0f1422"],
        [0.25, "#1e3a5f"],
        [0.55, "#6d28d9"],
        [0.80, "#a855f7"],
        [1.0,  "#f0abfc"],
    ],
    text=[[f"{v:,}" for v in row] for row in heat_z],
    texttemplate="%{text}",
    textfont={"size": 20, "family": "Roboto Mono", "color": "#ffffff"},
    hoverongaps=False,
    showscale=True,
    colorbar=dict(
        tickfont=dict(color="#94a3b8", size=14),
        outlinewidth=0,
        bgcolor="rgba(0,0,0,0)",
    ),
))

# Colonne delta : annotations à droite
for i, (cat_label, delta) in enumerate(zip(cat_labels, delta_col)):
    if delta > 0.1:
        arrow, color = "↑", "#22c55e"
    elif delta < -0.1:
        arrow, color = "↓", "#ef4444"
    else:
        arrow, color = "→", "#94a3b8"
    pct = abs(delta) * 100
    fig_heat.add_annotation(
        x=4.55, y=i,
        text=f"<b>{arrow} {pct:.0f}%</b>",
        showarrow=False,
        font=dict(size=16, color=color, family="Roboto Mono"),
        xanchor="left",
        yanchor="middle",
    )

fig_heat.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(5,10,20,0.6)",
    font=dict(family="Roboto", color="#94a3b8", size=16),
    xaxis=dict(
        tickfont=dict(size=18, color="#cbd5e1"),
        title_font=dict(size=18),
        range=[-0.5, 5.2],
    ),
    yaxis=dict(tickfont=dict(size=16, color="#cbd5e1")),
    margin=dict(l=20, r=80, t=20, b=20),
    height=340,
)
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown(
    "<div style='text-align:center;font-size:0.95rem;color:#64748b;margin-top:-10px;margin-bottom:24px'>"
    "Somme des occurrences par famille — plus c'est violet, plus l'activité est intense. "
    "La flèche compare le rythme des 3 derniers jours à la moyenne des 7 derniers jours."
    "</div>",
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════════════════════════════════════════
# SCATTER — Qualité du signal : occurrences vs articles distincts
# ════════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center;font-size:2.2rem;color:#a855f7;font-weight:700;padding-bottom:12px'>"
    f"Qualité du signal — {n_days}j</div>",
    unsafe_allow_html=True,
)

scatter_rows = [
    {
        "keyword":       kw,
        "occurrences":   counts.get(kw, 0),
        "article_count": art_counts.get(kw, 0),
        "category":      kw_cat_map.get(kw, "inconnu"),
    }
    for kw in counts
    if counts.get(kw, 0) > 0
]
df_sc = pd.DataFrame(scatter_rows)

if not df_sc.empty:
    med_occ  = df_sc["occurrences"].median()
    med_art  = df_sc["article_count"].median()
    x_max    = df_sc["occurrences"].max() * 1.12
    y_max    = df_sc["article_count"].max() * 1.12
    occ_q80  = df_sc["occurrences"].quantile(0.80)

    fig_sc = go.Figure()

    # Quadrants colorés en fond
    for x0, x1, y0, y1, fill in [
        (med_occ, x_max,   med_art, y_max,   "rgba(168,85,247,0.07)"),
        (med_occ, x_max,   0,       med_art, "rgba(239,68,68,0.05)"),
        (0,       med_occ, med_art, y_max,   "rgba(59,130,246,0.05)"),
        (0,       med_occ, 0,       med_art, "rgba(15,20,34,0.0)"),
    ]:
        fig_sc.add_shape(
            type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
            fillcolor=fill, line_width=0, layer="below",
        )

    # Un trace par catégorie
    for cat_key, cat_color in CAT_COLORS.items():
        sub = df_sc[df_sc["category"] == cat_key].copy()
        if sub.empty:
            continue
        size_norm = (sub["occurrences"] / df_sc["occurrences"].max() * 38 + 6).tolist()
        labels    = sub["keyword"].where(sub["occurrences"] >= occ_q80, "").tolist()
        fig_sc.add_trace(go.Scatter(
            x=sub["occurrences"],
            y=sub["article_count"],
            mode="markers+text",
            name=CATEGORIES[cat_key]["label"],
            marker=dict(size=size_norm, color=cat_color, line=dict(width=0), sizemode="diameter"),
            text=labels,
            textposition="top center",
            textfont=dict(size=11, color="#e2e8f0", family="Roboto"),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Occurrences : %{x}<br>"
                "Articles distincts : %{y}"
                "<extra></extra>"
            ),
            customdata=sub["keyword"].tolist(),
        ))

    # Lignes médiane
    fig_sc.add_hline(y=med_art, line_dash="dash", line_color="rgba(148,163,184,0.22)", line_width=1)
    fig_sc.add_vline(x=med_occ, line_dash="dash", line_color="rgba(148,163,184,0.22)", line_width=1)

    # Annotations quadrants
    quad_style = dict(
        showarrow=False,
        font=dict(size=12, color="rgba(148,163,184,0.50)", family="Roboto"),
        xanchor="center", yanchor="middle",
    )
    fig_sc.add_annotation(x=x_max * 0.78, y=y_max * 0.93, text="Signal fort & large",             **quad_style)
    fig_sc.add_annotation(x=x_max * 0.78, y=y_max * 0.07, text="Sur-représenté (peu d'articles)", **quad_style)
    fig_sc.add_annotation(x=x_max * 0.18, y=y_max * 0.93, text="Signal large & discret",          **quad_style)
    fig_sc.add_annotation(x=x_max * 0.18, y=y_max * 0.07, text="Signal faible",                   **quad_style)

    fig_sc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,10,20,0.6)",
        font=dict(family="Roboto", color="#94a3b8", size=16),
        xaxis=dict(
            gridcolor="#1e2a42", tickfont=dict(size=16, color="#94a3b8"),
            title="Occurrences (mentions)", title_font=dict(size=18), range=[0, x_max],
        ),
        yaxis=dict(
            gridcolor="#1e2a42", tickfont=dict(size=16, color="#94a3b8"),
            title="Articles distincts", title_font=dict(size=18), range=[0, y_max],
        ),
        legend=dict(font=dict(size=16), title_font=dict(size=16), title_text="Catégorie"),
        margin=dict(l=20, r=20, t=20, b=20),
        height=540,
    )

    # ── Rendu scatter avec capture du clic ────────────────────────────────────
    event = st.plotly_chart(
        fig_sc,
        use_container_width=True,
        on_select="rerun",
        key="scatter_k2",
    )

    st.markdown(
        "<div style='text-align:center;font-size:0.95rem;color:#64748b;margin-top:-10px'>"
        "Axe X : nombre de mentions — Axe Y : articles sources distincts. "
        "Les labels affichent les mots-clés du top 20%. "
        "Cliquez sur une bulle pour voir les articles associés."
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Panel articles au clic ────────────────────────────────────────────────
    points     = (event.selection or {}).get("points", [])
    clicked_kw = points[0].get("customdata", "") if points else ""

    if clicked_kw:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:1.6rem;font-weight:700;color:#a855f7;margin-bottom:12px'>"
            f"Articles mentionnant <span style='color:#22c55e'>{clicked_kw}</span>"
            f" — {n_days}j</div>",
            unsafe_allow_html=True,
        )

        try:
            df_arts = get_articles_by_keyword(clicked_kw, n_days)
        except Exception as e:
            st.error(f"Erreur chargement articles : {e}")
            df_arts = pd.DataFrame()

        if df_arts.empty:
            st.info(f"Aucun article trouvé pour « {clicked_kw} » sur {n_days}j.")
        else:
            st.markdown(
                f"<div style='color:#64748b;font-size:0.9rem;margin-bottom:16px'>"
                f"{len(df_arts)} article(s) trouvé(s)</div>",
                unsafe_allow_html=True,
            )
            cat_colors_map = {
                "failles":  "#ef4444", "infra":    "#3b82f6",
                "editeurs": "#f59e0b", "menaces":  "#a855f7",
            }
            for _, row in df_arts.iterrows():
                pub       = str(row.get("published_date", ""))[:10]
                src       = row.get("source", "")
                cat       = row.get("category", "")
                url       = row.get("url", "")
                title     = row.get("title", "Sans titre")
                cat_color = cat_colors_map.get(cat, "#64748b")
                title_html = (
                    f'<a href="{url}" target="_blank" '
                    f'style="color:#e2e8f0;text-decoration:none">{title}</a>'
                    if url else title
                )
                cat_html = (
                    f"&nbsp;·&nbsp;<span style='color:{cat_color}'>{cat}</span>"
                    if cat else ""
                )
                st.markdown(f"""
<div style="
    background:rgba(15,20,34,0.85);
    border:1px solid #1e2a42;
    border-left:3px solid {cat_color};
    border-radius:8px;
    padding:14px 18px;
    margin-bottom:10px;
">
    <div style="font-size:1.05rem;font-weight:600;color:#e2e8f0;margin-bottom:6px">
        {title_html}
    </div>
    <div style="font-size:0.85rem;color:#64748b">
        {src}&nbsp;·&nbsp;{pub}{cat_html}
    </div>
</div>
""", unsafe_allow_html=True)

else:
    st.info("Aucune donnée disponible pour le scatter sur cette période.")