"""
CyberPulse -- Threat Map
Articles geo-located by ATTACKED country (spaCy NER), fallback on source origin.
Victim organisation extracted via semantic regex + spaCy cross-validation.
Each event carries a confidence score (0–100) + label (forte / moyenne / faible).
Title is clickable → opens article in new tab.
"""

import json
import pathlib
import re
import random
import sys
import os

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

st.markdown("""
<style>
header[data-testid="stHeader"]      { display: none !important; }
.block-container                     { padding: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"]>section { padding: 0 !important; }
iframe                               { display: block; height: 100vh !important; width: 100% !important; }
</style>
""", unsafe_allow_html=True)
 
# ──────────────────────────────────────────────────────────────
# SPACY — chargement du modèle NER (cache Streamlit)
# ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_nlp():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None

nlp = load_nlp()

# ──────────────────────────────────────────────────────────────
# PATTERNS SÉMANTIQUES — détection de la victime
# ──────────────────────────────────────────────────────────────
_VICTIM_PATTERNS = [
    r"(?P<org>[\w][\w\s&,\.']+?)\s+(?:was|were|has been|have been|is)\s+(?:hit|hacked|breached|attacked|targeted|compromised|infected|affected|struck)",
    r"(?P<org>[\w][\w\s&,\.']+?)\s+(?:suffers?|suffered|reports?|reported|discloses?|disclosed)\s+(?:a\s+)?(?:data\s+breach|breach|attack|ransomware|hack|intrusion|incident)",
    r"(?:attack|breach|hack|ransomware|intrusion|incident|compromise)\s+(?:on|at|against)\s+(?P<org>[\w][\w\s&,\.']+)",
    r"ransomware\s+(?:hits?|attacks?|strikes?)\s+(?P<org>[\w][\w\s&,\.']+)",
    r"(?P<org>[\w][\w\s&,\.']+?)\s+data\s+(?:breach|leak|theft|stolen|exposed)",
    r"(?P<org>[\w][\w\s&,\.']+?)\s+(?:systems?|network|infrastructure)\s+(?:hacked|compromised|breached|attacked)",
    r"(?:hits?|strikes?)\s+(?P<org>[\w][\w\s&,\.']+)",
    r"targeting\s+(?P<org>[\w][\w\s&,\.']+)",
]

_STRONG_CYBER_KW = re.compile(
    r"ransomware|zero.?day|data\s+breach|\bcve\b|apt|malware|phishing|exploit|backdoor|botnet",
    re.IGNORECASE,
)

def _extract_victim(text: str) -> str | None:
    for pat in _VICTIM_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            candidate = m.group("org").strip(" ,.'")
            candidate = re.sub(
                r'\s+(by|and|in|the|a|an|for|with|from|over|via|after).*$',
                '', candidate, flags=re.IGNORECASE
            ).strip(" ,.'")
            if 3 < len(candidate) < 50:
                return candidate
    return None

