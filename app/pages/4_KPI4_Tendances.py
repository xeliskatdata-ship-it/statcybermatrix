"""
Evolution des mentions d'une menace dans le temps
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="KPI 4 - Tendances", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#0a0e1a;}
[data-testid="stSidebar"]{background:#0f1422!important;border-right:1px solid #1e2a42;}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#14b8a6;background:rgba(20,184,166,.1);
border:1px solid rgba(20,184,166,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #14b8a6;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}
.insight-box{background:rgba(20,184,166,0.07);border:1px solid rgba(20,184,166,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#5eead4;font-size:0.88rem;}
.warn-box{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);
border-radius:8px;padding:10px 16px;margin-top:10px;color:#fcd34d;font-size:0.82rem;}
</style>
""", unsafe_allow_html=True)

df = st.session_state.get('df_filtered', pd.DataFrame())
if df.empty:
    st.warning("Retournez sur la page d'accueil pour charger les donnees.")
    st.stop()

df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')

# --- En-tete ---
st.markdown('<div class="kpi-tag">KPI 4</div>', unsafe_allow_html=True)
st.markdown("### Evolution des mentions d'une menace dans le temps")
st.markdown("""
<div class="desc-box">
    <b>Objectif :</b> Suivre comment les mentions d'une menace specifique evoluent dans le temps.<br>
    <b>Lecture :</b> Un pic sur la courbe indique un evenement majeur lie a cette menace ce jour-la.
    Une tendance a la hausse signale un sujet emergent a surveiller.<br>
    <b>Conseil :</b> Utilisez la comparaison pour voir si deux menaces evoluent en meme temps (correlation possible).
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- Filtres ---
cats = sorted([c for c in df['category'].dropna().unique() if c != 'general'])
if not cats:
    st.warning("Aucune categorie de menace disponible.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    menace1 = st.selectbox("Menace a suivre", cats, key="k4_m1")
with col2:
    comparer = st.checkbox("Comparer avec une 2eme menace", key="k4_cmp")

# --- Fonction tendance ---
def get_trend(cat):
    dff = df[df['category'] == cat].copy()
    trend = (
        dff.groupby(dff['published_date'].dt.strftime('%Y-%m-%d'))
        .size().reset_index(name='mentions')
    )
    trend.columns = ['date', 'mentions']
    return trend.sort_values('date')

t1 = get_trend(menace1)

# --- Graphique ---
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=t1['date'], y=t1['mentions'],
    mode='lines+markers', name=menace1,
    line=dict(color='#14b8a6', width=2.5),
    marker=dict(size=6),
    fill='tozeroy', fillcolor='rgba(20,184,166,0.08)'
))

menace2 = None
if comparer:
    cats2   = [c for c in cats if c != menace1]
    menace2 = st.selectbox("2eme menace", cats2, key="k4_m2")
    t2 = get_trend(menace2)
    fig.add_trace(go.Scatter(
        x=t2['date'], y=t2['mentions'],
        mode='lines+markers', name=menace2,
        line=dict(color='#f59e0b', width=2.5),
        marker=dict(size=6),
    ))

fig.update_layout(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8'),
    xaxis=dict(gridcolor='#1e2a42', title='Date'),
    yaxis=dict(gridcolor='#1e2a42', title='Nombre de mentions'),
    legend=dict(orientation='h'),
    height=420,
    margin=dict(l=20, r=20, t=40, b=20),
    title=f"Mentions de '{menace1}'" + (f" vs '{menace2}'" if menace2 else "") + " dans le temps"
)
st.plotly_chart(fig, use_container_width=True)

# --- Insights ---
if not t1.empty:
    idx_max  = t1['mentions'].idxmax()
    idx_min  = t1['mentions'].idxmin()
    moy      = round(t1['mentions'].mean(), 1)
    total_m  = t1['mentions'].sum()

    st.markdown(f"""
    <div class="insight-box">
        <b>Insights sur '{menace1}' :</b><br>
        - Total de mentions : <b>{total_m}</b> sur la periode.<br>
        - Pic detecte le <b>{t1.loc[idx_max, 'date']}</b> avec <b>{t1.loc[idx_max, 'mentions']}</b> mentions.<br>
        - Jour le plus calme : <b>{t1.loc[idx_min, 'date']}</b> avec <b>{t1.loc[idx_min, 'mentions']}</b> mention(s).<br>
        - Moyenne quotidienne : <b>{moy}</b> articles / jour.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="warn-box">
        Aucune donnee disponible pour cette menace sur la periode selectionnee.
        Essayez une autre categorie ou relancez la collecte.
    </div>
    """, unsafe_allow_html=True)

# --- Export ---
st.markdown("---")
csv = t1.to_csv(index=False).encode('utf-8')
st.download_button(f"Telecharger tendances '{menace1}' (CSV)", csv,
    file_name=f"kpi4_{menace1}.csv", mime="text/csv")
