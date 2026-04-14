# 2_Suivi_des_mots-cles.py -- StatCyberMatrix i18n

import os, sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k2, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 2 - Threat Keywords", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
lang = st.session_state.get("lang", "en")
inject_sidebar_css(lang)
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

_title = {"en": "Keyword tracking", "fr": "Suivi des mots-cles"}
st.markdown(f'<div class="page-title">{_title[lang]}</div>', unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
try:
    df_raw = get_mart_k2()
    v3 = df_raw[df_raw['period_days'] == 3].copy()
    v15 = df_raw[df_raw['period_days'] == 15][['keyword', 'occurrences']].rename(columns={'occurrences':'occ_15j'})
    drift_df = pd.merge(v3, v15, on='keyword', how='left').fillna(0)
    drift_df['acceleration'] = (drift_df['occurrences'] + 1) / ((drift_df['occ_15j'] / 5) + 1)
    if 'category' not in drift_df.columns:
        drift_df['category'] = 'Threats'
except Exception as e:
    st.error(f"Data error: {e}"); st.stop()

# ── METRICS ──────────────────────────────────────────────────────────────────
nb_mots_cles = len(drift_df)
top_v = drift_df.sort_values('occurrences', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"
top_a = drift_df.sort_values('acceleration', ascending=False).iloc[0]['keyword'] if not drift_df.empty else "—"

_lbl_active = {"en": "Active keywords", "fr": "Mots-cles actifs"}
_lbl_vol = {"en": "Top volume", "fr": "Top volume"}
_lbl_vel = {"en": "Top velocity", "fr": "Top velocite"}

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700&family=JetBrains+Mono:wght@400;500&display=swap');
.grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; font-family:'JetBrains Mono',monospace; }}
.card {{ background:rgba(10,22,40,0.7); border:1px solid rgba(0,212,255,0.15); border-radius:8px; padding:16px; text-align:center; color:#c8d6e5; }}
.label {{ font-size:0.65rem; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px; color:#7a9cc8; }}
.value {{ font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:700; color:#00d4ff; }}
.btn {{ background:rgba(168,85,247,0.1); border:1px solid #a855f7; color:#a855f7; border-radius:6px; padding:10px; cursor:pointer; font-size:0.75rem; width:100%; font-family:'JetBrains Mono',monospace; }}
</style>
<div class="grid">
  <div class="card"><div class="label">{_lbl_active[lang]}</div><div class="value" id="cnt-k2">0</div></div>
  <div class="card"><div class="label">{_lbl_vol[lang]}</div><div class="value" style="font-size:1.1rem">{top_v}</div></div>
  <div class="card"><div class="label">{_lbl_vel[lang]}</div><div class="value" style="font-size:1.1rem">{top_a}</div></div>
  <div class="card" style="border:none;background:transparent;display:flex;align-items:center;"><button class="btn" onclick="window.parent.location.reload()">REFRESH</button></div>
</div>
<script>
(function(){{let o=document.getElementById('cnt-k2'),s=null;function step(t){{if(!s)s=t;let p=Math.min((t-s)/1200,1);o.textContent=Math.floor(p*{nb_mots_cles});if(p<1)requestAnimationFrame(step);}};requestAnimationFrame(step);}})();
</script>
""", height=120)

# ── TREEMAP ──────────────────────────────────────────────────────────────────
_tree_title = {"en": "Hierarchical analysis", "fr": "Analyse hierarchique"}
st.markdown(f'<div class="section-title">{_tree_title[lang]}</div>', unsafe_allow_html=True)

_, f_col, _ = st.columns([1, 2, 1])
with f_col:
    _slider_lbl = {"en": "Emergence threshold (acceleration)", "fr": "Seuil d'emergence (acceleration)"}
    min_accel = st.slider(_slider_lbl[lang], 0.5, 3.0, 1.0, step=0.1)

df_filtered = drift_df[drift_df['acceleration'] >= min_accel]

fig_tree = px.treemap(df_filtered, path=[px.Constant("Cyber Overview"), 'category', 'keyword'],
    values='occurrences', color='acceleration',
    color_continuous_scale=['#050a14', '#3b82f6', '#a855f7', '#00d4ff'], range_color=[0.5, 2.5])
fig_tree.update_traces(textinfo="label+value", textfont=dict(color="white"))
fig_tree.update_layout(margin=dict(t=0, b=0, l=10, r=10),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,10,20,0.4)",
    font=dict(family="JetBrains Mono", size=11, color="#c8d6e5"))
st.plotly_chart(fig_tree, use_container_width=True)

if not df_filtered.empty:
    top_accel_row = df_filtered.sort_values('acceleration', ascending=False).iloc[0]
    # keyword = terme technique, jamais traduit
    _ins1 = {
        "en": f"<b>Velocity analysis:</b> Keyword <b>{top_accel_row['keyword']}</b> has the highest acceleration ({top_accel_row['acceleration']:.2f}x), indicating an emerging trend or active campaign detected over the last 72h.",
        "fr": f"<b>Analyse de velocite :</b> Le mot-cle <b>{top_accel_row['keyword']}</b> presente la plus forte acceleration ({top_accel_row['acceleration']:.2f}x), indiquant une tendance emergente ou une campagne active detectee sur les dernieres 72h.",
    }
    st.markdown(f'<div class="insight-box">{_ins1[lang]}</div>', unsafe_allow_html=True)

# ── BAR CHART SNR ─────────────────────────────────────────────────────────────
_snr_title = {"en": "Signal reliability (unique sources)", "fr": "Fiabilite du signal (sources uniques)"}
st.markdown(f'<div class="section-title">{_snr_title[lang]}</div>', unsafe_allow_html=True)

df_snr = df_filtered.nlargest(15, 'occurrences').sort_values('source_count')
fig_snr = go.Figure(go.Bar(y=df_snr['keyword'], x=df_snr['source_count'], orientation='h',
    marker=dict(color='#a855f7', line=dict(color='rgba(0,212,255,0.3)', width=0.5)),
    hovertemplate="<b>%{y}</b><br>Sources: %{x}<extra></extra>"))
fig_snr.update_layout(**PLOTLY_THEME)
st.plotly_chart(fig_snr, use_container_width=True)

if not df_snr.empty:
    reliable_kw = df_snr.sort_values('source_count', ascending=False).iloc[0]
    _ins2 = {
        "en": f"<b>Signal reliability:</b> The term <b>{reliable_kw['keyword']}</b> is corroborated by <b>{reliable_kw['source_count']} distinct sources</b>. A high score here reduces the risk of false positives from single-source noise.",
        "fr": f"<b>Fiabilite du signal :</b> Le terme <b>{reliable_kw['keyword']}</b> est corrobore par <b>{reliable_kw['source_count']} sources distinctes</b>. Un score eleve reduit le risque de faux positif lie au bruit d'une source unique.",
    }
    st.markdown(f'<div class="insight-box">{_ins2[lang]}</div>', unsafe_allow_html=True)

# ── DEEP DIVE ─────────────────────────────────────────────────────────────────
_dd_title = {"en": "Explore articles", "fr": "Explorer les articles"}
st.markdown(f'<div class="section-title">{_dd_title[lang]}</div>', unsafe_allow_html=True)

_, d_col, _ = st.columns([1, 2, 1])
with d_col:
    _dd_lbl = {"en": "Filter by keyword", "fr": "Filtrer par mot-cle"}
    _dd_default = {"en": "-- Choose --", "fr": "-- Choisir --"}
    selected_kw = st.selectbox(_dd_lbl[lang], [_dd_default[lang]] + sorted(list(df_filtered['keyword'])))

if selected_kw not in (_dd_default["en"], _dd_default["fr"]):
    all_articles = get_stg_articles(limit=1000)
    relevant = all_articles[all_articles['title'].str.contains(selected_kw, case=False, na=False)].head(10)
    for _, row in relevant.iterrows():
        st.markdown(f"""
        <div class="article-card">
            <a href="{row['url']}" target="_blank">{row['title']}</a>
            <div style="font-size:0.68rem; color:#7a9cc8; margin-top:3px">{row['source']} · {str(row['published_date'])[:10]}</div>
        </div>
        """, unsafe_allow_html=True)