# ──────────────────────────────────────────────────────────────
# PAYS CIBLES → COORDONNÉES (noms anglais + noms français)
# ──────────────────────────────────────────────────────────────
TARGET_GEO: dict[str, tuple[str, float, float]] = {
    # ── Anglais ───────────────────────────────────────────────
    "United States"  : ("USA",              37.1,  -95.7),
    "US"             : ("USA",              37.1,  -95.7),
    "USA"            : ("USA",              37.1,  -95.7),
    "America"        : ("USA",              37.1,  -95.7),
    "United Kingdom" : ("UK",               51.5,   -0.1),
    "UK"             : ("UK",               51.5,   -0.1),
    "Britain"        : ("UK",               51.5,   -0.1),
    "England"        : ("UK",               51.5,   -0.1),
    "France"         : ("France",           48.8,    2.3),
    "Germany"        : ("Allemagne",        52.5,   13.4),
    "Russia"         : ("Russie",           55.7,   37.6),
    "China"          : ("Chine",            39.9,  116.4),
    "North Korea"    : ("Corée du Nord",    39.0,  125.7),
    "Iran"           : ("Iran",             35.7,   51.4),
    "Ukraine"        : ("Ukraine",          50.4,   30.5),
    "Israel"         : ("Israël",           31.8,   35.2),
    "Japan"          : ("Japon",            35.7,  139.7),
    "India"          : ("Inde",             20.6,   78.9),
    "Canada"         : ("Canada",           56.1, -106.3),
    "Australia"      : ("Australie",       -25.3,  133.8),
    "Brazil"         : ("Brésil",          -14.2,  -51.9),
    "Mexico"         : ("Mexique",          23.6, -102.6),
    "Spain"          : ("Espagne",          40.5,   -3.7),
    "Italy"          : ("Italie",           41.9,   12.6),
    "Poland"         : ("Pologne",          51.9,   19.1),
    "Netherlands"    : ("Pays-Bas",         52.1,    5.3),
    "Belgium"        : ("Belgique",         50.5,    4.5),
    "Switzerland"    : ("Suisse",           46.8,    8.2),
    "Sweden"         : ("Suède",            60.1,   18.6),
    "Norway"         : ("Norvège",          60.5,    8.5),
    "Finland"        : ("Finlande",         61.9,   25.7),
    "Denmark"        : ("Danemark",         56.3,    9.5),
    "Austria"        : ("Autriche",         47.5,   14.5),
    "Czech Republic" : ("Rép. Tchèque",     49.8,   15.5),
    "Romania"        : ("Roumanie",         45.9,   24.9),
    "Turkey"         : ("Turquie",          38.9,   35.2),
    "Saudi Arabia"   : ("Arabie Saoudite",  23.9,   45.1),
    "UAE"            : ("Émirats",          24.0,   54.0),
    "Singapore"      : ("Singapour",         1.3,  103.8),
    "South Korea"    : ("Corée du Sud",     35.9,  127.8),
    "Taiwan"         : ("Taïwan",           23.7,  120.9),
    "Hong Kong"      : ("Hong Kong",        22.3,  114.2),
    "Pakistan"       : ("Pakistan",         30.4,   69.3),
    "Indonesia"      : ("Indonésie",        -0.8,  113.9),
    "Malaysia"       : ("Malaisie",          4.2,  109.5),
    "Thailand"       : ("Thaïlande",        15.9,  100.9),
    "Vietnam"        : ("Vietnam",          14.1,  108.3),
    "Egypt"          : ("Égypte",           26.8,   30.8),
    "South Africa"   : ("Afrique du Sud",  -30.6,   22.9),
    "Nigeria"        : ("Nigeria",           9.1,    8.7),
    "Kenya"          : ("Kenya",            -0.0,   37.9),
    "Argentina"      : ("Argentine",       -38.4,  -63.6),
    "Colombia"       : ("Colombie",          4.6,  -74.1),
    "Luxembourg"     : ("Luxembourg",       49.8,    6.1),
    "Ireland"        : ("Irlande",          53.4,   -8.2),
    "Portugal"       : ("Portugal",         39.4,   -8.2),
    "Greece"         : ("Grèce",            39.1,   22.0),
    "Hungary"        : ("Hongrie",          47.2,   19.5),
    "Slovakia"       : ("Slovaquie",        48.7,   19.7),
    "Slovenia"       : ("Slovénie",         46.2,   14.8),
    "Croatia"        : ("Croatie",          45.1,   15.2),
    "Serbia"         : ("Serbie",           44.0,   21.0),
    "Bulgaria"       : ("Bulgarie",         42.7,   25.5),
    "Estonia"        : ("Estonie",          58.6,   25.0),
    "Latvia"         : ("Lettonie",         56.9,   24.6),
    "Lithuania"      : ("Lituanie",         55.2,   24.0),
    "NHS"            : ("UK",               51.5,   -0.1),
    "Europe"         : ("Europe",           54.5,   15.3),
    "NATO"           : ("Europe",           50.8,    4.4),
    # ── Français ──────────────────────────────────────────────
    "États-Unis"     : ("USA",              37.1,  -95.7),
    "Etats-Unis"     : ("USA",              37.1,  -95.7),
    "Royaume-Uni"    : ("UK",               51.5,   -0.1),
    "Allemagne"      : ("Allemagne",        52.5,   13.4),
    "Russie"         : ("Russie",           55.7,   37.6),
    "Chine"          : ("Chine",            39.9,  116.4),
    "Corée du Nord"  : ("Corée du Nord",    39.0,  125.7),
    "Corée du Sud"   : ("Corée du Sud",     35.9,  127.8),
    "Japon"          : ("Japon",            35.7,  139.7),
    "Inde"           : ("Inde",             20.6,   78.9),
    "Israël"         : ("Israël",           31.8,   35.2),
    "Australie"      : ("Australie",       -25.3,  133.8),
    "Brésil"         : ("Brésil",          -14.2,  -51.9),
    "Mexique"        : ("Mexique",          23.6, -102.6),
    "Espagne"        : ("Espagne",          40.5,   -3.7),
    "Italie"         : ("Italie",           41.9,   12.6),
    "Pologne"        : ("Pologne",          51.9,   19.1),
    "Pays-Bas"       : ("Pays-Bas",         52.1,    5.3),
    "Belgique"       : ("Belgique",         50.5,    4.5),
    "Suisse"         : ("Suisse",           46.8,    8.2),
    "Suède"          : ("Suède",            60.1,   18.6),
    "Norvège"        : ("Norvège",          60.5,    8.5),
    "Finlande"       : ("Finlande",         61.9,   25.7),
    "Danemark"       : ("Danemark",         56.3,    9.5),
    "Autriche"       : ("Autriche",         47.5,   14.5),
    "Rép. Tchèque"   : ("Rép. Tchèque",     49.8,   15.5),
    "Roumanie"       : ("Roumanie",         45.9,   24.9),
    "Turquie"        : ("Turquie",          38.9,   35.2),
    "Arabie Saoudite": ("Arabie Saoudite",  23.9,   45.1),
    "Émirats"        : ("Émirats",          24.0,   54.0),
    "Singapour"      : ("Singapour",         1.3,  103.8),
    "Taïwan"         : ("Taïwan",           23.7,  120.9),
    "Indonésie"      : ("Indonésie",        -0.8,  113.9),
    "Malaisie"       : ("Malaisie",          4.2,  109.5),
    "Thaïlande"      : ("Thaïlande",        15.9,  100.9),
    "Égypte"         : ("Égypte",           26.8,   30.8),
    "Afrique du Sud" : ("Afrique du Sud",  -30.6,   22.9),
    "Argentine"      : ("Argentine",       -38.4,  -63.6),
    "Colombie"       : ("Colombie",          4.6,  -74.1),
    "Irlande"        : ("Irlande",          53.4,   -8.2),
    "Grèce"          : ("Grèce",            39.1,   22.0),
    "Hongrie"        : ("Hongrie",          47.2,   19.5),
    "Slovaquie"      : ("Slovaquie",        48.7,   19.7),
    "Slovénie"       : ("Slovénie",         46.2,   14.8),
    "Croatie"        : ("Croatie",          45.1,   15.2),
    "Serbie"         : ("Serbie",           44.0,   21.0),
    "Bulgarie"       : ("Bulgarie",         42.7,   25.5),
    "Estonie"        : ("Estonie",          58.6,   25.0),
    "Lettonie"       : ("Lettonie",         56.9,   24.6),
    "Lituanie"       : ("Lituanie",         55.2,   24.0),
    "Liban"          : ("Liban",            33.9,   35.5),
    "Maroc"          : ("Maroc",            31.8,   -7.1),
    "Algérie"        : ("Algérie",          28.0,    1.7),
    "Tunisie"        : ("Tunisie",          33.9,    9.6),
    "Sénégal"        : ("Sénégal",          14.5,  -14.5),
    "Côte d'Ivoire"  : ("Côte d'Ivoire",     7.5,   -5.5),
}

