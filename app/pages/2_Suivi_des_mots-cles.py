# 2_kpi2_Mots_cles.py -- Version Optimisée : Treemap Riche et Hover Nettoyé

import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

# Import des fonctions de données
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k2, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 2 - Threat Keywords", layout="wide")

# ── CSS GLOBAL (Centrage et Cartes Articles) ──────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&family=Roboto+Mono:wght@400;700&display=swap');
.stApp { background-color: #050a14 !important; color: #94a3b8; }
.page-title { text-align:center; font-size:2.8rem; font-weight:700; color:#a855f7; margin-bottom:20px; line-height:1.2; }
.section-header-centered {
    text-align:center; font-family:'Roboto Mono',monospace; font-size:1.2rem;
    letter-spacing:.1em; text-transform:uppercase; color:#a855f7;
    border-bottom:1px solid rgba(168,85,247,0.3); width:fit-content;
    margin:40px auto 20px; padding-bottom:8px;
}
.metric-container { background: rgba(15,20,34,0.6); border: 1px solid rgba(168,85,247,0.2); border-radius: 8px; padding: 20px; text-align: center; backdrop-filter: blur(10px); }
.metric-label { font-size: 0.8rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 5px; }
.metric-value { font-family: 'Roboto Mono'; font-size: 2.2rem; font-weight: 700; color: #e2e8f0; }
.article-card { background: rgba(15,20,34,0.8); border: 1px solid #1e2a42; border-radius: 6px; padding: 12px 16px; margin-bottom: 8px; backdrop-filter: blur(6px); transition: 0.2s; }
.article-card:hover { border-color: #a855f7; background: rgba(20,28,48,0.9); }
.article-link { color: #e2e8f0; text-decoration: none; font-size: 0.95rem; font-weight: 500; }
.article-meta { margin-top: 6px; font-size: 0.75rem; color: #64748b; font-family: 'Roboto Mono'; }
</style>
""", unsafe_allow_html=True)

# --- NOUVEAU FOND ANIMÉ : Sentinel Code Rain (Remplace l'ECG) ---
components.html("""
<script>
(function() {
  var p = window.parent.document, w = window.parent;
  
  // Fonction pour démarrer la pluie de code
  function startCodeRain(){
    // Nettoyage de l'ancienne animation si elle existe
    var old=p.getElementById('sentinel-rain-bg'); if(old)old.parentNode.removeChild(old);
    
    // Création du Canvas
    var cv=p.createElement('canvas'); cv.id='sentinel-rain-bg';
    cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none; opacity: 0.12;'; // Opacité très faible
    p.body.appendChild(cv);
    
    var ctx=cv.getContext('2d'), W=cv.width=w.innerWidth, H=cv.height=w.innerHeight;
    
    // Config Cyber-Rain (Hexa, Binary, Threat terms)
    var codeSymbols = "01ABCDEF💀RATCVEAPTIPMALWARERANSOMWAREINFOCREDENTIALSBREACH";
    codeSymbols = codeSymbols.split("");
    
    var fontSize = 14;
    var columns = W / fontSize;
    var drops = [];
    
    // Initialisation des colonnes (position Y aléatoire)
    for (var x = 0; x < columns; x++) {{ drops[x] = Math.random() * (H / fontSize); }}
    
    var alive=true;
    
    // Fonction de dessin récursive
    function draw(){
      if(!p.getElementById('sentinel-rain-bg')||!alive)return;
      
      // Fond semi-transparent pour l'effet de traînée
      ctx.fillStyle = 'rgba(5, 10, 20, 0.05)';
      ctx.fillRect(0, 0, W, H);
      
      // Style du code défilant (Teinte violette subtile)
      ctx.fillStyle = '#a855f7'; 
      ctx.font = fontSize + 'px Roboto Mono, monospace';
      
      for (var i = 0; i < drops.length; i++) {{
        var text = codeSymbols[Math.floor(Math.random() * codeSymbols.length)];
        
        // On dessine le symbole
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        
        // On fait descendre la goutte
        drops[i]++;
        
        // Si elle touche le bas, on la remet en haut aléatoirement
        if (drops[i] * fontSize > H && Math.random() > 0.975) {{
          drops[i] = 0;
        }
      }
      requestAnimationFrame(draw);
    }
    
    draw(); 
    w.addEventListener('resize', function(){W=cv.width=w.innerWidth; H=cv.height=w.innerHeight;});
    return function(){alive=false;};
  }
  
  var stop = startCodeRain();
})();
</script>
""", height=0)ss

# ── DATA PROCESSING ──────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k2()
    v3 = df_raw[df_raw['period_days'] == 3].copy()
    v15 = df_raw[df_raw['period_days'] == 15][['keyword', 'occurrences']].rename(columns={'occurrences':'occ_15j'})
    drift_df = pd.merge(v3, v15, on='keyword', how='left').fillna(0)
    drift_df['acceleration'] = (drift_df['occurrences'] + 1) / ((drift_df['occ_15j'] / 5) + 1)
    if 'category' not in drift_df.columns:
        drift_df['category'] = 'Threats'
except Exception as e:
    st.error(f"Erreur data : {e}"); st.stop()

# ── EN-TÊTE CENTRÉ ────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Threat Keywords Intelligence</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-container"><div class="metric-label">Mots-clés Actifs</div><div class="metric-value">{len(drift_df)}</div></div>', unsafe_allow_html=True)
with col2:
    top_v = drift_df.sort_values('occurrences', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
    st.markdown(f'<div class="metric-container"><div class="metric-label">Top Volume</div><div class="metric-value" style="color:#a855f7">{top_v}</div></div>', unsafe_allow_html=True)
with col3:
    top_a = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
    st.markdown(f'<div class="metric-container"><div class="metric-label">Top Vélocité</div><div class="metric-value" style="color:#22c55e">{top_a}</div></div>', unsafe_allow_html=True)
with col4:
    if st.button("⟳ Refresh Data", use_container_width=True):
        force_refresh(); st.rerun()

# ── TREEMAP RICHE & CENTRÉ ────────────────────────────────────────────────────
st.markdown('<div class="section-header-centered">Analyse Hiérarchique</div>', unsafe_allow_html=True)

_, f_col, _ = st.columns([1, 2, 1])
with f_col:
    min_accel = st.slider("Seuil d'émergence (Indice d'accélération)", 0.5, 3.0, 1.0, step=0.1)

df_filtered = drift_df[drift_df['acceleration'] >= min_accel]

# On crée une colonne de texte personnalisée pour l'affichage statique dans les cases
df_filtered['display_text'] = df_filtered.apply(
    lambda x: f"<b>{x['keyword']}</b><br>{int(x['occurrences'])} articles<br>{x['acceleration']:.2f}x", axis=1
)

fig_tree = px.treemap(
    df_filtered,
    path=[px.Constant("Global Overview"), 'category', 'keyword'],
    values='occurrences',
    color='acceleration',
    color_continuous_scale='Purples',
    range_color=[0.5, 2.5],
    custom_data=['keyword', 'occurrences', 'acceleration']
)

# Configuration pour remplir le vide : on affiche le label + la valeur
fig_tree.update_traces(
    textinfo="label+value",
    hovertemplate="<b>Menace : %{customdata[0]}</b><br>Volume : %{customdata[1]} articles<br>Accélération : %{customdata[2]:.2f}x<extra></extra>",
    textfont=dict(size=14, family="Roboto Mono")
)

fig_tree.update_layout(margin=dict(t=0, b=0, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig_tree, use_container_width=True)

# ── GRAPHIQUE FIABILITÉ DU SIGNAL (HOVER NETTOYÉ) ──────────────────────────────
st.markdown('<div class="section-header-centered">Fiabilité du Signal</div>', unsafe_allow_html=True)

df_snr = df_filtered.nlargest(15, 'occurrences').sort_values('source_count')
fig_snr = go.Figure(go.Bar(
    y=df_snr['keyword'], x=df_snr['source_count'],
    orientation='h',
    marker=dict(color='#a855f7', line=dict(color='#f0abfc', width=1)),
    hovertemplate="<b>%{y}</b><br>Sources uniques : %{x}<extra></extra>"
))

fig_snr.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(15,20,34,0.4)", 
    height=450,
    margin=dict(t=20, b=20),
    xaxis=dict(title="Nombre de sources distinctes", gridcolor="rgba(255,255,255,0.05)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    font=dict(family="Roboto Mono", color="#94a3b8")
)
st.plotly_chart(fig_snr, use_container_width=True)

# ── DEEP DIVE CENTRÉ ──────────────────────────────────────────────────────────
st.markdown('<div class="section-header-centered">🔍 Deep Dive : Articles Relatés</div>', unsafe_allow_html=True)

_, d_col, _ = st.columns([1, 2, 1])
with d_col:
    selected_kw = st.selectbox("Sélectionner une menace pour extraire les articles", ["-- Choisir un mot-clé --"] + sorted(list(df_filtered['keyword'])))

if selected_kw != "-- Choisir un mot-clé --":
    try:
        all_articles = get_stg_articles(limit=2000)
        mask = all_articles['title'].str.contains(selected_kw, case=False, na=False)
        relevant = all_articles[mask].sort_values('published_date', ascending=False).head(10)
        
        if not relevant.empty:
            for _, row in relevant.iterrows():
                st.markdown(f"""
                <div class="article-card">
                    <div><a href="{row['url']}" target="_blank" class="article-link">{row['title']}</a></div>
                    <div class="article-meta">
                        {str(row['published_date'])[:10]} &nbsp;·&nbsp; 
                        <span style="background:rgba(168,85,247,0.15); color:#d8b4fe; border-radius:4px; padding:1px 8px;">{row['source']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Aucun article trouvé pour '{selected_kw}'.")
    except Exception as e:
        st.error(f"Erreur extraction : {e}")