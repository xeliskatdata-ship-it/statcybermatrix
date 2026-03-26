"""
CyberPulse — KPI 2
Suivi des mots-clés cyber
Chargement depuis PostgreSQL via get_mart_k2()
"""

import time
import pandas as pd
import plotly.express as px
import streamlit as st

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k2, force_refresh

st.set_page_config(page_title="KPI 2 - Mots-clés", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
.stApp{
    background-image: url("data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAMCAgMCAgMDAwMEAwMEBQgFBQQEBQoHBwYIDAoMDAsKCwsNDhIQDQ4RDgsLEBYQERMUFRUVDA8XGBYUGBIUFRT/wAARCANcBgwDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL") !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    background: rgba(5, 10, 20, 0.75);
    z-index: 0;
    pointer-events: none;
}
[data-testid="stAppViewContainer"] > * { position: relative; z-index: 1; }
[data-testid="stSidebar"]{background:#0f1422!important;border-right:1px solid #1e2a42;}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}

.kpi-tag{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#22c55e;background:rgba(34,197,94,.1);
border:1px solid rgba(34,197,94,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}

.desc-box{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #22c55e;
border-radius:8px;padding:14px 18px;margin-bottom:24px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}

.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'IBM Plex Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.badge-err{display:inline-flex;align-items:center;gap:6px;font-family:'IBM Plex Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#ef4444;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
</style>
""", unsafe_allow_html=True)

# ── En-tête ───────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 2</div>', unsafe_allow_html=True)
st.markdown("### Suivi des mots-clés")
st.markdown("""
<div class="desc-box">
    Cliquez sur un mot-clé pour afficher immédiatement tous les articles associés avec leurs liens.<br>
    Cellule grise : 0 article sur la période sélectionnée.
</div>
""", unsafe_allow_html=True)

# ── Refresh + badge ───────────────────────────────────────────────────────────
col_r, col_b, _ = st.columns([1, 2, 5])
with col_r:
    if st.button("⟳ Actualiser", use_container_width=True):
        force_refresh()
        st.rerun()

# ── Chargement ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_mart_k2():
    return get_mart_k2()

try:
    df_raw = load_mart_k2()
    load_ok = True
    load_ts = time.strftime("%H:%M:%S")
except Exception as e:
    load_ok = False
    load_err = str(e)

with col_b:
    if load_ok:
        st.markdown(
            f'<div class="badge-live"><span class="dot-live"></span>'
            f'PostgreSQL · {load_ts}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown('<div class="badge-err">✗ Erreur de connexion</div>', unsafe_allow_html=True)

if not load_ok:
    st.error(f"Impossible de charger mart_k2 : {load_err}")
    st.stop()

if df_raw.empty:
    st.warning("mart_k2 est vide. Vérifiez votre pipeline dbt.")
    st.stop()

# ── Catégories ────────────────────────────────────────────────────────────────
CATEGORIES = {
    "failles": {
        "label": "Vulnerabilities & Exploits", "color": "#ef4444",
        "subcats": {
            "Vulnerabilities": ["zero-day", "0-day", "cve", "rce", "remote code execution", "lpe", "privilege escalation"],
            "Techniques": ["sql injection", "xss", "cross-site scripting", "buffer overflow", "man-in-the-middle", "mitm", "supply chain attack", "supply chain"],
            "Data Leaks": ["data breach", "database dump", "leaked credentials", "exfiltration", "data leak", "exposed credentials"],
        },
    },
    "infra": {
        "label": "Infrastructures", "color": "#3b82f6",
        "subcats": {
            "Cloud": ["aws", "s3 bucket", "azure", "azure ad", "google cloud", "gcp", "kubernetes", "docker"],
            "Systems": ["active directory", "windows server", "linux kernel", "macos", "tcc"],
            "Networks": ["vpn", "firewall", "sd-wan", "dns tunneling", "firewall bypass", "vpn gateway"],
        },
    },
    "editeurs": {
        "label": "Critical Vendors", "color": "#f59e0b",
        "subcats": {
            "Hardware": ["cisco", "fortinet", "palo alto", "check point", "juniper", "ubiquiti", "f5"],
            "Software": ["microsoft 365", "exchange", "vmware", "esxi", "citrix", "sap", "salesforce", "atlassian", "confluence", "jira"],
        },
    },
    "menaces": {
        "label": "Threats & APT", "color": "#a855f7",
        "subcats": {
            "Malware": ["ransomware", "infostealer", "trojan", "rat", "botnet", "wiper", "malware"],
            "APT Groups": ["apt28", "lazarus", "lockbit", "revil", "fancy bear", "scattered spider", "volt typhoon"],
            "Indicators": ["ioc", "indicator of compromise", "ttp", "threat intelligence", "threat actor"],
        },
    },
}

PERIODS = {3: "3j", 7: "7j", 15: "15j", 30: "30j"}
CAT_COLORS = {"failles": "#ef4444", "infra": "#3b82f6", "editeurs": "#f59e0b", "menaces": "#a855f7"}

kw_cat_map = {
    kw: cat_key
    for cat_key, cat in CATEGORIES.items()
    for kws in cat["subcats"].values()
    for kw in kws
}

def get_counts(df, period):
    sub = df[df["period_days"] == period]
    return dict(zip(sub["keyword"], sub["occurrences"].fillna(0).astype(int)))

def get_article_counts(df, period):
    sub = df[df["period_days"] == period]
    return dict(zip(sub["keyword"], sub["article_count"].fillna(0).astype(int)))

def get_source_counts(df, period):
    sub = df[df["period_days"] == period]
    if "source_count" in sub.columns:
        return dict(zip(sub["keyword"], sub["source_count"].fillna(0).astype(int)))
    return {}

counts_all     = {p: get_counts(df_raw, p)        for p in PERIODS}
art_counts_all = {p: get_article_counts(df_raw, p) for p in PERIODS}
src_counts_all = {p: get_source_counts(df_raw, p)  for p in PERIODS}

# ── Slider période ────────────────────────────────────────────────────────────
col_sl, _ = st.columns([1, 3])
with col_sl:
    n_days = st.slider("Période d'affichage (jours)", min_value=3, max_value=30, value=7, step=1, key="k2_days")

_avail = sorted(PERIODS.keys())
period_sel = min(_avail, key=lambda p: abs(p - n_days))

counts     = counts_all[period_sel]
art_counts = art_counts_all[period_sel]
src_counts = src_counts_all[period_sel]

# ── Métriques résumées ────────────────────────────────────────────────────────
counts_7j = counts_all[7]
top_kw    = max(counts_7j, key=counts_7j.get) if any(counts_7j.values()) else "—"
total_7j  = sum(counts_7j.values())
nb_detect = sum(1 for v in counts_7j.values() if v > 0)
nb_articles_total = int(df_raw[df_raw["period_days"] == 7]["article_count"].sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Mots-clés détectés (7j)",    nb_detect)
m2.metric("Mot-clé le plus recherché (7j)", top_kw)
m3.metric("Total occurrences (7j)",    total_7j)
m4.metric("Articles correspondants (7j)", nb_articles_total)

st.markdown("<br>", unsafe_allow_html=True)

# ── Graphique Plotly ──────────────────────────────────────────────────────────
col_chart, col_opts = st.columns([4, 1])

with col_opts:
    top_n = st.selectbox("Top N", [10, 15, 20, 30], index=2, key="k2_topn")
    cat_filter = st.selectbox(
        "Catégorie",
        ["Toutes", "Vulnerabilities", "Infra", "Vendors", "Menaces"],
        key="k2_cat"
    )

cat_filter_map = {
    "Toutes": None, "Vulnerabilities": "failles",
    "Infra": "infra", "Vendors": "editeurs", "Menaces": "menaces"
}

entries = sorted(counts.items(), key=lambda x: x[1], reverse=True)
df_chart = pd.DataFrame(entries, columns=["keyword", "occurrences"])
df_chart["category"] = df_chart["keyword"].map(kw_cat_map)

if cat_filter_map[cat_filter]:
    df_chart = df_chart[df_chart["category"] == cat_filter_map[cat_filter]]

df_chart = df_chart.head(top_n).sort_values("occurrences")

with col_chart:
    fig = px.bar(
        df_chart, x="occurrences", y="keyword",
        orientation="h", color="category",
        color_discrete_map=CAT_COLORS,
        title=f"Top {top_n} mots-clés — {PERIODS[period_sel]}",
        labels={"occurrences": "Occurrences", "keyword": "", "category": "Catégorie"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,10,20,0.6)",
        font=dict(family="IBM Plex Sans", color="#94a3b8"),
        xaxis=dict(gridcolor="#1e2a42"),
        yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        legend_title="Catégorie",
        margin=dict(l=20, r=20, t=50, b=20),
        height=max(400, top_n * 28),
    )
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

# ── Export CSV ────────────────────────────────────────────────────────────────
st.markdown("---")
rows = [
    {
        "categorie"  : cat["label"],
        "sous_cat"   : sub,
        "mot_cle"    : kw,
        "occurrences": counts.get(kw, 0),
        "articles"   : art_counts.get(kw, 0),
        "sources"    : src_counts.get(kw, 0),
        "periode_j"  : period_sel,
    }
    for cat_key, cat in CATEGORIES.items()
    for sub, kws in cat["subcats"].items()
    for kw in kws
]
df_export = pd.DataFrame(rows).sort_values(["categorie", "occurrences"], ascending=[True, False])

import time as _time
ts = _time.strftime("%Y%m%d_%H%M%S")
st.download_button(
    "⬇ Télécharger les données (CSV)",
    df_export.to_csv(index=False).encode("utf-8"),
    file_name=f"kpi2_mots_cles_{ts}.csv",
    mime="text/csv",
)