# ──────────────────────────────────────────────────────────────
# SOURCE → GEOGRAPHIC COORDINATES (fallback)
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
# CATEGORY CLASSIFICATION
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

_KW_LIST = [
    "ransomware", "zero-day", "cve", "rce", "lpe", "malware", "phishing",
    "apt", "data breach", "exploit", "supply chain", "ddos", "trojan",
    "backdoor", "botnet", "ioc", "vulnerability", "patch",
]

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
# SCORE DE CONFIANCE
# ──────────────────────────────────────────────────────────────
def _compute_confidence(
    gpe_count: int,
    has_org: bool,
    regex_match: bool,
    spacy_org_match: bool,
    source_fallback: bool,
    multiple_gpe: bool,
    multiple_victims: bool,
    strong_kw_in_300: bool,
    has_strong_kw: bool,
) -> tuple[int, str]:
    score = 0

    if gpe_count > 0:
        score += 30
    if gpe_count > 1:
        score += 10

    if regex_match:
        score += 20
    if spacy_org_match:
        score += 20
    if regex_match and spacy_org_match:
        score += 20

    if has_strong_kw:
        score += 10
    if strong_kw_in_300:
        score += 10

    if source_fallback:
        score -= 20
    if not has_org:
        score -= 15
    if multiple_gpe:
        score -= 15
    if multiple_victims:
        score -= 10

    score = max(0, min(score, 100))

    if score >= 80:
        label = "forte"
    elif score >= 50:
        label = "moyenne"
    else:
        label = "faible"

    return score, label


