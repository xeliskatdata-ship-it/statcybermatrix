"""
CyberPulse -- KPI 1
Nombre d'articles collectes par jour / par source
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="KPI 1 - Articles", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#0a0e1a;}
[data-testid="stSidebar"]{background:#0f1422!important;border-right:1px solid #1e2a42;}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#3b82f6;background:rgba(59,130,246,.1);
border:1px solid rgba(59,130,246,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #3b82f6;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}
.insight-box{background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#93c5fd;font-size:0.88rem;}
.metric-card{background:#0f1422;border:1px solid #1e2a42;border-radius:8px;
padding:16px 18px;position:relative;overflow:hidden;}
.metric-card::after{content:'';position:absolute;top:0;left:0;width:3px;height:100%;background:#3b82f6;}
.metric-val{font-family:'IBM Plex Mono',monospace;font-size:1.6rem;font-weight:700;color:#e2e8f0;}
.metric-lbl{font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em;margin-top:4px;}
.metric-sub{font-size:0.78rem;color:#22c55e;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

COLORS = {
    "NewsAPI"         : "#3b82f6",
    "The Hacker News" : "#22c55e",
    "BleepingComputer": "#f59e0b",
    "Zataz"           : "#a855f7",
    "CISA Alerts"     : "#ef4444",
}

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8'),
)

# ---------------------------------------------------
# CHARGEMENT
# ---------------------------------------------------
df = st.session_state.get('df_filtered', pd.DataFrame())
if df.empty:
    st.warning("Retournez sur la page d'accueil pour charger les donnees.")
    st.stop()

df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')

# Fallback : si published_date vide, utiliser collected_at
if 'collected_at' in df.columns:
    df['collected_at'] = pd.to_datetime(df['collected_at'], errors='coerce')
    mask = df['published_date'].isna()
    df.loc[mask, 'published_date'] = df.loc[mask, 'collected_at']

# ---------------------------------------------------
# EN-TETE
# ---------------------------------------------------
st.markdown('<div class="kpi-tag">KPI 1</div>', unsafe_allow_html=True)
st.markdown("### Nombre d'articles collectes par jour / par source")
st.markdown("""
<div class="desc-box">
    <b>Objectif :</b> Suivre le volume de collecte quotidien et comparer l'activite de chaque source.<br>
    <b>Lecture :</b> Un pic sur une source indique generalement un evenement important ce jour-la.
    Une source a 0 peut signifier un probleme de collecte ou une absence de publication.<br>
    <b>Sources :</b> NewsAPI (API REST) · The Hacker News · BleepingComputer · Zataz · CISA Alerts (flux RSS).
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ---------------------------------------------------
# FILTRES
# ---------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    sources = sorted(df['source'].dropna().unique().tolist())
    sel_sources = st.multiselect("Sources a afficher", sources, default=sources, key="k1_src")
with col2:
    viz_type = st.radio("Type de graphique", ["Barres empilees", "Courbes"], horizontal=True, key="k1_viz")
with col3:
    mode_date = st.radio("Periode", ["7 derniers jours", "14 derniers jours", "30 derniers jours", "Choisir une date"], horizontal=False, key="k1_mode")

# Calcul de la fenetre selon le mode choisi
if mode_date == "7 derniers jours":
    n_days   = 7
    date_cut = pd.Timestamp.now() - pd.Timedelta(days=7)
elif mode_date == "14 derniers jours":
    n_days   = 14
    date_cut = pd.Timestamp.now() - pd.Timedelta(days=14)
elif mode_date == "30 derniers jours":
    n_days   = 30
    date_cut = pd.Timestamp.now() - pd.Timedelta(days=30)
else:
    # Selecteur de plage de dates personnalisee
    date_min  = df['published_date'].min().date()
    date_max  = df['published_date'].max().date()
    date_pick = st.date_input(
        "Choisir une plage de dates",
        value=(date_max - pd.Timedelta(days=7), date_max),
        min_value=date_min,
        max_value=date_max,
        key="k1_datepick"
    )
    if len(date_pick) == 2:
        date_cut = pd.Timestamp(date_pick[0])
        date_max_sel = pd.Timestamp(date_pick[1])
        n_days   = (date_pick[1] - date_pick[0]).days
    else:
        date_cut     = pd.Timestamp.now() - pd.Timedelta(days=7)
        date_max_sel = pd.Timestamp.now()
        n_days       = 7

if not sel_sources:
    st.warning("Selectionnez au moins une source.")
    st.stop()

# ---------------------------------------------------
# FILTRAGE & AGREGATION
# ---------------------------------------------------
dff = df[df['source'].isin(sel_sources)].copy()
if mode_date == "Choisir une date" and 'date_max_sel' in dir():
    dff = dff[
        (dff['published_date'] >= date_cut) &
        (dff['published_date'] <= date_max_sel)
    ]
else:
    dff = dff[dff['published_date'] >= date_cut]

