"""
Top mots-cles frequents (fenetre glissante)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re

st.set_page_config(page_title="KPI 2 - Mots-cles", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#0a0e1a;}
[data-testid="stSidebar"]{background:#0f1422!important;border-right:1px solid #1e2a42;}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#22c55e;background:rgba(34,197,94,.1);
border:1px solid rgba(34,197,94,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #22c55e;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}
.insight-box{background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#86efac;font-size:0.88rem;}
.warn-box{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);
border-radius:8px;padding:10px 16px;margin-top:10px;color:#fcd34d;font-size:0.82rem;}
</style>
""", unsafe_allow_html=True)

STOPWORDS = {
    'the','a','an','in','on','at','to','of','and','or','for','is','are','was',
    'with','that','this','it','as','be','by','from','has','have','not','but',
    'will','new','can','its','more','also','after','about','how','their','your',
    'all','one','two','they','been','into','than','over','our','we','you','he',
    'she','his','her','them','these','those','such','when','which','who','said',
    'up','out','if','so','no','do','get','just','now','been','using','used',
    'says','could','would','should','may','might','were','than','then','some',
    'other','only','like','make','what','when','where','while','between'
}

df = st.session_state.get('df_filtered', pd.DataFrame())
if df.empty:
    st.warning("Retournez sur la page d'accueil pour charger les donnees.")
    st.stop()

df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')

# --- En-tete ---
st.markdown('<div class="kpi-tag">KPI 2</div>', unsafe_allow_html=True)
st.markdown("### Top mots-cles frequents")
st.markdown("""
<div class="desc-box">
    <b>Objectif :</b> Identifier les termes les plus utilises dans les articles collectes sur une fenetre glissante.<br>
    <b>Lecture :</b> Les mots les plus frequents revelent les sujets dominants de la veille cyber sur la periode.<br>
    <b>Methode :</b> Extraction depuis les titres et descriptions · Suppression des mots vides (stopwords anglais) · Mots de 4 lettres minimum.
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- Filtres ---
col1, col2 = st.columns(2)
with col1:
    n_days = st.slider("Fenetre glissante (jours)", 3, 30, 30, key="k2_days")
with col2:
    top_n = st.slider("Nombre de mots-cles", 5, 20, 10, key="k2_topn")

# --- Filtrage ---
date_cut = pd.Timestamp.now() - pd.Timedelta(days=n_days)
dff = df[df['published_date'] >= date_cut].copy()

if dff.empty:
    st.markdown("""
    <div class="warn-box">
        Aucun article trouve sur cette fenetre. Les donnees collectees datent peut-etre de plus de 30 jours.
        Essayez d'elargir la fenetre ou relancez la collecte avec acquisition.py.
    </div>
    """, unsafe_allow_html=True)
    # Utiliser toutes les donnees disponibles comme fallback
    dff = df.copy()
    st.info(f"Affichage sur la totalite des donnees disponibles ({len(dff)} articles).")

# --- Extraction des mots ---
all_text = ' '.join(
    (dff['title'].fillna('') + ' ' + dff['description'].fillna('')).tolist()
).lower()
words = re.findall(r'\b[a-z]{4,}\b', all_text)
words = [w for w in words if w not in STOPWORDS]

if not words:
    st.warning("Aucun mot-cle extrait. Verifiez les donnees.")
    st.stop()

counter  = Counter(words)
top_words = counter.most_common(top_n)
df_kw = pd.DataFrame(top_words, columns=['mot_cle', 'occurrences'])

# --- Graphique + tableau ---
colA, colB = st.columns([3, 2])
with colA:
    fig = px.bar(
        df_kw.sort_values('occurrences'),
        x='occurrences', y='mot_cle', orientation='h',
        color='occurrences',
        color_continuous_scale=['#1e3a5f', '#22c55e'],
        title=f"Top {top_n} mots-cles -- {len(dff)} articles analyses",
        labels={'occurrences': 'Occurrences', 'mot_cle': 'Mot-cle'}
    )
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='IBM Plex Sans', color='#94a3b8'),
        xaxis=dict(gridcolor='#1e2a42'), yaxis=dict(gridcolor='#1e2a42'),
        coloraxis_showscale=False, showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20), height=420
    )
    st.plotly_chart(fig, use_container_width=True)

with colB:
    st.markdown("**Classement exact**")
    df_display = df_kw.copy()
    df_display.index = range(1, len(df_display) + 1)
    df_display.columns = ['Mot-cle', 'Occurrences']
    st.dataframe(df_display, use_container_width=True, height=400)

# --- Insight automatique ---
if not df_kw.empty:
    top1 = df_kw.iloc[0]
    top2 = df_kw.iloc[1] if len(df_kw) > 1 else None
    insight = f"- Mot-cle dominant : <b>{top1['mot_cle']}</b> avec <b>{top1['occurrences']}</b> occurrences."
    if top2 is not None:
        insight += f"<br>- Deuxieme terme : <b>{top2['mot_cle']}</b> ({top2['occurrences']} occurrences)."
    insight += f"<br>- Total de mots analyses : <b>{len(words):,}</b> · Vocabulaire unique : <b>{len(counter):,}</b> termes."
    st.markdown(f'<div class="insight-box"><b>Insights :</b><br>{insight}</div>',
                unsafe_allow_html=True)

# --- Export ---
st.markdown("---")
csv = df_kw.to_csv(index=False).encode('utf-8')
st.download_button("Telecharger les mots-cles (CSV)", csv,
    file_name="kpi2_mots_cles.csv", mime="text/csv")