# ──────────────────────────────────────────────────────────────
# NER — extraction pays cible (spaCy) + victime (regex + validation spaCy)
# ──────────────────────────────────────────────────────────────
def extract_target(
    title: str, desc: str
) -> tuple[str | None, float | None, float | None, str | None, int, str]:
    """
    Retourne (country, lat, lon, org_cible, confidence_score, confidence_label).
    Priorité : scan regex titre (FR+EN) → spaCy NER texte[:1000] → fallback source.
    """
    text = str(title) + ". " + str(desc or "")
    first_300 = text[:300]

    target_country = None
    target_lat     = None
    target_lon     = None
    org_cible      = None

    # ── 1. Scan direct du titre sur TARGET_GEO (noms FR + EN)
    #    Prioritaire : le titre est la partie la plus fiable et la plus concise
    for name, geo in TARGET_GEO.items():
        if re.search(r'\b' + re.escape(name) + r'\b', title, re.IGNORECASE):
            target_country, target_lat, target_lon = geo
            break

    # ── 2. Regex victime sur titre puis texte complet
    org_candidate = _extract_victim(title) or _extract_victim(text)
    regex_match   = org_candidate is not None

    strong_kw_in_300 = bool(_STRONG_CYBER_KW.search(first_300))
    has_strong_kw    = bool(_STRONG_CYBER_KW.search(text))

    gpe_hits: list[str] = []
    spacy_orgs: set[str] = set()
    spacy_org_match = False

    if nlp is not None:
        # Analyse sur les 1000 premiers caractères (au lieu de 500)
        doc = nlp(text[:1000])

        for ent in doc.ents:
            if ent.label_ == "GPE":
                match = TARGET_GEO.get(ent.text)
                if match:
                    gpe_hits.append(ent.text)
                    # spaCy complète le scan titre si rien trouvé
                    if target_country is None:
                        target_country, target_lat, target_lon = match

            elif ent.label_ == "ORG":
                spacy_orgs.add(ent.text)

        if org_candidate and spacy_orgs:
            spacy_org_match = any(
                org.lower() in org_candidate.lower() or
                org_candidate.lower() in org.lower()
                for org in spacy_orgs
            )
            org_cible = org_candidate if spacy_org_match else None

    # gpe_count inclut le match titre s'il n'est pas dans gpe_hits spaCy
    gpe_count    = len(gpe_hits) + (1 if target_country and not gpe_hits else 0)
    multiple_gpe = len(gpe_hits) > 1
    multiple_victims = (
        len([p for p in _VICTIM_PATTERNS
             if re.search(p, text, re.IGNORECASE)]) > 2
    )

    source_fallback = target_country is None

    confidence_score, confidence_label = _compute_confidence(
        gpe_count        = gpe_count,
        has_org          = org_cible is not None,
        regex_match      = regex_match,
        spacy_org_match  = spacy_org_match,
        source_fallback  = source_fallback,
        multiple_gpe     = multiple_gpe,
        multiple_victims = multiple_victims,
        strong_kw_in_300 = strong_kw_in_300,
        has_strong_kw    = has_strong_kw,
    )

    return target_country, target_lat, target_lon, org_cible, confidence_score, confidence_label


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
# JITTER PAR PAYS — défini une seule fois AVANT la boucle
# ──────────────────────────────────────────────────────────────
_JITTER = {
    "USA": 4.0, "Canada": 5.0, "Australie": 5.0, "Russie": 6.0,
    "Chine": 4.0, "Brésil": 4.0, "Inde": 3.0, "Mexique": 3.0,
    "France": 1.5, "Allemagne": 1.2, "UK": 0.8, "Italie": 1.2,
    "Espagne": 1.5, "Pologne": 1.0, "Ukraine": 1.5, "Turquie": 1.5,
    "Japon": 1.2, "Corée du Sud": 0.6, "Taïwan": 0.3,
    "Singapour": 0.15, "Hong Kong": 0.1, "Belgique": 0.4,
    "Pays-Bas": 0.4, "Suisse": 0.4, "Autriche": 0.6,
    "Europe": 3.0,
}