if dff.empty:
    # Fallback : toutes les donnees disponibles
    dff = df[df['source'].isin(sel_sources)].copy()
    st.info("Aucune donnee sur la fenetre selectionnee — affichage de toutes les donnees disponibles.")

# Agregation par jour et source
agg = (
    dff.groupby([dff['published_date'].dt.strftime('%Y-%m-%d'), 'source'])
    .size().reset_index(name='nb_articles')
)
agg.columns = ['date', 'source', 'nb_articles']

# Total par jour (pour tendance globale)
agg_total = agg.groupby('date')['nb_articles'].sum().reset_index()
agg_total.columns = ['date', 'total']

# % par source par jour
agg_pct = agg.copy()
agg_pct = agg_pct.merge(agg_total, on='date')
agg_pct['pct'] = (agg_pct['nb_articles'] / agg_pct['total'] * 100).round(1)

# ---------------------------------------------------
# GRAPHIQUE PRINCIPAL
# ---------------------------------------------------
if viz_type == "Barres empilees":
    fig = px.bar(
        agg, x='date', y='nb_articles', color='source',
        color_discrete_map=COLORS,
        barmode='stack',
        title=f"Articles collectes par jour -- {n_days} derniers jours (barres empilees)",
        labels={'nb_articles': 'Nb articles', 'date': 'Date', 'source': 'Source'}
    )
    # Ligne de tendance globale
    fig.add_trace(go.Scatter(
        x=agg_total['date'], y=agg_total['total'],
        mode='lines', name='Tendance globale',
        line=dict(color='#ffffff', width=1.5, dash='dot'),
        opacity=0.5
    ))
else:
    fig = px.line(
        agg, x='date', y='nb_articles', color='source',
        color_discrete_map=COLORS,
        markers=True,
        title=f"Articles collectes par jour -- {n_days} derniers jours (courbes)",
        labels={'nb_articles': 'Nb articles', 'date': 'Date', 'source': 'Source'}
    )
    # Ligne de tendance globale
    fig.add_trace(go.Scatter(
        x=agg_total['date'], y=agg_total['total'],
        mode='lines', name='Tendance globale',
        line=dict(color='#ffffff', width=2, dash='dot'),
        opacity=0.4
    ))

