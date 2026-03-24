"""
Sprint 2 : Nettoyage des articles bruts

Entree  : data/raw/articles_YYYY-MM-DD.csv
Sortie  : data/cleaned/articles_cleaned_YYYY-MM-DD.csv

Colonnes en entree  : source, title, description, url, published_at, collected_at
Colonnes en sortie  : source, title, description, url, published_at, collected_at,
                      published_date, content_length, category
"""

import pandas as pd
import os
import re
from datetime import datetime


# ---------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------

# Dossier source : fichiers bruts collectes par acquisition.py
RAW_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')

# Dossier destination : fichiers nettoyes prets pour l'ETL
CLEANED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'cleaned')
os.makedirs(CLEANED_DIR, exist_ok=True)

# Dictionnaire de detection des categories de menace par mots-cles
# Utilise dans add_columns() pour creer la colonne "category"
# Enrichi avec de nombreuses variantes et nouvelles categories
THREAT_KEYWORDS = {

    # --- Ransomware : logiciels de chiffrement et extorsion
    "ransomware"    : [
        "ransomware", "ransom", "lockbit", "blackcat", "ryuk", "conti",
        "akira", "alphv", "clop", "hive", "revil", "maze", "darkside",
        "encrypted", "decryptor", "double extortion", "ransomed",
        "play ransomware", "medusa", "8base", "hunters"
    ],

    # --- Phishing : usurpation d'identite et vol de credentials
    "phishing"      : [
        "phishing", "spear-phishing", "spearphishing", "credential",
        "spoofing", "smishing", "vishing", "whaling", "pretexting",
        "social engineering", "fake login", "credential harvesting",
        "business email compromise", "bec", "email fraud", "impersonation",
        "lure", "malicious email", "phish", "typosquatting"
    ],

    # --- Vulnerability : failles et patches de securite
    "vulnerability" : [
        "vulnerability", "vulnerabilities", "cve", "patch", "exploit",
        "zero-day", "zero day", "0day", "rce", "remote code execution",
        "sql injection", "xss", "cross-site", "buffer overflow",
        "privilege escalation", "authentication bypass", "arbitrary code",
        "security flaw", "security hole", "unpatched", "proof of concept",
        "poc", "nvd", "mitre", "cvss", "critical flaw", "security update",
        "security advisory", "disclosure", "severity", "attack surface",
        "misconfiguration", "exposed port", "open redirect"
    ],

    # --- Malware : logiciels malveillants generiques
    "malware"       : [
        "malware", "trojan", "backdoor", "spyware", "rootkit",
        "botnet", "worm", "virus", "keylogger", "stealer", "infostealer",
        "dropper", "loader", "payload", "rat", "remote access trojan",
        "adware", "fileless", "polymorphic", "obfuscated", "shellcode",
        "stealthy", "persistence", "command and control", "c2", "c&c",
        "redline", "raccoon", "agent tesla", "formbook", "asyncrat",
        "emotet", "trickbot", "qakbot", "cobalt strike"
    ],

    # --- APT : menaces persistantes avancees et acteurs etatiques
    "apt"           : [
        "apt", "nation-state", "nation state", "threat actor", "campaign",
        "espionage", "state-sponsored", "state sponsored", "cyber espionage",
        "advanced persistent", "lazarus", "fancy bear", "cozy bear",
        "sandworm", "charming kitten", "volt typhoon", "salt typhoon",
        "turla", "fin7", "ta505", "hafnium", "scattered spider",
        "intelligence gathering", "attribution", "geopolitical",
        "military cyber", "targeted attack", "ttp", "ttps"
    ],

    # --- DDoS : attaques par deni de service
    "ddos"          : [
        "ddos", "denial of service", "dos attack", "flood", "amplification",
        "distributed denial", "botnet attack", "traffic flood", "layer 7",
        "layer 4", "syn flood", "udp flood", "volumetric attack",
        "application layer attack", "bandwidth exhaustion", "killnet",
        "anonymous sudan", "hacktivist"
    ],

    # --- Data breach : fuites et vols de donnees
    "data_breach"   : [
        "data breach", "breach", "leak", "exposed", "stolen data",
        "exfiltration", "data theft", "data stolen", "personal data",
        "pii", "gdpr", "data dump", "database exposed", "records stolen",
        "customer data", "sensitive data", "compromised data",
        "information disclosure", "data loss", "insider threat",
        "unauthorized access", "data for sale", "dark web"
    ],

    # --- Supply chain : attaques via les chaines d'approvisionnement
    "supply_chain"  : [
        "supply chain", "third-party", "third party", "dependency",
        "open source attack", "software supply chain", "package",
        "npm", "pypi", "typosquatting package", "malicious package",
        "build system", "ci/cd", "devops attack", "solarwinds",
        "xz utils", "polyfill", "compromised library", "upstream attack"
    ],

    # --- Cloud : securite des infrastructures cloud
    "cloud"         : [
        "cloud", "aws", "azure", "google cloud", "gcp", "s3 bucket",
        "cloud storage", "misconfigured", "cloud security", "saas",
        "paas", "iaas", "kubernetes", "container security", "docker",
        "serverless", "cloud breach", "identity and access", "iam",
        "cloud exposure", "public bucket", "open bucket"
    ],

    # --- IoT : securite des objets connectes
    "iot"           : [
        "iot", "internet of things", "smart device", "connected device",
        "industrial control", "ics", "scada", "operational technology",
        "ot security", "embedded device", "firmware", "router",
        "ip camera", "smart home", "industrial iot", "iiot",
        "mirai", "botnet iot", "default credentials"
    ],

    # --- Cryptojacking : minage illegal de cryptomonnaies
    "cryptojacking" : [
        "cryptojacking", "cryptomining", "crypto mining", "monero",
        "coinhive", "mining malware", "cpu hijacking", "browser mining",
        "xmrig", "unauthorized mining", "crypto stealer",
        "cryptocurrency theft", "wallet drainer"
    ],

    # --- Regulation : conformite et cadre legal
    "regulation"    : [
        "regulation", "compliance", "gdpr", "hipaa", "pci dss",
        "nis2", "dora", "iso 27001", "nist", "sec disclosure",
        "cyber law", "legislation", "data protection", "privacy law",
        "fine", "penalty", "audit", "certification", "framework"
    ],

    # --- Incident response : gestion des incidents et forensics
    "incident"      : [
        "incident response", "breach response", "forensics", "investigation",
        "post-mortem", "remediation", "containment", "threat hunting",
        "detection", "siem", "edr", "xdr", "soar", "playbook",
        "ioc", "indicator of compromise", "threat intelligence",
        "cyber insurance", "recovery", "business continuity"
    ],
}


