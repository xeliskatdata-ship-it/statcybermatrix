"""
Repartition par type de menace
"""

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="KPI 3 - Menaces", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#0a0e1a;}
[data-testid="stSidebar"]{background:#0f1422!important;border-right:1px solid #1e2a42;}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#f59e0b;background:rgba(245,158,11,.1);
border:1px solid rgba(245,158,11,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #f59e0b;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}
.insight-box{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#fcd34d;font-size:0.88rem;}
.note-box{background:rgba(100,116,139,0.07);border:1px solid rgba(100,116,139,0.2);
border-radius:8px;padding:10px 16px;margin-top:12px;color:#94a3b8;font-size:0.82rem;}
</style>
""", unsafe_allow_html=True)

COLORS = ['#3b82f6','#22c55e','#f59e0b','#ef4444','#a855f7',
          '#14b8a6','#f97316','#ec4899','#64748b']

# Description des categories
CAT_DESC = {
    'ransomware'   : 'Logiciels qui chiffrent les donnees et demandent une rancon',
    'phishing'     : 'Attaques par usurpation d\'identite pour voler des identifiants',
    'vulnerability': 'Failles de securite dans des logiciels ou systemes (CVE)',
    'malware'      : 'Logiciels malveillants (trojans, backdoors, spyware...)',
    'apt'          : 'Menaces persistantes avancees, souvent etatiques',
    'ddos'         : 'Attaques par deni de service distribue',
    'data_breach'  : 'Fuites ou vols de donnees',
    'supply_chain' : 'Attaques via des dependances ou fournisseurs tiers',
    'general'      : 'Articles cyber ne correspondant a aucune categorie specifique',
}

df = st.session_state.get('df_filtered', pd.DataFrame())
if df.empty:
    st.warning("Retournez sur la page d'accueil pour charger les donnees.")
    st.stop()

# --- En-tete ---
st.markdown('<div class="kpi-tag">KPI 3</div>', unsafe_allow_html=True)
st.markdown("### Repartition par type de menace")
st.markdown("""
<div class="desc-box">
    <b>Objectif :</b> Visualiser la proportion de chaque type de menace dans les articles collectes.<br>
    <b>Lecture :</b> Une categorie dominante indique le sujet le plus couvert par la presse cyber sur la periode.<br>
    <b>Methode :</b> Detection automatique par mots-cles dans le titre et la description (voir cleaning.py).
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- Filtre source ---
sources = sorted(df['source'].dropna().unique().tolist())
sel_sources = st.multiselect("Filtrer par source", sources, default=sources, key="k3_src")
dff = df[df['source'].isin(sel_sources)] if sel_sources else df

# --- Agregation ---
agg = dff['category'].value_counts().reset_index()
agg.columns = ['categorie', 'nb_articles']

# --- Choix visualisation ---
viz = st.radio("Visualisation", ["Camembert (donut)", "Treemap"], horizontal=True)

if viz == "Camembert (donut)":
    fig = px.pie(
        agg, names='categorie', values='nb_articles',
        color_discrete_sequence=COLORS, hole=0.45,
        title=f"Repartition des types de menaces -- {len(dff)} articles"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
else:
    fig = px.treemap(
        agg, path=['categorie'], values='nb_articles',
        color='nb_articles',
        color_continuous_scale=['#1e3a5f', '#f59e0b'],
        title=f"Treemap des types de menaces -- {len(dff)} articles"
    )

fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8'),
    margin=dict(l=20, r=20, t=60, b=20), height=460
)
st.plotly_chart(fig, use_container_width=True)

# --- Insight automatique ---
top_cat    = agg.iloc[0]['categorie']
top_count  = agg.iloc[0]['nb_articles']
total      = agg['nb_articles'].sum()
top_pct    = round(top_count / total * 100, 1)
general_n  = agg[agg['categorie'] == 'general']['nb_articles'].sum() if 'general' in agg['categorie'].values else 0
general_pct= round(general_n / total * 100, 1)

st.markdown(f"""
<div class="insight-box">
    <b>Insights :</b><br>
    - Menace dominante : <b>{top_cat}</b> represente <b>{top_pct}%</b> des articles ({top_count} articles).<br>
    - La categorie <b>general</b> ({general_pct}%) regroupe les articles cyber sans mot-cle de menace identifie.
    Elle peut etre reduite en enrichissant le dictionnaire de mots-cles dans cleaning.py.
</div>
""", unsafe_allow_html=True)

# --- Tableau detail ---
st.markdown("---")
st.markdown("**Detail par categorie**")
agg_display = agg.copy()
agg_display['% du total'] = (agg_display['nb_articles'] / total * 100).round(1).astype(str) + ' %'
agg_display['Description'] = agg_display['categorie'].map(CAT_DESC)
agg_display.columns = ['Type de menace', 'Articles', '% du total', 'Description']
st.dataframe(agg_display, use_container_width=True, hide_index=True)

# --- Note methodologique ---
st.markdown("""
<div class="note-box">
    <b>Note :</b> La categorisation est basee sur une detection de mots-cles (ex: "ransomware", "CVE", "phishing"...).
    Un article est classe dans la premiere categorie dont un mot-cle apparait dans son titre ou description.
    Les articles sans correspondance sont classes en "general".
</div>
""", unsafe_allow_html=True)

# --- Export ---
st.markdown("---")
csv = agg_display.to_csv(index=False).encode('utf-8')
st.download_button("Telecharger la repartition (CSV)", csv,
    file_name="kpi3_menaces.csv", mime="text/csv")
