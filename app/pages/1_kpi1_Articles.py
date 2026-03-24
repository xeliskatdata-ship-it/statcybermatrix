"""
CyberPulse -- KPI 1
Articles collected per day / per source
Source de donnees : PostgreSQL (mart_k1)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from db_connect import get_mart_k1, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 1 - Articles", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{background:#050a14;}
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
.status-bar{background:#0f1422;border:1px solid #1e2a42;border-radius:6px;
padding:8px 14px;font-size:0.78rem;color:#64748b;margin-bottom:16px;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# PALETTE COULEURS PAR SOURCE
# -------------------------------------------------------
COLORS = {
    "NewsAPI"              : "#3b82f6",
    "The Hacker News"      : "#22c55e",
    "BleepingComputer"     : "#f59e0b",
    "CISA Alerts"          : "#ef4444",
    "Krebs on Security"    : "#06b6d4",
    "Dark Reading"         : "#8b5cf6",
    "SecurityWeek"         : "#f97316",
    "Cyber Scoop"          : "#10b981",
    "Threatpost"           : "#ec4899",
    "Schneier on Security" : "#14b8a6",
    "The Record"           : "#6366f1",
    "Infosecurity Magazine": "#84cc16",
    "Helpnet Security"     : "#fb923c",
    "Graham Cluley"        : "#a78bfa",
    "Zataz"                : "#a855f7",
    "ANSSI"                : "#0ea5e9",
    "CERT-EU"              : "#2563eb",
    "French Breaches"      : "#f43f5e",
    "Malwarebytes Labs"    : "#dc2626",
    "Naked Security"       : "#7c3aed",
    "We Live Security"     : "#059669",
    "Trend Micro"          : "#d97706",
    "Recorded Future Blog" : "#0891b2",
    "Cybereason"           : "#9333ea",
    "OSINT Curious"        : "#16a34a",
    "Bellingcat"           : "#ca8a04",
    "Intel471"             : "#0284c7",
    "Shodan Blog"          : "#b91c1c",
    "Maltego Blog"         : "#7e22ce",
    "NixIntel"             : "#15803d",
    "Sector035"            : "#b45309",
    "SANS ISC"             : "#1d4ed8",
    "Mandiant Blog"        : "#c2410c",
    "CrowdStrike Blog"     : "#e11d48",
    "Securelist"           : "#4f46e5",
    "Proofpoint"           : "#0369a1",
    "CIRCL"                : "#047857",
    "Abuse.ch"             : "#9f1239",
    "Citizen Lab"          : "#0e7490",
    "The Intercept"        : "#374151",
    "OCCRP"                : "#92400e",
    "GreyNoise Blog"       : "#1e3a5f",
    "Censys Blog"          : "#4338ca",
    "VulnCheck"            : "#166534",
    "AttackerKB"           : "#7f1d1d",
}

SOURCE_GROUPS = {
    "API REST"             : ["NewsAPI"],
    "Cyber generaliste"    : ["The Hacker News","BleepingComputer","CISA Alerts",
                               "Krebs on Security","Dark Reading","SecurityWeek",
                               "Cyber Scoop","Threatpost","Schneier on Security",
                               "The Record","Infosecurity Magazine","Helpnet Security",
                               "Graham Cluley","Zataz","ANSSI","CERT-EU","French Breaches"],
    "Cyber specialise"     : ["Malwarebytes Labs","Naked Security","We Live Security",
                               "Trend Micro","Recorded Future Blog","Cybereason"],
    "OSINT"                : ["OSINT Curious","Bellingcat","Intel471","Shodan Blog",
                               "Maltego Blog","NixIntel","Sector035"],
    "Threat Intelligence"  : ["SANS ISC","Mandiant Blog","CrowdStrike Blog",
                               "Securelist","Proofpoint","CIRCL","Abuse.ch"],
    "Investigation"        : ["Citizen Lab","The Intercept","OCCRP","GreyNoise Blog",
                               "Censys Blog","VulnCheck","AttackerKB"],
}

PLOTLY_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8'),
)

# -------------------------------------------------------
# EN-TETE
# -------------------------------------------------------
st.markdown('<div class="kpi-tag">KPI 1</div>', unsafe_allow_html=True)
st.markdown("### Articles collected per day / per source")
st.markdown("""
<div class="desc-box">
    <b>Objective:</b> Track daily collection volume and compare activity across sources.<br>
    <b>Reading:</b> A spike on a source typically indicates a major event that day.
    A source at 0 may indicate a collection issue or no publications.<br>
    <b>Data source:</b> PostgreSQL -- table <code>mart_k1</code> (computed by dbt).
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# -------------------------------------------------------
# CHARGEMENT TEMPS REEL DEPUIS POSTGRESQL
# -------------------------------------------------------
col_refresh, col_status = st.columns([1, 4])

