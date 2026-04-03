"""
CyberPulse -- KPI 4
Threat mention trends over time
Source de donnees : PostgreSQL (mart_k4)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from db_connect import get_mart_k4, force_refresh

st.set_page_config(page_title="KPI 4 - Trends", layout="wide")

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}

/* FOND SEMI-TRANSPARENT : laisse passer le canvas ECG en dessous.
   NE PAS utiliser background:#050a14 !important ici — ce serait opaque
   et masquerait le canvas. On copie la technique de KPI1. */
.stApp {
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}

[data-testid="stAppViewContainer"] > * { position:relative; z-index:1; }
[data-testid="stSidebar"] { z-index:2 !important; background:#0f1422!important; border-right:1px solid #1e2a42; }
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#14b8a6;background:rgba(20,184,166,.1);
border:1px solid rgba(20,184,166,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #14b8a6;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}
.insight-box{background:rgba(20,184,166,0.07);border:1px solid rgba(20,184,166,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#5eead4;font-size:0.88rem;}
.warn-box{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);
border-radius:8px;padding:10px 16px;margin-top:10px;color:#fcd34d;font-size:0.82rem;}
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


# Palette par categorie
CAT_COLORS = {
    'ransomware'   : '#ef4444',
    'malware'      : '#f97316',
    'vulnerability': '#3b82f6',
    'phishing'     : '#f59e0b',
    'apt'          : '#a855f7',
    'data_breach'  : '#ec4899',
    'supply_chain' : '#14b8a6',
    'ddos'         : '#22c55e',
    'general'      : '#64748b',
}

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8'),
)

def _rgba(hex_color, alpha):
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f'rgba({r},{g},{b},{alpha})'

# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 4</div>', unsafe_allow_html=True)
st.markdown("### Threat mention trends over time")
st.markdown("""
<div class="desc-box">
    <b>Objective:</b> Track how mentions of a threat evolve day by day.<br>
    <b>Reading:</b> A spike indicates a major event that day. A persistent rise signals an emerging topic.<br>
    <b>Data source:</b> PostgreSQL -- table <code>mart_k4</code> (categories by dbt regex, aggregated by date).
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
    df_raw  = get_mart_k4()
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
    st.warning("mart_k4 is empty. Run `dbt run --select mart_k4`.")
    st.stop()

# ── Filtres ───────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    periode_opts = {
        "Last 7 days" : 7,
        "Last 14 days": 14,
        "Last 30 days": 30,
        "Show all"    : None,
    }
    periode_lbl = st.selectbox("Time window", list(periode_opts.keys()), key="k4_per")
    n_days = periode_opts[periode_lbl]

with col_f2:
    cats_dispo = sorted([c for c in df_raw['category'].dropna().unique() if c != 'general'])
    cats_dispo_all = cats_dispo + (['general'] if 'general' in df_raw['category'].values else [])
    menace1 = st.selectbox("Primary threat", cats_dispo, key="k4_m1")

with col_f3:
    comparer = st.checkbox("Compare with other threats", key="k4_cmp")

menaces_extra = []
if comparer:
    cats_reste = [c for c in cats_dispo_all if c != menace1]
    menaces_extra = st.multiselect(
        "Threats to compare (max 3)",
        cats_reste,
        default=cats_reste[:1] if cats_reste else [],
        max_selections=3,
        key="k4_extra",
    )

col_o1, col_o2, col_o3 = st.columns(3)
with col_o1:
    show_ma  = st.checkbox("7-day moving average", value=True, key="k4_ma")
with col_o2:
    stacked  = st.checkbox("Stacked areas (if comparing)", value=False, key="k4_stack")
with col_o3:
    excl_gen = st.checkbox("Exclude 'general'", value=True, key="k4_gen")

# ── Filtrage ──────────────────────────────────────────────────────────────────
dff = df_raw.copy()
if n_days:
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=n_days)
    dff = dff[dff['published_date'] >= cutoff]
if excl_gen:
    dff = dff[dff['category'] != 'general']

def get_serie(df, cat):
    sub = df[df['category'] == cat][['published_date', 'nb_mentions']].copy()
    sub = sub.rename(columns={'published_date': 'date'})
    sub['date'] = pd.to_datetime(sub['date']).dt.normalize()
    sub = sub.groupby('date')['nb_mentions'].sum().reset_index()
    if sub.empty:
        return sub
    idx = pd.date_range(sub['date'].min(), sub['date'].max(), freq='D')
    sub = sub.set_index('date').reindex(idx, fill_value=0).reset_index()
    sub.columns = ['date', 'mentions']
    return sub

t1 = get_serie(dff, menace1)

if t1.empty:
    st.markdown('<div class="warn-box">No data for this threat. Try another category or extend the window.</div>', unsafe_allow_html=True)
    st.stop()

