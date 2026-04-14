# 3_Analyse_des_menaces.py -- StatCyberMatrix theme unifie

import sys, os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k3, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - Intelligence Menaces", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

# ── DATA ─────────────────────────────────────────────────────────────────────
try:
    df = get_mart_k3()
except:
    st.error("Erreur de base de données"); st.stop()

st.markdown('<div class="page-title">Intelligence Vectorielle des Menaces</div>', unsafe_allow_html=True)

# ── Top Section ──────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-title">Dominance par secteur (Treemap)</div>', unsafe_allow_html=True)
    fig_tree = px.treemap(
        df,
        path=[px.Constant("Menaces"), 'category', 'source'],
        values='nb_articles',
        color='nb_articles',
        color_continuous_scale=['#050a14', '#3b82f6', '#a855f7', '#00d4ff']
    )
    fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0), **PLOTLY_THEME)
    st.plotly_chart(fig_tree, use_container_width=True)

with col2:
    st.markdown('<div class="section-title">Résumé analyste</div>', unsafe_allow_html=True)
    if not df.empty:
        top_cat = df.groupby('category')['nb_articles'].sum().idxmax()
        st.markdown(f"""
        <div class="insight-box">
            <b>Vecteur Dominant :</b> {top_cat.upper()}<br><br>
            On observe une concentration critique sur le vecteur <b>{top_cat}</b>.
            Les consultants devraient prioriser les audits sur ce périmètre pour les prochaines 72h.
        </div>
        """, unsafe_allow_html=True)

        agg = df.groupby('category')['nb_articles'].sum().reset_index()
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=agg['nb_articles'], theta=agg['category'], fill='toself',
            line_color='#a855f7', fillcolor='rgba(168,85,247,0.15)'
        ))
        fig_radar.update_layout(
            polar=dict(bgcolor='rgba(5,10,20,0.4)', radialaxis=dict(visible=False)),
            showlegend=False, height=300, margin=dict(t=30, b=30), **PLOTLY_THEME
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# ── MATRICE ──────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Matrice de corrélation sources vs menaces</div>', unsafe_allow_html=True)

if not df.empty:
    pivot = df.pivot_table(index='source', columns='category', values='nb_articles', aggfunc='sum').fillna(0)

    max_val = pivot.values.max()
    max_pos = (pivot == max_val).stack().idxmax()
    source_max, cat_max = max_pos

    st.markdown(f"""
    <div class="insight-box">
        <b>Analyse de couverture :</b> La source <b>{source_max}</b> est le principal émetteur d'alertes
        sur le vecteur <b>{cat_max}</b> ({int(max_val)} articles).
        Cette matrice permet d'identifier les zones d'ombre ou les sur-représentations de certains flux.
    </div>
    """, unsafe_allow_html=True)

    fig_heat = px.imshow(
        pivot,
        labels=dict(x="Catégories de Menaces", y="Sources de Veille", color="Volume"),
        color_continuous_scale=['#050a14', '#3b82f6', '#a855f7', '#00d4ff'],
        aspect="auto"
    )
    fig_heat.update_layout(height=600, xaxis=dict(side="top"), margin=dict(t=100, b=50, l=50, r=50), **PLOTLY_THEME)
    if len(pivot.index) < 20:
        fig_heat.update_traces(text=pivot.values, texttemplate="%{text}")
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Deep Dive ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Deep Dive : derniers indicateurs</div>', unsafe_allow_html=True)
selected_cat = st.selectbox("Filtrer par vecteur", df['category'].unique() if not df.empty else ["N/A"])

df_raw_articles = get_stg_articles(limit=200)
filtered_articles = df_raw_articles[df_raw_articles['title'].str.contains(selected_cat, case=False, na=False)].head(10)

if not filtered_articles.empty:
    for _, row in filtered_articles.iterrows():
        st.markdown(f"""
        <div class="article-card">
            <a href="{row['url']}" target="_blank">{row['title']}</a>
            <div style="font-size:0.68rem; color:#7a9cc8; margin-top:3px">{row['source']}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Sélectionnez un vecteur pour afficher les articles récents correspondants.")