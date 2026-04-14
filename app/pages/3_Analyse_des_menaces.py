# 3_Analyse_des_menaces.py -- StatCyberMatrix i18n

import sys, os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k3, get_stg_articles, force_refresh

st.set_page_config(page_title="StatCyberMatrix - Intelligence Menaces", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
lang = st.session_state.get("lang", "en")
inject_sidebar_css(lang)
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

try:
    df = get_mart_k3()
except:
    st.error("Database error"); st.stop()

_title = {"en": "Threat vector intelligence", "fr": "Intelligence vectorielle des menaces"}
st.markdown(f'<div class="page-title">{_title[lang]}</div>', unsafe_allow_html=True)

# ── Top Section ──────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    _tree = {"en": "Sector dominance (Treemap)", "fr": "Dominance par secteur (Treemap)"}
    st.markdown(f'<div class="section-title">{_tree[lang]}</div>', unsafe_allow_html=True)
    fig_tree = px.treemap(df, path=[px.Constant("Threats"), 'category', 'source'],
        values='nb_articles', color='nb_articles',
        color_continuous_scale=['#050a14', '#3b82f6', '#a855f7', '#00d4ff'])
    fig_tree.update_layout(margin=dict(t=0, l=0, r=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,10,20,0.4)",
        font=dict(family="JetBrains Mono", size=11, color="#c8d6e5"))
    st.plotly_chart(fig_tree, use_container_width=True)

with col2:
    _sum = {"en": "Analyst summary", "fr": "Resume analyste"}
    st.markdown(f'<div class="section-title">{_sum[lang]}</div>', unsafe_allow_html=True)
    if not df.empty:
        top_cat = df.groupby('category')['nb_articles'].sum().idxmax()
        # category = terme technique, jamais traduit
        _ins = {
            "en": f"<b>Dominant vector:</b> {top_cat.upper()}<br><br>Critical concentration observed on the <b>{top_cat}</b> vector. Consultants should prioritize audits on this perimeter for the next 72h.",
            "fr": f"<b>Vecteur dominant :</b> {top_cat.upper()}<br><br>Concentration critique observee sur le vecteur <b>{top_cat}</b>. Les consultants devraient prioriser les audits sur ce perimetre pour les prochaines 72h.",
        }
        st.markdown(f'<div class="insight-box">{_ins[lang]}</div>', unsafe_allow_html=True)

        agg = df.groupby('category')['nb_articles'].sum().reset_index()
        fig_radar = go.Figure(data=go.Scatterpolar(r=agg['nb_articles'], theta=agg['category'],
            fill='toself', line_color='#a855f7', fillcolor='rgba(168,85,247,0.15)'))
        fig_radar.update_layout(polar=dict(bgcolor='rgba(5,10,20,0.4)', radialaxis=dict(visible=False)),
            showlegend=False, height=300, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="JetBrains Mono", size=11, color="#c8d6e5"), margin=dict(t=30, b=30, l=10, r=10))
        st.plotly_chart(fig_radar, use_container_width=True)

# ── MATRICE ──────────────────────────────────────────────────────────────────
_mat = {"en": "Correlation matrix: sources vs threats", "fr": "Matrice de correlation sources vs menaces"}
st.markdown(f'<div class="section-title">{_mat[lang]}</div>', unsafe_allow_html=True)

if not df.empty:
    pivot = df.pivot_table(index='source', columns='category', values='nb_articles', aggfunc='sum').fillna(0)
    max_val = pivot.values.max()
    max_pos = (pivot == max_val).stack().idxmax()
    source_max, cat_max = max_pos
    # source_max + cat_max = noms propres / termes techniques
    _ins2 = {
        "en": f"<b>Coverage analysis:</b> Source <b>{source_max}</b> is the main alert emitter on the <b>{cat_max}</b> vector ({int(max_val)} articles). This matrix identifies blind spots or over-representations in certain feeds.",
        "fr": f"<b>Analyse de couverture :</b> La source <b>{source_max}</b> est le principal emetteur d'alertes sur le vecteur <b>{cat_max}</b> ({int(max_val)} articles). Cette matrice permet d'identifier les zones d'ombre ou les sur-representations.",
    }
    st.markdown(f'<div class="insight-box">{_ins2[lang]}</div>', unsafe_allow_html=True)

    _lbl_x = {"en": "Threat categories", "fr": "Categories de menaces"}
    _lbl_y = {"en": "Intelligence sources", "fr": "Sources de veille"}
    fig_heat = px.imshow(pivot, labels=dict(x=_lbl_x[lang], y=_lbl_y[lang], color="Volume"),
        color_continuous_scale=['#050a14', '#3b82f6', '#a855f7', '#00d4ff'], aspect="auto")
    fig_heat.update_layout(height=600, xaxis=dict(side="top"), paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,10,20,0.4)", font=dict(family="JetBrains Mono", size=12, color="#c8d6e5"),
        margin=dict(t=100, b=50, l=50, r=50))
    if len(pivot.index) < 20:
        fig_heat.update_traces(text=pivot.values, texttemplate="%{text}")
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Deep Dive ────────────────────────────────────────────────────────────────
_dd = {"en": "Deep dive: latest indicators", "fr": "Deep Dive : derniers indicateurs"}
st.markdown(f'<div class="section-title">{_dd[lang]}</div>', unsafe_allow_html=True)

_dd_lbl = {"en": "Filter by vector", "fr": "Filtrer par vecteur"}
selected_cat = st.selectbox(_dd_lbl[lang], df['category'].unique() if not df.empty else ["N/A"])

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
    _no = {"en": "Select a vector to display recent articles.", "fr": "Selectionnez un vecteur pour afficher les articles recents."}
    st.info(_no[lang])