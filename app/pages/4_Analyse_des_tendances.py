# 4_Analyse_des_tendances.py -- StatCyberMatrix theme unifie

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
inject_sidebar_css()
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

# CSS complementaire pour cette page
st.markdown("""
<style>
.alert-highlight {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 6px; padding: 14px; margin-top: 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #c8d6e5;
}
.custom-table {
    width: 100%; border-collapse: collapse; margin: 16px 0;
    font-family: 'JetBrains Mono', monospace;
    background: rgba(10,22,40,0.6); border-radius: 8px; overflow: hidden;
    border: 1px solid rgba(0,212,255,0.1);
}
.custom-table th {
    background: rgba(0,212,255,0.06); color: #00d4ff; text-align: left;
    padding: 10px 14px; border-bottom: 1px solid rgba(0,212,255,0.15);
    text-transform: uppercase; letter-spacing: 1px; font-size: 0.72rem;
}
.custom-table td {
    padding: 10px 14px; border-bottom: 1px solid rgba(0,212,255,0.04);
    color: #c8d6e5; font-size: 0.78rem;
}
.status-crit { color: #ef4444; font-weight: 600; }
.status-warn { color: #f59e0b; }
.status-ok { color: #22c55e; }
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
try:
    df_mart = get_mart_k4()
    if not df_mart.empty:
        df_mart['published_date'] = pd.to_datetime(df_mart['published_date']).dt.normalize()
except Exception as e:
    st.error(f"Erreur technique : {e}"); st.stop()

with st.sidebar:
    st.markdown("### Analyse de Menaces")
    choix_temps = st.selectbox("Fenetre d'observation", ["7 derniers jours", "14 derniers jours", "30 derniers jours"], index=1)
    nb_jours = int(choix_temps.split()[0])
    cats_brutes = sorted(df_mart['category'].unique().tolist()) if not df_mart.empty else []
    cats_dispo = ["Tout"] + cats_brutes
    target = st.selectbox("Vecteur cible", cats_dispo)

if not df_mart.empty:
    date_limite = df_mart['published_date'].max() - timedelta(days=nb_jours)
    df_filtered = df_mart[df_mart['published_date'] >= date_limite].copy()

    st.markdown('<div class="page-title">Analyse des Tendances CTI</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="section-title">Indice d\'accélération (Z-Score) — {target}</div>', unsafe_allow_html=True)

    if target == "Tout":
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

        fig_radar = px.scatter(data_trend, x='nb_mentions', y='z_score', size='nb_mentions', color='z_score',
                               text=data_trend['published_date'].dt.strftime('%d/%m'),
                               color_continuous_scale=['#050a14', '#a855f7', '#00d4ff'], height=450)
        fig_radar.add_hline(y=2.0, line_dash="dash", line_color="#ef4444",
                            annotation_text="Seuil anomalie", annotation=dict(font_color="#ef4444", font_size=10))
        fig_radar.update_traces(textfont=dict(size=10, color="#c8d6e5"))
        fig_radar.update_layout(**PLOTLY_THEME)
        st.plotly_chart(fig_radar, use_container_width=True)

        status = "CRITIQUE" if top_emergence['z_score'] > 2 else "STABLE"
        color_status = "#ef4444" if top_emergence['z_score'] > 2 else "#22c55e"
        target_display = "tous vecteurs confondus" if target == "Tout" else f"la catégorie <b>{target}</b>"
        verbe_aux = "ont été" if vol_pic > 1 else "a été"
        participe_acc = "identifiées" if vol_pic > 1 else "identifiée"
        mot_mention = "mentions" if vol_pic > 1 else "mention"

        st.markdown(f"""
        <div class="insight-box">
            <b>Etat du signal :</b> <span style="color:{color_status}; font-weight:600;">{status}</span> (Score Z : {top_emergence['z_score']:.2f})
            <div class="alert-highlight">
                Le <b>{date_pic_str}</b>, un volume de <b>{vol_pic} {mot_mention}</b> {verbe_aux} {participe_acc}.
                Cela représente un bond de <b>{bond_percent:.1f}%</b> par rapport a l'activite habituelle pour {target_display}.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <table class="custom-table">
            <thead><tr><th>Valeur Z-Score</th><th>Signification pour le Consultant</th></tr></thead>
            <tbody>
                <tr><td>0</td><td><span class="status-ok">Activité normale</span> (calme plat)</td></tr>
                <tr><td>1 à 2</td><td><span class="status-warn">Vigilance</span> : bruit de fond en légère augmentation</td></tr>
                <tr><td>> 2</td><td><span class="status-crit">ANOMALIE</span> : Signal fort d'une attaque critique</td></tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="section-title">Sources au {date_pic_str} ({target})</div>', unsafe_allow_html=True)
        try:
            df_articles = get_stg_articles(limit=2000)
            df_articles['published_date'] = pd.to_datetime(df_articles['published_date']).dt.normalize()
            if target == "Tout":
                sources_pic = df_articles[df_articles['published_date'] == raw_date_pic]
            else:
                sources_pic = df_articles[(df_articles['published_date'] == raw_date_pic) & (df_articles['category'] == target)]
            if not sources_pic.empty:
                for _, row in sources_pic.iterrows():
                    url_val = row.get('url', '#')
                    cat_info = f" [{row['category']}]" if target == "Tout" else ""
                    st.markdown(f"""
                    <div class="article-card">
                        <a href="{url_val}" target="_blank">{row['title']}{cat_info}</a>
                        <div style="font-size:0.68rem; color:#7a9cc8; margin-top:3px">{row['source']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Aucun détail de source disponible.")
        except:
            st.warning("Erreur lors de la récupération des sources détaillées.")