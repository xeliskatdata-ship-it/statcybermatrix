# cleaning.py -- Nettoyage des articles bruts
# Sprint 2 : pipeline 7 etapes
# Sprint 5 : 942 mots-cles sur 13 categories
#
# Entree  : data/raw/articles_YYYY-MM-DD.csv
# Sortie  : data/cleaned/articles_cleaned_YYYY-MM-DD.csv

import logging
import os
import re
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)

# -- Chemins --
RAW_DIR     = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CLEANED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")
os.makedirs(CLEANED_DIR, exist_ok=True)

# -- 942 keywords sur 13 categories (~72 en moyenne) --
# detect_category() parcourt ce dict : premier match gagne
THREAT_KEYWORDS = {

    # Ransomware : chiffrement et extorsion (71 mots)
    "ransomware": [
        "ransomware", "ransom", "lockbit", "blackcat", "ryuk", "conti",
        "akira", "alphv", "clop", "hive", "revil", "maze", "darkside",
        "encrypted", "decryptor", "double extortion", "ransomed",
        "play ransomware", "medusa", "8base", "hunters",
        "royal ransomware", "rhysida", "black basta", "cuba ransomware",
        "bianlian", "ragnar locker", "vice society", "ransomhub", "qilin",
        "inc ransom", "embargo ransomware", "fog ransomware", "dragonforce",
        "cicada3301", "lynx ransomware", "meow ransomware", "triple extortion",
        "ransom note", "file encryption", "bitcoin ransom", "tor payment",
        "data hostage", "restore files", "file locker", "cryptolocker",
        "wannacry", "notpetya", "petya", "bad rabbit", "jigsaw ransomware",
        "dharma ransomware", "phobos ransomware", "makop ransomware",
        "stop djvu", "ransomware gang", "ransomware group", "ransom demand",
        "ransom payment", "ransom negotiations", "leak site", "shame site",
        "extortion group", "data site", "darknet leak", "file recovery",
        "backup destruction", "vss deletion", "shadow copy deletion",
        "wiper component", "encryption key",
    ],

    # Phishing : usurpation et vol de credentials (70 mots)
    "phishing": [
        "phishing", "spear-phishing", "spearphishing", "credential",
        "spoofing", "smishing", "vishing", "whaling", "pretexting",
        "social engineering", "fake login", "credential harvesting",
        "business email compromise", "bec", "email fraud", "impersonation",
        "lure", "malicious email", "phish", "typosquatting",
        "quishing", "qr code phishing", "adversary in the middle", "aitm",
        "evilginx", "modlishka", "html smuggling", "callback phishing",
        "invoice fraud", "payroll diversion", "gift card fraud",
        "wire transfer fraud", "account takeover", "ato",
        "password reset phishing", "fake invoice", "lookalike domain",
        "homograph attack", "punycode attack", "brand impersonation",
        "microsoft phishing", "office365 phishing", "mfa bypass", "otp theft",
        "session hijacking", "cookie theft", "malicious attachment",
        "macro attack", "office macro", "malicious link", "url redirection",
        "open redirector", "phishing kit", "phishing campaign",
        "phishing as a service", "phaas", "bulletproof hosting",
        "credential stuffing", "password spraying", "brute force",
        "account compromise", "executive impersonation", "ceo fraud",
        "domain spoofing", "email spoofing", "dkim bypass", "dmarc bypass",
        "spf bypass", "reply chain attack", "thread hijacking",
    ],

    # Vulnerability : failles et patches (85 mots)
    "vulnerability": [
        "vulnerability", "vulnerabilities", "cve", "patch", "exploit",
        "zero-day", "zero day", "0day", "rce", "remote code execution",
        "sql injection", "xss", "cross-site", "buffer overflow",
        "privilege escalation", "authentication bypass", "arbitrary code",
        "security flaw", "security hole", "unpatched", "proof of concept",
        "poc", "nvd", "mitre", "cvss", "critical flaw", "security update",
        "security advisory", "disclosure", "severity", "attack surface",
        "misconfiguration", "exposed port", "open redirect",
        "ssrf", "server-side request forgery", "xxe", "xml external entity",
        "idor", "insecure direct object reference", "path traversal",
        "directory traversal", "lfi", "rfi", "remote file inclusion",
        "deserialization", "prototype pollution", "race condition",
        "use after free", "heap overflow", "format string", "integer overflow",
        "null pointer", "memory corruption", "type confusion", "out of bounds",
        "code injection", "command injection", "ldap injection",
        "template injection", "ssti", "csrf", "cross-site request forgery",
        "clickjacking", "cache poisoning", "dns rebinding",
        "http request smuggling", "log4shell", "log4j", "proxylogon",
        "proxyshell", "eternalblue", "heartbleed", "shellshock", "spectre",
        "meltdown", "spring4shell", "citrix bleed", "moveit", "cve-2024",
        "patch bypass", "virtual patching", "n-day", "vendor advisory",
        "coordinated disclosure",
    ],

    # Malware : logiciels malveillants (85 mots)
    "malware": [
        "malware", "trojan", "backdoor", "spyware", "rootkit", "botnet",
        "worm", "virus", "keylogger", "stealer", "infostealer", "dropper",
        "loader", "payload", "rat", "remote access trojan", "adware",
        "fileless", "polymorphic", "obfuscated", "shellcode", "stealthy",
        "persistence", "command and control", "c2", "c&c", "redline",
        "raccoon", "agent tesla", "formbook", "asyncrat", "emotet",
        "trickbot", "qakbot", "cobalt strike",
        "njrat", "darkcomet", "remcos", "nanocore", "gh0st rat", "quasar rat",
        "havoc c2", "sliver", "brute ratel", "metasploit", "powershell empire",
        "mimikatz", "lazagne", "procdump", "bloodhound", "sharphound",
        "rubeus", "kerberoasting", "pass the hash", "pass the ticket",
        "golden ticket", "silver ticket", "dcsync", "lsass dump",
        "credential dumping", "process injection", "dll injection",
        "dll sideloading", "process hollowing", "parent pid spoofing",
        "token impersonation", "living off the land", "lotl", "lolbas",
        "lolbin", "certutil", "regsvr32", "mshta", "wscript", "rundll32",
        "msiexec", "wmi abuse", "scheduled task", "registry persistence",
        "startup folder", "service installation", "bootkit", "uefi malware",
        "firmware implant", "mdr evasion",
    ],

    # APT : menaces persistantes avancees (79 mots)
    "apt": [
        "apt", "nation-state", "nation state", "threat actor", "campaign",
        "espionage", "state-sponsored", "state sponsored", "cyber espionage",
        "advanced persistent", "lazarus", "fancy bear", "cozy bear",
        "sandworm", "charming kitten", "volt typhoon", "salt typhoon",
        "turla", "fin7", "ta505", "hafnium", "scattered spider",
        "intelligence gathering", "attribution", "geopolitical",
        "military cyber", "targeted attack", "ttp", "ttps",
        "apt28", "apt29", "apt41", "apt40", "apt10", "apt38", "muddywater",
        "oilrig", "apt34", "kimsuky", "bluenoroff", "andariel", "phosphorus",
        "nobelium", "midnight blizzard", "forest blizzard", "seashell blizzard",
        "silk typhoon", "flax typhoon", "granite typhoon", "star blizzard",
        "cadet blizzard", "unc3944", "unc2452", "intrusion set", "threat group",
        "cyber warfare", "offensive cyber", "hack and leak",
        "influence operation", "information operation", "destructive attack",
        "critical infrastructure attack", "long-term access", "lateral movement",
        "watering hole", "island hopping", "strategic web compromise",
        "supply chain espionage", "intellectual property theft",
        "defense contractor breach", "government espionage",
        "diplomatic espionage", "election interference", "sabotage",
        "pre-positioning", "tiered infrastructure", "bulletproof hosting apt",
        "fast flux", "domain generation algorithm",
    ],

    # DDoS : deni de service (68 mots)
    "ddos": [
        "ddos", "denial of service", "dos attack", "flood", "amplification",
        "distributed denial", "botnet attack", "traffic flood", "layer 7",
        "layer 4", "syn flood", "udp flood", "volumetric attack",
        "application layer attack", "bandwidth exhaustion", "killnet",
        "anonymous sudan", "hacktivist",
        "ntp amplification", "dns amplification", "memcached amplification",
        "ssdp amplification", "icmp flood", "http flood", "slowloris",
        "slow http", "rudy attack", "reflection attack", "carpet bombing",
        "pulse wave", "tcp reset", "protocol attack", "resource exhaustion",
        "connection flood", "ssl flood", "https flood", "api abuse",
        "bot traffic", "traffic scrubbing", "null routing", "anycast",
        "cdn bypass", "cloudflare bypass", "rate limiting bypass",
        "captcha bypass", "ddos for hire", "booter", "stresser", "ip stresser",
        "ddos-as-a-service", "ddos extortion", "ransom ddos", "rddos",
        "packet flood", "network disruption", "service disruption", "outage",
        "downtime", "availability attack", "layer 3 attack", "layer 7 attack",
        "web application ddos", "gaming ddos", "voip flood", "dns flood",
        "recursive dns attack", "nxdomain attack", "dns water torture",
    ],

    # Data breach : fuites et vols de donnees (73 mots)
    "data_breach": [
        "data breach", "breach", "leak", "exposed", "stolen data",
        "exfiltration", "data theft", "data stolen", "personal data", "pii",
        "gdpr", "data dump", "database exposed", "records stolen",
        "customer data", "sensitive data", "compromised data",
        "information disclosure", "data loss", "insider threat",
        "unauthorized access", "data for sale", "dark web",
        "medical records breach", "hipaa breach", "financial data breach",
        "credit card breach", "payment card breach", "social security number",
        "ssn exposure", "biometric data breach", "employee data breach",
        "salary data leaked", "email addresses leaked", "password hash dump",
        "plaintext passwords", "credential database", "combo list",
        "stealer log", "infostealer log", "telegram leak", "hacker forum",
        "breach forum", "raidforums", "haveibeenpwned", "data broker",
        "third party breach", "vendor breach", "cloud misconfiguration breach",
        "open elasticsearch", "open mongodb", "open redis", "open s3 bucket",
        "publicly exposed database", "unsecured database", "data scraping",
        "api data leak", "api key exposed", "github secret",
        "hardcoded credential", "accidental exposure", "privilege misuse",
        "data retention violation", "cross-border transfer",
        "data minimization violation", "right to erasure",
        "data subject request", "controller processor", "joint controller",
        "data protection officer", "dpo", "anonymization failure",
        "re-identification",
    ],

    # Supply chain : attaques chaine d'approvisionnement (69 mots)
    "supply_chain": [
        "supply chain", "third-party", "third party", "dependency",
        "open source attack", "software supply chain", "package", "npm",
        "pypi", "typosquatting package", "malicious package", "build system",
        "ci/cd", "devops attack", "solarwinds", "xz utils", "polyfill",
        "compromised library", "upstream attack",
        "rubygems", "nuget", "maven", "composer", "cargo", "pip install",
        "package manager", "dependency confusion", "namespace confusion",
        "package hijacking", "package takeover", "abandoned package",
        "open source poisoning", "git poisoning", "github actions attack",
        "gitlab attack", "jenkins attack", "artifactory attack", "sbom",
        "software bill of materials", "dependency scanning",
        "transitive dependency", "nested dependency", "lockfile attack",
        "manifest confusion", "install script attack", "postinstall hook",
        "obfuscated npm", "minified malware", "javascript poisoning",
        "electron app attack", "vscode extension attack",
        "browser extension attack", "wordpress plugin attack", "magecart",
        "web skimmer", "digital skimmer", "e-commerce skimmer",
        "javascript injection", "cdn poisoning", "update mechanism attack",
        "auto-update hijack", "signing key compromise", "code signing abuse",
        "trusted binary abuse", "vendor impersonation", "msp attack",
        "managed service provider", "software update poisoning",
        "backdoored sdk",
    ],

    # Cloud : securite infra cloud (73 mots)
    "cloud": [
        "cloud", "aws", "azure", "google cloud", "gcp", "s3 bucket",
        "cloud storage", "misconfigured", "cloud security", "saas", "paas",
        "iaas", "kubernetes", "container security", "docker", "serverless",
        "cloud breach", "identity and access", "iam", "cloud exposure",
        "public bucket", "open bucket",
        "cloud misconfiguration", "cloud account hijacking",
        "cloud credential theft", "access key exposed", "secret key exposed",
        "aws key exposed", "azure credential", "gcp service account",
        "overprivileged role", "privilege escalation cloud",
        "lateral movement cloud", "ec2 instance", "lambda function",
        "azure function", "container escape", "pod escape", "kubernetes rbac",
        "cluster admin", "etcd exposed", "kubernetes dashboard",
        "helm chart attack", "registry poisoning", "docker hub attack",
        "ecr poisoning", "cnapp", "cspm", "cwpp", "ciem", "sase",
        "zero trust cloud", "casb", "shadow it", "unsanctioned saas",
        "m365 attack", "sharepoint exposure", "teams phishing",
        "onedrive exposure", "google workspace attack", "gmail compromise",
        "okta attack", "identity provider attack", "sso abuse", "saml attack",
        "oauth abuse", "token theft cloud", "cloud ransomware", "cloud wiper",
        "cloud exfiltration", "resource hijacking", "cryptomining cloud",
        "cloud backdoor",
    ],

    # IoT : objets connectes (69 mots)
    "iot": [
        "iot", "internet of things", "smart device", "connected device",
        "industrial control", "ics", "scada", "operational technology",
        "ot security", "embedded device", "firmware", "router", "ip camera",
        "smart home", "industrial iot", "iiot", "mirai", "botnet iot",
        "default credentials",
        "plc attack", "programmable logic controller", "hmi attack",
        "human machine interface", "modbus", "dnp3", "profinet", "bacnet",
        "opc ua", "smart meter", "smart grid", "power grid attack",
        "water treatment attack", "medical device attack", "pacemaker hack",
        "hospital iot", "automotive attack", "connected car", "can bus attack",
        "ev charging attack", "smart tv attack", "smart speaker", "smart lock",
        "doorbell camera hack", "dvr exploit", "hikvision", "dahua",
        "axis camera", "ubiquiti", "mikrotik", "netgear exploit", "asus router",
        "tp-link exploit", "zyxel exploit", "firmware reverse engineering",
        "uart access", "jtag exploit", "shodan exposed device",
        "censys exposed device", "default password", "telnet exposed",
        "ssh exposed", "upnp exploit", "botnets iot", "ddos iot",
        "mirai variant", "bashlite", "moobot", "gafgyt", "iot malware",
    ],

    # Cryptojacking : minage illegal (63 mots)
    "cryptojacking": [
        "cryptojacking", "cryptomining", "crypto mining", "monero", "coinhive",
        "mining malware", "cpu hijacking", "browser mining", "xmrig",
        "unauthorized mining", "crypto stealer", "cryptocurrency theft",
        "wallet drainer",
        "bitcoin theft", "ethereum theft", "solana theft", "defi hack",
        "defi exploit", "flash loan attack", "rug pull", "exit scam",
        "nft theft", "nft scam", "opensea attack", "metamask drain",
        "web3 scam", "crypto wallet attack", "private key theft",
        "seed phrase theft", "mnemonic theft", "clipboard hijacking",
        "address substitution", "exchange hack", "hot wallet breach",
        "bridge exploit", "cross-chain bridge attack", "smart contract exploit",
        "reentrancy attack", "front running", "mev attack",
        "cryptocurrency scam", "pump and dump", "crypto laundering",
        "money mule crypto", "mining pool attack", "gpu miner hijack",
        "cloud mining fraud", "cryptojacking script", "webassembly miner",
        "hidden miner", "coin miner", "server mining", "container mining",
        "kubernetes mining", "cloud resource abuse", "cryptostealer",
        "wallet stealing malware", "browser extension stealer",
        "mobile crypto stealer", "fake wallet app", "airdrop scam",
        "ice phishing", "approval phishing",
    ],

    # Regulation : conformite et cadre legal (70 mots)
    "regulation": [
        "regulation", "compliance", "gdpr", "hipaa", "pci dss", "nis2",
        "dora", "iso 27001", "nist", "sec disclosure", "cyber law",
        "legislation", "data protection", "privacy law", "fine", "penalty",
        "audit", "certification", "framework",
        "ccpa", "cpra", "pipeda", "lgpd", "pdpa", "data sovereignty",
        "data residency", "data localization", "cross-border data transfer",
        "standard contractual clauses", "privacy shield", "adequacy decision",
        "data protection authority", "dpa investigation",
        "supervisory authority", "gdpr fine", "ico fine", "cnil fine",
        "mandatory disclosure", "breach notification", "72 hour notification",
        "sec cyber rule", "ftc safeguards rule", "nerc cip", "fisma",
        "fedramp", "cmmc", "soc 2", "soc 2 type ii", "iso 27701", "iso 22301",
        "pci dss v4", "swift cscf", "cyber resilience act",
        "ai act cybersecurity", "digital operational resilience",
        "critical entities resilience", "cer directive",
        "european cyber solidarity act", "enisa", "cisa directive",
        "executive order cybersecurity", "cyber incident report",
        "critical infrastructure protection", "information sharing",
        "public-private partnership", "national cybersecurity strategy",
        "cyber sanctions", "export control cybersecurity",
        "vulnerability disclosure policy", "responsible disclosure",
    ],

    # Incident response : gestion des incidents et forensics (71 mots)
    "incident": [
        "incident response", "breach response", "forensics", "investigation",
        "post-mortem", "remediation", "containment", "threat hunting",
        "detection", "siem", "edr", "xdr", "soar", "playbook", "ioc",
        "indicator of compromise", "threat intelligence", "cyber insurance",
        "recovery", "business continuity",
        "digital forensics", "dfir", "memory forensics", "disk forensics",
        "network forensics", "log analysis", "timeline analysis",
        "artifact collection", "chain of custody", "evidence preservation",
        "volatile data", "dead box forensics", "live response",
        "behavioral detection", "anomaly detection", "alert triage",
        "false positive", "mean time to detect", "mttd",
        "mean time to respond", "mttr", "dwell time", "kill chain",
        "mitre att&ck", "diamond model", "unified kill chain",
        "threat modeling", "purple team", "red team", "blue team",
        "tabletop exercise", "cyber exercise", "war game", "crisis management",
        "incident commander", "legal hold", "regulatory notification",
        "law enforcement notification", "threat sharing", "isac", "stix taxii",
        "misp", "opencti", "threat feed", "dark web monitoring",
        "executive briefing", "lessons learned", "root cause analysis",
        "after action report", "cyber resilience", "security operations center",
    ],
}


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def _clean_text(text):
    # Supprime HTML, entites, caracteres de controle, espaces multiples
    if not text or text == "":
        return ""
    text = re.sub(r"<[^>]+>", "", str(text))
    text = re.sub(r"&\w+;", " ", text)
    text = re.sub(r"[\x00-\x1F\x7F]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_date(val):
    # Normalise une date vers YYYY-MM-DD HH:MM:SS (UTC)
    if not val or val == "":
        return None
    try:
        val = str(val).replace("Z", "+00:00").strip()
        return pd.to_datetime(val, utc=True).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _detect_category(row):
    # Premier match gagne — meme logique que le CASE WHEN dbt
    text = (str(row.get("title", "")) + " " + str(row.get("description", ""))).lower()
    for category, keywords in THREAT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return "general"


# ---------------------------------------------------
# 1. CHARGEMENT
# ---------------------------------------------------
def _load_latest_raw():
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]
    if not files:
        raise FileNotFoundError("Aucun fichier CSV dans data/raw/")

    latest   = sorted(files)[-1]
    filepath = os.path.join(RAW_DIR, latest)
    df       = pd.read_csv(filepath, encoding="utf-8")

    log.info("Charge : %s (%d lignes x %d colonnes)", latest, *df.shape)
    return df, latest


