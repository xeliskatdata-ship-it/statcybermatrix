"""
StatCyberMatrix -- KPI 3
Analyse de la répartition des menaces
Design : fond bokeh, animation ECG, cartes animées (style KPI1)
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

# ── Helper : titre de section centré (évite la duplication HTML) ──────────────
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

.insight-box{background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#93c5fd;font-size:0.88rem;backdrop-filter:blur(8px);}

.section-title-center{font-family:'Roboto Mono',monospace;font-size:0.7rem;letter-spacing:.18em;
text-transform:uppercase;color:#64748b;border-bottom:1px solid #3b82f6;
padding-bottom:6px;margin:24px auto 16px;width:fit-content;display:block;text-align:center;}
</style>
""", unsafe_allow_html=True)

# ── Fond animé ECG (identique KPI1) ──────────────────────────────────────────
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
    st.warning("mart_k3 est vide. Lance `dbt run` depuis le dossier dbt/.")
    st.stop()

# ── Filtres sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtres")
    sources_all = sorted(df_raw['source'].dropna().unique().tolist())
    sel_sources = st.multiselect("Sources de données", sources_all, default=sources_all)

# Filtre appliqué — fallback sur tout si rien sélectionné
df = df_raw[df_raw['source'].isin(sel_sources)] if sel_sources else df_raw

# Agrégation catégorie → volume, tri descendant
agg = (
    df.groupby('category', as_index=False)['nb_articles']
    .sum()
    .sort_values('nb_articles', ascending=False)
)
total = int(agg['nb_articles'].sum())

# ── Métriques clés ────────────────────────────────────────────────────────────
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
    <div class="lbl">Volume Total</div>
    <div class="sub" style="color:#3b82f6">Articles analysés</div>
  </div>
  <div class="card">
    <div class="val" style="font-size:1.8rem">{top_cat.upper()}</div>
    <div class="lbl">Vecteur Critique</div>
    <div class="sub" style="color:#ef4444">{top_pct}% de la volumétrie</div>
  </div>
  <div class="card">
    <div class="val" id="v3">0</div>
    <div class="lbl">Catégories actives</div>
    <div class="sub" style="color:#f59e0b">Segments détectés</div>
  </div>
  <div class="card">
    <div class="val">LIVE</div>
    <div class="lbl">Status</div>
    <div class="sub" style="color:#22c55e">MàJ : {load_ts}</div>
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
animCount('v1', {total}, 1200, false);
animCount('v3', {nb_cats}, 800, false);
</script>
""", height=160)

# ── Graphique principal + config ──────────────────────────────────────────────
_section_title("Répartition des vecteurs de menace")

col_viz, col_side = st.columns([3, 1])

with col_side:
    _section_title("Configuration", size="0.7rem")
    viz_type = st.radio("Mode d'affichage", ["Radar Chart", "Donut Chart", "Bar Chart"])

    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse automatique :</b><br>
        La menace <b>{top_cat}</b> représente <b>{top_pct}%</b> du volume total
        ({top_val:,} articles sur {total:,}).
        Ce vecteur nécessite une surveillance accrue des logs SIEM correspondants.
    </div>
    """, unsafe_allow_html=True)

with col_viz:
    if viz_type == "Radar Chart":
        fig = go.Figure(data=go.Scatterpolar(
            r=agg['nb_articles'],
            theta=agg['category'].str.upper(),
            fill='toself',
            line_color='#3b82f6',
            fillcolor='rgba(59, 130, 246, 0.2)',
        ))
        fig.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, gridcolor='#1e2a42', color='#94a3b8'),
                angularaxis=dict(gridcolor='#1e2a42', color='#94a3b8'),
            ),
            **PLOTLY_BASE, height=450,
        )
    elif viz_type == "Donut Chart":
        fig = px.pie(
            agg, names='category', values='nb_articles', hole=0.6,
            color='category', color_discrete_map=COLORS_MAP,
        )
        fig.update_traces(textposition='outside', textinfo='label+percent')
        fig.update_layout(**PLOTLY_BASE, height=450, showlegend=False)
    else:
        # Bar horizontal — tri ascendant une seule fois
        agg_bar = agg.sort_values('nb_articles')
        fig = go.Figure(go.Bar(
            x=agg_bar['nb_articles'],
            y=agg_bar['category'],
            orientation='h',
            marker_color=[COLORS_MAP.get(c, '#3b82f6') for c in agg_bar['category']],
            hovertemplate='<b>%{y}</b><br>%{x} articles<extra></extra>',
        ))
        fig.update_layout(
            **PLOTLY_BASE, height=450,
            xaxis=dict(gridcolor='#1e2a42'),
            yaxis=dict(gridcolor='#1e2a42'),
        )

    st.plotly_chart(fig, use_container_width=True)