# ── Graphique ─────────────────────────────────────────────────────────────────
all_menaces = [menace1] + menaces_extra
palette = ['#14b8a6','#f59e0b','#ef4444','#a855f7','#3b82f6','#22c55e','#f97316','#ec4899']
fig = go.Figure()

for idx, cat in enumerate(all_menaces):
    serie = get_serie(dff, cat) if cat != menace1 else t1
    if serie.empty:
        continue
    col_hex = CAT_COLORS.get(cat, palette[idx % len(palette)])

    if stacked and len(all_menaces) > 1:
        fig.add_trace(go.Scatter(
            x=serie['date'], y=serie['mentions'], name=cat, mode='lines',
            line=dict(color=col_hex, width=1.5),
            stackgroup='one', fillcolor=_rgba(col_hex, 0.33),
        ))
    else:
        fig.add_trace(go.Scatter(
            x=serie['date'], y=serie['mentions'], name=cat, mode='lines+markers',
            line=dict(color=col_hex, width=2.5), marker=dict(size=5),
            fill='tozeroy' if idx == 0 and len(all_menaces) == 1 else None,
            fillcolor=_rgba(col_hex, 0.08) if idx == 0 and len(all_menaces) == 1 else None,
        ))

    if show_ma and len(serie) >= 3:
        ma = serie['mentions'].rolling(window=7, min_periods=1).mean().round(1)
        fig.add_trace(go.Scatter(
            x=serie['date'], y=ma, name=f"{cat} (7d avg)", mode='lines',
            line=dict(color=col_hex, width=1.5, dash='dot'), opacity=0.6,
        ))

fig.update_layout(
    **PLOTLY_BASE,
    xaxis=dict(gridcolor='#1e2a42', title='Date'),
    yaxis=dict(gridcolor='#1e2a42', title='Mentions / jour'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02,
                bgcolor='rgba(15,20,34,0.8)', bordercolor='#1e2a42', borderwidth=1),
    hovermode='x unified', height=460,
    margin=dict(l=20, r=20, t=60, b=20),
    title=(f"Trend: '{menace1}'"
           + (f" vs {len(menaces_extra)} other(s)" if menaces_extra else "")
           + f" -- {periode_lbl.lower()}"),
)
st.plotly_chart(fig, use_container_width=True)

# ── Métriques ─────────────────────────────────────────────────────────────────
idx_max = t1['mentions'].idxmax()
total_m = int(t1['mentions'].sum())
peak_v  = int(t1.loc[idx_max, 'mentions'])
peak_d  = str(t1.loc[idx_max, 'date'])[:10]
moy     = round(t1['mentions'].mean(), 1)
last7   = int(t1.tail(7)['mentions'].sum())
prev7   = int(t1.iloc[max(0, len(t1)-14):max(0, len(t1)-7)]['mentions'].sum())
delta7  = last7 - prev7

m1c, m2c, m3c, m4c = st.columns(4)
m1c.metric("Total mentions",   f"{total_m:,}")
m2c.metric("Pic",              f"{peak_v} le {peak_d}")
m3c.metric("Moy. quotidienne", f"{moy}/j")
m4c.metric("Last 7 days",      f"{last7:,}", f"{delta7:+d} vs prev. 7d")

st.markdown(f"""
<div class="insight-box">
    <b>Insights for '{menace1}':</b><br>
    Total: <b>{total_m:,}</b> mentions. Peak: <b>{peak_d}</b> ({peak_v} mentions).
    Average: <b>{moy}</b>/day.
    {"<br>⚠️ Rising trend: +{} vs previous 7 days.".format(delta7) if delta7 > 0 else ""}
</div>
""", unsafe_allow_html=True)

# ── Tableau ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("**Summary over the period**")
recap_rows = []
for cat in all_menaces:
    serie = get_serie(dff, cat)
    if serie.empty:
        continue
    recap_rows.append({
        "Menace"        : cat,
        "Total mentions": int(serie['mentions'].sum()),
        "Pic"           : int(serie['mentions'].max()),
        "Peak day"      : str(serie.loc[serie['mentions'].idxmax(), 'date'])[:10],
        "Avg / day"     : round(serie['mentions'].mean(), 1),
        "Last 7d"       : int(serie.tail(7)['mentions'].sum()),
    })
if recap_rows:
    st.dataframe(
        pd.DataFrame(recap_rows).sort_values("Total mentions", ascending=False),
        use_container_width=True, hide_index=True,
    )

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("---")
export_df = dff[dff['category'].isin(all_menaces)].copy()
export_df['published_date'] = export_df['published_date'].dt.strftime('%Y-%m-%d')
csv = export_df.sort_values(['published_date','category']).to_csv(index=False).encode('utf-8')
st.download_button(
    "Download data (CSV)", csv,
    file_name=f"kpi4_tendances_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)