# ---------------------------------------------------
# 2. SUPPRESSION DES DOUBLONS
# ---------------------------------------------------
def _remove_duplicates(df):
    before = len(df)
    df = df.drop_duplicates(subset=["url"],   keep="first")
    df = df.drop_duplicates(subset=["title"], keep="first")
    log.info("Doublons supprimes : %d  |  Restants : %d", before - len(df), len(df))
    return df


# ---------------------------------------------------
# 3. VALEURS MANQUANTES
# ---------------------------------------------------
def _handle_missing(df):
    fills = {"description": "", "title": "Sans titre", "url": "", "published_at": ""}
    df = df.fillna(fills)
    log.info("NaN remplaces")
    return df


# ---------------------------------------------------
# 4. NORMALISATION DES DATES
# ---------------------------------------------------
def _normalize_dates(df):
    df["published_at"]   = df["published_at"].apply(_parse_date)
    df["published_date"] = pd.to_datetime(df["published_at"], errors="coerce").dt.strftime("%Y-%m-%d")

    ok = df["published_at"].notna().sum()
    ko = df["published_at"].isna().sum()
    log.info("Dates : %d OK / %d non parsees", ok, ko)
    return df


# ---------------------------------------------------
# 5. NORMALISATION DU TEXTE
# ---------------------------------------------------
def _normalize_text(df):
    df["title"]       = df["title"].apply(_clean_text)
    df["description"] = df["description"].apply(_clean_text).str[:500]
    log.info("Textes normalises : %d articles", len(df))
    return df


