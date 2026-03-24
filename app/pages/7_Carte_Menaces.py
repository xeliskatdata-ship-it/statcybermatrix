"""
CyberPulse -- Threat Map
Real article data geo-located by source origin
"""

import json
import pathlib
import re
import random
import sys

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_stg_articles, get_mart_k6, force_refresh

st.set_page_config(
    page_title="Carte de veille cyber par catégorie de menaces",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit chrome so the map fills the page
st.markdown("""
<style>
header[data-testid="stHeader"]      { display: none !important; }
.block-container                     { padding: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"]>section { padding: 0 !important; }
[data-testid="stSidebar"]            { display: none !important; }
iframe                               { display: block; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SOURCE → GEOGRAPHIC COORDINATES
# Each source is assigned to its country of origin / primary focus
# ──────────────────────────────────────────────────────────────
SOURCE_GEO: dict[str, tuple[str, float, float]] = {
    "NewsAPI"              : ("USA",         37.1,  -95.7),
    "The Hacker News"      : ("USA",         37.1,  -95.7),
    "BleepingComputer"     : ("USA",         40.7,  -74.0),
    "CISA Alerts"          : ("USA",         38.9,  -77.0),
    "Krebs on Security"    : ("USA",         38.9,  -77.0),
    "Dark Reading"         : ("USA",         40.7,  -74.0),
    "SecurityWeek"         : ("USA",         37.4, -122.1),
    "Cyber Scoop"          : ("USA",         38.9,  -77.0),
    "Threatpost"           : ("USA",         40.7,  -74.0),
    "Schneier on Security" : ("USA",         42.4,  -71.1),
    "The Record"           : ("USA",         38.9,  -77.0),
    "Infosecurity Magazine": ("UK",          51.5,   -0.1),
    "Helpnet Security"     : ("Slovenia",    46.1,   14.5),
    "Graham Cluley"        : ("UK",          51.5,   -0.1),
    "Zataz"                : ("France",      48.8,    2.3),
    "ANSSI"                : ("France",      48.8,    2.3),
    "CERT-EU"              : ("Belgium",     50.8,    4.4),
    "French Breaches"      : ("France",      48.8,    2.3),
    "Malwarebytes Labs"    : ("USA",         37.4, -122.1),
    "Naked Security"       : ("UK",          51.5,   -0.1),
    "We Live Security"     : ("Slovakia",    48.1,   17.1),
    "Trend Micro"          : ("Japan",       35.7,  139.7),
    "Recorded Future Blog" : ("USA",         42.4,  -71.1),
    "Cybereason"           : ("USA",         42.4,  -71.1),
    "OSINT Curious"        : ("USA",         37.1,  -95.7),
    "Bellingcat"           : ("Netherlands", 52.4,    4.9),
    "Intel471"             : ("USA",         37.1,  -95.7),
    "Shodan Blog"          : ("USA",         32.7, -117.2),
    "Maltego Blog"         : ("Germany",     52.5,   13.4),
    "NixIntel"             : ("UK",          51.5,   -0.1),
    "Sector035"            : ("Germany",     52.5,   13.4),
    "SANS ISC"             : ("USA",         38.9,  -77.0),
    "Mandiant Blog"        : ("USA",         37.4, -122.1),
    "CrowdStrike Blog"     : ("USA",         33.2,  -97.1),
    "Securelist"           : ("Russia",      55.7,   37.6),
    "Proofpoint"           : ("USA",         37.4, -122.1),
    "CIRCL"                : ("Luxembourg",  49.6,    6.1),
    "Abuse.ch"             : ("Switzerland", 47.4,    8.5),
    "Citizen Lab"          : ("Canada",      43.7,  -79.4),
    "The Intercept"        : ("USA",         40.7,  -74.0),
    "OCCRP"                : ("Netherlands", 52.4,    4.9),
    "GreyNoise Blog"       : ("USA",         38.9,  -77.0),
    "Censys Blog"          : ("USA",         42.3,  -83.7),
    "VulnCheck"            : ("USA",         37.1,  -95.7),
    "AttackerKB"           : ("USA",         37.1,  -95.7),
}

# ──────────────────────────────────────────────────────────────
# CATEGORY CLASSIFICATION  (mirrors mart_k3.sql CASE logic)
# ──────────────────────────────────────────────────────────────
_PATTERNS = [
    ("ransomware",    r"ransomware|ransom"),
    ("phishing",      r"phishing|spear.{0,8}phishing|credential theft"),
    ("vulnerability", r"vulnerability|cve-[\d]|zero.?day|exploit|rce|lpe|privilege escalation|patch tuesday"),
    ("malware",       r"malware|trojan|backdoor|spyware|worm|keylogger|botnet|\brat\b|infostealer|wiper"),
    ("apt",           r"\bapt\b|apt\d+|lazarus|fancy bear|cozy bear|sandworm|volt typhoon|scattered spider|charming kitten"),
    ("data_breach",   r"data breach|data leak|database dump|exfiltrat|pii|stolen data|leaked credentials"),
    ("supply_chain",  r"supply.?chain|third.?party|\bnpm\b|\bpypi\b|dependency"),
    ("ddos",          r"\bddos\b|denial.?of.?service|volumetric"),
]

# Map category → HTML layer key
_CAT_LAYER = {
    "vulnerability" : "failles",
    "data_breach"   : "failles",
    "malware"       : "menaces",
    "ransomware"    : "menaces",
    "apt"           : "menaces",
    "phishing"      : "menaces",
    "supply_chain"  : "editeurs",
    "ddos"          : "infra",
    "general"       : "infra",
}

# Keywords to show in popups
_KW_LIST = [
    "ransomware", "zero-day", "cve", "rce", "lpe", "malware", "phishing",
    "apt", "data breach", "exploit", "supply chain", "ddos", "trojan",
    "backdoor", "botnet", "ioc", "vulnerability", "patch",
]

# Severity logic: critical articles → critical; apt/ransomware → high; rest → medium
_HIGH_CATS = {"ransomware", "apt", "data_breach"}


def _classify(title: str, desc: str) -> str:
    text = (str(title) + " " + str(desc or "")).lower()
    for cat, pat in _PATTERNS:
        if re.search(pat, text):
            return cat
    return "general"


def _is_critical(title: str, desc: str) -> bool:
    text = (str(title) + " " + str(desc or "")).lower()
    return bool(re.search(
        r"ransomware|zero.day|apt|malware|vulnerability|data.breach", text
    ))


def _extract_kw(title: str, desc: str) -> list[str]:
    text = (str(title) + " " + str(desc or "")).lower()
    found = [k for k in _KW_LIST if k in text]
    return found[:3] if found else ["cyber"]


# ──────────────────────────────────────────────────────────────
# LOAD DATA
# ──────────────────────────────────────────────────────────────
df = get_stg_articles(limit=500)

try:
    df_cve = get_mart_k6()
    n_cve = len(df_cve)
except Exception:
    n_cve = 0

# ──────────────────────────────────────────────────────────────
# BUILD EVENTS  (one per article, geo-located by source)
# ──────────────────────────────────────────────────────────────
rng = random.Random(42)  # deterministic jitter → stable layout on reload

events: list[dict] = []

for _, row in df.iterrows():
    src = str(row.get("source", ""))
    if src not in SOURCE_GEO:
        continue

    country, base_lat, base_lon = SOURCE_GEO[src]
    title = str(row.get("title", ""))[:100]
    desc  = str(row.get("description") or "")

    cat      = _classify(title, desc)
    layer    = _CAT_LAYER[cat]
    critical = _is_critical(title, desc)
    severity = (
        "critical" if critical
        else "high"   if cat in _HIGH_CATS
        else "medium"
    )
    kw = _extract_kw(title, desc)

    # Small jitter so markers don't pile on a single point
    jlat = round(base_lat + rng.uniform(-1.8, 1.8), 3)
    jlon = round(base_lon + rng.uniform(-1.8, 1.8), 3)

    pub_date = row.get("published_date")
    ts = pub_date.isoformat() if pd.notna(pub_date) else None

    events.append({
        "cat"     : layer,
        "lat"     : jlat,
        "lon"     : jlon,
        "country" : country,
        "title"   : title,
        "kw"      : kw,
        "severity": severity,
        "source"  : src,
        "ts"      : ts,
    })

# ──────────────────────────────────────────────────────────────
# AGGREGATE STATS
# ──────────────────────────────────────────────────────────────
n_events    = len(events)
n_countries = len({e["country"] for e in events})
n_crit      = sum(1 for e in events if e["severity"] == "critical")

cat_counts: dict[str, int] = {}
for e in events:
    cat_counts[e["cat"]] = cat_counts.get(e["cat"], 0) + 1

# ──────────────────────────────────────────────────────────────
# READ HTML TEMPLATE
# ──────────────────────────────────────────────────────────────
map_path = pathlib.Path(__file__).parent.parent / "carte_menaces.html"
html = map_path.read_text(encoding="utf-8")

# ── 1. Replace EVENTS array ───────────────────────────────────
events_js = json.dumps(events, ensure_ascii=False)
html = re.sub(
    r"const EVENTS\s*=\s*\[.*?\];",
    f"const EVENTS = {events_js};",
    html,
    flags=re.DOTALL,
)

# ── 2. Update nav stats ───────────────────────────────────────
html = re.sub(r'id="n-events">[^<]+', f'id="n-events">{n_events}', html)
html = re.sub(r'id="n-countries">[^<]+', f'id="n-countries">{n_countries}', html)

# ── 3. Update stat cards ──────────────────────────────────────
html = re.sub(
    r'(<div class="stat-n">)\s*897\s*(</div>\s*<div class="stat-l">Articles)',
    rf'\g<1>{n_events}\2',
    html,
)
html = re.sub(
    r'(<div class="stat-n">)\s*13\s*(</div>\s*<div class="stat-l">CVE)',
    rf'\g<1>{n_cve}\2',
    html,
)

# ── 4. Update layer event counts in sidebar ───────────────────
for layer_key, elem_id in [
    ("failles",  "c-failles"),
    ("infra",    "c-infra"),
    ("editeurs", "c-editeurs"),
    ("menaces",  "c-menaces"),
]:
    n = cat_counts.get(layer_key, 0)
    html = re.sub(
        rf'id="{elem_id}">[^<]*</div>',
        f'id="{elem_id}">{n} art</div>',
        html,
    )

# ──────────────────────────────────────────────────────────────
# RENDER
# ──────────────────────────────────────────────────────────────
if df.empty:
    st.warning("No articles in the database — run the acquisition pipeline first.")
else:
    components.html(html, height=1080, scrolling=False)
