"""
StatCyberMatrix -- Threat Map (Globe 3D)
Articles geo-located by ATTACKED country (spaCy NER), fallback on source origin.
Sprint 5 v4 : Three.js globe + animated arcs source->target
"""

import json
import pathlib
import re
import random
import sys
import os
from io import StringIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent / "src"))
from db_connect import get_stg_articles, get_mart_k6, force_refresh

st.set_page_config(
    page_title="Globe de veille cyber",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section {
    background: #050a14 !important;
    background-color: #050a14 !important;
}
header[data-testid="stHeader"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stAppViewContainer"] > section { padding: 0 !important; }
iframe { display: block; height: 100vh !important; width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# Desactive l'ECG canvas si present
components.html("""
<script>
(function() {
    var p = window.parent.document;
    var ecg = p.getElementById('ecg-bg');
    if (ecg) ecg.parentNode.removeChild(ecg);
})();
</script>
""", height=0)


# ==============================================================
# SPACY -- EN + FR (amelioration #2)
# ==============================================================
@st.cache_resource
def load_nlp():
    models = {}
    try:
        import spacy
        models['en'] = spacy.load("en_core_web_sm")
    except Exception:
        pass
    try:
        import spacy
        models['fr'] = spacy.load("fr_core_news_sm")
    except Exception:
        pass
    return models

_NLP = load_nlp()

_FR_SOURCES = {
    "Zataz", "ANSSI", "French Breaches", "CERT-EU",
    "LeMagIT Securite", "No.log",
    "Cybermalveillance", "IT-Connect", "UnderNews", "Cyber-news.fr",
    "Orange Cyberdefense", "Sekoia Blog",
}

def _get_nlp(source):
    if source in _FR_SOURCES and 'fr' in _NLP:
        return _NLP['fr']
    return _NLP.get('en')


# ==============================================================
# PATTERNS SEMANTIQUES -- detection victime
# ==============================================================
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

def _extract_victim(text):
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


# ==============================================================
# AMELIORATION #4 -- Patterns de contexte directs
# ==============================================================
_CONTEXT_PATTERNS = [
    r"(?:attack(?:ed|s|ing)?|breach(?:ed|es|ing)?|hack(?:ed|s|ing)?|compromis(?:ed|ing)?|target(?:ed|s|ing)?|struck|hit(?:s|ting)?)\s+(?:in|on|against|across)\s+(?P<country>[A-Z][\w\s\-']+)",
    r"(?P<country>[A-Z][\w\s\-']+?)\s+(?:hit|targeted|attacked|struck|breached|hacked|compromised)\s+by\b",
    r"target(?:s|ing)\s+(?P<country>[A-Z][\w\s\-']+?)(?:\s+(?:infrastructure|government|companies|organizations|firms|agencies|hospitals|banks|networks|users))",
    r"victims?\s+in\s+(?P<country>[A-Z][\w\s\-']+)",
    r"(?P<country>[A-Z][\w\s\-']+?)(?:'s|s')\s+(?:infrastructure|government|military|companies|hospitals|banks|networks|systems?|agencies|telecom|energy)\s+(?:hacked|attacked|breached|compromised|targeted|hit)",
    r"attaqu(?:e|es|er|ent)\s+(?:contre|en|sur|visant)\s+(?:le |la |les |l')?(?P<country>[A-Z][\w\s\-']+)",
    r"fuite\s+(?:de\s+donn[eE]es?\s+)?(?:en|chez|au|aux)\s+(?P<country>[A-Z][\w\s\-']+)",
    r"cyber.?attaqu(?:e|es)\s+(?:en|contre|sur|visant)\s+(?:le |la |les |l')?(?P<country>[A-Z][\w\s\-']+)",
    r"piratage\s+(?:en|de|du|des|au|aux)\s+(?:le |la |les |l')?(?P<country>[A-Z][\w\s\-']+)",
    r"(?P<country>[A-Z][\w\s\-']+?)\s+(?:victime|cibl[eE]e?)\s+(?:de|par|d')\s",
]

def _context_country(text):
    for pat in _CONTEXT_PATTERNS:
        m = re.search(pat, text)
        if m:
            candidate = m.group("country").strip(" ,.'")
            candidate = re.sub(
                r'\s+(and|or|with|after|before|during|since|the|a|an|by|is|has|was|were|from|for|over|via).*$',
                '', candidate, flags=re.IGNORECASE
            ).strip(" ,.'")
            geo = TARGET_GEO.get(candidate)
            if geo:
                return geo
            for name, g in TARGET_GEO.items():
                if name.lower() == candidate.lower():
                    return g
    return None


# ==============================================================
# ATTRIBUTION -- APT/groupe -> pays attaquant
# ==============================================================
_APT_COUNTRY = {
    # Russie -- etat + ransomware gangs (majorite RU-linked)
    "fancy bear": "Russie", "apt28": "Russie", "cozy bear": "Russie",
    "apt29": "Russie", "sandworm": "Russie", "turla": "Russie",
    "gamaredon": "Russie", "evil corp": "Russie", "nobelium": "Russie",
    "star blizzard": "Russie", "midnight blizzard": "Russie",
    "seashell blizzard": "Russie", "ember bear": "Russie",
    "revil": "Russie", "conti": "Russie", "lockbit": "Russie",
    "black basta": "Russie", "clop": "Russie", "cl0p": "Russie",
    "darkside": "Russie", "blackcat": "Russie", "alphv": "Russie",
    "qilin": "Russie", "akira": "Russie", "play ransomware": "Russie",
    "play": "Russie", "medusa": "Russie", "8base": "Russie",
    "bianlian": "Russie", "rhysida": "Russie", "royal": "Russie",
    "blacksuit": "Russie", "black suit": "Russie",
    "hunters international": "Russie", "inc ransom": "Russie",
    "ransomhub": "Russie", "dragonforce": "Russie",
    "cactus": "Russie", "trigona": "Russie", "snatch": "Russie",
    "cuba ransomware": "Russie", "hive": "Russie",
    "vice society": "Russie", "ragnar locker": "Russie",
    "blackbyte": "Russie", "avos locker": "Russie",
    "phobos": "Russie", "mallox": "Russie",
    "nightspire": "Russie", "termite": "Russie",
    "fog": "Russie", "lynx": "Russie", "embargo": "Russie",
    "noescape": "Russie", "nokoyawa": "Russie",
    # Chine -- etat
    "volt typhoon": "Chine", "salt typhoon": "Chine",
    "flax typhoon": "Chine", "charcoal typhoon": "Chine",
    "silk typhoon": "Chine", "brass typhoon": "Chine",
    "apt41": "Chine", "apt10": "Chine", "apt31": "Chine",
    "apt40": "Chine", "apt27": "Chine", "apt3": "Chine",
    "apt17": "Chine", "hafnium": "Chine",
    "mustang panda": "Chine", "winnti": "Chine",
    "backdoor diplomacy": "Chine", "gallium": "Chine",
    "cicada": "Chine", "bronze starlight": "Chine",
    "earth lusca": "Chine", "earth estries": "Chine",
    "space pirates": "Chine", "ghost emperor": "Chine",
    "weaver ant": "Chine", "storm-0558": "Chine",
    # Coree du Nord
    "lazarus": "Coree du Nord", "kimsuky": "Coree du Nord",
    "apt38": "Coree du Nord", "andariel": "Coree du Nord",
    "bluenoroff": "Coree du Nord", "sapphire sleet": "Coree du Nord",
    "citrine sleet": "Coree du Nord", "diamond sleet": "Coree du Nord",
    "jade sleet": "Coree du Nord", "bureau 121": "Coree du Nord",
    "labyrinth chollima": "Coree du Nord",
    # Iran
    "charming kitten": "Iran", "apt35": "Iran", "apt33": "Iran",
    "apt34": "Iran", "apt42": "Iran", "muddywater": "Iran",
    "oilrig": "Iran", "agrius": "Iran", "moses staff": "Iran",
    "peach sandstorm": "Iran", "mint sandstorm": "Iran",
    "cotton sandstorm": "Iran", "imperial kitten": "Iran",
    "tortoiseshell": "Iran", "lyceum": "Iran",
    # Autres
    "scattered spider": "USA", "lapsus$": "UK",
    "shinyhunters": "France",
}

# Coordonnees des pays attaquants
_ATTACKER_GEO = {
    "Russie": (55.7, 37.6), "Chine": (39.9, 116.4),
    "Coree du Nord": (39.0, 125.7), "Iran": (35.7, 51.4),
    "USA": (37.1, -95.7), "UK": (51.5, -0.1),
    "France": (48.8, 2.3),
}

# Patterns d'attribution dans le texte (EN + FR)
_ATTRIB_PATTERNS = [
    # EN -- country-linked
    r"(?P<country>Russia|Russian|China|Chinese|North\s+Korea|North\s+Korean|Iran|Iranian)[\s\-]+(?:linked|backed|sponsored|affiliated|aligned|nexus|based|state)",
    r"(?:linked|backed|sponsored|affiliated|attributed)\s+(?:to\s+)?(?P<country>Russia|China|North\s+Korea|Iran|DPRK)",
    r"(?P<country>Russia|China|North\s+Korea|Iran|DPRK)\s+(?:hackers?|threat\s+actors?|cyber\s+(?:espionage|attack|group|operation))",
    r"(?:state[\s\-]sponsored|nation[\s\-]state)\s+(?:threat\s+)?(?:actor|group|hacker)s?\s+(?:from|in|based\s+in)\s+(?P<country>Russia|China|North\s+Korea|Iran)",
    # EN -- ransomware claimed
    r"(?:claimed|claim)\s+(?:by|responsibility)\s+(?:the\s+)?(?:ransomware\s+)?(?:group|gang|operator)?\s*(?P<country>Russia|China|North\s+Korea|Iran)",
    # FR -- attribution directe
    r"(?:attribu|li[eéÉ]|rattach)[eéÉ]e?\s+(?:[aà]\s+la?\s+)?(?P<country>Russie|Chine|Cor[eéÉ]e\s+du\s+Nord|Iran)",
    r"(?:hackers?|pirates?|groupe|gang)\s+(?P<country>russe|chinois|nord[\s\-]cor[eéÉ]en|iranien)s?",
    # FR -- revendication (tres courant dans la presse FR)
    r"(?:revendiqu[eéÉ]e?|revendication)\s+(?:par|du\s+groupe)\s+",
    r"(?:attaque|piratage|ransomware)\s+(?:contre|visant|ciblant)\s+(?:la\s+)?(?:France|.*?fran[cçÇ]ais)",
    # FR -- "le groupe X a attaque"
    r"le\s+groupe\s+(?:de\s+)?(?:ransomware\s+)?(?:[\w\s]+)\s+(?:a\s+)?(?:revendiqu|attaqu|cibl|vis)[eéÉ]",
]

_COUNTRY_NORMALIZE = {
    "Russia": "Russie", "Russian": "Russie", "russe": "Russie",
    "China": "Chine", "Chinese": "Chine", "chinois": "Chine",
    "North Korea": "Coree du Nord", "North Korean": "Coree du Nord",
    "DPRK": "Coree du Nord", "nord-coreen": "Coree du Nord",
    "nord coreen": "Coree du Nord",
    "Iran": "Iran", "Iranian": "Iran", "iranien": "Iran",
    "Russie": "Russie", "Chine": "Chine",
    "Coree du Nord": "Coree du Nord",
}

def _extract_attacker(title, desc):
    """Retourne (pays, lat, lon) de l'attaquant si attribution claire, sinon None."""
    text = (str(title) + " " + str(desc or "")).lower()

    # Passe 1 : recherche APT nommee
    for apt_name, country in _APT_COUNTRY.items():
        if apt_name in text:
            geo = _ATTACKER_GEO.get(country)
            if geo:
                return country, geo[0], geo[1]

    # Passe 2 : patterns d'attribution
    full_text = str(title) + " " + str(desc or "")
    for pat in _ATTRIB_PATTERNS:
        m = re.search(pat, full_text, re.IGNORECASE)
        if m:
            try:
                raw = m.group("country").strip()
            except (IndexError, AttributeError):
                continue
            normalized = _COUNTRY_NORMALIZE.get(raw, raw)
            geo = _ATTACKER_GEO.get(normalized)
            if geo:
                return normalized, geo[0], geo[1]

    return None, None, None
# ==============================================================
_CYBER_VICTIM_WORDS = {
    "attacked", "breached", "hacked", "compromised", "targeted", "hit",
    "struck", "victim", "victims", "infected", "ransomware", "breach",
    "attack", "cyberattack", "hack", "intrusion", "malware", "phishing",
    "exploit", "vulnerability",
    "attaque", "attaquee", "piratage", "pirate", "piratee", "victime",
    "ciblee", "cible", "compromise", "compromis", "fuite", "intrusion",
}

def _score_gpe_by_proximity(doc, gpe_text, gpe_start):
    score = 0
    for token in doc:
        if token.text.lower() in _CYBER_VICTIM_WORDS:
            distance = abs(token.i - gpe_start)
            if distance <= 5:
                score += 10
            elif distance <= 15:
                score += 5
            elif distance <= 30:
                score += 2
    return score


# ==============================================================
# PAYS CIBLES -> COORDONNEES
# ==============================================================
TARGET_GEO = {
    "United States": ("USA", 37.1, -95.7), "US": ("USA", 37.1, -95.7),
    "USA": ("USA", 37.1, -95.7), "America": ("USA", 37.1, -95.7),
    "United Kingdom": ("UK", 51.5, -0.1), "UK": ("UK", 51.5, -0.1),
    "Britain": ("UK", 51.5, -0.1), "England": ("UK", 51.5, -0.1),
    "France": ("France", 48.8, 2.3), "Germany": ("Allemagne", 52.5, 13.4),
    "Russia": ("Russie", 55.7, 37.6), "China": ("Chine", 39.9, 116.4),
    "North Korea": ("Coree du Nord", 39.0, 125.7), "Iran": ("Iran", 35.7, 51.4),
    "Ukraine": ("Ukraine", 50.4, 30.5), "Israel": ("Israel", 31.8, 35.2),
    "Japan": ("Japon", 35.7, 139.7), "India": ("Inde", 20.6, 78.9),
    "Canada": ("Canada", 56.1, -106.3), "Australia": ("Australie", -25.3, 133.8),
    "Brazil": ("Bresil", -14.2, -51.9), "Mexico": ("Mexique", 23.6, -102.6),
    "Spain": ("Espagne", 40.5, -3.7), "Italy": ("Italie", 41.9, 12.6),
    "Poland": ("Pologne", 51.9, 19.1), "Netherlands": ("Pays-Bas", 52.1, 5.3),
    "Belgium": ("Belgique", 50.5, 4.5), "Switzerland": ("Suisse", 46.8, 8.2),
    "Sweden": ("Suede", 60.1, 18.6), "Norway": ("Norvege", 60.5, 8.5),
    "Finland": ("Finlande", 61.9, 25.7), "Denmark": ("Danemark", 56.3, 9.5),
    "Austria": ("Autriche", 47.5, 14.5), "Czech Republic": ("Rep. Tcheque", 49.8, 15.5),
    "Romania": ("Roumanie", 45.9, 24.9), "Turkey": ("Turquie", 38.9, 35.2),
    "Saudi Arabia": ("Arabie Saoudite", 23.9, 45.1), "UAE": ("Emirats", 24.0, 54.0),
    "Singapore": ("Singapour", 1.3, 103.8), "South Korea": ("Coree du Sud", 35.9, 127.8),
    "Taiwan": ("Taiwan", 23.7, 120.9), "Hong Kong": ("Hong Kong", 22.3, 114.2),
    "Pakistan": ("Pakistan", 30.4, 69.3), "Indonesia": ("Indonesie", -0.8, 113.9),
    "Malaysia": ("Malaisie", 4.2, 109.5), "Thailand": ("Thailande", 15.9, 100.9),
    "Vietnam": ("Vietnam", 14.1, 108.3), "Egypt": ("Egypte", 26.8, 30.8),
    "South Africa": ("Afrique du Sud", -30.6, 22.9), "Nigeria": ("Nigeria", 9.1, 8.7),
    "Kenya": ("Kenya", -0.0, 37.9), "Argentina": ("Argentine", -38.4, -63.6),
    "Colombia": ("Colombie", 4.6, -74.1), "Luxembourg": ("Luxembourg", 49.8, 6.1),
    "Ireland": ("Irlande", 53.4, -8.2), "Portugal": ("Portugal", 39.4, -8.2),
    "Greece": ("Grece", 39.1, 22.0), "Hungary": ("Hongrie", 47.2, 19.5),
    "Slovakia": ("Slovaquie", 48.7, 19.7), "Slovenia": ("Slovenie", 46.2, 14.8),
    "Croatia": ("Croatie", 45.1, 15.2), "Serbia": ("Serbie", 44.0, 21.0),
    "Bulgaria": ("Bulgarie", 42.7, 25.5), "Estonia": ("Estonie", 58.6, 25.0),
    "Latvia": ("Lettonie", 56.9, 24.6), "Lithuania": ("Lituanie", 55.2, 24.0),
    "NHS": ("UK", 51.5, -0.1), "Europe": ("Europe", 54.5, 15.3),
    "NATO": ("Europe", 50.8, 4.4),
    "Etats-Unis": ("USA", 37.1, -95.7), "Royaume-Uni": ("UK", 51.5, -0.1),
    "Allemagne": ("Allemagne", 52.5, 13.4), "Russie": ("Russie", 55.7, 37.6),
    "Chine": ("Chine", 39.9, 116.4), "Coree du Nord": ("Coree du Nord", 39.0, 125.7),
    "Coree du Sud": ("Coree du Sud", 35.9, 127.8), "Japon": ("Japon", 35.7, 139.7),
    "Inde": ("Inde", 20.6, 78.9), "Israel": ("Israel", 31.8, 35.2),
    "Australie": ("Australie", -25.3, 133.8), "Bresil": ("Bresil", -14.2, -51.9),
    "Mexique": ("Mexique", 23.6, -102.6), "Espagne": ("Espagne", 40.5, -3.7),
    "Italie": ("Italie", 41.9, 12.6), "Pologne": ("Pologne", 51.9, 19.1),
    "Pays-Bas": ("Pays-Bas", 52.1, 5.3), "Belgique": ("Belgique", 50.5, 4.5),
    "Suisse": ("Suisse", 46.8, 8.2), "Suede": ("Suede", 60.1, 18.6),
    "Norvege": ("Norvege", 60.5, 8.5), "Finlande": ("Finlande", 61.9, 25.7),
    "Danemark": ("Danemark", 56.3, 9.5), "Autriche": ("Autriche", 47.5, 14.5),
    "Rep. Tcheque": ("Rep. Tcheque", 49.8, 15.5), "Roumanie": ("Roumanie", 45.9, 24.9),
    "Turquie": ("Turquie", 38.9, 35.2), "Arabie Saoudite": ("Arabie Saoudite", 23.9, 45.1),
    "Emirats": ("Emirats", 24.0, 54.0), "Singapour": ("Singapour", 1.3, 103.8),
    "Taiwan": ("Taiwan", 23.7, 120.9), "Indonesie": ("Indonesie", -0.8, 113.9),
    "Malaisie": ("Malaisie", 4.2, 109.5), "Thailande": ("Thailande", 15.9, 100.9),
    "Egypte": ("Egypte", 26.8, 30.8), "Afrique du Sud": ("Afrique du Sud", -30.6, 22.9),
    "Argentine": ("Argentine", -38.4, -63.6), "Colombie": ("Colombie", 4.6, -74.1),
    "Irlande": ("Irlande", 53.4, -8.2), "Grece": ("Grece", 39.1, 22.0),
    "Hongrie": ("Hongrie", 47.2, 19.5), "Slovaquie": ("Slovaquie", 48.7, 19.7),
    "Slovenie": ("Slovenie", 46.2, 14.8), "Croatie": ("Croatie", 45.1, 15.2),
    "Serbie": ("Serbie", 44.0, 21.0), "Bulgarie": ("Bulgarie", 42.7, 25.5),
    "Estonie": ("Estonie", 58.6, 25.0), "Lettonie": ("Lettonie", 56.9, 24.6),
    "Lituanie": ("Lituanie", 55.2, 24.0), "Liban": ("Liban", 33.9, 35.5),
    "Maroc": ("Maroc", 31.8, -7.1), "Algerie": ("Algerie", 28.0, 1.7),
    "Tunisie": ("Tunisie", 33.9, 9.6), "Senegal": ("Senegal", 14.5, -14.5),
    "Cote d'Ivoire": ("Cote d'Ivoire", 7.5, -5.5),
}

SOURCE_GEO = {
    "NewsAPI": ("USA", 37.1, -95.7), "The Hacker News": ("USA", 37.1, -95.7),
    "BleepingComputer": ("USA", 40.7, -74.0), "CISA Alerts": ("USA", 38.9, -77.0),
    "Krebs on Security": ("USA", 38.9, -77.0), "Dark Reading": ("USA", 40.7, -74.0),
    "SecurityWeek": ("USA", 37.4, -122.1), "Cyber Scoop": ("USA", 38.9, -77.0),
    "Threatpost": ("USA", 40.7, -74.0), "Schneier on Security": ("USA", 42.4, -71.1),
    "The Record": ("USA", 38.9, -77.0), "Infosecurity Magazine": ("UK", 51.5, -0.1),
    "Helpnet Security": ("Slovenia", 46.1, 14.5), "Graham Cluley": ("UK", 51.5, -0.1),
    "Zataz": ("France", 48.8, 2.3), "ANSSI": ("France", 48.8, 2.3),
    "CERT-EU": ("Belgium", 50.8, 4.4), "French Breaches": ("France", 48.8, 2.3),
    "Malwarebytes Labs": ("USA", 37.4, -122.1), "Naked Security": ("UK", 51.5, -0.1),
    "We Live Security": ("Slovakia", 48.1, 17.1), "Trend Micro": ("Japan", 35.7, 139.7),
    "Recorded Future Blog": ("USA", 42.4, -71.1), "Cybereason": ("USA", 42.4, -71.1),
    "OSINT Curious": ("USA", 37.1, -95.7), "Bellingcat": ("Netherlands", 52.4, 4.9),
    "Intel471": ("USA", 37.1, -95.7), "Shodan Blog": ("USA", 32.7, -117.2),
    "Maltego Blog": ("Germany", 52.5, 13.4), "NixIntel": ("UK", 51.5, -0.1),
    "Sector035": ("Germany", 52.5, 13.4), "SANS ISC": ("USA", 38.9, -77.0),
    "Mandiant Blog": ("USA", 37.4, -122.1), "CrowdStrike Blog": ("USA", 33.2, -97.1),
    "Securelist": ("Russia", 55.7, 37.6), "Proofpoint": ("USA", 37.4, -122.1),
    "CIRCL": ("Luxembourg", 49.6, 6.1), "Abuse.ch": ("Switzerland", 47.4, 8.5),
    "Citizen Lab": ("Canada", 43.7, -79.4), "The Intercept": ("USA", 40.7, -74.0),
    "OCCRP": ("Netherlands", 52.4, 4.9), "GreyNoise Blog": ("USA", 38.9, -77.0),
    "Censys Blog": ("USA", 42.3, -83.7), "VulnCheck": ("USA", 37.1, -95.7),
    "AttackerKB": ("USA", 37.1, -95.7), "AlienVault OTX": ("USA", 37.1, -95.7),
    "NVD": ("USA", 38.9, -77.0), "Unit42 (Palo Alto)": ("USA", 37.4, -122.1),
    "Talos Intelligence": ("USA", 41.8, -87.6), "Microsoft Security": ("USA", 47.6, -122.1),
    "IBM X-Force": ("USA", 40.7, -74.0), "Elastic Security": ("USA", 37.4, -122.1),
    "Secureworks": ("USA", 33.7, -84.4), "SentinelOne": ("USA", 37.4, -122.1),
    "WithSecure Labs": ("Finland", 60.2, 24.9), "The DFIR Report": ("USA", 37.1, -95.7),
    "Red Canary": ("USA", 39.7, -104.9), "Huntress": ("USA", 39.1, -77.2),
    "NCSC UK": ("UK", 51.5, -0.1), "ENISA": ("Belgium", 50.8, 4.4),
    "Wired Security": ("USA", 37.8, -122.4), "Ars Technica Security": ("USA", 37.8, -122.4),
    "LeMagIT Securite": ("France", 48.8, 2.3), "No.log": ("France", 48.8, 2.3),
    # Sprint 6 -- nouvelles API
    "Ransomware.live": ("France", 48.8, 2.3),
    "ThreatFox": ("Switzerland", 47.4, 8.5),
    "URLhaus": ("Switzerland", 47.4, 8.5),
    "MalwareBazaar": ("Switzerland", 47.4, 8.5),
    # Sprint 6 -- 20 nouveaux RSS
    "Cybermalveillance": ("France", 48.8, 2.3),
    "IT-Connect": ("France", 48.8, 2.3),
    "UnderNews": ("France", 48.8, 2.3),
    "Cyber-news.fr": ("France", 48.8, 2.3),
    "Cyble Blog": ("USA", 37.1, -95.7),
    "SOCRadar Blog": ("USA", 37.1, -95.7),
    "Flashpoint Blog": ("USA", 40.7, -74.0),
    "Security Affairs": ("Italy", 41.9, 12.6),
    "Cyber Security News": ("USA", 37.1, -95.7),
    "Google Threat Intel": ("USA", 37.4, -122.1),
    "Check Point Research": ("Israel", 32.1, 34.8),
    "Fortinet Threat Research": ("USA", 37.4, -122.1),
    "Sophos News": ("UK", 51.5, -0.1),
    "Trellix Blog": ("USA", 37.1, -95.7),
    "IntelligenceX Blog": ("Czech Republic", 50.1, 14.4),
    "CERT-NZ": ("New Zealand", -41.3, 174.8),
    "CERT-AU": ("Australia", -35.3, 149.1),
    "BSI Allemagne": ("Germany", 52.5, 13.4),
    "JPCERT Japon": ("Japan", 35.7, 139.7),
    "Google Security Blog": ("USA", 37.4, -122.1),
    # Sprint 6 batch 2 -- 19 nouveaux RSS
    "TechCrunch Security": ("USA", 37.8, -122.4),
    "Cyber Defense Magazine": ("USA", 37.1, -95.7),
    "Heimdal Blog": ("Denmark", 55.7, 12.6),
    "Troy Hunt": ("Australia", -33.9, 151.2),
    "Bitdefender Labs": ("Romania", 44.4, 26.1),
    "Volexity Blog": ("USA", 38.9, -77.0),
    "Rapid7 Blog": ("USA", 42.4, -71.1),
    "Tenable Blog": ("USA", 39.0, -77.5),
    "Qualys Blog": ("USA", 37.4, -122.1),
    "Nozomi Networks": ("USA", 37.4, -122.1),
    "ZDI Advisories": ("USA", 33.2, -97.1),
    "AWS Security Blog": ("USA", 47.6, -122.3),
    "GitHub Security": ("USA", 37.8, -122.4),
    "Cloudflare Blog": ("USA", 37.8, -122.4),
    "Europol": ("Netherlands", 52.1, 4.3),
    "Interpol Cyber": ("France", 45.7, 4.8),
    "Malware Traffic Analysis": ("USA", 37.1, -95.7),
    "Orange Cyberdefense": ("France", 48.8, 2.3),
    "Sekoia Blog": ("France", 48.8, 2.3),
}


# ==============================================================
# CATEGORY / KEYWORDS / SEVERITY
# ==============================================================
_PATTERNS = [
    ("ransomware", r"ransomware|ransom"),
    ("phishing", r"phishing|spear.{0,8}phishing|credential theft"),
    ("vulnerability", r"vulnerability|cve-[\d]|zero.?day|exploit|rce|lpe|privilege escalation|patch tuesday"),
    ("malware", r"malware|trojan|backdoor|spyware|worm|keylogger|botnet|\brat\b|infostealer|wiper"),
    ("apt", r"\bapt\b|apt\d+|lazarus|fancy bear|cozy bear|sandworm|volt typhoon|scattered spider|charming kitten"),
    ("data_breach", r"data breach|data leak|database dump|exfiltrat|pii|stolen data|leaked credentials"),
    ("supply_chain", r"supply.?chain|third.?party|\bnpm\b|\bpypi\b|dependency"),
    ("ddos", r"\bddos\b|denial.?of.?service|volumetric"),
]
_CAT_LAYER = {
    "vulnerability": "failles", "data_breach": "failles",
    "malware": "menaces", "ransomware": "menaces", "apt": "menaces",
    "phishing": "menaces", "supply_chain": "editeurs",
    "ddos": "infra", "general": "infra",
}
_KW_LIST = [
    "ransomware", "zero-day", "cve", "rce", "lpe", "malware", "phishing",
    "apt", "data breach", "exploit", "supply chain", "ddos", "trojan",
    "backdoor", "botnet", "ioc", "vulnerability", "patch",
]
_HIGH_CATS = {"ransomware", "apt", "data_breach"}

def _classify(title, desc):
    text = (str(title) + " " + str(desc or "")).lower()
    for cat, pat in _PATTERNS:
        if re.search(pat, text):
            return cat
    return "general"

def _is_critical(title, desc):
    text = (str(title) + " " + str(desc or "")).lower()
    return bool(re.search(r"ransomware|zero.day|apt|malware|vulnerability|data.breach", text))

def _extract_kw(title, desc):
    text = (str(title) + " " + str(desc or "")).lower()
    found = [k for k in _KW_LIST if k in text]
    return found[:3] if found else ["cyber"]


# ==============================================================
# CONFIDENCE SCORE
# ==============================================================
def _compute_confidence(gpe_count, has_org, regex_match, spacy_org_match,
                        source_fallback, multiple_gpe, multiple_victims,
                        strong_kw_in_300, has_strong_kw, context_hit=False):
    score = 0
    if not source_fallback:
        score += 40 if not multiple_gpe else 22
    if context_hit:
        score += 8
    if regex_match and spacy_org_match:
        score += 35
    elif regex_match:
        score += 18
    elif spacy_org_match:
        score += 12
    if strong_kw_in_300:
        score += 15
    elif has_strong_kw:
        score += 6
    if source_fallback:
        score -= 20
    if multiple_victims:
        score -= 8
    score = max(0, min(score, 100))
    if score >= 70:
        label = "forte"
    elif score >= 45:
        label = "moyenne"
    else:
        label = "faible"
    return score, label


# ==============================================================
# EXTRACT TARGET -- version amelioree (4 ameliorations)
# ==============================================================
def extract_target(title, desc, source=""):
    text = str(title) + ". " + str(desc or "")
    first_300 = text[:300]
    target_country = target_lat = target_lon = org_cible = None
    context_hit = False

    # Etape 1 : patterns de contexte directs (#4)
    ctx = _context_country(text)
    if ctx:
        target_country, target_lat, target_lon = ctx
        context_hit = True

    # Etape 2 : scan titre sur TARGET_GEO
    if target_country is None:
        for name, geo in TARGET_GEO.items():
            if re.search(r'\b' + re.escape(name) + r'\b', title, re.IGNORECASE):
                target_country, target_lat, target_lon = geo
                break

    # Etape 2b : scan description (#1)
    if target_country is None:
        desc_text = str(desc or "")[:1000]
        for name, geo in TARGET_GEO.items():
            if len(name) >= 4 and re.search(r'\b' + re.escape(name) + r'\b', desc_text, re.IGNORECASE):
                target_country, target_lat, target_lon = geo
                break

    # Extraction victime
    org_candidate = _extract_victim(title) or _extract_victim(text)
    regex_match = org_candidate is not None
    strong_kw_in_300 = bool(_STRONG_CYBER_KW.search(first_300))
    has_strong_kw = bool(_STRONG_CYBER_KW.search(text))
    gpe_hits = []
    spacy_orgs = set()
    spacy_org_match = False

    # Etape 3 : spaCy NER avec proximite (#2 + #3)
    nlp = _get_nlp(source)
    if nlp is not None:
        doc = nlp(text[:1500])
        gpe_candidates = []
        for ent in doc.ents:
            if ent.label_ == "GPE":
                geo = TARGET_GEO.get(ent.text)
                if geo:
                    prox_score = _score_gpe_by_proximity(doc, ent.text, ent.start)
                    gpe_candidates.append((ent.text, geo, prox_score))
                    gpe_hits.append(ent.text)
            elif ent.label_ == "ORG":
                spacy_orgs.add(ent.text)

        if target_country is None and gpe_candidates:
            gpe_candidates.sort(key=lambda x: -x[2])
            best = gpe_candidates[0]
            target_country, target_lat, target_lon = best[1]

        if org_candidate and spacy_orgs:
            spacy_org_match = any(
                org.lower() in org_candidate.lower() or org_candidate.lower() in org.lower()
                for org in spacy_orgs
            )
            org_cible = org_candidate if spacy_org_match else None

    gpe_count = len(gpe_hits) + (1 if target_country and not gpe_hits else 0)
    multiple_gpe = len(gpe_hits) > 1
    multiple_victims = len([p for p in _VICTIM_PATTERNS if re.search(p, text, re.IGNORECASE)]) > 2
    source_fallback = target_country is None

    confidence_score, confidence_label = _compute_confidence(
        gpe_count, org_cible is not None, regex_match, spacy_org_match,
        source_fallback, multiple_gpe, multiple_victims,
        strong_kw_in_300, has_strong_kw, context_hit,
    )
    return target_country, target_lat, target_lon, org_cible, confidence_score, confidence_label


# ==============================================================
# LOAD DATA
# ==============================================================
df = get_stg_articles(limit=1000)
try:
    df_cve = get_mart_k6()
    n_cve = len(df_cve)
except Exception:
    n_cve = 0

_JITTER = {
    "USA": 4.0, "Canada": 5.0, "Australie": 5.0, "Russie": 6.0,
    "Chine": 4.0, "Bresil": 4.0, "Inde": 3.0, "Mexique": 3.0,
    "France": 1.5, "Allemagne": 1.2, "UK": 0.8, "Italie": 1.2,
    "Espagne": 1.5, "Pologne": 1.0, "Ukraine": 1.5, "Turquie": 1.5,
    "Japon": 1.2, "Coree du Sud": 0.6, "Taiwan": 0.3,
    "Singapour": 0.15, "Hong Kong": 0.1, "Belgique": 0.4,
    "Pays-Bas": 0.4, "Suisse": 0.4, "Autriche": 0.6, "Europe": 3.0,
}


# ==============================================================
# BUILD EVENTS -- cache 5 min, avec coordonnees source pour arcs
# ==============================================================
@st.cache_data(ttl=300, show_spinner="Analyse géographique des articles...")
def _build_events(df_json):
    df_local = pd.read_json(StringIO(df_json))
    rng = random.Random(42)
    evts = []

    for _, row in df_local.iterrows():
        src = str(row.get("source", ""))
        if src not in SOURCE_GEO:
            continue
        title = str(row.get("title", ""))[:100]
        desc = str(row.get("description") or "")

        t_country, t_lat, t_lon, org_cible, conf_score, conf_label = extract_target(title, desc, src)

        if t_lat is None:
            fallback_country, t_lat, t_lon = SOURCE_GEO[src]
            t_country = fallback_country
            geo_mode = "source"
        else:
            geo_mode = "target"

        cat = _classify(title, desc)
        layer = _CAT_LAYER[cat]
        critical = _is_critical(title, desc)
        severity = "critical" if critical else "high" if cat in _HIGH_CATS else "medium"
        kw = _extract_kw(title, desc)
        _j = _JITTER.get(t_country, 1.0)
        jlat = round(t_lat + rng.gauss(0, _j * 0.4), 3)
        jlon = round(t_lon + rng.gauss(0, _j * 0.6), 3)
        pub_date = row.get("published_date")
        ts = str(pub_date) if pd.notna(pub_date) else None

        # Attribution : extraction du pays attaquant (APT / patterns)
        atk_country, atk_lat, atk_lon = _extract_attacker(title, desc)

        evts.append({
            "cat": layer, "lat": jlat, "lon": jlon, "country": t_country,
            "title": title, "kw": kw, "severity": severity, "source": src,
            "org_cible": org_cible or "", "geo_mode": geo_mode, "ts": ts,
            "url": str(row.get("url", "") or ""),
            "conf_score": conf_score, "conf_label": conf_label,
            "atk_country": atk_country,
            "atk_lat": atk_lat, "atk_lon": atk_lon,
        })

    # Deduplication
    seen = set()
    dedup = []
    for ev in evts:
        key = re.sub(r'[^a-z0-9]', '', ev["title"].lower())[:60]
        if key not in seen:
            seen.add(key)
            dedup.append(ev)
    return dedup


events = _build_events(df.to_json())

# Stats
n_events = len(events)
n_countries = len({e["country"] for e in events})
n_crit = sum(1 for e in events if e["severity"] == "critical")
cat_counts = {}
for e in events:
    cat_counts[e["cat"]] = cat_counts.get(e["cat"], 0) + 1

# ==============================================================
# HTML TEMPLATE + INJECT
# ==============================================================
map_path = pathlib.Path(__file__).parent.parent / "carte_menaces_globe.html"
html = map_path.read_text(encoding="utf-8")

# Inject events data
# Inject events data -- escape </ to prevent </script> breaking HTML
events_js = json.dumps(events, ensure_ascii=True).replace('</', '<\\/')
# str.replace au lieu de re.sub — evite les problemes de backslash regex
_EVENTS_PLACEHOLDER = "var EVENTS = [\n  {cat:'failles',lat:38.9,lon:-77.0,country:'USA',title:'placeholder',kw:['rce'],severity:'critical',source:'CISA Alerts',org_cible:'',geo_mode:'target',url:'',conf_score:85,conf_label:'forte',ts:null,atk_country:null,atk_lat:null,atk_lon:null}\n];"
html = html.replace(_EVENTS_PLACEHOLDER, f"var EVENTS = {events_js};")

# Inject nav stats
html = re.sub(r'id="n-events">[^<]+', f'id="n-events">{n_events}', html)
html = re.sub(r'id="n-countries">[^<]+', f'id="n-countries">{n_countries}', html)

# Inject category counts
for layer_key, elem_id in [("failles", "c-failles"), ("infra", "c-infra"),
                           ("editeurs", "c-editeurs"), ("menaces", "c-menaces")]:
    n = cat_counts.get(layer_key, 0)
    html = re.sub(rf'id="{elem_id}">[^<]*</div>', f'id="{elem_id}">{n} art</div>', html)

# Inject stats overlay
html = re.sub(r'id="so-articles">[^<]+', f'id="so-articles">{n_events}', html)
html = re.sub(r'id="so-crit">[^<]+', f'id="so-crit">{n_crit}', html)

n_sources_actives = len({e["source"] for e in events})
html = re.sub(
    r'id="sb-sources-title">[^<]*</div>',
    f'id="sb-sources-title">{n_sources_actives} Sources actives</div>',
    html,
)

if df.empty:
    st.warning("Aucun article en base — lancez le pipeline d'acquisition.")
else:
    components.html(html, height=10000, scrolling=False)