# ---------------------------------------------------
# 6. COLONNES METIER
# ---------------------------------------------------
def _add_columns(df):
    df["content_length"] = df["description"].str.len()
    df["category"]       = df.apply(_detect_category, axis=1)

    dist = df["category"].value_counts()
    for cat, n in dist.items():
        log.info("  %-20s : %d", cat, n)
    return df


# ---------------------------------------------------
# 7. SAUVEGARDE
# ---------------------------------------------------
def _save_cleaned(df, source_filename):
    date_part = source_filename.replace("articles_", "").replace(".csv", "")
    filepath  = os.path.join(CLEANED_DIR, f"articles_cleaned_{date_part}.csv")
    df.to_csv(filepath, index=False, encoding="utf-8")
    log.info("Sauvegarde : %d articles -> %s", len(df), filepath)
    return filepath


# ---------------------------------------------------
# ORCHESTRATION
# ---------------------------------------------------
def main():
    log.info("=" * 50)
    log.info("CyberPulse -- Nettoyage S5 -- 942 keywords / 13 categories")
    log.info("=" * 50)

    df, source_filename = _load_latest_raw()
    df = _remove_duplicates(df)
    df = _handle_missing(df)
    df = _normalize_dates(df)
    df = _normalize_text(df)
    df = _add_columns(df)
    filepath = _save_cleaned(df, source_filename)

    return filepath


if __name__ == "__main__":
    main()