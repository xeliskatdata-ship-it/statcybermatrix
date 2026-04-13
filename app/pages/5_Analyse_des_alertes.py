import sys, os
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Configuration chemins
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k5, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 5 Alertes", layout="wide")

# ── HELPER TITRE ──────────────────────────────────────────────────────────
def _section_title(text: str, size: str = "1.4rem"):
    st.markdown(
        f"<div style='text-align:center;font-family:Roboto Mono,monospace;font-size:{size};"
        "letter-spacing:.1em;text-transform:uppercase;color:#3b82f6;"
        "border-bottom:1px solid #3b82f6;padding-bottom:8px;width:fit-content;"
         f"margin:28px auto 16px'>{text}</div>",
        unsafe_allow_html=True,
    )

# ── CSS GLOBAL ET ARRIERE-PLAN ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif; color: #ffffff !important;}
.stApp { background-color: #050a14 !important; }

[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3,
.stSelectbox label, .stCheckbox p, .stTable td, .stTable th {
    color: #ffffff !important;
}

.page-title {
    text-align: center; font-size: 2.8rem; font-weight: 700; color: #3b82f6;
    margin-bottom: 20px; text-shadow: 0 0 15px rgba(59,130,246,0.5);
}

.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

.insight-box {
    background: rgba(10, 20, 40, 0.8);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 8px; padding: 25px; margin: 15px auto;
    backdrop-filter: blur(10px); max-width: 95%;
}

.alert-highlight {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid #3b82f6;
    border-radius: 5px; padding: 15px; margin-top: 15px;
    font-family: 'Roboto Mono', monospace;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  function startCodeRain(){
    var old=p.getElementById('sentinel-rain-bg-k5'); if(old)old.parentNode.removeChild(old);
    var cv=p.createElement('canvas'); cv.id='sentinel-rain-bg-k5';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.15;';
    p.body.appendChild(cv);
    var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
    var codeSymbols = "01ABCDEFSRATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH".split("");
    var fontSize = 14; var columns = W / fontSize; var drops = [];
    for (var i = 0; i < columns; i++) { drops[i] = Math.random() * (H / fontSize); }
    function draw(){
      if(!p.getElementById('sentinel-rain-bg-k5'))return;
      ctx.fillStyle = 'rgba(5, 10, 20, 0.1)'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = '#3b82f6'; ctx.font = fontSize + 'px Roboto Mono';
      for (var i = 0; i < drops.length; i++) {
        var text = codeSymbols[Math.floor(Math.random() * codeSymbols.length)];
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

# ── PALETTE ET CONFIG GRAPHIQUES ──────────────────────────────────────────────
PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(5,10,20,0.6)',
    font=dict(family='Roboto', color='#94a3b8'),
)

# ── LOGIQUE DONNÉES ──────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k5()
    if df_raw is None or df_raw.empty:
        st.warning("Base de données vide. Verifiez la table mart_k5.")
        st.stop()
    df_raw['semaine'] = pd.to_datetime(df_raw['semaine'])
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()

# ── EN-TETE ET REFRESH ────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Threat Intelligence Matrix</div>', unsafe_allow_html=True)

_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Synchroniser", use_container_width=True):
        force_refresh()
        st.rerun()

load_ts = datetime.now().strftime('%H:%M:%S')
with col_b:
    st.markdown(
        f'<div class="badge-live"><span class="dot-live"></span>'
        f'LIVE - MaJ {load_ts} - {int(df_raw["nb_alertes"].sum()):,} alertes</div>',
        unsafe_allow_html=True,
    )

# ── FILTRES SIDEBAR ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Filtres Analytiques")
    lookback = st.select_slider("Fenetre temporelle (jours)", options=[7, 14, 30, 90], value=30)
    cutoff_date = df_raw['semaine'].max() - timedelta(days=lookback)
    df = df_raw[df_raw['semaine'] >= cutoff_date].copy()

    st.markdown("---")
    cats_all = sorted(df['category'].unique())
    target_cat = st.multiselect("Vecteurs de menace", options=cats_all, default=cats_all)
    df = df[df['category'].isin(target_cat)]

# ── METRIQUES CARDS ───────────────────────────────────────────────────────────
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
    backdrop-filter:blur(8px);
}}
.card::before {{ content:''; position:absolute; top:0; left:0; width:100%; height:3px; border-radius:10px 10px 0 0; }}
.card:nth-child(1)::before {{ background:#3b82f6; }}
.card:nth-child(2)::before {{ background:#14b8a6; }}
.card:nth-child(3)::before {{ background:{v_color}; }}
.card:nth-child(4)::before {{ background:#f59e0b; }}
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
    <div class="sub" style="color:#f59e0b">{nb_vecteurs} types</div>
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

# ── GRAPHIQUES AVANCÉS ────────────────────────────────────────────────────────
_section_title("Analyse Décisionnelle et Densité")

col_l, col_r = st.columns([1, 1])

with col_l:
    # ── HEATMAP (DENSITÉ TEMPORELLE CORRECTION ABSSCISSES ET HOVER) ──────────
    st.markdown("<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:12px'>Densité Temporelle (Heatmap)</div>", unsafe_allow_html=True)
    
    # Pivotage des données pour la heatmap
    pivot_df = df.pivot_table(index='category', columns='semaine', values='nb_alertes', aggfunc='sum')
    
    # Création Heatmap
    # Renommage de 'color' en 'Nombre d'alertes' et formatage date dans hover_data
    fig_heat = px.imshow(pivot_df, 
                         color_continuous_scale='Blues', 
                         aspect="auto",
                         labels=dict(color="Nombre d'alertes"))

    # Correction formatage axe X (Semaine) pour lisibilité (jj/mm/aa sur ligne 1, heure ligne 2)
    # Et formatage de la date dans la bulle d'aide
    fig_heat.update_xaxes(tickformat="%d/%m/%y\n%H:%M")
    
    fig_heat.update_traces(hovertemplate="Semaine: %{x|%d/%m/%Y %H:%M}<br>Catégorie: %{y}<br>Nombre d'alertes: %{z}<extra></extra>")

    fig_heat.update_layout(**PLOTLY_BASE, margin=dict(t=10, b=20, l=10, r=10))
    st.plotly_chart(fig_heat, use_container_width=True)

with col_r:
    # ── RADAR CHART (PROFIL DE MENACE CORRECTION HOVER) ─────────────────────
    st.markdown("<div style='text-align:center;color:#94a3b8;font-size:1.1rem;margin-bottom:12px'>Profil de Menace (Radar)</div>", unsafe_allow_html=True)
    
    # Préparation données moyenne par catégorie sur la période
    radar_data = df.groupby('category')['nb_alertes'].mean().reset_index()
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_data['nb_alertes'],
        theta=radar_data['category'],
        fill='toself',
        line_color='#3b82f6',
        # Renommage explicite de 'theta' en Vecteur et 'r' en Moyenne dans la bulle
        hovertemplate="Vecteur de menace: %{theta}<br>Moyenne d'alertes hebdo: %{r:.1f}<extra></extra>"
    ))

    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(15,20,34,0.6)",
            radialaxis=dict(visible=True, gridcolor="#1e2a42", tickfont=dict(color="#cbd5e1")),
            angularaxis=dict(gridcolor="#1e2a42", tickfont=dict(color="#cbd5e1"))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Roboto', color='#94a3b8'),
        margin=dict(t=30, b=20, l=10, r=10),
        height=400
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── INSIGHTS DECISIONNELS ─────────────────────────────────────────────────────
_section_title("Interprétation des Tendances")

if total_hits > 0 and not weekly_stats.empty:
    # Calculs Pareto
    ranking = df.groupby('category', as_index=False)['nb_alertes'].sum().sort_values('nb_alertes', ascending=False)
    top_cat = ranking.iloc[0]['category']
    top_val = int(ranking.iloc[0]['nb_alertes'])
    top_pct = round(top_val / total_hits * 100, 1)
    
    ranking['cum_pct'] = ranking['nb_alertes'].cumsum() / total_hits * 100
    nb_cat_80 = len(ranking[ranking['cum_pct'] <= 85]) + 1
    
    # Calculs Pic
    pic_semaine = weekly_stats.idxmax().strftime('%d/%m/%Y')
    pic_val = int(weekly_stats.max())
    deviation_pic = round(((pic_val - avg_hits) / avg_hits * 100), 1) if avg_hits > 0 else 0

    st.markdown(f"""
    <div class="insight-box">
        <div style="font-family:'Roboto Mono'; color:#3b82f6; margin-bottom:15px; font-weight:700;">
            > ANALYSE DECISIONNELLE DU FLUX CTI
        </div>
        Loi de Pareto : Seules {nb_cat_80} catégories sur {nb_vecteurs} représentent plus de 80% du volume total ({total_hits} alertes). 
        L'effort de remédiation doit se concentrer prioritairement sur la catégorie {top_cat} ({top_pct}% du flux).
        
        <div class="alert-highlight">
        Analyse de Pic : Un maximum d'activité a été détecté la semaine du {pic_semaine} avec {pic_val} alertes, 
        soit une hausse de {deviation_pic}% par rapport à la charge habituelle sur la période observée.
        </div>
        
        Stabilité du Signal : Avec une volatilité hebdo de {volatility} ({'Signal stable' if is_stable else 'Signal bruyant/instable'}), 
        le consultant doit {'maintenir les seuils actuels de détection' if is_stable else 'revoir les politiques de corrélation pour réduire la fatigue des analystes SOC'}.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")