# ---------------------------------------------------
# 1. CHARGEMENT
# ---------------------------------------------------
def load_latest_raw():
    """
    Charge le fichier CSV brut le plus recent depuis data/raw/.
    Retourne le DataFrame et le nom du fichier source.
    """
    # Lister tous les fichiers CSV dans data/raw/
    files = [f for f in os.listdir(RAW_DIR) if f.endswith('.csv')]

    if not files:
        raise FileNotFoundError("Aucun fichier CSV dans data/raw/")

    # Prendre le plus recent (tri alphabetique = tri chronologique avec format YYYY-MM-DD)
    latest   = sorted(files)[-1]
    filepath = os.path.join(RAW_DIR, latest)

    # Charger en DataFrame pandas
    df = pd.read_csv(filepath, encoding='utf-8')

    print(f"Fichier charge       : {latest}")
    print(f"Dimensions initiales : {df.shape[0]} lignes x {df.shape[1]} colonnes")
    print(f"Colonnes             : {list(df.columns)}")

    return df, latest


# ---------------------------------------------------
# 2. SUPPRESSION DES DOUBLONS
# ---------------------------------------------------
def remove_duplicates(df):
    """
    Supprime les articles en double.

    Criteres de doublon :
      - Meme URL   : deux sources qui publient le meme lien
      - Meme titre : articles repris mot pour mot sous une URL differente
    """
    before = len(df)

    # Supprimer les doublons sur l'URL (identifiant unique d'un article)
    df = df.drop_duplicates(subset=['url'], keep='first')

    # Supprimer les doublons sur le titre (articles republies)
    df = df.drop_duplicates(subset=['title'], keep='first')

    after = len(df)
    print(f"Doublons supprimes   : {before - after}  |  Articles restants : {after}")

    return df


