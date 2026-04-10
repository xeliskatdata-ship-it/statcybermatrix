# utils_lang.py -- Internationalisation FR/EN
# Sprint 5 : 95+ cles interface + traduction articles via deep-translator
# Usage : t("KPI 3 title", lang) / translate_text(text, "fr")

from deep_translator import GoogleTranslator

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
    "Refresh":                  {"fr": "Rafraîchir les données",            "en": "Refresh data"},
    "Last update":              {"fr": "Dernière mise à jour",              "en": "Last update"},
    "Filter by period":         {"fr": "Filtrer par période",               "en": "Filter by period"},
    "All":                      {"fr": "Tout",                              "en": "All"},
    "Last 24h":                 {"fr": "Dernières 24h",                     "en": "Last 24h"},
    "Last 7 days":              {"fr": "7 derniers jours",                  "en": "Last 7 days"},
    "Last 30 days":             {"fr": "30 derniers jours",                 "en": "Last 30 days"},
    "Loading":                  {"fr": "Chargement...",                     "en": "Loading..."},

    # -- Accueil --
    "Overview":                 {"fr": "Vue d'ensemble",                    "en": "Overview"},
    "Articles collected":       {"fr": "Articles collectés",                "en": "Articles collected"},
    "Filtered articles":        {"fr": "Articles filtres",                  "en": "Filtered articles"},
    "Top threat":               {"fr": "Menace principale",                 "en": "Top threat"},
    "Top source":               {"fr": "Source la + active",                "en": "Most active source"},
    "Avg length":               {"fr": "Longueur moy.",                     "en": "Avg length"},
    "Data preview":             {"fr": "Apercu des donnees",                "en": "Data preview"},
    "Download CSV":             {"fr": "Telecharger (CSV)",                 "en": "Download (CSV)"},
    "Export CSV":               {"fr": "Exporter CSV",                      "en": "Export CSV"},
    "Hourly collection":        {"fr": "Collecte toutes les heures",        "en": "Hourly collection"},
    "See analysis":             {"fr": "Voir l'analyse →",                  "en": "See analysis →"},
    "See map":                  {"fr": "Voir la carte →",                   "en": "See map →"},
    "Navigation hint":          {"fr": "Utilisez la barre laterale pour naviguer entre les KPIs.",
                                 "en": "Use the sidebar to navigate between KPIs."},
    "No data":                  {"fr": "Aucune donnee disponible avec les filtres selectionnes.",
                                 "en": "No data available with selected filters."},
    "Go to home":               {"fr": "Retournez sur l'accueil pour charger les donnees.",
                                 "en": "Go back to home to load data."},

    # -- KPI 1 : Articles --
    "KPI 1 title":              {"fr": "Articles collectes par jour / par source",
                                 "en": "Articles collected per day / per source"},
    "Publication date":         {"fr": "Date de publication",               "en": "Publication date"},
    "Source name":              {"fr": "Nom de la source",                  "en": "Source name"},
    "Number of articles":       {"fr": "Nombre d'articles",                 "en": "Number of articles"},
    "Daily volume":             {"fr": "Volume quotidien",                  "en": "Daily volume"},
    "Top sources":              {"fr": "Top sources",                       "en": "Top sources"},
    "Summary by source":        {"fr": "Resume par source",                 "en": "Summary by source"},

    # -- KPI 2 : Mots-cles --
    "KPI 2 title":              {"fr": "Top mots-cles frequents (7 jours glissants)",
                                 "en": "Top frequent keywords (7-day rolling window)"},
    "Keywords":                 {"fr": "Mots-clés",                         "en": "Keywords"},
    "Occurrences":              {"fr": "Occurrences",                       "en": "Occurrences"},
    "Category":                 {"fr": "Catégorie",                         "en": "Category"},
    "Source count":             {"fr": "Nb de sources",                     "en": "Source count"},
    "Article count":            {"fr": "Nb d'articles",                     "en": "Article count"},
    "Top N keywords":           {"fr": "Nombre de mots-cles",              "en": "Number of keywords"},
    "Heatmap":                  {"fr": "Carte de chaleur",                  "en": "Heatmap"},
    "Related articles":         {"fr": "Articles liés",                     "en": "Related articles"},

    # -- KPI 3 : Menaces --
    "KPI 3 title":              {"fr": "Repartition par type de menace",    "en": "Distribution by threat type"},
    "Threat category":          {"fr": "Catégorie de menace",               "en": "Threat category"},
    "Distribution":             {"fr": "Répartition",                       "en": "Distribution"},
    "Proportion":               {"fr": "Proportion",                        "en": "Proportion"},
    "Visualization":            {"fr": "Visualisation",                     "en": "Visualization"},
    "Donut chart":              {"fr": "Camembert (donut)",                 "en": "Donut chart"},
    "Treemap":                  {"fr": "Treemap",                           "en": "Treemap"},
    "Detail by threat":         {"fr": "Detail par menace",                 "en": "Detail by threat"},

    # -- KPI 4 : Tendances --
    "KPI 4 title":              {"fr": "Evolution des mentions d'une menace dans le temps",
                                 "en": "Evolution of threat mentions over time"},
    "Trend":                    {"fr": "Tendance",                          "en": "Trend"},
    "Mentions":                 {"fr": "Mentions",                          "en": "Mentions"},
    "Weekly":                   {"fr": "Hebdomadaire",                      "en": "Weekly"},
    "Monthly":                  {"fr": "Mensuel",                           "en": "Monthly"},
    "Evolution":                {"fr": "Évolution",                         "en": "Evolution"},
    "Last N days":              {"fr": "Derniers N jours",                  "en": "Last N days"},
    "Threat to track":          {"fr": "Menace a suivre",                   "en": "Threat to track"},
    "Compare with":             {"fr": "Comparer avec",                     "en": "Compare with"},
    "Filter by threat":         {"fr": "Filtrer par menace",                "en": "Filter by threat"},
    "Peak detected":            {"fr": "Pic detecte le",                    "en": "Peak detected on"},
    "With mentions":            {"fr": "mentions",                          "en": "mentions"},

    # -- KPI 5 : Alertes --
    "KPI 5 title":              {"fr": "Alertes critiques par semaine",     "en": "Critical alerts per week"},
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
    "CVE":                      {"fr": "CVE",                               "en": "CVE"},
    "CVE ID":                   {"fr": "Identifiant CVE",                   "en": "CVE ID"},
    "Nb mentions":              {"fr": "Nb de mentions",                    "en": "Nb mentions"},
    "CVE details":              {"fr": "Détails CVE",                       "en": "CVE details"},
    "Top N CVE":                {"fr": "Nombre de CVE",                     "en": "Number of CVEs"},
    "Exact ranking":            {"fr": "Classement exact",                  "en": "Exact ranking"},
    "Sorted table":             {"fr": "Tableau classe",                    "en": "Sorted table"},
    "Ranked table":             {"fr": "Tableau classe",                    "en": "Ranked table"},
    "No CVE found":             {"fr": "Aucune CVE detectee.",              "en": "No CVE detected."},
    "Translate":                {"fr": "Traduire",                          "en": "Translate"},

    # -- Carte des menaces --
    "Threat map":               {"fr": "Carte mondiale des menaces",        "en": "World threat map"},
    "Attacked country":         {"fr": "Pays attaqué",                      "en": "Attacked country"},
    "Source country":           {"fr": "Pays de la source",                 "en": "Source country"},
    "Confidence":               {"fr": "Confiance",                         "en": "Confidence"},
    "High":                     {"fr": "Forte",                             "en": "High"},
    "Medium":                   {"fr": "Moyenne",                           "en": "Medium"},
    "Low":                      {"fr": "Faible",                            "en": "Low"},
    "Victim":                   {"fr": "Victime",                           "en": "Victim"},
    "Threat":                   {"fr": "Menace",                            "en": "Threat"},
    "Geolocation":              {"fr": "Géolocalisation",                   "en": "Geolocation"},

    # -- Categories (labels UI) --
    "ransomware":               {"fr": "Ransomware",                        "en": "Ransomware"},
    "phishing":                 {"fr": "Phishing",                          "en": "Phishing"},
    "vulnerability":            {"fr": "Vulnérabilité",                     "en": "Vulnerability"},
    "malware":                  {"fr": "Malware",                           "en": "Malware"},
    "apt":                      {"fr": "APT",                               "en": "APT"},
    "ddos":                     {"fr": "DDoS",                              "en": "DDoS"},
    "data_breach":              {"fr": "Fuite de données",                  "en": "Data breach"},
    "supply_chain":             {"fr": "Supply chain",                      "en": "Supply chain"},
    "cryptography":             {"fr": "Cryptographie",                     "en": "Cryptography"},
    "defense":                  {"fr": "Défense",                           "en": "Defense"},
    "offensive":                {"fr": "Offensif",                          "en": "Offensive"},
    "compliance":               {"fr": "Conformité",                        "en": "Compliance"},
    "identity":                 {"fr": "Identité",                          "en": "Identity"},
    "general":                  {"fr": "Général",                           "en": "General"},
}


def t(key, lang="fr"):
    # Retourne la traduction ou la cle brute si absente
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, key)


def translate_text(text, target_lang="fr"):
    # Traduit un texte via Google Translate (deep-translator)
    if not text or str(text).strip() == "":
        return text
    try:
        return GoogleTranslator(source="auto", target=target_lang).translate(str(text)) or text
    except Exception:
        return text


def translate_dataframe(df, cols, target_lang="fr"):
    # Traduit les colonnes d'un DataFrame -- skip si deja en anglais
    if target_lang == "en":
        return df
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: translate_text(x, target_lang))
    return df