fig.update_layout(
    **PLOTLY_BASE,
    xaxis=dict(gridcolor='#1e2a42'),
    yaxis=dict(gridcolor='#1e2a42'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02),
    margin=dict(l=20, r=20, t=60, b=20),
    height=420,
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# HEATMAP % PAR SOURCE PAR JOUR
# ---------------------------------------------------
st.markdown("---")
st.markdown("**Activite par source et par jour**")
st.markdown(
    "<div style='color:#64748b;font-size:0.82rem;margin-bottom:12px'>"
    "La heatmap montre l'intensite de publication de chaque source par jour. "
    "Plus la couleur est foncee, plus la source est active ce jour-la. "
    "Survolez une cellule pour voir le nombre exact d'articles."
    "</div>",
    unsafe_allow_html=True
)

# Pivoter pour la heatmap : lignes = sources, colonnes = dates
heatmap_data = agg.pivot_table(
    index='source', columns='date', values='nb_articles', aggfunc='sum', fill_value=0
)

fig_heat = go.Figure(go.Heatmap(
    z=heatmap_data.values,
    x=heatmap_data.columns.tolist(),
    y=heatmap_data.index.tolist(),
    colorscale=[
        [0.0,  '#0f1422'],
        [0.15, '#1e3a5f'],
        [0.4,  '#1d4ed8'],
        [0.7,  '#3b82f6'],
        [1.0,  '#93c5fd'],
    ],
    hoverongaps=False,
    hovertemplate='<b>%{y}</b><br>Date : %{x}<br>Articles : %{z}<extra></extra>',
    text=heatmap_data.values,
    texttemplate='%{text}',
    textfont=dict(size=11, color='white'),
    showscale=True,
    colorbar=dict(
        title='Articles',
        tickfont=dict(color='#94a3b8'),
    )
))

fig_heat.update_layout(
    **PLOTLY_BASE,
    xaxis=dict(gridcolor='#1e2a42', title='Date', tickangle=-30),
    yaxis=dict(gridcolor='#1e2a42', title=''),
    margin=dict(l=20, r=20, t=20, b=60),
    height=60 + len(heatmap_data) * 42,
)
st.plotly_chart(fig_heat, use_container_width=True)

# Tableau interactif avec filtres natifs Streamlit
with st.expander("Voir le tableau de donnees detaille"):
    pivot_display = heatmap_data.copy()
    pivot_display['TOTAL'] = pivot_display.sum(axis=1)
    pivot_display = pivot_display.sort_values('TOTAL', ascending=False)
    st.dataframe(
        pivot_display.style.background_gradient(
            cmap='Blues', axis=None,
            subset=[c for c in pivot_display.columns if c != 'TOTAL']
        ).format("{:.0f}"),
        use_container_width=True
    )

# ---------------------------------------------------
# CAMEMBERT PARTS DE MARCHE
# ---------------------------------------------------
st.markdown("---")
col_pie, col_stats = st.columns([1, 1.6])

with col_pie:
    st.markdown("**Parts de marche des sources**")
    agg_src = agg.groupby('source')['nb_articles'].sum().reset_index()
    fig_pie = px.pie(
        agg_src, names='source', values='nb_articles',
        color='source', color_discrete_map=COLORS,
        hole=0.45,
        title=f"Repartition globale sur {n_days} jours"
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(
        **PLOTLY_BASE,
        margin=dict(l=10, r=10, t=60, b=10),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_stats:
    st.markdown("**Resume par source**")
    cols_metrics = st.columns(min(len(sel_sources), 3))
    for i, src in enumerate(sel_sources):
        src_data = agg[agg['source'] == src]
        total    = int(src_data['nb_articles'].sum())
        avg      = round(src_data['nb_articles'].mean(), 1) if total > 0 else 0
        pct_src  = round(total / agg['nb_articles'].sum() * 100, 1) if agg['nb_articles'].sum() > 0 else 0
        col_idx  = i % 3
        cols_metrics[col_idx].markdown(f"""
        <div class="metric-card" style="margin-bottom:10px">
            <div class="metric-val">{total}</div>
            <div class="metric-lbl">{src}</div>
            <div class="metric-sub">{pct_src}% · ~{avg}/jour</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------
# INSIGHTS
# ---------------------------------------------------
if not agg.empty:
    top_source = agg.groupby('source')['nb_articles'].sum().idxmax()
    top_total  = int(agg.groupby('source')['nb_articles'].sum().max())
    top_day    = agg.loc[agg['nb_articles'].idxmax()]
    total_all  = int(agg['nb_articles'].sum())

    st.markdown(f"""
    <div class="insight-box">
        <b>Insights :</b><br>
        - Total collecte sur la periode : <b>{total_all}</b> articles toutes sources confondues.<br>
        - Source la plus active : <b>{top_source}</b> avec <b>{top_total}</b> articles ({round(top_total/total_all*100,1)}% du total).<br>
        - Pic de collecte : <b>{top_day['date']}</b> -- <b>{top_day['nb_articles']}</b> articles depuis <b>{top_day['source']}</b>.
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------
# EXPORT
# ---------------------------------------------------
st.markdown("---")
csv = dff.to_csv(index=False).encode('utf-8')
st.download_button("Telecharger les donnees (CSV)", csv,
    file_name="kpi1_articles.csv", mime="text/csv")


# ---------------------------------------------------
# SECTION : ARTICLES PAR CLIC SOURCE
# ---------------------------------------------------
st.markdown("---")
st.markdown("**Filtrer les articles par source**")
st.markdown(
    "<div style='color:#64748b;font-size:0.82rem;margin-bottom:12px'>"
    "Selectionnez une source pour afficher ses articles."
    "</div>",
    unsafe_allow_html=True
)

src_select = st.selectbox(
    "Choisir une source",
    options=["-- Toutes les sources --"] + sorted(dff['source'].dropna().unique().tolist()),
    key="k1_src_detail"
)

if src_select != "-- Toutes les sources --":
    df_detail = dff[dff['source'] == src_select].copy()
    df_detail = df_detail.sort_values('published_date', ascending=False)

    st.markdown(f"""
    <div style='background:#0f1422;border:1px solid #1e2a42;
    border-left:3px solid {COLORS.get(src_select, "#3b82f6")};
    border-radius:8px;padding:12px 18px;margin-bottom:16px'>
        <span style='font-family:IBM Plex Mono,monospace;font-size:0.8rem;
        color:{COLORS.get(src_select, "#3b82f6")}'>{src_select.upper()}</span>
        <span style='color:#64748b;font-size:0.8rem'> -- {len(df_detail)} articles</span>
    </div>
    """, unsafe_allow_html=True)

    for _, row in df_detail.head(20).iterrows():
        titre = str(row.get('title', 'Sans titre'))
        url   = str(row.get('url', ''))
        date  = str(row.get('published_date', ''))[:10]
        cat   = str(row.get('category', 'general'))
        lien  = (f'<a href="{url}" target="_blank" '
                 f'style="color:#e2e8f0;text-decoration:none">{titre}</a>'
                 if url else titre)
        st.markdown(
            f"<div style='background:#0f1422;border:1px solid #1e2a42;"
            f"border-radius:6px;padding:12px 16px;margin-bottom:8px'>"
            f"<div style='font-size:0.9rem'>{lien}</div>"
            f"<div style='margin-top:6px;font-size:0.75rem;color:#475569'>"
            f"{date} &nbsp;·&nbsp;"
            f"<span style='background:rgba(59,130,246,.15);color:#93c5fd;"
            f"border-radius:4px;padding:1px 8px'>{cat}</span>"
            f"</div></div>",
            unsafe_allow_html=True
        )

    if len(df_detail) > 20:
        st.caption(f"... et {len(df_detail) - 20} autres articles non affiches.")