# ---------------------------------------------------
# 3. TRAITEMENT DES VALEURS MANQUANTES
# ---------------------------------------------------
def handle_missing(df):
    """
    Remplace les NaN par des valeurs neutres pour eviter les erreurs en aval.

    Etat constate sur les donnees reelles (325 articles, 2026-03-18) :
      - description : 10 NaN  --> remplace par chaine vide ''
      - title       :  0 NaN  --> traite par precaution
      - url         :  0 NaN  --> traite par precaution
      - published_at:  0 NaN  --> traite par precaution
    """
    before = df.isnull().sum().sum()

    # Remplacer les descriptions manquantes par une chaine vide
    df['description'] = df['description'].fillna('')

    # Remplacer les titres manquants par une valeur neutre lisible
    df['title'] = df['title'].fillna('Sans titre')

    # Remplacer les URLs manquantes par une chaine vide
    df['url'] = df['url'].fillna('')

    # Remplacer les dates manquantes (sera None apres normalisation)
    df['published_at'] = df['published_at'].fillna('')

    after = df.isnull().sum().sum()
    print(f"Valeurs manquantes   : {before} --> {after}")

    return df


# ---------------------------------------------------
# 4. NORMALISATION DES DATES
# ---------------------------------------------------
def normalize_dates(df):
    """
    Convertit published_at au format standard YYYY-MM-DD HH:MM:SS.

    Format entree (ISO 8601) : '2026-03-12T15:40:00Z'
    Format sortie             : '2026-03-12 15:40:00'

    MODIFIE  : published_at  --> format lisible sans fuseau horaire
    CREE     : published_date --> date seule (YYYY-MM-DD) pour les agregations KPI
    """
    def parse_date(val):
        if not val or val == '':
            return None
        try:
            # Remplacer Z par +00:00 pour que pandas comprenne le fuseau UTC
            val = str(val).replace('Z', '+00:00').strip()
            dt  = pd.to_datetime(val, utc=True)
            # Retourner sans le fuseau horaire pour simplifier le stockage
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return None

    # Appliquer la conversion sur chaque valeur de la colonne
    df['published_at'] = df['published_at'].apply(parse_date)

    # NOUVELLE COLONNE published_date : date seule sans heure, pour les KPIs temporels
    df['published_date'] = pd.to_datetime(
        df['published_at'], errors='coerce'
    ).dt.strftime('%Y-%m-%d')

    ok = df['published_at'].notna().sum()
    ko = df['published_at'].isna().sum()
    print(f"Dates normalisees    : {ok} OK  |  {ko} non parsees")

    return df


# ---------------------------------------------------
# 5. NORMALISATION DU TEXTE
# ---------------------------------------------------
def normalize_text(df):
    """
    Nettoie les colonnes textuelles title et description.

    MODIFIE : title       --> suppression HTML, espaces, caracteres speciaux
    MODIFIE : description --> suppression HTML + troncature a 500 caracteres max

    Operations appliquees :
      - Suppression des balises HTML residuelles  (<b>, <p>, <a href=...> etc.)
      - Suppression des entites HTML              (&amp; &nbsp; &lt; etc.)
      - Suppression des caracteres de controle    (\x00 \x1F etc.)
      - Normalisation des espaces multiples en un seul espace
    """
    def clean_text(text):
        if not text or text == '':
            return ''
        # Supprimer les balises HTML residuelles
        text = re.sub(r'<[^>]+>', '', str(text))
        # Supprimer les entites HTML
        text = re.sub(r'&\w+;', ' ', text)
        # Supprimer les caracteres de controle invisibles
        text = re.sub(r'[\x00-\x1F\x7F]', '', text)
        # Remplacer les espaces multiples par un seul espace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    # Nettoyer les deux colonnes textuelles
    df['title']       = df['title'].apply(clean_text)
    df['description'] = df['description'].apply(clean_text)

    # Tronquer les descriptions a 500 caracteres pour eviter les problemes en base
    df['description'] = df['description'].str[:500]

    print(f"Textes normalises    : {len(df)} articles traites")

    return df


