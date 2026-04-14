# page_theme.py -- Style unifie StatCyberMatrix
# Esthetique Carte Menaces : Syne + JetBrains Mono, dark cyber, cyan/violet
# Usage : from page_theme import inject_theme, PLOTLY_THEME

import streamlit as st
import streamlit.components.v1 as components


def inject_theme():
    """Injecte le CSS global + animation code rain sur la page."""

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

    /* ── Base ── */
    html, body, .stApp, [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > section {
        background: #050a14 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Masquer le header Streamlit */
    header[data-testid="stHeader"] { display: none !important; }

    /* Tout le texte en clair */
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    .stSelectbox label, .stSlider label,
    [data-testid="stWidgetLabel"] label {
        color: #c8d6e5 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ── Titres ── */
    .page-title {
        text-align: center;
        font-family: 'Syne', sans-serif !important;
        font-size: 2.2rem;
        font-weight: 700;
        color: #ffffff !important;
        margin: 20px 0 10px;
        text-shadow: 0 0 20px rgba(0,212,255,0.3);
    }

    .section-title {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.85rem;
        color: #00d4ff;
        margin: 30px 0 12px;
        border-left: 3px solid #a855f7;
        padding-left: 14px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }

    /* ── Insight box ── */
    .insight-box {
        background: rgba(0, 212, 255, 0.04);
        border: 1px solid rgba(0, 212, 255, 0.15);
        border-left: 3px solid #a855f7;
        border-radius: 6px;
        padding: 14px 18px;
        margin: 10px 0 25px;
        color: #c8d6e5;
        font-size: 0.82rem;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1.6;
    }
    .insight-box b {
        color: #00d4ff !important;
    }

    /* ── Article cards ── */
    .article-card {
        background: rgba(0, 212, 255, 0.03);
        border-left: 3px solid #a855f7;
        padding: 10px 15px;
        margin-bottom: 6px;
        border-radius: 4px;
        transition: background 0.2s;
    }
    .article-card:hover {
        background: rgba(0, 212, 255, 0.08);
    }
    .article-card a {
        color: #e8f0fe !important;
        text-decoration: none !important;
        font-size: 0.82rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .article-card a:hover {
        color: #00d4ff !important;
    }

    /* ── Selectbox / inputs ── */
    div[data-baseweb="select"] {
        background-color: rgba(10, 22, 40, 0.9) !important;
        border: 1px solid rgba(0, 212, 255, 0.15) !important;
        border-radius: 6px;
    }
    div[data-baseweb="select"] * {
        color: #c8d6e5 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ── Tabs Streamlit ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.78rem;
        color: #7a9cc8 !important;
        background: rgba(10, 22, 40, 0.6) !important;
        border: 1px solid rgba(0, 212, 255, 0.1) !important;
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        color: #00d4ff !important;
        background: rgba(0, 212, 255, 0.08) !important;
        border-bottom: 2px solid #a855f7 !important;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: rgba(10, 22, 40, 0.6);
        border: 1px solid rgba(0, 212, 255, 0.1);
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] {
        color: #7a9cc8 !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ── Tables ── */
    .stDataFrame, [data-testid="stDataFrame"] {
        font-family: 'JetBrains Mono', monospace !important;
    }
    thead th {
        background: rgba(0, 212, 255, 0.08) !important;
        color: #00d4ff !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
    }
    tbody td {
        color: #c8d6e5 !important;
        font-size: 0.78rem !important;
        border-bottom: 1px solid rgba(0, 212, 255, 0.06) !important;
    }

    /* ── Plotly containers ── */
    .js-plotly-plot .plotly .modebar { opacity: 0.3; }
    .js-plotly-plot .plotly .modebar:hover { opacity: 1; }
    </style>
    """, unsafe_allow_html=True)

    # Code rain en arriere-plan
    components.html("""
    <script>
    (function() {
      var p = window.parent.document, w = window.parent;
      var old = p.getElementById('matrix-rain');
      if (old) old.parentNode.removeChild(old);
      var cv = p.createElement('canvas');
      cv.id = 'matrix-rain';
      cv.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-1;pointer-events:none;opacity:0.07;';
      p.body.appendChild(cv);
      var ctx = cv.getContext('2d'), W = cv.width = w.innerWidth, H = cv.height = w.innerHeight;
      var chars = '01ABCDEFCVEAPTMALWARERANSOMWAREBREACH'.split('');
      var sz = 14, cols = Math.floor(W / sz), drops = [];
      for (var i = 0; i < cols; i++) drops[i] = Math.random() * (H / sz);
      function draw() {
        if (!p.getElementById('matrix-rain')) return;
        ctx.fillStyle = 'rgba(5,10,20,0.06)';
        ctx.fillRect(0, 0, W, H);
        ctx.fillStyle = '#a855f7';
        ctx.font = sz + 'px JetBrains Mono';
        for (var i = 0; i < drops.length; i++) {
          ctx.fillText(chars[Math.floor(Math.random() * chars.length)], i * sz, drops[i] * sz);
          drops[i]++;
          if (drops[i] * sz > H && Math.random() > 0.975) drops[i] = 0;
        }
        requestAnimationFrame(draw);
      }
      draw();
      w.addEventListener('resize', function() { W = cv.width = w.innerWidth; H = cv.height = w.innerHeight; });
    })();
    </script>
    """, height=0)


# Config Plotly coherente avec le theme
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(5,10,20,0.4)",
    font=dict(family="JetBrains Mono", size=11, color="#c8d6e5"),
    margin=dict(l=40, r=40, t=40, b=40),
    colorway=["#00d4ff", "#a855f7", "#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6"],
    xaxis=dict(gridcolor="rgba(0,212,255,0.06)", zerolinecolor="rgba(0,212,255,0.1)"),
    yaxis=dict(gridcolor="rgba(0,212,255,0.06)", zerolinecolor="rgba(0,212,255,0.1)"),
)