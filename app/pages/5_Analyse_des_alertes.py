# 5_Analyse_des_alertes.py -- StatCyberMatrix i18n

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
lang = st.session_state.get("lang", "en")
inject_sidebar_css(lang)
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

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
        _empty = {"en": "Empty database.", "fr": "Base de donnees vide."}
        st.warning(_empty[lang]); st.stop()
    df_raw['semaine'] = pd.to_datetime(df_raw['semaine'])
except Exception as e:
    st.error(f"Connection error: {e}"); st.stop()

# ── HEADER ───────────────────────────────────────────────────────────────────
_title = {"en": "Threat intelligence matrix", "fr": "Threat Intelligence Matrix"}
st.markdown(f'<div class="page-title">{_title[lang]}</div>', unsafe_allow_html=True)

_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    _sync = {"en": "Sync", "fr": "Synchroniser"}
    if st.button(_sync[lang], use_container_width=True):
        force_refresh(); st.rerun()

load_ts = datetime.now().strftime('%H:%M:%S')
_alerts_w = {"en": "alerts", "fr": "alertes"}
with col_b:
    st.markdown(
        f'<div class="badge-live"><span class="dot-live"></span>'
        f'LIVE — {load_ts} — {int(df_raw["nb_alertes"].sum()):,} {_alerts_w[lang]}</div>',
        unsafe_allow_html=True,
    )

# ── FILTRES ──────────────────────────────────────────────────────────────────
_sb_title = {"en": "### Threat analysis", "fr": "### Analyse de menaces"}
_sb_window = {"en": "Observation window", "fr": "Fenetre d'observation"}
_sb_target = {"en": "Target vector", "fr": "Vecteur cible"}

with st.sidebar:
    st.markdown(_sb_title[lang])
    lookback = st.selectbox(_sb_window[lang], options=[7, 14, 30, 90], index=2)
    cutoff_date = df_raw['semaine'].max() - timedelta(days=lookback)
    df = df_raw[df_raw['semaine'] >= cutoff_date].copy()
    cats_all = sorted(df['category'].unique())
    target_cat = st.multiselect(_sb_target[lang], options=cats_all, default=cats_all)
    df = df[df['category'].isin(target_cat)]

# ── GRAPHIQUES ───────────────────────────────────────────────────────────────
_analysis = {"en": "Decision analysis and density", "fr": "Analyse decisionnelle et densite"}
st.markdown(f'<div class="section-title">{_analysis[lang]}</div>', unsafe_allow_html=True)

col_l, col_r = st.columns([1, 1])

with col_l:
    _heat = {"en": "Temporal density (Heatmap)", "fr": "Densite temporelle (Heatmap)"}
    st.markdown(f'<div class="section-title">{_heat[lang]}</div>', unsafe_allow_html=True)
    pivot_df = df.pivot_table(index='category', columns='semaine', values='nb_alertes', aggfunc='sum')
    fig_heat = px.imshow(pivot_df, color_continuous_scale=['#050a14', '#3b82f6', '#a855f7', '#00d4ff'], aspect="auto")
    fig_heat.update_xaxes(tickformat="%d/%m/%y")
    _h_date = {"en": "Date", "fr": "Date"}
    _h_cat = {"en": "Category", "fr": "Categorie"}
    _h_alerts = {"en": "Alerts", "fr": "Alertes"}
    fig_heat.update_traces(hovertemplate=f"{_h_date[lang]}: %{{x|%d/%m/%Y}}<br>{_h_cat[lang]}: %{{y}}<br>{_h_alerts[lang]}: %{{z}}<extra></extra>")
    fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,10,20,0.4)",
        font=dict(family="JetBrains Mono", size=11, color="#c8d6e5"), margin=dict(t=10, b=20, l=10, r=10))
    st.plotly_chart(fig_heat, use_container_width=True)

with col_r:
    _radar = {"en": "Threat profile (Radar)", "fr": "Profil de menace (Radar)"}
    st.markdown(f'<div class="section-title">{_radar[lang]}</div>', unsafe_allow_html=True)
    radar_data = df.groupby('category')['nb_alertes'].mean().reset_index()
    _hover = {"en": "Vector", "fr": "Vecteur"}
    _avg = {"en": "Average", "fr": "Moyenne"}
    fig_radar = go.Figure(go.Scatterpolar(
        r=radar_data['nb_alertes'], theta=radar_data['category'], fill='toself',
        line_color='#a855f7', fillcolor='rgba(168,85,247,0.15)',
        hovertemplate=f"{_hover[lang]}: %{{theta}}<br>{_avg[lang]}: %{{r:.1f}}<extra></extra>"
    ))
    fig_radar.update_layout(
        polar=dict(bgcolor="rgba(5,10,20,0.4)", radialaxis=dict(visible=True, gridcolor="rgba(0,212,255,0.08)"),
                   angularaxis=dict(gridcolor="rgba(0,212,255,0.08)")),
        height=400, margin=dict(t=30, b=20, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(family="JetBrains Mono", size=11, color="#c8d6e5"))
    st.plotly_chart(fig_radar, use_container_width=True)

# ── INSIGHTS ─────────────────────────────────────────────────────────────────
_interp = {"en": "Trend interpretation", "fr": "Interpretation des tendances"}
st.markdown(f'<div class="section-title">{_interp[lang]}</div>', unsafe_allow_html=True)

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

    # top_cat = category name (technical term, never translated)
    _ins = {
        "en": f"""<b>Pareto law:</b> The <b>{top_cat}</b> category alone concentrates <b>{top_pct}%</b> of the total flow observed over the period ({total_hits} alerts). Remediation efforts should be prioritized on this vector.
        <br><br><b>Peak analysis:</b> Maximum activity was detected the week of <b>{pic_semaine}</b> with <b>{pic_val} alerts</b>, a <b>{deviation_pic}%</b> surge compared to the usual load.""",
        "fr": f"""<b>Loi de Pareto :</b> La categorie <b>{top_cat}</b> concentre a elle seule <b>{top_pct}%</b> du flux total observe sur la periode ({total_hits} alertes). L'effort de remediation doit etre priorise sur ce vecteur.
        <br><br><b>Analyse de pic :</b> Un maximum d'activite a ete detecte la semaine du <b>{pic_semaine}</b> avec <b>{pic_val} alertes</b>, soit une hausse de <b>{deviation_pic}%</b> par rapport a la charge habituelle.""",
    }
    st.markdown(f'<div class="insight-box">{_ins[lang]}</div>', unsafe_allow_html=True)