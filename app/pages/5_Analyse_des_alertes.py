# 5_Analyse_des_alertes.py -- StatCyberMatrix theme unifie

import sys, os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k5, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 5 Alertes", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

# Badge live CSS
st.markdown("""
<style>
.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'JetBrains Mono',monospace;
font-size:0.65rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.06);border:1px solid rgba(34,197,94,.15);
border-radius:20px;padding:4px 12px;}
.dot-live{width:6px;height:6px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k5()
    if df_raw is None or df_raw.empty:
        st.warning("Base de données vide."); st.stop()
    df_raw['semaine'] = pd.to_datetime(df_raw['semaine'])
except Exception as e:
    st.error(f"Erreur de connexion : {e}"); st.stop()

# ── HEADER ───────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Threat Intelligence Matrix</div>', unsafe_allow_html=True)

_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Synchroniser", use_container_width=True):
        force_refresh(); st.rerun()

load_ts = datetime.now().strftime('%H:%M:%S')
with col_b:
    st.markdown(
        f'<div class="badge-live"><span class="dot-live"></span>'
        f'LIVE — MaJ {load_ts} — {int(df_raw["nb_alertes"].sum()):,} alertes</div>',
        unsafe_allow_html=True,
    )

# ── FILTRES ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Analyse de Menaces")
    lookback = st.selectbox("Fenetre d'observation", options=[7, 14, 30, 90], index=2)
    cutoff_date = df_raw['semaine'].max() - timedelta(days=lookback)
    df = df_raw[df_raw['semaine'] >= cutoff_date].copy()
    cats_all = sorted(df['category'].unique())
    target_cat = st.multiselect("Vecteur cible", options=cats_all, default=cats_all)
    df = df[df['category'].isin(target_cat)]

# ── GRAPHIQUES ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Analyse décisionnelle et densité</div>', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1])

with col_l:
    st.markdown('<div class="section-title">Densité temporelle (Heatmap)</div>', unsafe_allow_html=True)
    pivot_df = df.pivot_table(index='category', columns='semaine', values='nb_alertes', aggfunc='sum')
    fig_heat = px.imshow(pivot_df, color_continuous_scale=['#050a14', '#3b82f6', '#a855f7', '#00d4ff'], aspect="auto")
    fig_heat.update_xaxes(tickformat="%d/%m/%y")
    fig_heat.update_traces(hovertemplate="Date: %{x|%d/%m/%Y}<br>Catégorie: %{y}<br>Alertes: %{z}<extra></extra>")
    fig_heat.update_layout(margin=dict(t=10, b=20, l=10, r=10), **PLOTLY_THEME)
    st.plotly_chart(fig_heat, use_container_width=True)

with col_r:
    st.markdown('<div class="section-title">Profil de menace (Radar)</div>', unsafe_allow_html=True)
    radar_data = df.groupby('category')['nb_alertes'].mean().reset_index()
    fig_radar = go.Figure(go.Scatterpolar(
        r=radar_data['nb_alertes'], theta=radar_data['category'], fill='toself',
        line_color='#a855f7', fillcolor='rgba(168,85,247,0.15)',
        hovertemplate="Vecteur: %{theta}<br>Moyenne: %{r:.1f}<extra></extra>"
    ))
    fig_radar.update_layout(
        polar=dict(bgcolor="rgba(5,10,20,0.4)", radialaxis=dict(visible=True, gridcolor="rgba(0,212,255,0.08)"),
                   angularaxis=dict(gridcolor="rgba(0,212,255,0.08)")),
        height=400, margin=dict(t=30, b=20, l=10, r=10), **PLOTLY_THEME
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# ── INSIGHTS ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Interprétation des tendances</div>', unsafe_allow_html=True)

if not df.empty:
    total_hits = int(df['nb_alertes'].sum())
    weekly_stats = df.groupby('semaine')['nb_alertes'].sum()
    avg_hits = weekly_stats.mean()
    ranking = df.groupby('category')['nb_alertes'].sum().sort_values(ascending=False)
    top_cat = ranking.index[0]
    top_pct = round(ranking.iloc[0] / total_hits * 100, 1)

    pic_semaine = weekly_stats.idxmax().strftime('%d/%m/%Y')
    pic_val = int(weekly_stats.max())
    deviation_pic = round(((pic_val - avg_hits) / avg_hits * 100), 1) if avg_hits > 0 else 0

    st.markdown(f"""
    <div class="insight-box">
        <b>Loi de Pareto :</b> La catégorie <b>{top_cat}</b> concentre à elle seule <b>{top_pct}%</b> du flux total
        observé sur la période ({total_hits} alertes). L'effort de remédiation doit être priorisé sur ce vecteur.
        <br><br>
        <b>Analyse de Pic :</b> Un maximum d'activité a été détecté la semaine du <b>{pic_semaine}</b> avec <b>{pic_val} alertes</b>,
        soit une hausse de <b>{deviation_pic}%</b> par rapport à la charge habituelle.
    </div>
    """, unsafe_allow_html=True)