# ── Heatmap Sources × Catégories ─────────────────────────────────────────────
_section_title("Matrice d'occurrence par source")
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:20px'>"
    "Croisement source × catégorie. Plus la couleur est intense, plus le volume est élevé."
    "</div>", unsafe_allow_html=True,
)

# Pivot avec tri par volume total descendant
pivot = df.pivot_table(index='source', columns='category', values='nb_articles', aggfunc='sum', fill_value=0)
pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

if not pivot.empty:
    fig_heat = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[[0.0, '#0a1628'], [0.15, '#1e3a5f'], [0.4, '#1d4ed8'], [0.7, '#3b82f6'], [1.0, '#93c5fd']],
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>%{x}<br>%{z} articles<extra></extra>',
        showscale=True,
        colorbar=dict(title='Articles', tickfont=dict(color='#94a3b8', size=14)),
    ))
    fig_heat.update_layout(
        **PLOTLY_BASE,
        xaxis=dict(gridcolor='#1e2a42', tickangle=-30, tickfont=dict(size=14, color='#94a3b8')),
        yaxis=dict(gridcolor='#1e2a42', tickfont=dict(size=14, color='#cbd5e1')),
        margin=dict(l=20, r=20, t=10, b=40),
        height=max(300, 50 + len(pivot) * 35),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Interprétation & Insights ─────────────────────────────────────────────────
if total > 0:
    second_cat = agg.iloc[1]['category'] if len(agg) > 1 else "—"
    second_val = int(agg.iloc[1]['nb_articles']) if len(agg) > 1 else 0
    second_pct = round(second_val / total * 100, 1) if total > 0 else 0
    general_row = agg[agg['category'] == 'general']
    general_pct = round(int(general_row['nb_articles'].iloc[0]) / total * 100, 1) if not general_row.empty else 0

    # Concentration top-2 : si > 50% du volume, signal de sur-représentation
    top2_pct = round(top_pct + second_pct, 1)

    st.markdown(f"""
    <div class="insight-box">
        <b>Interprétation & Insights</b><br><br>
        • <b>Concentration :</b> les deux premiers vecteurs (<b>{top_cat}</b> + <b>{second_cat}</b>)
          cumulent <b>{top2_pct}%</b> du corpus.
          {'Sur-représentation — vérifier si les sources ne sont pas biaisées vers ces thèmes.' if top2_pct > 55 else 'Répartition équilibrée.'}<br>
        • <b>Bruit :</b> {general_pct}% d'articles « general » non catégorisés.
          {'Au-delà de 15 %, enrichir les règles de classification (keywords / spaCy).' if general_pct > 15 else 'Taux acceptable.'}<br>
        • <b>Action :</b> croiser cette répartition avec les alertes SIEM du SOC
          pour valider que la couverture médiatique reflète bien l'activité réelle des menaces.
    </div>
    """, unsafe_allow_html=True)

# ── Détail données ────────────────────────────────────────────────────────────
with st.expander("Détails des données brutes"):
    agg_display = agg.copy()
    agg_display['proportion'] = (agg_display['nb_articles'] / total * 100).round(1).astype(str) + '%'
    agg_display['description'] = agg_display['category'].map(CAT_DESC).fillna('N/A')
    st.dataframe(agg_display, use_container_width=True, hide_index=True)

    csv = agg_display.to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Exporter en CSV", csv, "StatCyberMatrix_kpi3.csv", "text/csv")