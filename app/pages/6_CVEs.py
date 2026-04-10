"""
CyberPulse -- KPI 6
Most mentioned CVEs + NVD details
Design : fond bokeh, animation ECG, cartes animees (style KPI1)
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import requests
import time
import sys, pathlib
import os

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_mart_k6, get_stg_articles, force_refresh

st.set_page_config(page_title="CyberPulse - KPI 6 CVE", layout="wide")

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

.desc-box {
    background: rgba(15,20,34,0.8);
    border: 1px solid #1e2a42;
    border-left: 3px solid #3b82f6;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 20px;
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
    backdrop-filter: blur(8px);
}
.desc-line { color: #94a3b8; font-size: 0.92rem; line-height: 1.8; }
.desc-line b { color: #cbd5e1; }

.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.insight-box{background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#93c5fd;font-size:0.88rem;backdrop-filter:blur(8px);}

.warn-box{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);
border-radius:8px;padding:12px 16px;margin-top:10px;color:#fcd34d;font-size:0.88rem;}

.note-box{background:rgba(100,116,139,0.07);border:1px solid rgba(100,116,139,0.2);
border-radius:8px;padding:10px 16px;margin-top:12px;color:#94a3b8;font-size:0.82rem;}

.cve-card{background:rgba(15,20,34,0.85);border:1px solid #1e2a42;border-radius:10px;
padding:20px 24px;margin-top:16px;backdrop-filter:blur(8px);}
.cve-card-title{font-family:'Roboto Mono',monospace;font-size:1.1rem;font-weight:700;color:#e2e8f0;}
.cve-card-score{font-family:'Roboto Mono',monospace;font-size:2rem;font-weight:700;}
.score-critical{color:#ef4444;}
.score-high{color:#f97316;}
.score-medium{color:#f59e0b;}
.score-low{color:#22c55e;}
.cve-desc{color:#94a3b8;font-size:0.88rem;line-height:1.7;margin-top:10px;}
.badge{display:inline-block;border-radius:4px;padding:2px 10px;font-size:0.75rem;font-weight:600;margin-right:6px;}
.badge-red{background:rgba(239,68,68,.15);color:#ef4444;border:1px solid rgba(239,68,68,.3);}
.badge-orange{background:rgba(249,115,22,.15);color:#f97316;border:1px solid rgba(249,115,22,.3);}
.badge-yellow{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid rgba(245,158,11,.3);}
.badge-green{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3);}
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
      r: Math.random()*1.5+0.3, phase: Math.random()*Math.PI*2,
      speed: Math.random()*0.008+0.004,
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

# ── Config ────────────────────────────────────────────────────────────────────
PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(5,10,20,0.6)',
    font=dict(family='Roboto', color='#94a3b8'),
)

# Mapping severite → classes CSS
_SCORE_CLASSES = {
    'CRITICAL': ('score-critical', 'badge-red'),
    'HIGH':     ('score-high',     'badge-orange'),
    'MEDIUM':   ('score-medium',   'badge-yellow'),
    'LOW':      ('score-low',      'badge-green'),
}


# ── NVD API ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _fetch_cve_details(cve_id):
    """Appel NVD v2 — cache 1h pour eviter le rate-limit."""
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    try:
        resp = requests.get(url, timeout=10,
                            headers={"User-Agent": "CyberPulse-Dashboard/1.0"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        vulns = data.get('vulnerabilities', [])
        if not vulns:
            return None
        cve_data = vulns[0].get('cve', {})

        # Description EN
        descriptions = cve_data.get('descriptions', [])
        desc_en = next((d['value'] for d in descriptions if d['lang'] == 'en'), 'N/A')

        # Score CVSS — cascade v3.1 → v3.0 → v2
        score, severity = None, 'N/A'
        metrics = cve_data.get('metrics', {})
        for key in ('cvssMetricV31', 'cvssMetricV30'):
            if key in metrics:
                m = metrics[key][0]['cvssData']
                score = m.get('baseScore')
                severity = m.get('baseSeverity', 'N/A')
                break
        else:
            if 'cvssMetricV2' in metrics:
                m = metrics['cvssMetricV2'][0]['cvssData']
                score = m.get('baseScore')
                severity = metrics['cvssMetricV2'][0].get('baseSeverity', 'N/A')

        # Produit affecte via CPE
        produit = 'N/A'
        configs = cve_data.get('configurations', [])
        if configs:
            nodes = configs[0].get('nodes', [])
            if nodes:
                cpe_matches = nodes[0].get('cpeMatch', [])
                if cpe_matches:
                    parts = cpe_matches[0].get('criteria', '').split(':')
                    if len(parts) >= 5:
                        produit = f"{parts[3]} / {parts[4]}"

        refs = [r['url'] for r in cve_data.get('references', [])[:3]]
        published = cve_data.get('published', 'N/A')[:10]

        return {
            'id': cve_id,
            'description': desc_en,
            'score': score,
            'severity': severity,
            'produit': produit,
            'published': published,
            'references': refs,
        }
    except Exception:
        return None


def _render_cve_card(details):
    """Affiche une fiche CVE formatee."""
    if not details:
        st.warning("Details indisponibles pour cette CVE (API NVD injoignable ou CVE inconnue).")
        return

    score_class, badge_class = _SCORE_CLASSES.get(details['severity'], ('score-medium', 'badge-yellow'))
    score_display = f"{details['score']:.1f}" if details['score'] else 'N/A'

    refs_html = ''.join(
        f'<a href="{ref}" target="_blank" style="color:#3b82f6;font-size:0.8rem;'
        f'display:block;margin-top:4px">{ref[:80]}...</a>'
        for ref in details['references']
    )

    st.markdown(f"""
    <div class="cve-card">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px">
            <div>
                <div class="cve-card-title">{details['id']}</div>
                <div style="margin-top:8px">
                    <span class="badge {badge_class}">{details['severity']}</span>
                    <span style="color:#64748b;font-size:0.8rem">Publie le {details['published']}</span>
                </div>
                <div style="color:#64748b;font-size:0.82rem;margin-top:6px">
                    Produit affecte : <b style="color:#94a3b8">{details['produit']}</b>
                </div>
            </div>
            <div style="text-align:center">
                <div class="cve-card-score {score_class}">{score_display}</div>
                <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:.1em">Score CVSS</div>
            </div>
        </div>
        <div class="cve-desc">{details['description']}</div>
        <div style="margin-top:12px;color:#64748b;font-size:0.78rem">References officielles :</div>
        {refs_html}
    </div>
    """, unsafe_allow_html=True)


# ── En-tete ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 6</div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">CVEs les plus mentionnees</div>', unsafe_allow_html=True)

# ── Refresh + badge ───────────────────────────────────────────────────────────
_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Synchroniser", use_container_width=True):
        force_refresh()
        st.rerun()

# ── Description ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="desc-box">
    <div class="desc-line">
        <b>Objectif :</b> Identifier les CVEs officielles les plus citees dans les articles collectes.<br>
        <b>Lecture :</b> Une CVE tres mentionnee indique une vulnerabilite activement couverte — souvent exploitee ou recemment patchee.<br>
        <b>Format CVE :</b> CVE-ANNEE-ID (ex. CVE-2024-1234) — standard international MITRE.<br>
        <b>Details :</b> Scores et descriptions proviennent de l'API officielle NVD (National Vulnerability Database).
    </div>
</div>
""", unsafe_allow_html=True)

