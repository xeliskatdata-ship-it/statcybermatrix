"""Build script -- genere 6_KPI6_CVE.py avec le blob base64 injecte."""
import re, pathlib, sys

# --- Extraire le blob depuis KPI3 ---
src = pathlib.Path(__file__).parent / "cyberpulse" / "app" / "pages" / "3_KPI3_Menaces.py"
if not src.exists():
    src = pathlib.Path(__file__).parent / "app" / "pages" / "3_KPI3_Menaces.py"
text = src.read_text(encoding="utf-8")
m = re.search(r'_BG\s*=\s*"(data:image/[^"]+)"', text)
if not m:
    m2 = re.search(r"background-image:\s*url\('(data:image/[^']+)'\)", text)
    if not m2:
        print("ERREUR : blob introuvable dans KPI3"); sys.exit(1)
    blob = m2.group(1)
else:
    blob = m.group(1)

print(f"Blob extrait : {blob[:60]}... ({len(blob)} chars)")

TEMPLATE = r'''"""
CyberPulse -- KPI 6
Top CVE les plus mentionnees + details NVD
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import time
import sys, pathlib
from deep_translator import GoogleTranslator

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_mart_k6, force_refresh

st.set_page_config(page_title="KPI 6 - CVE", layout="wide")

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
letter-spacing:.15em;text-transform:uppercase;color:#a855f7;background:rgba(168,85,247,.1);
border:1px solid rgba(168,85,247,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}}
.desc-box{{background:#0f1422;border:1px solid #1e2a42;border-left:3px solid #a855f7;
border-radius:8px;padding:14px 18px;margin-bottom:20px;color:#94a3b8;font-size:0.88rem;line-height:1.7;}}
.insight-box{{background:rgba(168,85,247,0.07);border:1px solid rgba(168,85,247,0.2);
border-radius:8px;padding:12px 18px;margin-top:16px;color:#d8b4fe;font-size:0.88rem;}}
.warn-box{{background:rgba(245,158,11,0.07);border:1px solid rgba(245,158,11,0.2);
border-radius:8px;padding:12px 16px;margin-top:10px;color:#fcd34d;font-size:0.88rem;}}
.note-box{{background:rgba(100,116,139,0.07);border:1px solid rgba(100,116,139,0.2);
border-radius:8px;padding:10px 16px;margin-top:12px;color:#94a3b8;font-size:0.82rem;}}
.cve-card{{background:#0f1422;border:1px solid #1e2a42;border-radius:10px;padding:20px 24px;margin-top:16px;}}
.cve-card-title{{font-family:'IBM Plex Mono',monospace;font-size:1.1rem;font-weight:700;color:#e2e8f0;}}
.cve-card-score{{font-family:'IBM Plex Mono',monospace;font-size:2rem;font-weight:700;}}
.score-critical{{color:#ef4444;}}
.score-high{{color:#f97316;}}
.score-medium{{color:#f59e0b;}}
.score-low{{color:#22c55e;}}
.cve-desc{{color:#94a3b8;font-size:0.88rem;line-height:1.7;margin-top:10px;}}
.badge{{display:inline-block;border-radius:4px;padding:2px 10px;font-size:0.75rem;font-weight:600;margin-right:6px;}}
.badge-red{{background:rgba(239,68,68,.15);color:#ef4444;border:1px solid rgba(239,68,68,.3);}}
.badge-orange{{background:rgba(249,115,22,.15);color:#f97316;border:1px solid rgba(249,115,22,.3);}}
.badge-yellow{{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid rgba(245,158,11,.3);}}
.badge-green{{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3);}}
.live-dot{{display:inline-block;width:7px;height:7px;border-radius:50%;
background:#22c55e;margin-right:6px;animation:pulse 2s infinite;}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------
# FONCTIONS NVD API
# ---------------------------------------------------
def translate_to_french(text):
    if not text or text == 'N/A':
        return text
    try:
        return GoogleTranslator(source='en', target='fr').translate(str(text))
    except Exception:
        return text


@st.cache_data(ttl=3600)
def fetch_cve_details(cve_id, lang='fr'):
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    try:
        resp = requests.get(url, timeout=10,
                           headers={{"User-Agent": "CyberPulse-Dashboard/1.0"}})
        if resp.status_code != 200:
            return None
        data = resp.json()
        vulns = data.get('vulnerabilities', [])
        if not vulns:
            return None
        cve_data = vulns[0].get('cve', {{}})
        descriptions = cve_data.get('descriptions', [])
        desc_en = next((d['value'] for d in descriptions if d['lang'] == 'en'), 'N/A')
        score    = None
        severity = 'N/A'
        metrics  = cve_data.get('metrics', {{}})
        if 'cvssMetricV31' in metrics:
            m        = metrics['cvssMetricV31'][0]['cvssData']
            score    = m.get('baseScore')
            severity = m.get('baseSeverity', 'N/A')
        elif 'cvssMetricV30' in metrics:
            m        = metrics['cvssMetricV30'][0]['cvssData']
            score    = m.get('baseScore')
            severity = m.get('baseSeverity', 'N/A')
        elif 'cvssMetricV2' in metrics:
            m        = metrics['cvssMetricV2'][0]['cvssData']
            score    = m.get('baseScore')
            severity = metrics['cvssMetricV2'][0].get('baseSeverity', 'N/A')
        configs = cve_data.get('configurations', [])
        produit = 'N/A'
        if configs:
            nodes = configs[0].get('nodes', [])
            if nodes:
                cpe_matches = nodes[0].get('cpeMatch', [])
                if cpe_matches:
                    cpe = cpe_matches[0].get('criteria', '')
                    parts = cpe.split(':')
                    if len(parts) >= 5:
                        produit = f"{{parts[3]}} / {{parts[4]}}"
        refs = [r['url'] for r in cve_data.get('references', [])[:3]]
        published = cve_data.get('published', 'N/A')
        if published != 'N/A':
            published = published[:10]
        description_finale = translate_to_french(desc_en) if lang == 'fr' else desc_en
        return {{
            'id'         : cve_id,
            'description': description_finale,
            'score'      : score,
            'severity'   : severity,
            'produit'    : produit,
            'published'  : published,
            'references' : refs,
        }}
    except Exception:
        return None


def get_score_class(severity):
    mapping = {{
        'CRITICAL': ('score-critical', 'badge-red'),
        'HIGH'    : ('score-high',     'badge-orange'),
        'MEDIUM'  : ('score-medium',   'badge-yellow'),
        'LOW'     : ('score-low',      'badge-green'),
    }}
    return mapping.get(severity, ('score-medium', 'badge-yellow'))


def render_cve_card(details):
    if not details:
        st.warning("Details non disponibles pour cette CVE (API NVD inaccessible ou CVE inconnue).")
        return
    score_class, badge_class = get_score_class(details['severity'])
    score_display = f"{{details['score']:.1f}}" if details['score'] else 'N/A'
    refs_html = ''
    for ref in details['references']:
        refs_html += f'<a href="{{ref}}" target="_blank" style="color:#a855f7;font-size:0.8rem;display:block;margin-top:4px">{{ref[:80]}}...</a>'
    st.markdown(f"""
    <div class="cve-card">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:16px">
            <div>
                <div class="cve-card-title">{{details['id']}}</div>
                <div style="margin-top:8px">
                    <span class="badge {{badge_class}}">{{details['severity']}}</span>
                    <span style="color:#64748b;font-size:0.8rem">Publie le {{details['published']}}</span>
                </div>
                <div style="color:#64748b;font-size:0.82rem;margin-top:6px">
                    Produit affecte : <b style="color:#94a3b8">{{details['produit']}}</b>
                </div>
            </div>
            <div style="text-align:center">
                <div class="cve-card-score {{score_class}}">{{score_display}}</div>
                <div style="font-size:0.7rem;color:#64748b;text-transform:uppercase;letter-spacing:.1em">Score CVSS</div>
            </div>
        </div>
        <div class="cve-desc">{{details['description']}}</div>
        <div style="margin-top:12px;color:#64748b;font-size:0.78rem">References officielles :</div>
        {{refs_html}}
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------
# CHARGEMENT DONNEES
# ---------------------------------------------------
col_h, col_r = st.columns([8, 1])
with col_h:
    st.markdown('<div class="kpi-tag">KPI 6</div>', unsafe_allow_html=True)
    st.markdown("### Top CVE les plus mentionnees")
with col_r:
    if st.button("Rafraichir", key="k6_refresh"):
        force_refresh()
        st.rerun()

st.markdown("""
<div class="desc-box">
    <b>Objectif :</b> Identifier les vulnerabilites officielles (CVE) les plus citees dans les articles collectes.<br>
    <b>Lecture :</b> Une CVE tres mentionnee indique une vulnerabilite activement couverte -- souvent exploitee ou recemment patchee.<br>
    <b>Format CVE :</b> CVE-ANNEE-IDENTIFIANT (ex: CVE-2024-1234) -- standard international MITRE.<br>
    <b>Details :</b> Les scores et descriptions proviennent de l'API officielle NVD (National Vulnerability Database).
</div>
""", unsafe_allow_html=True)
st.markdown("---")

df = get_mart_k6()

if df.empty:
    st.markdown("""
    <div class="warn-box">
        <b>Aucune CVE detectee dans les articles actuels.</b><br><br>
        Explications possibles :<br>
        - Les descriptions sont trop courtes pour contenir des references CVE completes.<br>
        - Relancez la collecte avec acquisition.py pour obtenir de nouveaux articles.<br>
        - Les CVE apparaissent surtout dans les articles CISA Alerts et BleepingComputer.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown(
    f'<span class="live-dot"></span>'
    f'<span style="color:#64748b;font-size:0.78rem">'
    f'Donnees PostgreSQL -- {{len(df)}} CVE disponibles</span>',
    unsafe_allow_html=True
)

# --- Slider top N ---
top_n = st.slider("Nombre de CVE a afficher", 5, min(20, len(df)), min(10, len(df)), key="k6_topn")
agg   = df.head(top_n).copy()
agg.columns = ['CVE', 'Mentions']
agg['Annee'] = agg['CVE'].str.extract(r'CVE-(\d{{4}})-')

# ---------------------------------------------------
# SECTION 1 : TABLEAU + GRAPHIQUE
# ---------------------------------------------------
st.markdown("#### Vue d'ensemble")
col1, col2 = st.columns([1.3, 1])

with col1:
    st.markdown("**Tableau classe**")
    st.dataframe(
        agg[['CVE', 'Mentions', 'Annee']],
        use_container_width=True,
        hide_index=True,
        height=400
    )

with col2:
    fig = go.Figure(go.Bar(
        x=agg['Mentions'], y=agg['CVE'],
        orientation='h',
        marker_color='#a855f7',
        text=agg['Mentions'], textposition='outside',
        textfont=dict(color='#94a3b8')
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='IBM Plex Sans', color='#94a3b8'),
        xaxis=dict(gridcolor='#1e2a42', title='Mentions'),
        yaxis=dict(gridcolor='#1e2a42', autorange='reversed'),
        height=400, showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- Insights ---
total_uniques = len(df)
top_cve       = agg.iloc[0]['CVE']
top_mentions  = agg.iloc[0]['Mentions']

st.markdown(f"""
<div class="insight-box">
    <b>Insights :</b><br>
    - CVE la plus mentionnee : <b>{{top_cve}}</b> ({{top_mentions}} mentions).<br>
    - Total de CVE uniques detectees dans la base : <b>{{total_uniques}}</b>.<br>
    - Annees representees : {{', '.join(sorted(agg['Annee'].dropna().unique(), reverse=True))}}.
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SECTION 2 : FICHE DETAIL PAR CVE
# ---------------------------------------------------
st.markdown("---")
st.markdown("#### Fiche detail d'une CVE")
st.markdown(
    "<div style='color:#64748b;font-size:0.85rem;margin-bottom:12px'>"
    "Selectionnez une CVE pour afficher ses details officiels depuis la base NVD."
    "</div>",
    unsafe_allow_html=True
)

cve_selectionnee = st.selectbox(
    "Choisir une CVE",
    options=agg['CVE'].tolist(),
    key="k6_detail"
)

if st.button("Charger les details depuis NVD", key="k6_fetch"):
    with st.spinner(f"Interrogation de l'API NVD pour {{cve_selectionnee}}..."):
        details = fetch_cve_details(cve_selectionnee, lang='fr')
        time.sleep(0.5)
    render_cve_card(details)

st.markdown("""
<div class="note-box">
    <b>Sources :</b>
    Les details sont issus de l'API officielle NVD (nvd.nist.gov) -- gratuite et sans cle.
    Pour consulter une CVE directement :
    <a href="https://nvd.nist.gov/vuln/search" target="_blank" style="color:#a855f7">nvd.nist.gov</a>
    ou <a href="https://www.cve.org" target="_blank" style="color:#a855f7">cve.org</a>.
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------
# SECTION 3 : REFERENCE CVSS
# ---------------------------------------------------
st.markdown("---")
st.markdown("#### Reference -- Echelle de score CVSS")
st.markdown(
    "<div style='color:#64748b;font-size:0.85rem;margin-bottom:16px'>"
    "Le score CVSS (Common Vulnerability Scoring System) est un standard international "
    "qui mesure la gravite d'une vulnerabilite de 0 a 10."
    "</div>",
    unsafe_allow_html=True
)

scores = [
    ("9.0 - 10.0", "CRITICAL", "#ef4444", "badge-red",
     "Exploitable a distance, sans authentification. Impact total sur le systeme. Patch immediat obligatoire."),
    ("7.0 - 8.9",  "HIGH",     "#f97316", "badge-orange",
     "Exploitation facile, impact important. Peut compromettre des donnees ou services critiques."),
    ("4.0 - 6.9",  "MEDIUM",   "#f59e0b", "badge-yellow",
     "Exploitation sous conditions. Impact modere, a corriger dans les prochains cycles de patch."),
    ("0.1 - 3.9",  "LOW",      "#22c55e", "badge-green",
     "Difficile a exploiter. Impact limite. A surveiller mais pas urgent."),
]

cols = st.columns(4)
for i, (score, niveau, couleur, badge, texte) in enumerate(scores):
    cols[i].markdown(
        f"<div style='background:#0f1422;border:1px solid #1e2a42;border-radius:8px;"
        f"padding:16px;border-top:3px solid {{couleur}}'>"
        f"<div style='font-family:IBM Plex Mono,monospace;font-size:1.3rem;"
        f"font-weight:700;color:{{couleur}}'>{{score}}</div>"
        f"<div style='margin:8px 0'><span class='badge {{badge}}'>{{niveau}}</span></div>"
        f"<div style='color:#64748b;font-size:0.8rem;line-height:1.6'>{{texte}}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div class="note-box">
    <b>Comment le score est calcule ?</b><br>
    Le CVSS prend en compte 3 dimensions :
    <br>- <b>Exploitabilite</b> : accessible depuis internet ? authentification requise ? interaction humaine ?
    <br>- <b>Impact</b> : confidentialite des donnees ? integrite du systeme ? disponibilite du service ?
    <br>- <b>Portee</b> : l'attaque se limite-t-elle au systeme cible ou se propage-t-elle ?
    <br><br>
    <b>Exemples celebres :</b>
    Log4Shell (CVE-2021-44228) = 10.0 &nbsp;|&nbsp;
    EternalBlue (CVE-2017-0144) = 9.3 (origine de WannaCry) &nbsp;|&nbsp;
    Heartbleed (CVE-2014-0160) = 7.5
    <br><br>
    <b style='color:#ef4444'>Tout score >= 7.0 doit etre patche en urgence.</b>
    Un score >= 9.0 necessite une action immediate.
</div>
""", unsafe_allow_html=True)

# --- Export ---
st.markdown("---")
csv = agg.to_csv(index=False).encode('utf-8')
st.download_button("Telecharger les CVE (CSV)", csv,
    file_name="kpi6_cve.csv", mime="text/csv")
'''

content = TEMPLATE.replace("__BLOB__", blob)

out = pathlib.Path(__file__).parent / "cyberpulse" / "app" / "pages" / "6_KPI6_CVE.py"
if not out.parent.exists():
    out = pathlib.Path(__file__).parent / "app" / "pages" / "6_KPI6_CVE.py"
out.write_text(content, encoding="utf-8")
print(f"Ecrit : {out} ({out.stat().st_size // 1024} KB)")
