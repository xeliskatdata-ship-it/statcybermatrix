"""
Langues supportees : Francais (FR) / Anglais (EN)
Utilise : deep-translator pour les articles, dictionnaire pour l'interface
"""

from deep_translator import GoogleTranslator

# ---------------------------------------------------
# DICTIONNAIRE DE L'INTERFACE
# Les cles sont en anglais, les valeurs en francais
# ---------------------------------------------------
TRANSLATIONS = {
    # Navigation
    "Home"                    : {"fr": "Accueil",            "en": "Home"},
    "Sources active"          : {"fr": "Sources actives",    "en": "Active sources"},
    "Articles loaded"         : {"fr": "Articles charges",   "en": "Articles loaded"},
    "Global filters"          : {"fr": "Filtres globaux",    "en": "Global filters"},
    "Sources"                 : {"fr": "Sources",            "en": "Sources"},
    "Period"                  : {"fr": "Periode",            "en": "Period"},
    "Threat type"             : {"fr": "Type de menace",     "en": "Threat type"},
    "Language"                : {"fr": "Langue",             "en": "Language"},

    # Page accueil
    "Overview"                : {"fr": "Vue d'ensemble",     "en": "Overview"},
    "Filtered articles"       : {"fr": "Articles filtres",   "en": "Filtered articles"},
    "Top threat"              : {"fr": "Menace principale",  "en": "Top threat"},
    "Top source"              : {"fr": "Source la + active", "en": "Most active source"},
    "Avg length"              : {"fr": "Longueur moy.",      "en": "Avg length"},
    "Data preview"            : {"fr": "Apercu des donnees", "en": "Data preview"},
    "Download CSV"            : {"fr": "Telecharger (CSV)",  "en": "Download (CSV)"},
    "Navigation hint"         : {
        "fr": "Utilisez la barre laterale pour naviguer entre les KPIs.",
        "en": "Use the sidebar to navigate between KPIs."
    },

    # KPI titres
    "KPI 1 title"             : {
        "fr": "Articles collectes par jour / par source",
        "en": "Articles collected per day / per source"
    },
    "KPI 2 title"             : {
        "fr": "Top mots-cles frequents (7 jours glissants)",
        "en": "Top frequent keywords (7-day rolling window)"
    },
    "KPI 3 title"             : {
        "fr": "Repartition par type de menace",
        "en": "Distribution by threat type"
    },
    "KPI 4 title"             : {
        "fr": "Evolution des mentions d'une menace dans le temps",
        "en": "Evolution of threat mentions over time"
    },
    "KPI 5 title"             : {
        "fr": "Alertes critiques par semaine",
        "en": "Critical alerts per week"
    },
    "KPI 6 title"             : {
        "fr": "Top CVE les plus mentionnees",
        "en": "Most mentioned CVEs"
    },

    # Labels communs
    "Last N days"             : {"fr": "Derniers N jours",        "en": "Last N days"},
    "Threat to track"         : {"fr": "Menace a suivre",         "en": "Threat to track"},
    "Compare with"            : {"fr": "Comparer avec",           "en": "Compare with"},
    "Alert threshold"         : {"fr": "Seuil d'alerte",          "en": "Alert threshold"},
    "Top N keywords"          : {"fr": "Nombre de mots-cles",     "en": "Number of keywords"},
    "Top N CVE"               : {"fr": "Nombre de CVE",           "en": "Number of CVEs"},
    "Exact ranking"           : {"fr": "Classement exact",        "en": "Exact ranking"},
    "Summary by source"       : {"fr": "Resume par source",       "en": "Summary by source"},
    "Peak detected"           : {"fr": "Pic detecte le",          "en": "Peak detected on"},
    "With mentions"           : {"fr": "mentions",                "en": "mentions"},
    "Weeks above threshold"   : {"fr": "Semaines ayant depasse le seuil :", "en": "Weeks above threshold:"},
    "No alert"                : {"fr": "Aucune semaine n'a depasse le seuil.", "en": "No week exceeded the threshold."},
    "Critical categories"     : {"fr": "Categories critiques",    "en": "Critical categories"},
    "Visualization"           : {"fr": "Visualisation",           "en": "Visualization"},
    "Donut chart"             : {"fr": "Camembert (donut)",       "en": "Donut chart"},
    "Treemap"                 : {"fr": "Treemap",                 "en": "Treemap"},
    "Detail by threat"        : {"fr": "Detail par menace",       "en": "Detail by threat"},
    "Sorted table"            : {"fr": "Tableau classe",          "en": "Sorted table"},
    "No CVE found"            : {"fr": "Aucune CVE detectee.",    "en": "No CVE detected."},
    "No data"                 : {"fr": "Aucune donnee disponible avec les filtres selectionnes.", "en": "No data available with selected filters."},
    "Go to home"              : {"fr": "Retournez sur l'accueil pour charger les donnees.", "en": "Go back to home to load data."},
    "Ranked table"            : {"fr": "Tableau classe",          "en": "Ranked table"},
}


def t(key, lang="fr"):
    """
    Retourne la traduction d'une cle d'interface.
    lang = 'fr' ou 'en'
    """
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, key)


def translate_text(text, target_lang="fr"):
    """
    Traduit un texte via Google Translate (deep-translator).
    target_lang : 'fr' pour francais, 'en' pour anglais
    Retourne le texte original en cas d'erreur.
    """
    if not text or str(text).strip() == '':
        return text
    try:
        result = GoogleTranslator(source='auto', target=target_lang).translate(str(text))
        return result if result else text
    except Exception:
        return text


def translate_dataframe(df, cols, target_lang="fr"):
    """
    Traduit les colonnes specifiees d'un DataFrame.
    Utilise uniquement si target_lang != 'en' (les articles sont en anglais par defaut).

    cols : liste des colonnes a traduire ex: ['title', 'description']
    """
    if target_lang == "en":
        return df  # Pas de traduction necessaire

    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: translate_text(x, target_lang))
    return df
