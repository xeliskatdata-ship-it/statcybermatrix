# sidebar_css.py -- CSS sidebar + i18n EN/FR
# Usage : from sidebar_css import inject_sidebar_css; inject_sidebar_css(lang)

import json
import streamlit as st
import streamlit.components.v1 as components

_NAV_LABELS = {
    "Accueil":                {"en": "Home",                "fr": "Accueil"},
    "Articles collectes":     {"en": "Collected articles",  "fr": "Articles collectes"},
    "Suivi des mots-cles":    {"en": "Keyword tracking",    "fr": "Suivi des mots-cles"},
    "Analyse des menaces":    {"en": "Threat analysis",     "fr": "Analyse des menaces"},
    "Analyse des tendances":  {"en": "Trend analysis",      "fr": "Analyse des tendances"},
    "Analyse des alertes":    {"en": "Alert analysis",      "fr": "Analyse des alertes"},
    "CVEs":                   {"en": "CVEs",                "fr": "CVEs"},
    "Carte Menaces":          {"en": "Threat map",          "fr": "Carte Menaces"},
}


def inject_sidebar_css(lang="en"):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500&display=swap');

    [data-testid="stSidebar"] {
        background: #050a14 !important;
        border-right: 1px solid rgba(30,111,255,0.15) !important;
    }
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, #3b82f6, #a855f7, #3b82f6);
        background-size: 200% 100%;
        animation: sidebar-gradient 4s linear infinite;
        z-index: 10;
    }
    @keyframes sidebar-gradient {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    [data-testid="stSidebar"] * { color: #7a9cc8 !important; }

    a[data-testid="stSidebarNavLink"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
        color: #7a9cc8 !important;
        padding: 10px 18px !important;
        margin: 1px 8px !important;
        border-radius: 0 !important;
        border-left: 3px solid transparent !important;
        transition: all 0.2s ease !important;
        text-decoration: none !important;
        display: block !important;
        background: transparent !important;
    }
    a[data-testid="stSidebarNavLink"]:hover {
        color: #e8f0fe !important;
        background: rgba(30,111,255,0.06) !important;
    }
    a[data-testid="stSidebarNavLink"][aria-current="page"] {
        color: #e8f0fe !important;
        background: linear-gradient(90deg, rgba(30,111,255,0.15), transparent) !important;
        border-left: 3px solid #a855f7 !important;
    }
    a[data-testid="stSidebarNavLink"] svg { display: none !important; }

    li:has(a[href*="Accueil"]) { border-bottom: 1px solid rgba(30,111,255,0.1) !important; padding-bottom: 8px !important; margin-bottom: 8px !important; }
    li:has(a[href*="Carte"]) { border-top: 1px solid rgba(30,111,255,0.1) !important; padding-top: 8px !important; margin-top: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

    # Build rename map : any known label -> target lang label
    rename_map = {}
    for base, langs in _NAV_LABELS.items():
        target = langs.get(lang, base)
        rename_map[base] = target
        for lv in langs.values():
            rename_map[lv] = target

    map_json = json.dumps(rename_map)

    components.html(f"""
    <script>
    (function() {{
        var map = {map_json};
        var p = window.parent.document;
        function renameLinks() {{
            var spans = p.querySelectorAll('a[data-testid="stSidebarNavLink"] span');
            if (!spans.length) return;
            spans.forEach(function(s) {{
                var txt = s.textContent.trim();
                if (map[txt] && map[txt] !== txt) s.textContent = map[txt];
            }});
        }}
        renameLinks();
        setTimeout(renameLinks, 300);
        setTimeout(renameLinks, 800);
        setTimeout(renameLinks, 2000);
        setTimeout(renameLinks, 4000);
        var sb = p.querySelector('[data-testid="stSidebar"]');
        if (sb) {{
            var obs = new MutationObserver(function() {{ renameLinks(); }});
            obs.observe(sb, {{ childList: true, subtree: true, characterData: true }});
            setTimeout(function() {{ obs.disconnect(); }}, 10000);
        }}
    }})();
    </script>
    """, height=0)