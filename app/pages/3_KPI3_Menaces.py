"""
CyberPulse -- KPI 3
Breakdown by threat type
Source de donnees : PostgreSQL (mart_k3)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from db_connect import get_mart_k3, force_refresh

st.set_page_config(page_title="KPI 3 - Threats", layout="wide")

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp { background: #050a14 !important; }
[data-testid="stAppViewContainer"] > * { position:relative; z-index:1; }
[data-testid="stSidebar"] { z-index:2 !important; background:#0f1422!important; border-right:1px solid #1e2a42; }
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#f59e0b;background:rgba(245,158,11,.1);
border:1px solid rgba(245,158,11,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #f59e0b;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}
.insight-box{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#fcd34d;font-size:0.88rem;}
.note-box{background:rgba(100,116,139,0.07);border:1px solid rgba(100,116,139,0.2);
border-radius:8px;padding:10px 16px;margin-top:12px;color:#94a3b8;font-size:0.82rem;}
.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'IBM Plex Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.badge-err{display:inline-flex;align-items:center;gap:6px;font-family:'IBM Plex Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#ef4444;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
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


COLORS = [
    '#ef4444', '#f59e0b', '#3b82f6', '#a855f7',
    '#22c55e', '#14b8a6', '#f97316', '#ec4899', '#64748b',
]

CAT_DESC = {
    'ransomware'   : 'Software that encrypts data and demands a ransom',
    'phishing'     : "Attacks using identity spoofing to steal credentials",
    'vulnerability': 'Security flaws in software or systems (CVE)',
    'malware'      : 'Malicious software (trojans, backdoors, spyware...)',
    'apt'          : 'Advanced persistent threats, often state-sponsored',
    'ddos'         : 'Distributed denial-of-service attacks',
    'data_breach'  : 'Data leaks or theft',
    'supply_chain' : 'Attacks via third-party dependencies or suppliers',
    'general'      : 'Cyber articles without an identified threat category',
}

CAT_ORDER = [
    'ransomware', 'malware', 'vulnerability', 'phishing',
    'apt', 'data_breach', 'supply_chain', 'ddos', 'general',
]

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8'),
)

# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 3</div>', unsafe_allow_html=True)
st.markdown("### Breakdown by threat type")
st.markdown("""
<div class="desc-box">
    <b>Objective:</b> Visualise the proportion of each threat type in collected articles.<br>
    <b>Reading:</b> A dominant category indicates the most covered topic in the period.<br>
    <b>Data source:</b> PostgreSQL -- table <code>mart_k3</code> (categories computed by dbt regex).
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Chargement PostgreSQL ─────────────────────────────────────────────────────
col_refresh, col_badge, _ = st.columns([1, 2, 5])

with col_refresh:
    if st.button("Refresh", type="primary", use_container_width=True):
        force_refresh()
        st.rerun()

try:
    df_raw  = get_mart_k3()
    load_ok = True
    load_ts = datetime.now().strftime('%H:%M:%S')
except Exception as e:
    load_ok  = False
    load_err = str(e)

with col_badge:
    if load_ok:
        st.markdown(
            f'<div class="badge-live"><span class="dot-live"></span>'
            f'PostgreSQL · {load_ts}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="badge-err">✗ Erreur connexion</div>', unsafe_allow_html=True)

if not load_ok:
    st.error(f"Could not connect to PostgreSQL : {load_err}\n\nCheck that Docker is running.")
    st.stop()

if df_raw.empty:
    st.warning("mart_k3 is empty. Run `dbt run --select mart_k3`.")
    st.stop()

# ── Filtres ───────────────────────────────────────────────────────────────────
sources_dispo = sorted(df_raw['source'].dropna().unique().tolist())
sel_sources   = st.multiselect(
    "Filter by source", sources_dispo, default=sources_dispo, key="k3_src"
)

dff = df_raw[df_raw['source'].isin(sel_sources)] if sel_sources else df_raw

agg = (
    dff.groupby('category')['nb_articles']
    .sum()
    .reset_index()
    .rename(columns={'category': 'categorie'})
    .sort_values('nb_articles', ascending=False)
)
total = int(agg['nb_articles'].sum())

if agg.empty or total == 0:
    st.warning("No data for selected sources.")
    st.stop()

# ── Graphiques ────────────────────────────────────────────────────────────────
col_viz, col_ctrl = st.columns([4, 1])

with col_ctrl:
    st.markdown("<br>", unsafe_allow_html=True)
    viz = st.radio("Visualisation", ["Donut", "Treemap", "Bars"], key="k3_viz")

