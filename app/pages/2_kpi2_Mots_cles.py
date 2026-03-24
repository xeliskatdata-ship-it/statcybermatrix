"""
CyberPulse — KPI 2
Mots-clés cyber — cartes + tableau articles
Chargement depuis PostgreSQL via get_mart_k2() + get_stg_articles()
"""

import json
import re
import time

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ── Import fonctions PostgreSQL ──────────────────────────────────────────────
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), '..', '..', 'src'))
from db_connect import get_mart_k2, get_stg_articles, force_refresh

# ── Config page ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="KPI 2 - Keywords", layout="wide")

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

/* Badge statut source */
.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'IBM Plex Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#22c55e;background:rgba(34,197,94,.08);border:1px solid rgba(34,197,94,.2);
border-radius:20px;padding:4px 12px;}
.badge-err{display:inline-flex;align-items:center;gap:6px;font-family:'IBM Plex Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;
color:#ef4444;background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);
border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;
animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}

/* Cartes mots-clés */
.card-wrap { margin-bottom: 8px; }
.card-wrap button {
    width: 100% !important;
    min-height: 90px !important;
    border-radius: 12px !important;
    border: 1px solid #1e2a42 !important;
    background: #0f1422 !important;
    color: #94a3b8 !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    padding: 12px !important;
    text-align: center !important;
    white-space: pre-wrap !important;
    line-height: 1.6 !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
}
.card-wrap button:hover {
    border-color: #3b82f6 !important;
    background: rgba(59,130,246,0.08) !important;
    color: #e2e8f0 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4) !important;
}
.cat-red    button { border-left: 3px solid #ef4444 !important; }
.cat-blue   button { border-left: 3px solid #3b82f6 !important; }
.cat-amber  button { border-left: 3px solid #f59e0b !important; }
.cat-purple button { border-left: 3px solid #a855f7 !important; }

.cat-red.active    button { background: rgba(239,68,68,0.15) !important;  border-color: #ef4444 !important; color:#fca5a5 !important; }
.cat-blue.active   button { background: rgba(59,130,246,0.15) !important; border-color: #3b82f6 !important; color:#93c5fd !important; }
.cat-amber.active  button { background: rgba(245,158,11,0.15) !important; border-color: #f59e0b !important; color:#fcd34d !important; }
.cat-purple.active button { background: rgba(168,85,247,0.15) !important; border-color: #a855f7 !important; color:#d8b4fe !important; }

.cat-inactive button { opacity: 0.3 !important; cursor: default !important; }

.section-head {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem; letter-spacing: .18em;
    text-transform: uppercase;
    padding: 6px 0 10px 10px;
    border-left: 3px solid;
    margin: 20px 0 8px;
}
</style>
""", unsafe_allow_html=True)

# ── Dictionnaire 4 catégories (définition locale, stable) ───────────────────
CATEGORIES = {
    "failles": {
        "label"  : "Vulnerabilities & Exploits",
        "color"  : "#ef4444",
        "css"    : "cat-red",
        "subcats": {
            "Vulnerabilities": ["zero-day", "0-day", "cve", "rce",
                               "remote code execution", "lpe", "privilege escalation"],
            "Techniques"    : ["sql injection", "xss", "cross-site scripting",
                               "buffer overflow", "man-in-the-middle", "mitm",
                               "supply chain attack", "supply chain"],
            "Data Leaks"        : ["data breach", "database dump", "leaked credentials",
                               "exfiltration", "data leak", "exposed credentials"],
        },
    },
    "infra": {
        "label"  : "Infrastructures",
        "color"  : "#3b82f6",
        "css"    : "cat-blue",
        "subcats": {
            "Cloud"   : ["aws", "s3 bucket", "azure", "azure ad",
                         "google cloud", "gcp", "kubernetes", "docker"],
            "Systems": ["active directory", "windows server", "linux kernel",
                         "macos", "tcc"],
            "Networks" : ["vpn", "firewall", "sd-wan", "dns tunneling",
                         "firewall bypass", "vpn gateway"],
        },
    },
    "editeurs": {
        "label"  : "Critical Vendors",
        "color"  : "#f59e0b",
        "css"    : "cat-amber",
        "subcats": {
            "Hardware": ["cisco", "fortinet", "palo alto", "check point",
                         "juniper", "ubiquiti", "f5"],
            "Software": ["microsoft 365", "exchange", "vmware", "esxi",
                         "citrix", "sap", "salesforce", "atlassian",
                         "confluence", "jira"],
        },
    },
    "menaces": {
        "label"  : "Threats & APT",
        "color"  : "#a855f7",
        "css"    : "cat-purple",
        "subcats": {
            "Malware"     : ["ransomware", "infostealer", "trojan", "rat",
                             "botnet", "wiper", "malware"],
            "APT Groups" : ["apt28", "lazarus", "lockbit", "revil",
                             "fancy bear", "scattered spider", "volt typhoon"],
            "Indicators" : ["ioc", "indicator of compromise", "ttp",
                             "threat intelligence", "threat actor"],
        },
    },
}

# ── En-tête ──────────────────────────────────────────────────────────────────
st.markdown('<div class="kpi-tag">KPI 2</div>', unsafe_allow_html=True)
st.markdown("### Keyword monitoring")
st.markdown("""
<div class="desc-box">
    Click on a keyword to immediately display
    all associated articles with their links.
    Grey cards = absent from the current period.
    <br>Data loaded from <strong>mart_k2</strong> (PostgreSQL).
</div>
""", unsafe_allow_html=True)

# ── Bouton Rafraîchir + badge statut ─────────────────────────────────────────
col_refresh, col_badge, _ = st.columns([1, 2, 5])
with col_refresh:
    if st.button("⟳ Refresh", key="k2_refresh"):
        force_refresh()
        st.rerun()

# ── Chargement mart_k2 depuis PostgreSQL ─────────────────────────────────────
# mart_k2 colonnes attendues :
#   keyword       TEXT    — mot-clé
#   category      TEXT    — ex. "failles"
#   sub_category  TEXT    — ex. "Vulnerabilities"
#   period_days   INT     — 3, 7, 15 ou 30
#   occurrences   INT     — nb occurrences dans la période
#   article_count INT     — nb articles distincts contenant le mot-clé

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

with col_badge:
    if load_ok:
        st.markdown(
            f'<div class="badge-live"><span class="dot-live"></span>'
            f'PostgreSQL · {load_ts}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="badge-err">✗ Connection error</div>',
            unsafe_allow_html=True,
        )

if not load_ok:
    st.error(f"Unable to load mart_k2: {load_err}")
    st.stop()

if df_raw.empty:
    st.warning("mart_k2 is empty. Check your dbt pipeline.")
    st.stop()

# ── Helpers : lecture directe depuis mart_k2 ─────────────────────────────────

def get_counts(df_k2: pd.DataFrame, period: int) -> dict:
    """Renvoie {keyword: occurrences} pour une période donnée."""
    sub = df_k2[df_k2["period_days"] == period]
    return dict(zip(sub["keyword"], sub["occurrences"].fillna(0).astype(int)))


def get_article_counts(df_k2: pd.DataFrame, period: int) -> dict:
    """Renvoie {keyword: article_count} pour une période donnée."""
    sub = df_k2[df_k2["period_days"] == period]
    return dict(zip(sub["keyword"], sub["article_count"].fillna(0).astype(int)))


# Période affichée dans le slider → sélection cohérente
PERIODS = {3: "3j", 7: "7j", 15: "15j", 30: "30j"}

counts_all = {p: get_counts(df_raw, p)       for p in PERIODS}
art_counts_all = {p: get_article_counts(df_raw, p) for p in PERIODS}

# Période sélectionnée par l'utilisateur (slider → valeur entière)
col_sl, _ = st.columns([1, 3])
with col_sl:
    n_days = st.slider(
        "Display window (days)",
        min_value=3, max_value=30,
        value=7,
        step=1,
        key="k2_days",
        help="Filters the reference window for cards and the articles panel.",
    )

# Période normalisée sur les valeurs disponibles dans mart_k2
_avail = sorted(PERIODS.keys())
period_sel = min(_avail, key=lambda p: abs(p - n_days))

counts       = counts_all[period_sel]
art_counts   = art_counts_all[period_sel]

# ── KPIs résumés ─────────────────────────────────────────────────────────────
counts_7j  = counts_all[7]
top_kw     = max(counts_7j, key=counts_7j.get) if any(counts_7j.values()) else "—"
total_7j   = sum(counts_7j.values())
nb_detect  = sum(1 for v in counts_7j.values() if v > 0)
nb_articles_total = int(
    df_raw[df_raw["period_days"] == 7]["article_count"].sum()
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Keywords detected (7d)",    nb_detect)
m2.metric("Top keyword (7d)",           top_kw)
m3.metric("Total occurrences (7d)",   total_7j)
m4.metric("Articles matched (7d)",    nb_articles_total)

st.markdown("<br>", unsafe_allow_html=True)

# ── Graphique Chart.js (barres horizontales, multi-période) ──────────────────
kw_cat_map = {
    kw: cat_key
    for cat_key, cat in CATEGORIES.items()
    for kws in cat["subcats"].values()
    for kw in kws
}

data_js     = json.dumps(
    {PERIODS[p]: counts_all[p] for p in PERIODS},
    ensure_ascii=False,
)
cat_map_js  = json.dumps(kw_cat_map, ensure_ascii=False)
cat_cols_js = json.dumps({
    "failles" : "#ef4444",
    "infra"   : "#3b82f6",
    "editeurs": "#f59e0b",
    "menaces" : "#a855f7",
})

chart_css = """
body{margin:0;font-family:system-ui,sans-serif;background:transparent}
.ctrl{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px}
.btn{font-size:12px;padding:4px 14px;border-radius:6px;border:1px solid #334155;
background:transparent;color:#94a3b8;cursor:pointer}
.btn.active{background:#1e2a42;color:#e2e8f0;font-weight:600}
.pill{font-size:12px;padding:3px 10px;border-radius:20px;border:1px solid;
background:transparent;cursor:pointer}
.pill.active{font-weight:600;opacity:1}
select{font-size:12px;padding:4px 8px;border-radius:6px;border:1px solid #334155;
background:#0f1422;color:#94a3b8}
.leg{display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;font-size:12px;color:#64748b}
.dot{width:10px;height:10px;border-radius:2px;flex-shrink:0;display:inline-block}
"""

chart_html = (
    "<style>" + chart_css + "</style>"
    + """
<div class="ctrl">
  <span style="font-size:12px;color:#64748b">Period:</span>
  <button class="btn" onclick="setP('3j')"  id="b3">3j</button>
  <button class="btn active" onclick="setP('7j')" id="b7">7j</button>
  <button class="btn" onclick="setP('15j')" id="b15">15j</button>
  <button class="btn" onclick="setP('30j')" id="b30">30j</button>
  <span style="margin-left:12px;font-size:12px;color:#64748b">Top</span>
  <select id="topN" onchange="render()">
    <option value="10">10</option>
    <option value="15">15</option>
    <option value="20" selected>20</option>
    <option value="30">30</option>
  </select>
  <span style="font-size:12px;color:#64748b">keywords</span>
</div>
<div class="ctrl">
  <span style="font-size:12px;color:#64748b">Category:</span>
  <button class="pill active" onclick="setCat('all')" id="call"
    style="border-color:#475569;color:#94a3b8">All</button>
  <button class="pill" onclick="setCat('failles')" id="cfailles"
    style="border-color:#ef4444;color:#ef4444">Vulnerabilities</button>
  <button class="pill" onclick="setCat('infra')" id="cinfra"
    style="border-color:#3b82f6;color:#3b82f6">Infra</button>
  <button class="pill" onclick="setCat('editeurs')" id="cediteurs"
    style="border-color:#f59e0b;color:#f59e0b">Vendors</button>
  <button class="pill" onclick="setCat('menaces')" id="cmenaces"
    style="border-color:#a855f7;color:#a855f7">Menaces</button>
</div>
<div id="wrap" style="position:relative;width:100%;height:400px">
  <canvas id="kwChart"></canvas>
</div>
<div class="leg" id="leg"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
"""
    + "var DATA=" + data_js + ";"
    + "var CAT_MAP=" + cat_map_js + ";"
    + "var COLS=" + cat_cols_js + ";"
    + """
var period="7j",cat="all",chart=null;
function setP(p){
  period=p;
  ["3j","7j","15j","30j"].forEach(function(x){
    var el=document.getElementById("b"+x.replace("j",""));
    el.classList.toggle("active",x===p);
  });
  render();
}
function setCat(c){
  cat=c;
  ["all","failles","infra","editeurs","menaces"].forEach(function(x){
    document.getElementById("c"+x).classList.toggle("active",x===c);
  });
  render();
}
function render(){
  var topN=parseInt(document.getElementById("topN").value);
  var entries=Object.entries(DATA[period]||{});
  if(cat!=="all") entries=entries.filter(function(e){return CAT_MAP[e[0]]===cat;});
  entries=entries.sort(function(a,b){return b[1]-a[1];}).slice(0,topN);
  var labels=entries.map(function(e){return e[0];});
  var values=entries.map(function(e){return e[1];});
  var colors=labels.map(function(kw){return COLS[CAT_MAP[kw]]||"#64748b";});
  var h=Math.max(320,entries.length*34+60);
  document.getElementById("wrap").style.height=h+"px";
  if(chart) chart.destroy();
  chart=new Chart(document.getElementById("kwChart"),{
    type:"bar",
    data:{labels:labels,datasets:[{
      data:values,
      backgroundColor:colors.map(function(c){return c+"CC";}),
      borderColor:colors,borderWidth:1,borderRadius:4
    }]},
    options:{
      indexAxis:"y",responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{callbacks:{
          label:function(ctx){return " "+ctx.raw+" occurrences";},
          afterLabel:function(ctx){return " category: "+(CAT_MAP[ctx.label]||"—");}
        }}
      },
      scales:{
        x:{grid:{color:"rgba(255,255,255,0.06)"},ticks:{color:"#64748b",font:{size:12}}},
        y:{grid:{display:false},ticks:{color:"#94a3b8",font:{size:12},autoSkip:false}}
      }
    }
  });
  document.getElementById("leg").innerHTML=Object.entries(COLS)
    .map(function(e){
      return '<span><span class="dot" style="background:'+e[1]+'"></span>'+e[0]+'</span>';
    }).join("");
}
render();
</script>
"""
)

components.html(chart_html, height=520, scrolling=False)

st.markdown("---")

# ── Layout : cartes gauche · articles droite ─────────────────────────────────
col_cards, col_articles = st.columns([1.4, 1.6], gap="large")

with col_cards:
    for cat_key, cat in CATEGORIES.items():
        st.markdown(
            f'<div class="section-head" style="color:{cat["color"]};border-color:{cat["color"]}">'
            f'{cat["label"].upper()}</div>',
            unsafe_allow_html=True,
        )
        for sub, keywords in cat["subcats"].items():
            st.caption(sub)
            cols = st.columns(4)
            for i, kw in enumerate(keywords):
                n_occ  = counts.get(kw, 0)
                n_art  = art_counts.get(kw, 0)
                active = n_art > 0
                sel    = st.session_state.get("k2_selected") == kw

                css_cls = cat["css"]
                if sel:
                    css_cls += " active"
                elif not active:
                    css_cls = "cat-inactive"

                with cols[i % 4]:
                    st.markdown(f'<div class="card-wrap {css_cls}">', unsafe_allow_html=True)
                    label = (
                        f"{kw}\n▶ {n_art} article(s)"
                        if active
                        else f"{kw}\n—"
                    )
                    if st.button(
                        label,
                        key=f"k_{cat_key}_{sub}_{kw}",
                        use_container_width=True,
                        disabled=not active,
                    ):
                        st.session_state["k2_selected"] = kw
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            st.write("")

# ── Panneau articles ──────────────────────────────────────────────────────────
with col_articles:
    selected = st.session_state.get("k2_selected")

    if not selected:
        st.markdown("""
        <div style='text-align:center;padding:80px 20px;color:#475569'>
            <div style='font-size:2.5rem;margin-bottom:16px'>🔍</div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.82rem'>
                Click on a keyword<br>to view its articles
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Articles depuis stg_articles (requête directe PostgreSQL)
        try:
            art_df = get_stg_articles(keyword=selected)
        except Exception as e:
            art_df = pd.DataFrame()
            st.warning(f"Error in get_stg_articles: {e}")

        n_occ = counts.get(selected, 0)

        # Couleur de la catégorie du mot-clé
        cat_color = "#3b82f6"
        for cat in CATEGORIES.values():
            for kws in cat["subcats"].values():
                if selected in kws:
                    cat_color = cat["color"]
                    break

        st.markdown(f"""
        <div style='background:#0f1422;border:1px solid #1e2a42;
        border-top:3px solid {cat_color};border-radius:12px;
        padding:18px 20px;margin-bottom:16px'>
            <div style='font-family:IBM Plex Mono,monospace;font-size:1.1rem;
            font-weight:700;color:{cat_color}'>{selected}</div>
            <div style='font-size:0.78rem;color:#64748b;margin-top:4px'>
                {n_occ} occurrence(s) · {len(art_df)} article(s) with link
                · period {period_sel}d
            </div>
        </div>
        """, unsafe_allow_html=True)

        if art_df.empty:
            st.info("No articles with a valid URL for this keyword.")
        else:
            # Normalisation colonnes (get_stg_articles retourne title/source/url)
            art_df = art_df[["title", "source", "url"]].copy()
            art_df.columns = ["Titre", "Source", "URL"]
            # Filtrer les URL vides
            art_df = art_df[
                art_df["URL"].notna()
                & (art_df["URL"].astype(str).str.strip() != "")
                & (art_df["URL"].astype(str) != "nan")
            ].reset_index(drop=True)

            st.dataframe(
                art_df,
                use_container_width=True,
                hide_index=True,
                height=min(650, 44 + len(art_df) * 38),
                column_config={
                    "Titre" : st.column_config.TextColumn("Title",  width="large"),
                    "Source": st.column_config.TextColumn("Source", width="small"),
                    "URL"   : st.column_config.LinkColumn(
                        "Link",
                        display_text="↗ Open",
                        width="small",
                    ),
                },
            )

        if st.button("✕ Clear selection", key="k2_close"):
            del st.session_state["k2_selected"]
            st.rerun()

# ── Export CSV horodaté ───────────────────────────────────────────────────────
st.markdown("---")

rows = [
    {
        "categorie"  : cat["label"],
        "sous_cat"   : sub,
        "mot_cle"    : kw,
        "occurrences": counts.get(kw, 0),
        "articles"   : art_counts.get(kw, 0),
        "periode_j"  : period_sel,
    }
    for cat_key, cat in CATEGORIES.items()
    for sub, kws in cat["subcats"].items()
    for kw in kws
]
df_export = pd.DataFrame(rows).sort_values(
    ["categorie", "occurrences"], ascending=[True, False]
)

ts = time.strftime("%Y%m%d_%H%M%S")
st.download_button(
    "⬇ Download keywords (CSV)",
    df_export.to_csv(index=False).encode("utf-8"),
    file_name=f"kpi2_mots_cles_{ts}.csv",
    mime="text/csv",
)