# ── Chargement ────────────────────────────────────────────────────────────────
df_raw = get_mart_k6()

if df_raw.empty:
    st.markdown("""
    <div class="warn-box">
        <b>Aucune CVE detectee dans les articles actuels.</b><br><br>
        Explications possibles :<br>
        - Les descriptions sont trop courtes pour contenir des references CVE completes.<br>
        - Relancez acquisition.py pour obtenir de nouveaux articles.<br>
        - Les CVEs apparaissent principalement dans les articles CISA Alerts et BleepingComputer.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

with col_b:
    st.markdown(
        f'<div class="badge-live"><span class="dot-live"></span>'
        f'LIVE - {len(df_raw)} CVEs disponibles</div>',
        unsafe_allow_html=True,
    )

# ── Slider top N ──────────────────────────────────────────────────────────────
top_n = st.slider("Nombre de CVEs a afficher", 5, min(20, len(df_raw)), min(10, len(df_raw)), key="k6_topn")
agg = df_raw.head(top_n).copy()
agg.columns = ['CVE', 'Mentions']
agg['Annee'] = agg['CVE'].str.extract(r'CVE-(\d{4})-')

# ── Metriques animees ─────────────────────────────────────────────────────────
_section_title("Vue d'ensemble")

total_uniques = len(df_raw)
top_cve = agg.iloc[0]['CVE']
top_mentions = int(agg.iloc[0]['Mentions'])
nb_annees = agg['Annee'].dropna().nunique()
annees_str = ', '.join(sorted(agg['Annee'].dropna().unique(), reverse=True))

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
.card:nth-child(2)::before {{ background:#ef4444; }}
.card:nth-child(3)::before {{ background:#f59e0b; }}
.card:nth-child(4)::before {{ background:#22c55e; }}
.card:hover {{ border-color:#3b82f6; transform:translateY(-3px); box-shadow:0 8px 28px rgba(59,130,246,0.18); background:rgba(20,28,48,0.95); }}
.val {{ font-family:'Roboto Mono',monospace; font-size:3rem; font-weight:700; color:#e2e8f0; }}
.lbl {{ font-size:1rem; color:#94a3b8; text-transform:uppercase; letter-spacing:.08em; margin-top:10px; }}
.sub {{ font-size:1.1rem; margin-top:8px; font-weight:500; }}
</style>
<div class="grid">
  <div class="card">
    <div class="val" id="v1">0</div>
    <div class="lbl">CVEs uniques</div>
    <div class="sub" style="color:#3b82f6">Detectees en base</div>
  </div>
  <div class="card">
    <div class="val" style="font-size:1.5rem">{top_cve}</div>
    <div class="lbl">CVE la + citee</div>
    <div class="sub" style="color:#ef4444">{top_mentions} mentions</div>
  </div>
  <div class="card">
    <div class="val" id="v3">0</div>
    <div class="lbl">Top {top_n} affichees</div>
    <div class="sub" style="color:#f59e0b">Selection courante</div>
  </div>
  <div class="card">
    <div class="val" id="v4">0</div>
    <div class="lbl">Annees couvertes</div>
    <div class="sub" style="color:#22c55e">{annees_str}</div>
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
animCount('v1', {total_uniques}, 1200, false);
animCount('v3', {top_n}, 800, false);
animCount('v4', {nb_annees}, 600, false);
</script>
""", height=160)

