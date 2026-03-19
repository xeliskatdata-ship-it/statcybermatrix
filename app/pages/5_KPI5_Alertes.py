"""
Nombre d'alertes critiques par semaine
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="KPI 5 - Alertes", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#0a0e1a;}
[data-testid="stSidebar"]{background:#0f1422!important;border-right:1px solid #1e2a42;}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#ef4444;background:rgba(239,68,68,.1);
border:1px solid rgba(239,68,68,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #ef4444;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}
.insight-box{background:rgba(239,68,68,0.07);border:1px solid rgba(239,68,68,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#fca5a5;font-size:0.88rem;}
.alert-badge{background:rgba(239,68,68,.15);border:1px solid rgba(239,68,68,.3);
color:#ef4444;border-radius:6px;padding:6px 14px;font-size:.82rem;
font-weight:600;display:inline-block;margin:4px 4px 0 0;}
.ok-box{background:rgba(34,197,94,0.07);border:1px solid rgba(34,197,94,0.2);
border-radius:8px;padding:10px 16px;margin-top:12px;color:#86efac;font-size:0.88rem;}
.cat-grid{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;}
.cat-pill{background:#1e2a42;border:1px solid #334155;border-radius:20px;
padding:4px 12px;font-size:0.78rem;color:#94a3b8;}
</style>
""", unsafe_allow_html=True)

# Categories considerees comme critiques (justification ci-dessous)
CRITICAL_CATS = ['ransomware', 'vulnerability', 'apt', 'data_breach']

CAT_JUSTIF = {
    'ransomware'   : 'Impact operationnel immediat (chiffrement, extorsion)',
    'vulnerability': 'Failles exploitables pouvant compromettre des systemes',
    'apt'          : 'Menaces etatiques ciblees, souvent longues et discretes',
    'data_breach'  : 'Fuite de donnees sensibles avec consequences legales',
}

df = st.session_state.get('df_filtered', pd.DataFrame())
if df.empty:
    st.warning("Retournez sur la page d'accueil pour charger les donnees.")
    st.stop()

df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')

# --- En-tete ---
st.markdown('<div class="kpi-tag">KPI 5</div>', unsafe_allow_html=True)
st.markdown("### Nombre d'alertes critiques par semaine")
st.markdown("""
<div class="desc-box">
    <b>Objectif :</b> Visualiser le volume d'alertes issues des categories les plus dangereuses, semaine par semaine.<br>
    <b>Lecture :</b> Les barres rouges depassent le seuil critique que vous definissez.
    Un depassement signale une semaine a surveiller de pres.<br>
    <b>Seuil :</b> Ajustable selon votre contexte — un seuil bas = plus de sensibilite, un seuil haut = alertes majeures uniquement.
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- Seuil ---
seuil = st.slider("Seuil d'alerte critique (nb articles / semaine)", 1, 30, 5, key="k5_seuil")

# --- Categories critiques choisies ---
cats_choisies = st.multiselect(
    "Categories considerees comme critiques",
    options=['ransomware', 'vulnerability', 'apt', 'data_breach', 'malware', 'phishing', 'ddos', 'supply_chain'],
    default=CRITICAL_CATS,
    key="k5_cats"
)

if not cats_choisies:
    st.warning("Selectionnez au moins une categorie critique.")
    st.stop()

# --- Justification des categories ---
with st.expander("Pourquoi ces categories sont considerees critiques ?"):
    for cat in cats_choisies:
        justif = CAT_JUSTIF.get(cat, 'Menace a fort impact potentiel')
        st.markdown(f"- **{cat}** : {justif}")

# --- Filtrage et agregation ---
df_crit = df[df['category'].isin(cats_choisies)].copy()

if df_crit.empty:
    st.warning("Aucun article critique trouve avec les filtres actuels.")
    st.stop()

df_crit['semaine'] = df_crit['published_date'].dt.to_period('W').astype(str)
agg = df_crit.groupby('semaine').size().reset_index(name='alertes')
agg = agg.sort_values('semaine')

colors = ['#ef4444' if v >= seuil else '#3b82f6' for v in agg['alertes']]

# --- Graphique ---
fig = go.Figure(go.Bar(
    x=agg['semaine'], y=agg['alertes'],
    marker_color=colors,
    text=agg['alertes'], textposition='outside',
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
    yaxis=dict(gridcolor='#1e2a42', title='Nombre d\'alertes'),
    height=420, showlegend=False,
    margin=dict(l=20, r=20, t=40, b=20),
    title=f"Alertes critiques par semaine (seuil = {seuil})"
)
st.plotly_chart(fig, use_container_width=True)

# --- Insights ---
total_alertes    = int(agg['alertes'].sum())
semaines_critiques = agg[agg['alertes'] >= seuil]
moy_semaine      = round(agg['alertes'].mean(), 1)

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
            f'<span class="alert-badge">Semaine {row["semaine"]} &mdash; {row["alertes"]} alertes</span>',
            unsafe_allow_html=True
        )
else:
    st.markdown("""
    <div class="ok-box">
        Aucune semaine n'a depasse le seuil critique. La situation est sous controle sur la periode.
    </div>
    """, unsafe_allow_html=True)

# --- Export ---
st.markdown("---")
csv = agg.to_csv(index=False).encode('utf-8')
st.download_button("Telecharger les alertes (CSV)", csv,
    file_name="kpi5_alertes.csv", mime="text/csv")