with col_viz:
    if viz == "Donut":
        fig = px.pie(
            agg, names='categorie', values='nb_articles',
            color_discrete_sequence=COLORS,
            hole=0.45,
            title=f"Threat breakdown -- {total:,} articles ({len(sel_sources)} sources)"
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(**PLOTLY_BASE, margin=dict(l=20, r=20, t=60, b=20), height=460)

    elif viz == "Treemap":
        fig = px.treemap(
            agg, path=['categorie'], values='nb_articles',
            color='nb_articles',
            color_continuous_scale=[[0.0, '#1e3a5f'], [0.5, '#f59e0b'], [1.0, '#ef4444']],
            title=f"Threat treemap -- {total:,} articles"
        )
        fig.update_layout(**PLOTLY_BASE, margin=dict(l=20, r=20, t=60, b=20), height=460)

    else:
        agg_sorted = agg.sort_values('nb_articles')
        fig = px.bar(
            agg_sorted, x='nb_articles', y='categorie',
            orientation='h',
            color='categorie',
            color_discrete_sequence=COLORS,
            title=f"Threats by article count -- {total:,} articles"
        )
        fig.update_layout(
            **PLOTLY_BASE,
            xaxis=dict(gridcolor='#1e2a42'),
            yaxis=dict(gridcolor='#1e2a42'),
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20),
            height=400,
        )

    st.plotly_chart(fig, use_container_width=True)

# ── Métriques rapides ─────────────────────────────────────────────────────────
top_cat     = agg.iloc[0]['categorie']
top_count   = int(agg.iloc[0]['nb_articles'])
top_pct     = round(top_count / total * 100, 1)
nb_cats     = int((agg['nb_articles'] > 0).sum())
general_n   = int(agg[agg['categorie'] == 'general']['nb_articles'].sum()) if 'general' in agg['categorie'].values else 0
general_pct = round(general_n / total * 100, 1)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total articles",     f"{total:,}")
m2.metric("Active categories", nb_cats)
m3.metric(f"Top : {top_cat}",   f"{top_pct}%", f"{top_count} articles")
m4.metric("Uncategorised",    f"{general_pct}%", f"{general_n} articles")

# ── Insights automatiques ─────────────────────────────────────────────────────
st.markdown(f"""
<div class="insight-box">
    <b>Insights:</b><br>
    Dominant threat: <b>{top_cat}</b> -- <b>{top_pct}%</b> of articles ({top_count:,}).<br>
    The <b>general</b> category ({general_pct}%) covers articles with no detected keyword.
    Enrich the regex in <code>mart_k3.sql</code> to reduce this percentage.
</div>
""", unsafe_allow_html=True)

# ── Heatmap source x catégorie ────────────────────────────────────────────────
st.markdown("---")
st.markdown("**Breakdown by source and category**")
st.markdown(
    "<div style='color:#64748b;font-size:0.82rem;margin-bottom:12px'>"
    "Number of articles per source for each threat category."
    "</div>",
    unsafe_allow_html=True
)

pivot = dff.pivot_table(
    index='source', columns='category', values='nb_articles',
    aggfunc='sum', fill_value=0
)
col_order = [c for c in CAT_ORDER if c in pivot.columns] + [c for c in pivot.columns if c not in CAT_ORDER]
pivot     = pivot[col_order]
pivot['TOTAL'] = pivot.sum(axis=1)
pivot     = pivot.sort_values('TOTAL', ascending=False)

with st.expander("View source x threat heatmap", expanded=True):
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.drop(columns=['TOTAL']).values,
        x=pivot.drop(columns=['TOTAL']).columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0,  '#0f1422'],
            [0.15, '#78350f'],
            [0.5,  '#f59e0b'],
            [1.0,  '#ef4444'],
        ],
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>Category: %{x}<br>Articles: %{z}<extra></extra>',
        text=pivot.drop(columns=['TOTAL']).values,
        texttemplate='%{text}',
        textfont=dict(size=11, color='white'),
        showscale=True,
        colorbar=dict(title='Articles', tickfont=dict(color='#94a3b8')),
    ))
    fig_heat.update_layout(
        **PLOTLY_BASE,
        xaxis=dict(title='', tickangle=-30, gridcolor='#1e2a42'),
        yaxis=dict(title='', gridcolor='#1e2a42'),
        margin=dict(l=20, r=20, t=20, b=60),
        height=max(250, 60 + len(pivot) * 38),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Tableau détail ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("**Detail by category**")

agg_display = agg.copy()
agg_display['% du total']  = (agg_display['nb_articles'] / total * 100).round(1).astype(str) + ' %'
agg_display['Description'] = agg_display['categorie'].map(CAT_DESC).fillna('--')
agg_display.columns        = ['Threat type', 'Articles', '% of total', 'Description']
st.dataframe(agg_display, use_container_width=True, hide_index=True)

# ── Note méthodologique ───────────────────────────────────────────────────────
st.markdown("""
<div class="note-box">
    <b>Method:</b> Categorisation is computed by regex in <code>mart_k3.sql</code>
    on the title and description. The CASE order determines priority
    (ransomware &gt; phishing &gt; vulnerability &gt; ... &gt; general).
</div>
""", unsafe_allow_html=True)

# ── Export CSV ────────────────────────────────────────────────────────────────
st.markdown("---")
csv = agg_display.to_csv(index=False).encode('utf-8')
st.download_button(
    "Download breakdown (CSV)",
    csv,
    file_name=f"kpi3_menaces_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)