import streamlit as st
import pandas as pd
import os
import sys

# Ajout src/ au path pour importer utils_lang
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils_lang import t, translate_dataframe

# ---------------------------------------------------
# CONFIGURATION PAGE
# ---------------------------------------------------
st.set_page_config(
    page_title="CyberPulse",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------
# STYLE
# ---------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #0a0e1a; }
[data-testid="stSidebar"] {
    background: #0f1422 !important;
    border-right: 1px solid #1e2a42;
}
[data-testid="stSidebar"] * { color: #a8b8d0 !important; }
.metric-card {
    background: #0f1422;
    border: 1px solid #1e2a42;
    border-radius: 8px;
    padding: 18px 22px;
    position: relative;
    overflow: hidden;
}
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 3px; height: 100%;
    background: #3b82f6;
}
.metric-card.green::after  { background: #22c55e; }
.metric-card.orange::after { background: #f59e0b; }
.metric-card.red::after    { background: #ef4444; }
.metric-card.teal::after   { background: #14b8a6; }
.metric-val {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2rem; font-weight: 700; color: #e2e8f0;
}
.metric-lbl { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }
.metric-sub { font-size: 0.8rem; color: #22c55e; margin-top: 6px; }
.section-tag {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem; letter-spacing: 0.15em; text-transform: uppercase;
    color: #3b82f6; background: rgba(59,130,246,0.1);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 4px; padding: 3px 10px; margin-bottom: 14px;
}
.banner {
    background: linear-gradient(135deg, #0f1422 0%, #111827 60%, #0d1b2a 100%);
    border: 1px solid #1e2a42; border-radius: 12px;
    padding: 32px 36px; margin-bottom: 28px;
}
.banner-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.2rem; font-weight: 700; color: #e2e8f0;
}
.banner-sub { font-size: 0.95rem; color: #64748b; margin-top: 6px; }
.live-dot {
    display: inline-block; width: 7px; height: 7px;
    background: #22c55e; border-radius: 50%; margin-right: 7px;
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# CHARGEMENT DES DONNEES
# ---------------------------------------------------
@st.cache_data
def load_data():
    cleaned_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
    files = [f for f in os.listdir(cleaned_dir) if f.startswith('articles_cleaned')]
    if not files:
        return pd.DataFrame()
    latest   = sorted(files)[-1]
    filepath = os.path.join(cleaned_dir, latest)
    df = pd.read_csv(filepath, encoding='utf-8')
    df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')
    return df

df = load_data()

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 8px 0'>
        <div style='font-family:IBM Plex Mono,monospace;font-size:1.1rem;
                    font-weight:700;color:#e2e8f0;'>CyberPulse</div>
        <div style='font-size:0.72rem;color:#64748b;margin-top:2px'>
            Veille cyber automatisee
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # --- SELECTEUR DE LANGUE ---
    lang_choice = st.selectbox(
        t("Language", "fr"),
        options=["Francais", "English"],
        index=0,
        key="lang_select"
    )
    lang = "fr" if lang_choice == "Francais" else "en"

    # Stocker la langue en session pour toutes les pages
    st.session_state['lang'] = lang

    st.divider()

    # --- FILTRES ---
    st.markdown(f"**{t('Global filters', lang)}**")

    sources_dispo = sorted(df['source'].dropna().unique().tolist()) if not df.empty else []
    sources_sel = st.multiselect(
        t("Sources", lang),
        options=sources_dispo,
        default=sources_dispo,
        key="global_sources"
    )

    if not df.empty and df['published_date'].notna().any():
        date_min   = df['published_date'].min().date()
        date_max   = df['published_date'].max().date()
        date_range = st.date_input(
            t("Period", lang),
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
            key="global_dates"
        )
    else:
        date_range = None

    cats_dispo = sorted(df['category'].dropna().unique().tolist()) if not df.empty else []
    cats_sel = st.multiselect(
        t("Threat type", lang),
        options=cats_dispo,
        default=cats_dispo,
        key="global_cats"
    )

    st.divider()
    st.markdown(
        f"<div style='font-size:0.72rem;color:#475569'>"
        f"Sprint 2 · Mars 2026<br>{len(df)} {t('Articles loaded', lang)}</div>",
        unsafe_allow_html=True
    )

# ---------------------------------------------------
# FILTRAGE
# ---------------------------------------------------
def apply_filters(dataframe):
    dff = dataframe.copy()
    if sources_sel:
        dff = dff[dff['source'].isin(sources_sel)]
    if cats_sel:
        dff = dff[dff['category'].isin(cats_sel)]
    if date_range and len(date_range) == 2:
        dff = dff[
            (dff['published_date'].dt.date >= date_range[0]) &
            (dff['published_date'].dt.date <= date_range[1])
        ]
    return dff

dff = apply_filters(df)

# Stocker en session pour les pages KPI
st.session_state['df_filtered'] = dff
st.session_state['df_full']     = df

# ---------------------------------------------------
# PAGE D'ACCUEIL
# ---------------------------------------------------
st.markdown(f"""
<div class="banner">
    <div class="banner-title">CyberPulse</div>
    <div class="banner-sub">
        <span class="live-dot"></span>
        {"Veille automatique des menaces cyber" if lang == "fr" else "Automated cyber threat monitoring"}
        &nbsp;·&nbsp; {len(sources_sel)} {t('Sources active', lang)}
        &nbsp;·&nbsp; {len(dff)} {"articles" if lang == "fr" else "articles"}
    </div>
</div>
""", unsafe_allow_html=True)

# --- Metriques ---
st.markdown(f'<div class="section-tag">{t("Overview", lang)}</div>', unsafe_allow_html=True)

c1, c2, c3, c4, c5 = st.columns(5)

total      = len(dff)
nb_sources = dff['source'].nunique()      if not dff.empty else 0
top_cat    = dff['category'].value_counts().index[0] if not dff.empty else "—"
top_source = dff['source'].value_counts().index[0]   if not dff.empty else "—"
moy_len    = int(dff['content_length'].mean())        if not dff.empty else 0

for col, val, lbl, sub, cls in [
    (c1, str(total),      t("Filtered articles", lang), f"{nb_sources} {t('Sources active', lang)}", ""),
    (c2, str(nb_sources), t("Sources active", lang),    "NewsAPI + RSS",                              "green"),
    (c3, top_cat,         t("Top threat", lang),        "by volume" if lang == "en" else "par volume","orange"),
    (c4, top_source,      t("Top source", lang),        "by count"  if lang == "en" else "par nb",    "teal"),
    (c5, str(moy_len),    t("Avg length", lang),        "chars",                                      "red"),
]:
    col.markdown(f"""
    <div class="metric-card {cls}">
        <div class="metric-val">{val}</div>
        <div class="metric-lbl">{lbl}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- Apercu ---
st.markdown(f'<div class="section-tag">{t("Data preview", lang)}</div>', unsafe_allow_html=True)

if not dff.empty:
    cols_affichees = ['source', 'title', 'published_date', 'category', 'content_length']

    # Traduire les titres si langue francaise demandee
    # Note : desactive par defaut car lent sur gros volumes
    # Pour activer : decommenter la ligne suivante
    # dff_display = translate_dataframe(dff, ['title'], lang)

    st.dataframe(
        dff[cols_affichees].sort_values('published_date', ascending=False).head(20),
        use_container_width=True,
        hide_index=True,
        height=380
    )
    st.markdown("<br>", unsafe_allow_html=True)
    csv = dff.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=t("Download CSV", lang),
        data=csv,
        file_name=f"cyberpulse_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )
else:
    st.warning(t("No data", lang))

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f'<div class="section-tag">Navigation</div>', unsafe_allow_html=True)
st.markdown(
    f"<div style='color:#64748b;font-size:0.88rem'>{t('Navigation hint', lang)}</div>",
    unsafe_allow_html=True
)
