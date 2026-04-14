# 4_Analyse_des_tendances.py -- StatCyberMatrix i18n

import sys, os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k4, get_stg_articles

st.set_page_config(page_title="StatCyberMatrix - KPI 4 Tendances", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
lang = st.session_state.get("lang", "en")
inject_sidebar_css(lang)
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

st.markdown("""
<style>
.alert-highlight {
    background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.4);
    border-radius: 6px; padding: 14px; margin-top: 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #c8d6e5;
}
.custom-table { width:100%; border-collapse:collapse; margin:16px 0; font-family:'JetBrains Mono',monospace; background:rgba(10,22,40,0.6); border-radius:8px; overflow:hidden; border:1px solid rgba(0,212,255,0.1); }
.custom-table th { background:rgba(0,212,255,0.06); color:#00d4ff; text-align:left; padding:10px 14px; border-bottom:1px solid rgba(0,212,255,0.15); text-transform:uppercase; letter-spacing:1px; font-size:0.72rem; }
.custom-table td { padding:10px 14px; border-bottom:1px solid rgba(0,212,255,0.04); color:#c8d6e5; font-size:0.78rem; }
.status-crit { color:#ef4444; font-weight:600; }
.status-warn { color:#f59e0b; }
.status-ok { color:#22c55e; }
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
try:
    df_mart = get_mart_k4()
    if not df_mart.empty:
        df_mart['published_date'] = pd.to_datetime(df_mart['published_date']).dt.normalize()
except Exception as e:
    st.error(f"Technical error: {e}"); st.stop()

_sb_title = {"en": "### Threat analysis", "fr": "### Analyse de menaces"}
_sb_window = {"en": "Observation window", "fr": "Fenetre d'observation"}
_sb_periods = {"en": ["Last 7 days", "Last 14 days", "Last 30 days"], "fr": ["7 derniers jours", "14 derniers jours", "30 derniers jours"]}
_sb_target = {"en": "Target vector", "fr": "Vecteur cible"}
_sb_all = {"en": "All", "fr": "Tout"}

with st.sidebar:
    st.markdown(_sb_title[lang])
    idx = st.selectbox(_sb_window[lang], options=range(3), format_func=lambda i: _sb_periods[lang][i], index=1)
    nb_jours = [7, 14, 30][idx]
    cats_brutes = sorted(df_mart['category'].unique().tolist()) if not df_mart.empty else []
    cats_dispo = [_sb_all[lang]] + cats_brutes
    target = st.selectbox(_sb_target[lang], cats_dispo)

is_all = target in (_sb_all["en"], _sb_all["fr"])

if not df_mart.empty:
    date_limite = df_mart['published_date'].max() - timedelta(days=nb_jours)
    df_filtered = df_mart[df_mart['published_date'] >= date_limite].copy()

    _page_title = {"en": "CTI trend analysis", "fr": "Analyse des tendances CTI"}
    st.markdown(f'<div class="page-title">{_page_title[lang]}</div>', unsafe_allow_html=True)

    _zscore_title = {"en": f"Acceleration index (Z-Score) — {target}", "fr": f"Indice d'acceleration (Z-Score) — {target}"}
    st.markdown(f'<div class="section-title">{_zscore_title[lang]}</div>', unsafe_allow_html=True)

    if is_all:
        data_trend = df_filtered.groupby('published_date')['nb_mentions'].sum().reset_index()
    else:
        data_trend = df_filtered[df_filtered['category'] == target].groupby('published_date')['nb_mentions'].sum().reset_index()

    if not data_trend.empty:
        mean_val = data_trend['nb_mentions'].mean()
        std_val = data_trend['nb_mentions'].std()
        data_trend['z_score'] = (data_trend['nb_mentions'] - mean_val) / std_val if std_val > 0 else 0

        top_emergence = data_trend.sort_values('z_score', ascending=False).iloc[0]
        raw_date_pic = top_emergence['published_date']
        date_pic_str = raw_date_pic.strftime('%d/%m/%Y')
        vol_pic = int(top_emergence['nb_mentions'])
        bond_percent = ((vol_pic - mean_val) / mean_val * 100) if mean_val > 0 else 0

        _anomaly = {"en": "Anomaly threshold", "fr": "Seuil anomalie"}
        fig = px.scatter(data_trend, x='nb_mentions', y='z_score', size='nb_mentions', color='z_score',
            text=data_trend['published_date'].dt.strftime('%d/%m'),
            color_continuous_scale=['#050a14', '#a855f7', '#00d4ff'], height=450)
        fig.add_hline(y=2.0, line_dash="dash", line_color="#ef4444",
            annotation_text=_anomaly[lang], annotation=dict(font_color="#ef4444", font_size=10))
        fig.update_traces(textfont=dict(size=10, color="#c8d6e5"))
        fig.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig, use_container_width=True)

        status = "CRITICAL" if top_emergence['z_score'] > 2 else "STABLE"
        color_status = "#ef4444" if top_emergence['z_score'] > 2 else "#22c55e"

        if lang == "en":
            mentions_w = "mentions" if vol_pic > 1 else "mention"
            target_d = "all vectors combined" if is_all else f"the <b>{target}</b> category"
            _alert_html = f"""On <b>{date_pic_str}</b>, a volume of <b>{vol_pic} {mentions_w}</b> was identified. This represents a <b>{bond_percent:.1f}%</b> surge compared to normal activity for {target_d}."""
        else:
            mentions_w = "mentions" if vol_pic > 1 else "mention"
            v_aux = "ont ete" if vol_pic > 1 else "a ete"
            p_acc = "identifiees" if vol_pic > 1 else "identifiee"
            target_d = "tous vecteurs confondus" if is_all else f"la categorie <b>{target}</b>"
            _alert_html = f"""Le <b>{date_pic_str}</b>, un volume de <b>{vol_pic} {mentions_w}</b> {v_aux} {p_acc}. Cela represente un bond de <b>{bond_percent:.1f}%</b> par rapport a l'activite habituelle pour {target_d}."""

        _sig = {"en": "Signal status:", "fr": "Etat du signal :"}
        st.markdown(f"""
        <div class="insight-box">
            <b>{_sig[lang]}</b> <span style="color:{color_status};font-weight:600;">{status}</span> (Z-Score: {top_emergence['z_score']:.2f})
            <div class="alert-highlight">{_alert_html}</div>
        </div>
        """, unsafe_allow_html=True)

        _tbl_zscore = {"en": "Z-Score value", "fr": "Valeur Z-Score"}
        _tbl_meaning = {"en": "Meaning for consultants", "fr": "Signification pour le consultant"}
        _tbl_normal = {"en": "Normal activity", "fr": "Activite normale"}
        _tbl_calm = {"en": "(flat calm)", "fr": "(calme plat)"}
        _tbl_watch = {"en": "Watchfulness", "fr": "Vigilance"}
        _tbl_noise = {"en": ": background noise slightly increasing", "fr": ": bruit de fond en legere augmentation"}
        _tbl_anom = {"en": "ANOMALY", "fr": "ANOMALIE"}
        _tbl_strong = {"en": ": strong signal of a critical attack", "fr": ": signal fort d'une attaque critique"}

        st.markdown(f"""
        <table class="custom-table">
            <thead><tr><th>{_tbl_zscore[lang]}</th><th>{_tbl_meaning[lang]}</th></tr></thead>
            <tbody>
                <tr><td>0</td><td><span class="status-ok">{_tbl_normal[lang]}</span> {_tbl_calm[lang]}</td></tr>
                <tr><td>1 — 2</td><td><span class="status-warn">{_tbl_watch[lang]}</span>{_tbl_noise[lang]}</td></tr>
                <tr><td>> 2</td><td><span class="status-crit">{_tbl_anom[lang]}</span>{_tbl_strong[lang]}</td></tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

        _src_title = {"en": f"Sources on {date_pic_str} ({target})", "fr": f"Sources au {date_pic_str} ({target})"}
        st.markdown(f'<div class="section-title">{_src_title[lang]}</div>', unsafe_allow_html=True)
        try:
            df_articles = get_stg_articles(limit=2000)
            df_articles['published_date'] = pd.to_datetime(df_articles['published_date']).dt.normalize()
            if is_all:
                sources_pic = df_articles[df_articles['published_date'] == raw_date_pic]
            else:
                sources_pic = df_articles[(df_articles['published_date'] == raw_date_pic) & (df_articles['category'] == target)]
            if not sources_pic.empty:
                for _, row in sources_pic.iterrows():
                    url_val = row.get('url', '#')
                    cat_info = f" [{row['category']}]" if is_all else ""
                    st.markdown(f"""
                    <div class="article-card">
                        <a href="{url_val}" target="_blank">{row['title']}{cat_info}</a>
                        <div style="font-size:0.68rem; color:#7a9cc8; margin-top:3px">{row['source']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                _no = {"en": "No source details available.", "fr": "Aucun detail de source disponible."}
                st.info(_no[lang])
        except:
            _err = {"en": "Error retrieving detailed sources.", "fr": "Erreur lors de la recuperation des sources detaillees."}
            st.warning(_err[lang])