# ── Tableau + Graphique ───────────────────────────────────────────────────────
_section_title("Classement des CVEs")

col1, col2 = st.columns([1.3, 1])

with col1:
    st.markdown(
        "<div style='color:#94a3b8;font-size:1.1rem;margin-bottom:12px'>Tableau classe</div>",
        unsafe_allow_html=True,
    )
    st.dataframe(
        agg[['CVE', 'Mentions', 'Annee']],
        use_container_width=True, hide_index=True, height=400,
    )

with col2:
    fig = go.Figure(go.Bar(
        x=agg['Mentions'], y=agg['CVE'],
        orientation='h',
        marker_color='#3b82f6',
        text=agg['Mentions'], textposition='outside',
        textfont=dict(color='#94a3b8'),
        hovertemplate='<b>%{y}</b><br>%{x} mentions<extra></extra>',
    ))
    fig.update_layout(
        **PLOTLY_BASE,
        xaxis=dict(gridcolor='#1e2a42', title='Mentions', tickfont=dict(size=14)),
        yaxis=dict(gridcolor='#1e2a42', autorange='reversed', tickfont=dict(size=14, color='#cbd5e1')),
        height=400, showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Interpretation & Insights ─────────────────────────────────────────────────
# Concentration top-1 vs reste — signal de sur-mediatisation
total_mentions = int(agg['Mentions'].sum())
top1_pct = round(top_mentions / total_mentions * 100, 1) if total_mentions > 0 else 0

st.markdown(f"""
<div class="insight-box">
    <b>Interpretation & Insights</b><br><br>
    - <b>Mediatisation :</b> {top_cve} concentre {top1_pct}% des mentions du top {top_n}.
      {'Sur-mediatisation probable — verifier si cette CVE est effectivement exploitee en conditions reelles (KEV CISA).'
       if top1_pct > 40 else 'Repartition equilibree entre les CVEs du classement.'}<br>
    - <b>Couverture temporelle :</b> {nb_annees} annee(s) representee(s) ({annees_str}).
      {'Des CVEs anciennes persistent dans le flux — verifier qu elles sont bien patchees dans l infra.'
       if nb_annees > 2 else 'Flux concentre sur des CVEs recentes.'}<br>
    - <b>Action :</b> croiser ce classement avec le catalogue KEV (Known Exploited Vulnerabilities) de la CISA
      pour prioriser les CVEs activement exploitees dans les campagnes en cours.
</div>
""", unsafe_allow_html=True)

# ── Fiche detail CVE ──────────────────────────────────────────────────────────
_section_title("Fiche detail CVE")
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:12px'>"
    "Selectionnez une CVE pour afficher ses details officiels depuis la base NVD."
    "</div>",
    unsafe_allow_html=True,
)

