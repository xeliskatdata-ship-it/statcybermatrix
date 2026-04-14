# utils_lang.py -- Internationalisation EN/FR
# Defaut : anglais. Le francais traduit tout SAUF :
#   - noms de categories de menaces (ransomware, phishing, apt...)
#   - noms des sources (The Hacker News, Zataz...)
#   - noms des attaquants / groupes APT (LockBit, Fancy Bear...)
# Usage : t("KPI 3 title", lang) / translate_text(text, "fr")

from deep_translator import GoogleTranslator

# Colonnes a ne JAMAIS traduire (noms propres, categories techniques)
NO_TRANSLATE_COLS = {"source", "category", "atk_country", "attacker", "group_name", "cve_id", "url"}

TRANSLATIONS = {
    # -- Navigation / Sidebar --
    "Home":                     {"fr": "Accueil",                           "en": "Home"},
    "Language":                 {"fr": "Langue",                            "en": "Language"},
    "Sources active":           {"fr": "Sources actives",                   "en": "Active sources"},
    "Articles loaded":          {"fr": "Articles charges",                  "en": "Articles loaded"},
    "Global filters":           {"fr": "Filtres globaux",                   "en": "Global filters"},
    "Sources":                  {"fr": "Sources",                           "en": "Sources"},
    "Period":                   {"fr": "Periode",                           "en": "Period"},
    "Threat type":              {"fr": "Type de menace",                    "en": "Threat type"},
    "Refresh":                  {"fr": "Rafraichir les donnees",            "en": "Refresh data"},
    "Last update":              {"fr": "Derniere mise a jour",              "en": "Last update"},
    "Filter by period":         {"fr": "Filtrer par periode",               "en": "Filter by period"},
    "All":                      {"fr": "Tout",                              "en": "All"},
    "Last 24h":                 {"fr": "Dernieres 24h",                     "en": "Last 24h"},
    "Last 7 days":              {"fr": "7 derniers jours",                  "en": "Last 7 days"},
    "Last 30 days":             {"fr": "30 derniers jours",                 "en": "Last 30 days"},
    "Loading":                  {"fr": "Chargement...",                     "en": "Loading..."},

    # -- Accueil --
    "Overview":                 {"fr": "Vue d'ensemble",                    "en": "Overview"},
    "Articles collected":       {"fr": "Articles collectes",                "en": "Articles collected"},
    "Filtered articles":        {"fr": "Articles filtres",                  "en": "Filtered articles"},
    "Top threat":               {"fr": "Menace principale",                 "en": "Top threat"},
    "Top source":               {"fr": "Source la + active",                "en": "Most active source"},
    "Avg length":               {"fr": "Longueur moy.",                     "en": "Avg length"},
    "Data preview":             {"fr": "Apercu des donnees",                "en": "Data preview"},
    "Download CSV":             {"fr": "Telecharger (CSV)",                 "en": "Download (CSV)"},
    "Export CSV":               {"fr": "Exporter CSV",                      "en": "Export CSV"},
    "Hourly collection":        {"fr": "Collecte toutes les heures",        "en": "Hourly collection"},
    "Cyber monitoring":         {"fr": "Veille automatique de l'actualite cyber",
                                 "en": "Automated cyber threat monitoring"},
    "See analysis":             {"fr": "Voir l'analyse",                    "en": "See analysis"},
    "See map":                  {"fr": "Voir la carte",                     "en": "See map"},
    "Navigation hint":          {"fr": "Utilisez la barre laterale pour naviguer entre les KPIs.",
                                 "en": "Use the sidebar to navigate between KPIs."},
    "No data":                  {"fr": "Aucune donnee disponible avec les filtres selectionnes.",
                                 "en": "No data available with selected filters."},
    "Go to home":               {"fr": "Retournez sur l'accueil pour charger les donnees.",
                                 "en": "Go back to home to load data."},
    "Active sources":           {"fr": "Sources actives",                   "en": "Active sources"},
    "Open live map":            {"fr": "Ouvrir la carte live",              "en": "Open live map"},

    # -- KPI 1 : Articles --
    "KPI 1 title":              {"fr": "Articles collectes par jour / par source",
                                 "en": "Articles collected per day / per source"},
    "KPI 1 desc":               {"fr": "Volume par source et evolution temporelle",
                                 "en": "Volume per source and temporal evolution"},
    "Publication date":         {"fr": "Date de publication",               "en": "Publication date"},
    "Source name":              {"fr": "Nom de la source",                  "en": "Source name"},
    "Number of articles":       {"fr": "Nombre d'articles",                 "en": "Number of articles"},
    "Daily volume":             {"fr": "Volume quotidien",                  "en": "Daily volume"},
    "Top sources":              {"fr": "Top sources",                       "en": "Top sources"},
    "Summary by source":        {"fr": "Resume par source",                 "en": "Summary by source"},

    # -- KPI 2 : Keywords --
    "KPI 2 title":              {"fr": "Top mots-cles frequents (7 jours glissants)",
                                 "en": "Top frequent keywords (7-day rolling window)"},
    "KPI 2 desc":               {"fr": "Frequence des termes et sujets dominants",
                                 "en": "Term frequency and dominant topics"},
    "Keywords":                 {"fr": "Mots-cles",                         "en": "Keywords"},
    "Occurrences":              {"fr": "Occurrences",                       "en": "Occurrences"},
    "Category":                 {"fr": "Categorie",                         "en": "Category"},
    "Source count":             {"fr": "Nb de sources",                     "en": "Source count"},
    "Article count":            {"fr": "Nb d'articles",                     "en": "Article count"},
    "Top N keywords":           {"fr": "Nombre de mots-cles",              "en": "Number of keywords"},
    "Heatmap":                  {"fr": "Carte de chaleur",                  "en": "Heatmap"},
    "Related articles":         {"fr": "Articles lies",                     "en": "Related articles"},

    # -- KPI 3 : Threats --
    "KPI 3 title":              {"fr": "Repartition par type de menace",    "en": "Distribution by threat type"},
    "KPI 3 desc":               {"fr": "Repartition Ransomware, Phishing, APT...",
                                 "en": "Breakdown: Ransomware, Phishing, APT..."},
    "Threat category":          {"fr": "Categorie de menace",               "en": "Threat category"},
    "Distribution":             {"fr": "Repartition",                       "en": "Distribution"},
    "Proportion":               {"fr": "Proportion",                        "en": "Proportion"},
    "Visualization":            {"fr": "Visualisation",                     "en": "Visualization"},
    "Donut chart":              {"fr": "Camembert (donut)",                 "en": "Donut chart"},
    "Treemap":                  {"fr": "Treemap",                           "en": "Treemap"},
    "Detail by threat":         {"fr": "Detail par menace",                 "en": "Detail by threat"},

    # -- KPI 4 : Trends --
    "KPI 4 title":              {"fr": "Evolution des mentions d'une menace dans le temps",
                                 "en": "Evolution of threat mentions over time"},
    "KPI 4 desc":               {"fr": "Evolution hebdomadaire des vecteurs",
                                 "en": "Weekly evolution of threat vectors"},
    "Trend":                    {"fr": "Tendance",                          "en": "Trend"},
    "Mentions":                 {"fr": "Mentions",                          "en": "Mentions"},
    "Weekly":                   {"fr": "Hebdomadaire",                      "en": "Weekly"},
    "Monthly":                  {"fr": "Mensuel",                           "en": "Monthly"},
    "Evolution":                {"fr": "Evolution",                         "en": "Evolution"},
    "Last N days":              {"fr": "Derniers N jours",                  "en": "Last N days"},
    "Threat to track":          {"fr": "Menace a suivre",                   "en": "Threat to track"},
    "Compare with":             {"fr": "Comparer avec",                     "en": "Compare with"},
    "Filter by threat":         {"fr": "Filtrer par menace",                "en": "Filter by threat"},
    "Peak detected":            {"fr": "Pic detecte le",                    "en": "Peak detected on"},
    "With mentions":            {"fr": "mentions",                          "en": "mentions"},

    # -- KPI 5 : Alerts --
    "KPI 5 title":              {"fr": "Alertes critiques par semaine",     "en": "Critical alerts per week"},
    "KPI 5 desc":               {"fr": "Nombre d'alertes critiques et volatilite",
                                 "en": "Critical alert count and volatility"},
    "Alerts":                   {"fr": "Alertes",                           "en": "Alerts"},
    "Critical alerts":          {"fr": "Alertes critiques",                 "en": "Critical alerts"},
    "Week":                     {"fr": "Semaine",                           "en": "Week"},
    "Alert threshold":          {"fr": "Seuil d'alerte",                    "en": "Alert threshold"},
    "Above threshold":          {"fr": "Au-dessus du seuil",               "en": "Above threshold"},
    "Weeks above threshold":    {"fr": "Semaines ayant depasse le seuil :", "en": "Weeks above threshold:"},
    "No alert":                 {"fr": "Aucune semaine n'a depasse le seuil.", "en": "No week exceeded the threshold."},
    "Critical categories":      {"fr": "Categories critiques",              "en": "Critical categories"},

    # -- KPI 6 : CVE --
    "KPI 6 title":              {"fr": "Top CVE les plus mentionnees",      "en": "Most mentioned CVEs"},
    "KPI 6 desc":               {"fr": "Vulnerabilites officielles detaillees",
                                 "en": "Detailed official vulnerabilities"},
    "CVE":                      {"fr": "CVE",                               "en": "CVE"},
    "CVE ID":                   {"fr": "Identifiant CVE",                   "en": "CVE ID"},
    "Nb mentions":              {"fr": "Nb de mentions",                    "en": "Nb mentions"},
    "CVE details":              {"fr": "Details CVE",                       "en": "CVE details"},
    "Top N CVE":                {"fr": "Nombre de CVE",                     "en": "Number of CVEs"},
    "Exact ranking":            {"fr": "Classement exact",                  "en": "Exact ranking"},
    "Sorted table":             {"fr": "Tableau classe",                    "en": "Sorted table"},
    "Ranked table":             {"fr": "Tableau classe",                    "en": "Ranked table"},
    "No CVE found":             {"fr": "Aucune CVE detectee.",              "en": "No CVE detected."},
    "Translate":                {"fr": "Traduire",                          "en": "Translate"},

    # -- Carte des menaces --
    "Threat map":               {"fr": "Carte mondiale des menaces",        "en": "World threat map"},
    "Threat map desc":          {"fr": "Visualisation geographique des hotspots et origines des attaques.",
                                 "en": "Geographic visualization of attack hotspots and origins."},
    "Attacked country":         {"fr": "Pays attaque",                      "en": "Attacked country"},
    "Source country":           {"fr": "Pays de la source",                 "en": "Source country"},
    "Confidence":               {"fr": "Confiance",                         "en": "Confidence"},
    "High":                     {"fr": "Forte",                             "en": "High"},
    "Medium":                   {"fr": "Moyenne",                           "en": "Medium"},
    "Low":                      {"fr": "Faible",                            "en": "Low"},
    "Victim":                   {"fr": "Victime",                           "en": "Victim"},
    "Threat":                   {"fr": "Menace",                            "en": "Threat"},
    "Geolocation":              {"fr": "Geolocalisation",                   "en": "Geolocation"},
    "Real time":                {"fr": "Temps reel",                        "en": "Real time"},
}


def t(key, lang="en"):
    """Retourne la traduction. Defaut = anglais."""
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, key)


def translate_text(text, target_lang="en"):
    """Traduit un texte libre via Google Translate. Skip si deja en anglais."""
    if target_lang == "en" or not text or str(text).strip() == "":
        return text
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(str(text)) or text
    except Exception:
        return text


def translate_dataframe(df, cols, target_lang="en"):
    """Traduit les colonnes d'un DataFrame.
    Skip les colonnes dans NO_TRANSLATE_COLS (categories, sources, attaquants).
    Skip si langue = anglais (donnees deja en EN).
    """
    if target_lang == "en":
        return df
    df = df.copy()
    for col in cols:
        if col in df.columns and col not in NO_TRANSLATE_COLS:
            df[col] = df[col].apply(lambda x: translate_text(x, target_lang))
    return df