# ──────────────────────────────────────────────────────────────
# BUILD EVENTS
# ──────────────────────────────────────────────────────────────
rng = random.Random(42)
events: list[dict] = []

for _, row in df.iterrows():
    src = str(row.get("source", ""))
    if src not in SOURCE_GEO:
        continue

    title = str(row.get("title", ""))[:100]
    desc  = str(row.get("description") or "")

    t_country, t_lat, t_lon, org_cible, conf_score, conf_label = extract_target(title, desc)

    if t_lat is None:
        fallback_country, t_lat, t_lon = SOURCE_GEO[src]
        t_country = fallback_country
        geo_mode  = "source"
    else:
        geo_mode = "target"

    cat      = _classify(title, desc)
    layer    = _CAT_LAYER[cat]
    critical = _is_critical(title, desc)
    severity = (
        "critical" if critical
        else "high"   if cat in _HIGH_CATS
        else "medium"
    )
    kw = _extract_kw(title, desc)

    _j   = _JITTER.get(t_country, 1.0)
    jlat = round(t_lat + rng.gauss(0, _j * 0.4), 3)
    jlon = round(t_lon + rng.gauss(0, _j * 0.6), 3)

    pub_date = row.get("published_date")
    ts = pub_date.isoformat() if pd.notna(pub_date) else None

    events.append({
        "cat"        : layer,
        "lat"        : jlat,
        "lon"        : jlon,
        "country"    : t_country,
        "title"      : title,
        "kw"         : kw,
        "severity"   : severity,
        "source"     : src,
        "org_cible"  : org_cible or "",
        "geo_mode"   : geo_mode,
        "ts"         : ts,
        "url"        : str(row.get("url", "") or ""),
        "conf_score" : conf_score,
        "conf_label" : conf_label,
    })

# ──────────────────────────────────────────────────────────────
# DÉDUPLICATION — un point par titre unique
# ──────────────────────────────────────────────────────────────
def _normalize(title: str) -> str:
    return re.sub(r'[^a-z0-9]', '', title.lower())

seen_titles: set[str] = set()
events_dedup: list[dict] = []

for ev in events:
    key = _normalize(ev["title"])[:60]
    if key not in seen_titles:
        seen_titles.add(key)
        events_dedup.append(ev)

events = events_dedup

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

events_js = json.dumps(events, ensure_ascii=False)
html = re.sub(
    r"const EVENTS\s*=\s*\[.*?\];",
    f"const EVENTS = {events_js};",
    html,
    flags=re.DOTALL,
)

html = re.sub(r'id="n-events">[^<]+',    f'id="n-events">{n_events}',    html)
html = re.sub(r'id="n-countries">[^<]+', f'id="n-countries">{n_countries}', html)

html = re.sub(
    r'(<div class="stat-n">)\s*897\s*(</div>\s*<div class="stat-l">Articles)',
    rf'\g<1>{n_events}\2', html,
)
html = re.sub(
    r'(<div class="stat-n">)\s*13\s*(</div>\s*<div class="stat-l">CVE)',
    rf'\g<1>{n_cve}\2', html,
)

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

n_sources_actives = len({e["source"] for e in events})
html = re.sub(
    r'<div class="sb-title">\d+ Sources actives</div>',
    f'<div class="sb-title">{n_sources_actives} Sources actives</div>',
    html,
)

# ──────────────────────────────────────────────────────────────
# INJECTION TOKEN JAWG — depuis .env via JAWG_TOKEN
# ──────────────────────────────────────────────────────────────
jawg_token = os.getenv("JAWG_TOKEN", "")
html = html.replace("__JAWG_TOKEN__", jawg_token)

# ──────────────────────────────────────────────────────────────
# RENDER
# ──────────────────────────────────────────────────────────────
if df.empty:
    st.warning("No articles in the database — run the acquisition pipeline first.")
else:
    components.html(html, height=10000, scrolling=False)
    