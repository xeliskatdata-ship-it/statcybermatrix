"""Build script -- genere 5_KPI5_Alertes.py avec le blob base64 injecte."""
import re, pathlib, sys

# --- Extraire le blob depuis KPI3 (deja construit) ---
src = pathlib.Path(__file__).parent / "cyberpulse" / "app" / "pages" / "3_KPI3_Menaces.py"
if not src.exists():
    src = pathlib.Path(__file__).parent / "app" / "pages" / "3_KPI3_Menaces.py"
text = src.read_text(encoding="utf-8")
m = re.search(r'_BG\s*=\s*"(data:image/[^"]+)"', text)
if not m:
    # Fallback: chercher dans le CSS inline
    m2 = re.search(r"background-image:\s*url\('(data:image/[^']+)'\)", text)
    if not m2:
        print("ERREUR : blob introuvable dans KPI3"); sys.exit(1)
    blob = m2.group(1)
else:
    blob = m.group(1)

print(f"Blob extrait : {blob[:60]}... ({len(blob)} chars)")

TEMPLATE = r'''"""
CyberPulse -- KPI 5
Nombre d'alertes critiques par semaine et categorie
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_mart_k5, force_refresh

st.set_page_config(page_title="KPI 5 - Alertes", layout="wide")

_BG = "__BLOB__"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{{font-family:'IBM Plex Sans',sans-serif;}}
.stApp{{
    background-image: url('{_BG}') !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
}}
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    background: rgba(5, 10, 20, 0.75);
    z-index: 0;
    pointer-events: none;
}}
[data-testid="stAppViewContainer"] > * {{
    position: relative;
    z-index: 1;
}}
[data-testid="stSidebar"]{{background:#0f1422!important;border-right:1px solid #1e2a42;}}
[data-testid="stSidebar"] *{{color:#a8b8d0!important;}}
.kpi-tag{{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#ef4444;background:rgba(239,68,68,.1);
border:1px solid rgba(239,68,68,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}}
.desc-box{{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #ef4444;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}}
.insight-box{{background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#fca5a5;font-size:0.88rem;}}
.alert-badge{{background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);
color:#ef4444;border-radius:6px;padding:6px 14px;font-size:.82rem;
font-weight:600;display:inline-block;margin:4px 4px 0 0;}}
.ok-box{{background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);
border-radius:8px;padding:10px 16px;margin-top:12px;color:#86efac;font-size:0.88rem;}}
.live-dot{{display:inline-block;width:7px;height:7px;border-radius:50%;
background:#22c55e;margin-right:6px;animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
</style>
""", unsafe_allow_html=True)

# --- Categories et justifications ---
CRITICAL_CATS = ['ransomware', 'vulnerability', 'apt', 'data_breach']

CAT_JUSTIF = {
    'ransomware'   : 'Impact operationnel immediat (chiffrement, extorsion)',
    'vulnerability': 'Failles exploitables pouvant compromettre des systemes',
    'apt'          : 'Menaces etatiques ciblees, souvent longues et discretes',
    'data_breach'  : 'Fuite de donnees sensibles avec consequences legales',
    'malware'      : 'Codes malveillants actifs (trojans, backdoors, wipers)',
    'phishing'     : 'Hameconnage cible avec vol de credentials',
    'ddos'         : 'Attaques volumetriques sur disponibilite des services',
    'supply_chain' : 'Compromission de la chaine logistique logicielle',
    'general'      : 'Articles sans categorie specifique identifiee',
}

# --- En-tete ---
col_h, col_r = st.columns([8, 1])
with col_h:
    st.markdown('<div class="kpi-tag">KPI 5</div>', unsafe_allow_html=True)
    st.markdown("### Nombre d'alertes critiques par semaine")
with col_r:
    if st.button("Rafraichir", key="k5_refresh"):
        force_refresh()
        st.rerun()

st.markdown("""
<div class="desc-box">
    <b>Objectif :</b> Visualiser le volume d'alertes issues des categories les plus dangereuses, semaine par semaine.<br>
    <b>Lecture :</b> Les barres rouges depassent le seuil critique que vous definissez.
    Un depassement signale une semaine a surveiller de pres.<br>
    <b>Seuil :</b> Ajustable selon votre contexte -- un seuil bas = plus de sensibilite, un seuil haut = alertes majeures uniquement.
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- Chargement donnees ---
df = get_mart_k5()

if df.empty:
    st.warning("Aucune donnee disponible. Verifiez que mart_k5 est bien construit (dbt run).")
    st.stop()

st.markdown(
    f'<span class="live-dot"></span>'
    f'<span style="color:#64748b;font-size:0.78rem">'
    f'Donnees PostgreSQL -- {len(df)} lignes chargees</span>',
    unsafe_allow_html=True
)

# --- Controles ---
seuil = st.slider("Seuil d'alerte critique (nb articles / semaine)", 1, 30, 5, key="k5_seuil")

cats_choisies = st.multiselect(
    "Categories considerees comme critiques",
    options=['ransomware', 'vulnerability', 'apt', 'data_breach', 'malware', 'phishing', 'ddos', 'supply_chain'],
    default=CRITICAL_CATS,
    key="k5_cats"
)

if not cats_choisies:
    st.warning("Selectionnez au moins une categorie critique.")
    st.stop()

# --- Justification ---
with st.expander("Pourquoi ces categories sont considerees critiques ?"):
    for cat in cats_choisies:
        justif = CAT_JUSTIF.get(cat, 'Menace a fort impact potentiel')
        st.markdown(f"- **{cat}** : {justif}")

# --- Filtrage et agregation ---
df_crit = df[df['category'].isin(cats_choisies)].copy()

if df_crit.empty:
    st.warning("Aucun article critique trouve avec les filtres actuels.")
    st.stop()

agg = (
    df_crit.groupby('semaine')['nb_alertes']
    .sum()
    .reset_index()
    .sort_values('semaine')
)
agg['semaine_str'] = agg['semaine'].dt.strftime('%Y-%W')

colors = ['#ef4444' if v >= seuil else '#3b82f6' for v in agg['nb_alertes']]

# --- Graphique ---
fig = go.Figure(go.Bar(
    x=agg['semaine_str'], y=agg['nb_alertes'],
    marker_color=colors,
    text=agg['nb_alertes'], textposition='outside',
    textfont=dict(color='#94a3b8')
))
fig.add_hline(
    y=seuil, line_dash='dash', line_color='#f59e0b', line_width=2,
    annotation_text=f"Seuil critique = {seuil}",
    annotation_font_color='#f59e0b', annotation_font_size=12
)
fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8'),
    xaxis=dict(gridcolor='#1e2a42', title='Semaine'),
    yaxis=dict(gridcolor='#1e2a42', title="Nombre d'alertes"),
    height=420, showlegend=False,
    margin=dict(l=20, r=20, t=40, b=20),
    title=f"Alertes critiques par semaine (seuil = {seuil})"
)
st.plotly_chart(fig, use_container_width=True)

# --- Metriques ---
total_alertes      = int(agg['nb_alertes'].sum())
semaines_critiques = agg[agg['nb_alertes'] >= seuil]
moy_semaine        = round(agg['nb_alertes'].mean(), 1)
semaine_max        = agg.loc[agg['nb_alertes'].idxmax(), 'semaine_str'] if not agg.empty else 'N/A'

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total alertes", total_alertes)
m2.metric("Moy. / semaine", moy_semaine)
m3.metric("Semaines > seuil", f"{len(semaines_critiques)} / {len(agg)}")
m4.metric("Semaine la + chargee", semaine_max)

# --- Insights ---
st.markdown(f"""
<div class="insight-box">
    <b>Insights :</b><br>
    - Total d'alertes critiques sur la periode : <b>{total_alertes}</b>.<br>
    - Moyenne par semaine : <b>{moy_semaine}</b> alertes.<br>
    - Semaines ayant depasse le seuil ({seuil}) : <b>{len(semaines_critiques)}</b> / {len(agg)}.
</div>
""", unsafe_allow_html=True)

if not semaines_critiques.empty:
    st.markdown("<br><b>Semaines en alerte :</b>", unsafe_allow_html=True)
    for _, row in semaines_critiques.iterrows():
        st.markdown(
            f'<span class="alert-badge">Semaine {row["semaine_str"]} &mdash; {int(row["nb_alertes"])} alertes</span>',
            unsafe_allow_html=True
        )
else:
    st.markdown("""
    <div class="ok-box">
        Aucune semaine n'a depasse le seuil critique. La situation est sous controle sur la periode.
    </div>
    """, unsafe_allow_html=True)

# --- Detail par categorie ---
st.markdown("---")
st.markdown("#### Repartition par categorie sur la periode")
cat_agg = (
    df_crit.groupby('category')['nb_alertes']
    .sum()
    .reset_index()
    .sort_values('nb_alertes', ascending=False)
)
cat_agg.columns = ['Categorie', 'Alertes']
st.dataframe(cat_agg, use_container_width=True, hide_index=True)

# --- Export ---
st.markdown("---")
csv = agg[['semaine_str', 'nb_alertes']].rename(
    columns={{'semaine_str': 'semaine'}}
).to_csv(index=False).encode('utf-8')
st.download_button("Telecharger les alertes (CSV)", csv,
    file_name="kpi5_alertes.csv", mime="text/csv")
'''

# Injection du blob
content = TEMPLATE.replace("__BLOB__", blob)

out = pathlib.Path(__file__).parent / "cyberpulse" / "app" / "pages" / "5_KPI5_Alertes.py"
if not out.parent.exists():
    out = pathlib.Path(__file__).parent / "app" / "pages" / "5_KPI5_Alertes.py"
out.write_text(content, encoding="utf-8")
print(f"Ecrit : {out} ({out.stat().st_size // 1024} KB)")