cve_selectionnee = st.selectbox("Choisir une CVE", options=agg['CVE'].tolist(), key="k6_detail")

if st.button("Charger les details depuis NVD", key="k6_fetch"):
    with st.spinner(f"Interrogation de l'API NVD pour {cve_selectionnee}..."):
        details = _fetch_cve_details(cve_selectionnee)
        time.sleep(0.5)
    _render_cve_card(details)

# ── Reference CVSS ────────────────────────────────────────────────────────────
_section_title("Reference -- Echelle de score CVSS")
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:16px'>"
    "Le score CVSS (Common Vulnerability Scoring System) mesure la severite d'une vulnerabilite de 0 a 10."
    "</div>",
    unsafe_allow_html=True,
)

scores = [
    ("9.0 - 10.0", "CRITICAL", "#ef4444", "badge-red",
     "Exploitable a distance sans authentification. Impact total sur le systeme. Patch immediat requis."),
    ("7.0 - 8.9",  "HIGH",     "#f97316", "badge-orange",
     "Facile a exploiter, impact significatif. Peut compromettre des donnees ou services critiques."),
    ("4.0 - 6.9",  "MEDIUM",   "#f59e0b", "badge-yellow",
     "Exploitable sous certaines conditions. Impact modere, a traiter dans les prochains cycles de patch."),
    ("0.1 - 3.9",  "LOW",      "#22c55e", "badge-green",
     "Difficile a exploiter. Impact limite. A surveiller mais pas urgent."),
]

cols = st.columns(4)
for i, (score, niveau, couleur, badge, texte) in enumerate(scores):
    cols[i].markdown(
        f"<div style='background:rgba(15,20,34,0.85);border:1px solid #1e2a42;border-radius:8px;"
        f"padding:16px;border-top:3px solid {couleur};backdrop-filter:blur(8px)'>"
        f"<div style='font-family:Roboto Mono,monospace;font-size:1.3rem;"
        f"font-weight:700;color:{couleur}'>{score}</div>"
        f"<div style='margin:8px 0'><span class='badge {badge}'>{niveau}</span></div>"
        f"<div style='color:#64748b;font-size:0.8rem;line-height:1.6'>{texte}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("""
<div class="note-box">
    <b>Comment le score est-il calcule ?</b><br>
    Le CVSS considere 3 dimensions :
    <br>- <b>Exploitabilite</b> : accessible depuis internet ? authentification requise ? interaction humaine ?
    <br>- <b>Impact</b> : confidentialite des donnees ? integrite du systeme ? disponibilite du service ?
    <br>- <b>Portee</b> : l'attaque est-elle limitee au systeme cible ou se propage-t-elle ?
    <br><br>
    <b>Exemples celebres :</b>
    Log4Shell (CVE-2021-44228) = 10.0 &nbsp;|&nbsp;
    EternalBlue (CVE-2017-0144) = 9.3 (origine de WannaCry) &nbsp;|&nbsp;
    Heartbleed (CVE-2014-0160) = 7.5
    <br><br>
    <b style='color:#ef4444'>Tout score >= 7.0 doit etre patche en urgence.</b>
    Un score >= 9.0 necessite une action immediate.
</div>
""", unsafe_allow_html=True)

# ── Export ────────────────────────────────────────────────────────────────────
with st.expander("Details des donnees brutes"):
    st.dataframe(agg, use_container_width=True, hide_index=True)
    csv = agg.to_csv(index=False).encode('utf-8')
    st.download_button("Exporter les CVEs (CSV)", csv, "cyberpulse_kpi6.csv", "text/csv")
    