# ---------------------------------------------------
# 6. CREATION DES COLONNES UTILES
# ---------------------------------------------------
def detect_category(row):
    """
    Detecte la categorie de menace d'un article a partir de ses mots-cles.

    Parcourt THREAT_KEYWORDS et retourne la premiere categorie trouvee
    dans la concatenation title + description (en minuscules).
    Retourne 'general' si aucun mot-cle ne correspond.

    Sortie au niveau du module pour pouvoir etre testee independamment :
      from cleaning import detect_category
    """
    # Concatener title + description en minuscules pour la recherche
    text = (str(row.get('title', '')) + ' ' + str(row.get('description', ''))).lower()

    # Parcourir chaque categorie et tester ses mots-cles
    for category, keywords in THREAT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                # Retourner la premiere categorie trouvee
                return category

    # Aucun mot-cle trouve : classer en "general"
    return 'general'


# ---------------------------------------------------
# 6. CREATION DES COLONNES UTILES
# ---------------------------------------------------
def add_columns(df):
    """
    Ajoute deux colonnes metier pour les KPIs du dashboard Streamlit.

    CREE : content_length
      --> Longueur de la description en nombre de caracteres
      --> Utile pour filtrer les articles trop courts (peu informatifs)
      --> Alimente le KPI "qualite des sources"

    CREE : category
      --> Type de menace detecte par detect_category() sur title + description
      --> Valeurs possibles : ransomware, phishing, vulnerability, malware,
                              apt, ddos, data_breach, supply_chain, general
      --> Utilise le dictionnaire THREAT_KEYWORDS defini en haut du fichier
      --> Alimente le KPI3 (repartition par type de menace) et KPI4 (tendances)
    """
    # NOUVELLE COLONNE content_length : longueur de la description nettoyee
    df['content_length'] = df['description'].str.len()

    # NOUVELLE COLONNE category : appel de detect_category() au niveau module
    df['category'] = df.apply(detect_category, axis=1)

    # Afficher la distribution des categories pour verification
    print("Distribution des categories :")
    for cat, count in df['category'].value_counts().items():
        print(f"  {cat:<20} : {count} articles")

    return df


# ---------------------------------------------------
# 7. SAUVEGARDE
# ---------------------------------------------------
def save_cleaned(df, source_filename):
    """
    Sauvegarde le DataFrame nettoye dans data/cleaned/.

    Nom du fichier de sortie : articles_cleaned_YYYY-MM-DD.csv

    Colonnes finales du fichier nettoye :
      source, title, description, url, published_at, collected_at,
      published_date (NOUVEAU), content_length (NOUVEAU), category (NOUVEAU)
    """
    # Construire le nom du fichier de sortie a partir de la date du fichier source
    date_part = source_filename.replace('articles_', '').replace('.csv', '')
    filename  = f"articles_cleaned_{date_part}.csv"
    filepath  = os.path.join(CLEANED_DIR, filename)

    # Sauvegarder sans l'index pandas (index=False evite une colonne numerotation inutile)
    df.to_csv(filepath, index=False, encoding='utf-8')

    print(f"Fichier sauvegarde   : {filepath}")
    print(f"  > {len(df)} articles")
    print(f"  > Colonnes finales : {list(df.columns)}")

    return filepath


# ---------------------------------------------------
# FONCTION PRINCIPALE
# ---------------------------------------------------
def clean_all():
    """
    Orchestre le pipeline de nettoyage dans l'ordre :
    Chargement -> Doublons -> NaN -> Dates -> Texte -> Colonnes -> Sauvegarde
    """
    print("=" * 55)
    print("CyberPulse -- Nettoyage S2")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # Charger le fichier brut le plus recent
    df, source_filename = load_latest_raw()

    print("\n-- Etape 1 : Suppression des doublons --")
    df = remove_duplicates(df)

    print("\n-- Etape 2 : Traitement des valeurs manquantes --")
    df = handle_missing(df)

    print("\n-- Etape 3 : Normalisation des dates --")
    df = normalize_dates(df)

    print("\n-- Etape 4 : Normalisation du texte --")
    df = normalize_text(df)

    print("\n-- Etape 5 : Creation des colonnes utiles --")
    df = add_columns(df)

    print("\n-- Etape 6 : Sauvegarde --")
    filepath = save_cleaned(df, source_filename)

    print("\nNettoyage termine !")
    return filepath


# ---------------------------------------------------
# LANCEMENT DIRECT
# ---------------------------------------------------
if __name__ == "__main__":
    clean_all()
