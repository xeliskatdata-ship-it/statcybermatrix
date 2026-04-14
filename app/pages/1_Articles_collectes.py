# 1_Articles_collectes.py -- StatCyberMatrix theme unifie + i18n

import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k1, get_stg_articles, force_refresh
from utils_lang import t

st.set_page_config(page_title="StatCyberMatrix - Veille", layout="wide")

from sidebar_css import inject_sidebar_css
lang = st.session_state.get("lang", "en")
inject_sidebar_css(lang)
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

# ── DATA ─────────────────────────────────────────────────────────────────────
try:
    df = get_mart_k1()
    df['published_date'] = pd.to_datetime(df['published_date'])
except Exception as e:
    st.error(f"Erreur Connexion : {e}"); st.stop()

# ── TITRE & FILTRE ───────────────────────────────────────────────────────────
_titles = {"en": "Collected articles & Emerging signals", "fr": "Articles collectes & Signaux emergents"}
st.markdown(f'<div class="page-title">{_titles[lang]}</div>', unsafe_allow_html=True)

_periods = {
    "en": ["Last 3 days", "Last 7 days", "Last 14 days", "Last 30 days"],
    "fr": ["3 derniers jours", "7 derniers jours", "14 derniers jours", "30 derniers jours"],
}
_days_vals = [3, 7, 14, 30]

with st.container():
    _, col_f2, _ = st.columns([1, 1, 1])
    with col_f2:
        _label = {"en": "Analysis period:", "fr": "Periode d'analyse :"}
        idx = st.selectbox(_label[lang], options=range(4), format_func=lambda i: _periods[lang][i], index=1)
        selected_days = _days_vals[idx]

# ── CALCULS ──────────────────────────────────────────────────────────────────
now = datetime.now()
limit_date = now - timedelta(days=selected_days)
df_filtered = df[df['published_date'] >= limit_date]

df_24h = df[df['published_date'] >= (now - timedelta(days=1))]
df_hist = df[(df['published_date'] >= limit_date) & (df['published_date'] < (now - timedelta(days=1)))]

vol_24h = df_24h.groupby('source')['nb_articles'].sum().reset_index(name='today')
vol_hist = df_hist.groupby('source')['nb_articles'].sum().reset_index(name='total_hist')
vol_hist['avg_daily'] = vol_hist['total_hist'] / (selected_days - 1) if selected_days > 1 else 1

trend_df = pd.merge(vol_24h, vol_hist, on='source', how='left').fillna(0)
trend_df['velocity_score'] = (trend_df['today'] + 1) / (trend_df['avg_daily'] + 1)

# ── RADAR VÉLOCITÉ ────────────────────────────────────────────────────────────
_radar_title = {"en": "Emergence radar (last 24h)", "fr": "Radar d'emergence (dernieres 24h)"}
st.markdown(f'<div class="section-title">{_radar_title[lang]}</div>', unsafe_allow_html=True)

_x_label = {"en": "Article volume", "fr": "Volume articles"}
_y_label = {"en": "Acceleration index", "fr": "Indice d'acceleration"}
_threshold = {"en": "Alert threshold", "fr": "Seuil d'alerte"}

fig_radar = px.scatter(
    trend_df, x="today", y="velocity_score", size="today", color="velocity_score",
    text="source", labels={"today": _x_label[lang], "velocity_score": _y_label[lang]},
    color_continuous_scale=[[0, "#0d1117"], [0.3, "#3b82f6"], [0.6, "#a855f7"], [1, "#00d4ff"]],
    height=500
)
fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#a855f7", annotation_text=_threshold[lang],
                    annotation=dict(font_color="#a855f7", font_size=11))
fig_radar.update_traces(textposition='top center', textfont=dict(size=10, color="#c8d6e5"))
fig_radar.update_layout(**PLOTLY_THEME)
st.plotly_chart(fig_radar, use_container_width=True)

if not trend_df.empty:
    top_accel = trend_df.sort_values('velocity_score', ascending=False).iloc[0]
    _insight = {
        "en": f"<b>Flow analysis:</b> Source <b>{top_accel['source']}</b> shows abnormal activity with an acceleration index of <b>{top_accel['velocity_score']:.1f}x</b>. Increased monitoring of this feed is recommended.",
        "fr": f"<b>Analyse des flux :</b> La source <b>{top_accel['source']}</b> montre une activite anormale avec un indice d'acceleration de <b>{top_accel['velocity_score']:.1f}x</b>. Une surveillance accrue de ce flux est recommandee.",
    }
    st.markdown(f'<div class="insight-box">{_insight[lang]}</div>', unsafe_allow_html=True)

# ── ÉVOLUTION TEMPORELLE ──────────────────────────────────────────────────────
_evo_title = {"en": f"Temporal evolution ({selected_days} days)", "fr": f"Suivi de l'evolution temporelle ({selected_days} jours)"}
st.markdown(f'<div class="section-title">{_evo_title[lang]}</div>', unsafe_allow_html=True)

fast_sources = trend_df.sort_values('velocity_score', ascending=False).head(5)['source'].tolist()
df_evo = df_filtered[df_filtered['source'].isin(fast_sources)].sort_values('published_date')

fig_line = px.line(
    df_evo, x='published_date', y='nb_articles', color='source', markers=True, height=400,
    color_discrete_sequence=["#00d4ff", "#a855f7", "#3b82f6", "#22c55e", "#f59e0b"]
)
fig_line.update_layout(**PLOTLY_THEME, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)))
st.plotly_chart(fig_line, use_container_width=True)

if not df_evo.empty:
    total_articles = df_filtered['nb_articles'].sum()
    _insight2 = {
        "en": f"<b>Temporal trend:</b> A total of <b>{int(total_articles)} articles</b> were analyzed over the period. Curve stability confirms the reliability of automated API collection.",
        "fr": f"<b>Tendance temporelle :</b> Un volume total de <b>{int(total_articles)} articles</b> a ete analyse sur la periode. La stabilite des courbes confirme la fiabilite des collectes automatiques.",
    }
    st.markdown(f'<div class="insight-box">{_insight2[lang]}</div>', unsafe_allow_html=True)

# ── DERNIERS FLUX ────────────────────────────────────────────────────────────
_flux_title = {"en": "Latest collected feeds", "fr": "Derniers flux collectes"}
st.markdown(f'<div class="section-title">{_flux_title[lang]}</div>', unsafe_allow_html=True)

c1, c2 = st.columns([1, 3])
with c1:
    unique_sources = sorted(trend_df['source'].unique()) if not trend_df.empty else ["No data"]
    _src_label = {"en": "Source to inspect", "fr": "Source a inspecter"}
    src_select = st.selectbox(_src_label[lang], unique_sources)
with c2:
    df_detail = get_stg_articles(limit=100)
    df_src = df_detail[df_detail["source"] == src_select].sort_values("published_date", ascending=False).head(8)

    if df_src.empty:
        _no_art = {"en": "No recent articles for this source.", "fr": "Aucun article recent pour cette source."}
        st.info(_no_art[lang])
    else:
        for _, row in df_src.iterrows():
            # source + category = noms propres / termes techniques -> jamais traduits
            st.markdown(f"""
            <div class="article-card">
                <a href="{row['url']}" target="_blank">{row['title']}</a>
                <div style="font-size:0.7rem; color:#7a9cc8; margin-top:3px">{str(row['published_date'])[:16]} · {row['category']}</div>
            </div>
            """, unsafe_allow_html=True)