with col_refresh:
    if st.button("Refresh", type="primary", use_container_width=True):
        force_refresh()
        st.rerun()

try:
    df = get_mart_k1()
    nb_lignes = len(df)

    with col_status:
        st.markdown(
            f"<div class='status-bar'>"
            f"Source: <span style='color:#22c55e'>PostgreSQL (mart_k1)</span>"
            f" &nbsp;·&nbsp; <b style='color:#e2e8f0'>{nb_lignes:,}</b> rows"
            f" &nbsp;·&nbsp; Cache TTL 2 min"
            f" &nbsp;·&nbsp; Read at: "
            f"<span style='color:#94a3b8'>{datetime.now().strftime('%H:%M:%S')}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

except Exception as e:
    st.error(
        f"Could not connect to PostgreSQL: {e}\n\n"
        "Check that Docker is running: `docker compose up -d`"
    )
    st.stop()

if df.empty:
    st.warning(
        "mart_k1 is empty. "
        "Run `python db/load_to_db.py` then `dbt run` from the dbt/ folder."
    )
    st.stop()

# -------------------------------------------------------
# FILTRES
# -------------------------------------------------------
sources_dispo = sorted(df['source'].dropna().unique().tolist())

col1, col2, col3 = st.columns(3)

with col1:
    groupes_dispo = ["All groups"] + [
        g for g, srcs in SOURCE_GROUPS.items()
        if any(s in sources_dispo for s in srcs)
    ]
    groupe_sel = st.selectbox("Source group", groupes_dispo, key="k1_groupe")

    if groupe_sel == "All groups":
        sources = sources_dispo
    else:
        sources = [s for s in SOURCE_GROUPS.get(groupe_sel, []) if s in sources_dispo]

    sel_sources = st.multiselect(
        "Sources to display", sources, default=sources, key="k1_src"
    )

with col2:
    viz_type = st.radio(
        "Chart type",
        ["Stacked bars", "Lines"],
        horizontal=True,
        key="k1_viz"
    )

with col3:
    mode_date = st.radio(
        "Period",
        ["Last 7 days", "Last 14 days", "Last 30 days", "Choose a date"],
        horizontal=False,
        key="k1_mode"
    )

# Calcul de la fenetre temporelle
date_max_sel = None

if mode_date == "Last 7 days":
    n_days   = 7
    date_cut = pd.Timestamp.now() - pd.Timedelta(days=7)
elif mode_date == "Last 14 days":
    n_days   = 14
    date_cut = pd.Timestamp.now() - pd.Timedelta(days=14)
elif mode_date == "Last 30 days":
    n_days   = 30
    date_cut = pd.Timestamp.now() - pd.Timedelta(days=30)
else:
    date_min_data = df['published_date'].min().date()
    date_max_data = df['published_date'].max().date()
    date_pick = st.date_input(
        "Select a date range",
        value=(date_max_data - pd.Timedelta(days=7), date_max_data),
        min_value=date_min_data,
        max_value=date_max_data,
        key="k1_datepick"
    )
    if len(date_pick) == 2:
        date_cut     = pd.Timestamp(date_pick[0])
        date_max_sel = pd.Timestamp(date_pick[1])
        n_days       = (date_pick[1] - date_pick[0]).days
    else:
        date_cut = pd.Timestamp.now() - pd.Timedelta(days=7)
        n_days   = 7

if not sel_sources:
    st.warning("Please select at least one source.")
    st.stop()

# -------------------------------------------------------
# FILTRAGE (mart_k1 est deja agrege : published_date / source / nb_articles)
# -------------------------------------------------------
mask_src  = df['source'].isin(sel_sources)
mask_date = df['published_date'] >= date_cut

if date_max_sel is not None:
    mask_date = mask_date & (df['published_date'] <= date_max_sel)

agg = df[mask_src & mask_date].copy()

if agg.empty:
    # Fallback: all available data for selected sources
    agg = df[mask_src].copy()
    st.info(
        "No data for the selected time window "
        "-- showing all available data."
    )

agg['date'] = agg['published_date'].dt.strftime('%Y-%m-%d')
agg = agg[['date', 'source', 'nb_articles']].copy()

# Total par jour (tendance globale)
agg_total = agg.groupby('date')['nb_articles'].sum().reset_index()
agg_total.columns = ['date', 'total']

# -------------------------------------------------------
# GRAPHIQUE PRINCIPAL
# -------------------------------------------------------
if viz_type == "Stacked bars":
    fig = px.bar(
        agg, x='date', y='nb_articles', color='source',
        color_discrete_map=COLORS,
        barmode='stack',
        title=f"Articles collected per day -- last {n_days} days (stacked bars)",
        labels={'nb_articles': 'Articles', 'date': 'Date', 'source': 'Source'}
    )
else:
    fig = px.line(
        agg, x='date', y='nb_articles', color='source',
        color_discrete_map=COLORS,
        markers=True,
        title=f"Articles collected per day -- last {n_days} days (lines)",
        labels={'nb_articles': 'Articles', 'date': 'Date', 'source': 'Source'}
    )

# Global trend line
fig.add_trace(go.Scatter(
    x=agg_total['date'], y=agg_total['total'],
    mode='lines', name='Global trend',
    line=dict(color='#ffffff', width=1.5, dash='dot'),
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

# -------------------------------------------------------
# HEATMAP ACTIVITE PAR SOURCE PAR JOUR
# -------------------------------------------------------
st.markdown("---")
st.markdown("**Activity by source and day**")
st.markdown(
    "<div style='color:#64748b;font-size:0.82rem;margin-bottom:12px'>"
    "Publication intensity per source per day. "
    "The darker the colour, the more active the source was that day."
    "</div>",
    unsafe_allow_html=True
)

heatmap_data = agg.pivot_table(
    index='source', columns='date',
    values='nb_articles', aggfunc='sum', fill_value=0
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
    hovertemplate='<b>%{y}</b><br>Date: %{x}<br>Articles: %{z}<extra></extra>',
    text=heatmap_data.values,
    texttemplate='%{text}',
    textfont=dict(size=11, color='white'),
    showscale=True,
    colorbar=dict(title='Articles', tickfont=dict(color='#94a3b8')),
))

fig_heat.update_layout(
    **PLOTLY_BASE,
    xaxis=dict(gridcolor='#1e2a42', title='Date', tickangle=-30),
    yaxis=dict(gridcolor='#1e2a42', title=''),
    margin=dict(l=20, r=20, t=20, b=60),
    height=60 + len(heatmap_data) * 42,
)
st.plotly_chart(fig_heat, use_container_width=True)

with st.expander("View detailed data table"):
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

# -------------------------------------------------------
# CAMEMBERT + METRIQUES PAR SOURCE
# -------------------------------------------------------
st.markdown("---")
col_pie, col_stats = st.columns([1, 1.6])

with col_pie:
    st.markdown("**Source market share**")
    agg_src = agg.groupby('source')['nb_articles'].sum().reset_index()
    fig_pie = px.pie(
        agg_src, names='source', values='nb_articles',
        color='source', color_discrete_map=COLORS,
        hole=0.45,
        title=f"Overall distribution over {n_days} days"
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
    st.markdown("**Summary by source**")
    total_global = agg['nb_articles'].sum()
    cols_metrics = st.columns(min(len(sel_sources), 3))
    for i, src in enumerate(sel_sources):
        src_data = agg[agg['source'] == src]
        total    = int(src_data['nb_articles'].sum())
        avg      = round(src_data['nb_articles'].mean(), 1) if total > 0 else 0
        pct_src  = round(total / total_global * 100, 1) if total_global > 0 else 0
        col_idx  = i % 3
        cols_metrics[col_idx].markdown(f"""
        <div class="metric-card" style="margin-bottom:10px">
            <div class="metric-val">{total}</div>
            <div class="metric-lbl">{src}</div>
            <div class="metric-sub">{pct_src}% &nbsp;·&nbsp; ~{avg}/day</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------
# INSIGHTS AUTOMATIQUES
# -------------------------------------------------------
if not agg.empty and total_global > 0:
    top_source = agg.groupby('source')['nb_articles'].sum().idxmax()
    top_total  = int(agg.groupby('source')['nb_articles'].sum().max())
    top_day    = agg.loc[agg['nb_articles'].idxmax()]

    st.markdown(f"""
    <div class="insight-box">
        <b>Insights:</b><br>
        Total collected over the period: <b>{int(total_global):,}</b> articles.<br>
        Most active source: <b>{top_source}</b> with <b>{top_total}</b> articles
        ({round(top_total / total_global * 100, 1)}% of total).<br>
        Collection peak: <b>{top_day['date']}</b> --
        <b>{int(top_day['nb_articles'])}</b> articles from <b>{top_day['source']}</b>.
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------
# DETAIL ARTICLES PAR SOURCE (depuis stg_articles)
# -------------------------------------------------------
st.markdown("---")
st.markdown("**Recent articles by source**")
st.markdown(
    "<div style='color:#64748b;font-size:0.82rem;margin-bottom:12px'>"
    "Select a source to display its most recent articles "
    "(read in real time from stg_articles)."
    "</div>",
    unsafe_allow_html=True
)

src_select = st.selectbox(
    "Choose a source",
    options=["-- Select --"] + sorted(sel_sources),
    key="k1_src_detail"
)

if src_select != "-- Select --":
    try:
        df_articles = get_stg_articles(limit=2000)
        df_detail   = df_articles[df_articles['source'] == src_select].copy()
        df_detail   = df_detail.sort_values('published_date', ascending=False)
    except Exception as e:
        st.error(f"Error reading stg_articles: {e}")
        df_detail = pd.DataFrame()

    if df_detail.empty:
        st.info(f"No articles available for {src_select}.")
    else:
        couleur = COLORS.get(src_select, "#3b82f6")
        st.markdown(f"""
        <div style='background:#0f1422;border:1px solid #1e2a42;
        border-left:3px solid {couleur};border-radius:8px;
        padding:12px 18px;margin-bottom:16px'>
            <span style='font-family:IBM Plex Mono,monospace;font-size:0.8rem;
            color:{couleur}'>{src_select.upper()}</span>
            <span style='color:#64748b;font-size:0.8rem'>
             -- {len(df_detail)} articles available
            </span>
        </div>
        """, unsafe_allow_html=True)

        for _, row in df_detail.head(20).iterrows():
            titre = str(row.get('title', 'No title'))
            url   = str(row.get('url', ''))
            date  = str(row.get('published_date', ''))[:10]
            cat   = str(row.get('category', 'general'))
            lien  = (
                f'<a href="{url}" target="_blank" '
                f'style="color:#e2e8f0;text-decoration:none">{titre}</a>'
                if url and url != 'nan' else titre
            )
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
            st.caption(f"... and {len(df_detail) - 20} more articles not shown.")

# -------------------------------------------------------
# EXPORT CSV
# -------------------------------------------------------
st.markdown("---")
export_df = agg.copy()
export_df.columns = ['date', 'source', 'nb_articles']
csv = export_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download data (CSV)",
    data=csv,
    file_name=f"kpi1_articles_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv"
)
