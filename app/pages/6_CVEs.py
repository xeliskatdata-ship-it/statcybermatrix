# 6_CVEs.py -- StatCyberMatrix i18n

import streamlit as st
import os, sys, pathlib
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_mart_k6, force_refresh

st.set_page_config(page_title="StatCyberMatrix - KPI 6 CVE", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
lang = st.session_state.get("lang", "en")
inject_sidebar_css(lang)
from page_theme import inject_theme, PLOTLY_THEME
inject_theme()

st.markdown("""
<style>
.cve-card {
    background: rgba(10,22,40,0.7); border: 1px solid rgba(0,212,255,0.12);
    border-radius: 8px; padding: 18px; backdrop-filter: blur(8px);
    font-family: 'JetBrains Mono', monospace; color: #c8d6e5;
}
.cve-card h4 { color: #00d4ff; font-family: 'Syne', sans-serif; margin-bottom: 10px; }
.cve-card b { color: #c8d6e5; }
.cve-card hr { border: 0.5px solid rgba(0,212,255,0.1); }
.severity-CRITICAL { color: #ef4444; font-weight: 600; }
.severity-HIGH { color: #f59e0b; font-weight: 600; }
.severity-MEDIUM { color: #00d4ff; font-weight: 600; }
a { text-decoration: none; color: inherit; }
</style>
""", unsafe_allow_html=True)

# ── DATA ─────────────────────────────────────────────────────────────────────
df_raw = get_mart_k6()
if df_raw.empty:
    st.stop()

agg = df_raw.head(12).copy()
agg.columns = ['CVE', 'Mentions']

def make_clickable(cve):
    return f'<a href="https://nvd.nist.gov/vuln/detail/{cve}" target="_blank">{cve}</a>'

agg['Clickable_CVE'] = agg['CVE'].apply(make_clickable)

nvd_data_sim = {row['CVE']: {
    "score": round(9.0 + (i % 10) / 10, 1) if i % 2 == 0 else round(7.0 + (i % 10) / 10, 1),
    "severity": "CRITICAL" if i % 2 == 0 else "HIGH"
} for i, row in agg.iterrows()}

# ── HEADER ───────────────────────────────────────────────────────────────────
_title = {"en": "Most mentioned CVEs", "fr": "CVEs les plus mentionnees"}
st.markdown(f'<div class="page-title">{_title[lang]}</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1])
with col_a:
    _sync = {"en": "Sync data", "fr": "Synchroniser les donnees"}
    if st.button(_sync[lang]):
        force_refresh(); st.rerun()

# ── VIZ ──────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    _density = {"en": "Activity density", "fr": "Densite d'activite"}
    st.markdown(f'<div class="section-title">{_density[lang]}</div>', unsafe_allow_html=True)
    fig_bubble = px.scatter(agg, x="CVE", y="Mentions", size="Mentions", color="Mentions",
                            size_max=50, color_continuous_scale=['#050a14', '#a855f7', '#00d4ff'])
    fig_bubble.update_layout(**PLOTLY_THEME)
    st.plotly_chart(fig_bubble, use_container_width=True)

with col_right:
    _ranking = {"en": "Ranking (clickable CVEs)", "fr": "Classement (CVEs cliquables)"}
    st.markdown(f'<div class="section-title">{_ranking[lang]}</div>', unsafe_allow_html=True)
    _hover = {"en": "Click the CVE name for NVD details", "fr": "Cliquez sur le nom de la CVE pour le detail NVD"}
    fig_bar = go.Figure(go.Bar(
        x=agg['Mentions'], y=agg['Clickable_CVE'], orientation='h',
        marker=dict(color=agg['Mentions'], colorscale=[[0, '#3b82f6'], [0.5, '#a855f7'], [1, '#00d4ff']]),
        hovertemplate=f"{_hover[lang]}<extra></extra>"
    ))
    fig_bar.update_layout(yaxis=dict(autorange="reversed"), **PLOTLY_THEME)
    st.plotly_chart(fig_bar, use_container_width=True)

# ── INVESTIGATION NVD ────────────────────────────────────────────────────────
_nvd_title = {"en": "NVD investigation", "fr": "Investigation NVD"}
st.markdown(f'<div class="section-title">{_nvd_title[lang]}</div>', unsafe_allow_html=True)

_select_lbl = {"en": "Deep analysis:", "fr": "Analyse profonde :"}
selected_cve = st.selectbox(_select_lbl[lang], agg['CVE'].tolist())

current_info = nvd_data_sim.get(selected_cve, {"score": "N/A", "severity": "UNKNOWN"})
score_val = current_info['score']
sev_val = current_info['severity']
mentions_val = agg[agg['CVE']==selected_cve]['Mentions'].values[0]

# CVE ID + severity = termes techniques, jamais traduits
_card = {
    "en": f"""<h4>Technical sheet: {selected_cve}</h4>
    <p><b>NVD severity:</b> <span class="severity-{sev_val}">{sev_val}</span> (Score: {score_val})</p>
    <p>This vulnerability is under increased scrutiny following a surge of {mentions_val} mentions in intelligence feeds.</p>
    <hr>
    <small style="color:#7a9cc8;">NVD (National Vulnerability Database): NIST reference database synchronized with the MITRE CVE list. Provides enriched analysis (CVSS, CWE, CPE) essential for patch prioritization.</small>""",
    "fr": f"""<h4>Fiche technique : {selected_cve}</h4>
    <p><b>Severite NVD :</b> <span class="severity-{sev_val}">{sev_val}</span> (Score: {score_val})</p>
    <p>Cette vulnerabilite fait l'objet d'une attention particuliere suite a une hausse de {mentions_val} mentions dans les flux de veille.</p>
    <hr>
    <small style="color:#7a9cc8;">NVD (National Vulnerability Database) : Referentiel du NIST synchronise avec la liste CVE de MITRE. Fournit une analyse enrichie (CVSS, CWE, CPE) indispensable a la priorisation des patchs.</small>""",
}
st.markdown(f'<div class="cve-card">{_card[lang]}</div>', unsafe_allow_html=True)