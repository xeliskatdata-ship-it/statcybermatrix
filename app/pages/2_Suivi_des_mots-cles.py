# 2_kpi2_Mots_cles.py -- KPI 2 : Suivi des mots-cles cyber
# Heatmap categorie x periode, lollipop fiabilite signal, compteurs animes
# v3 : ECG vert PT=5, bar labels, lollipop avec details chiffres+sources

import os
import sys
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from db_connect import get_mart_k2, get_stg_articles, force_refresh

st.set_page_config(page_title="KPI 2 - Mots-clés", layout="wide")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from sidebar_css import inject_sidebar_css
inject_sidebar_css()

# ── CSS global ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
html,body,[class*="css"]{font-family:'Roboto',sans-serif;}
.stApp{
    background: radial-gradient(ellipse at 20% 50%, rgba(14,40,80,0.9) 0%, #050a14 60%),
                radial-gradient(ellipse at 80% 20%, rgba(8,30,60,0.8) 0%, transparent 50%);
    background-color: #050a14 !important;
}
.stApp::before {
    content:''; position:fixed; inset:0;
    background-image:
        radial-gradient(circle, rgba(59,130,246,0.15) 1px, transparent 1px),
        radial-gradient(circle, rgba(96,165,250,0.08) 1px, transparent 1px),
        radial-gradient(circle, rgba(147,197,253,0.06) 1px, transparent 1px);
    background-size: 80px 80px, 130px 130px, 200px 200px;
    background-position: 0 0, 40px 40px, 80px 80px;
    filter:blur(0.8px); z-index:0; pointer-events:none;
}
[data-testid="stAppViewContainer"] > * { position:relative; z-index:1; }
[data-testid="stSidebar"]{background:#0a1628!important;border-right:1px solid rgba(30,111,255,0.2);}
[data-testid="stSidebar"] *{color:#a8b8d0!important;}
.kpi-tag{display:inline-block;font-family:'Roboto Mono',monospace;font-size:0.65rem;
letter-spacing:.15em;text-transform:uppercase;color:#22c55e;background:rgba(34,197,94,.1);
border:1px solid rgba(34,197,94,.2);border-radius:4px;padding:3px 10px;margin-bottom:14px;}
.page-title{text-align:center;font-size:3rem;font-weight:700;color:#a855f7;margin-bottom:20px;line-height:1.2;}
.desc-box{background:rgba(15,20,34,0.85);border:1px solid #1e2a42;border-left:3px solid #22c55e;
border-radius:8px;padding:14px 20px;margin-bottom:24px;color:#94a3b8;font-size:0.75rem;
line-height:1.8;text-align:center;max-width:900px;margin-left:auto;margin-right:auto;}
.badge-live{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:1rem;letter-spacing:.08em;color:#22c55e;background:rgba(34,197,94,.08);
border:1px solid rgba(34,197,94,.2);border-radius:20px;padding:8px 18px;}
.badge-err{display:inline-flex;align-items:center;gap:6px;font-family:'Roboto Mono',monospace;
font-size:0.68rem;letter-spacing:.12em;text-transform:uppercase;color:#ef4444;
background:rgba(239,68,68,.08);border:1px solid rgba(239,68,68,.2);border-radius:20px;padding:4px 12px;}
.dot-live{width:7px;height:7px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
div[data-testid="stButton"] button {
    background:rgba(34,197,94,0.12)!important;border:1px solid rgba(34,197,94,0.4)!important;
    color:#22c55e!important;font-size:1.2rem!important;font-weight:600!important;
    border-radius:8px!important;padding:10px 24px!important;
}
div[data-testid="stButton"] button:hover{background:rgba(34,197,94,0.25)!important;}
</style>
""", unsafe_allow_html=True)

# ── ECG (point reduit PT=10) ──────────────────────────────────────────────────
components.html("""
<script>
(function(){var p=window.parent.document,w=window.parent,PT=5,TR=270,SP=2;
function ecg(x,H){var m=PT+10,a=H/2-m,mod=x%220,r;if(mod<70)r=Math.sin(mod*.05)*5;
else if(mod<80)r=(mod-70)*13;else if(mod<85)r=130-(mod-80)*55;else if(mod<90)r=-145+(mod-85)*32;
else if(mod<100)r=-25+(mod-90)*3;else if(mod<115)r=Math.sin((mod-100)*.4)*9;
else r=Math.sin(mod*.04)*3;return(r/130)*a;}
function go(){var old=p.getElementById('ecg-bg');if(old)old.remove();
var cv=p.createElement('canvas');cv.id='ecg-bg';
cv.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
p.body.appendChild(cv);var ctx=cv.getContext('2d'),t=0,ex=0,h=[],alive=true;
function rs(){cv.width=p.documentElement.clientWidth;cv.height=p.documentElement.clientHeight;}
rs();w.addEventListener('resize',rs);
var dots=[];for(var i=0;i<50;i++)dots.push({x:Math.random()*cv.width,y:Math.random()*cv.height,
r:Math.random()*1.5+.3,ph:Math.random()*Math.PI*2,sp:Math.random()*.008+.004,
dx:(Math.random()-.5)*.15,dy:(Math.random()-.5)*.15,
c:Math.random()>.6?'59,130,246':(Math.random()>.5?'168,85,247':'20,184,166')});
var rings=[];function ar(){rings.push({r:0,a:.45});}ar();
function draw(){if(!p.getElementById('ecg-bg')||!alive)return;
var W=cv.width,H=cv.height;ctx.clearRect(0,0,W,H);t+=.016;
var g=ctx.createRadialGradient(W/2,H/2,0,W/2,H/2,W*.6);
g.addColorStop(0,'rgba(14,30,60,.35)');g.addColorStop(1,'rgba(5,10,20,0)');
ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
rings.forEach(function(r,i){r.r+=1;r.a-=.005;if(r.a<=0){rings.splice(i,1);return;}
ctx.beginPath();ctx.arc(W/2,H/2,r.r,0,Math.PI*2);
ctx.strokeStyle='rgba(59,130,246,'+r.a*.35+')';ctx.lineWidth=1;ctx.stroke();});
if(Math.floor(t*1.2)%3===0&&rings.length<6)ar();
dots.forEach(function(d){d.ph+=d.sp;d.x+=d.dx;d.y+=d.dy;
if(d.x<0)d.x=W;if(d.x>W)d.x=0;if(d.y<0)d.y=H;if(d.y>H)d.y=0;
var op=.3+Math.abs(Math.sin(d.ph))*.5;
ctx.beginPath();ctx.arc(d.x,d.y,d.r,0,Math.PI*2);
ctx.fillStyle='rgba('+d.c+','+op+')';ctx.fill();});
h.push({x:ex%W,y:H/2-ecg(ex,H)});ex+=SP;
var mx=Math.round(TR/SP);if(h.length>mx)h.shift();
if(h.length>1){for(var k=1;k<h.length;k++){var pr=k/h.length,al=pr*.85,
sp=Math.abs(h[k].y-H/2)>H*.08;ctx.beginPath();ctx.moveTo(h[k-1].x,h[k-1].y);
ctx.lineTo(h[k].x,h[k].y);ctx.strokeStyle=sp?'rgba(57,255,20,'+al+')':'rgba(59,130,246,'+(al*.6)+')';
ctx.lineWidth=sp?3.5:1.8;ctx.stroke();}
var hd=h[h.length-1];var gl=ctx.createRadialGradient(hd.x,hd.y,0,hd.x,hd.y,PT*3);
gl.addColorStop(0,'rgba(57,255,20,.45)');gl.addColorStop(1,'rgba(57,255,20,0)');
ctx.fillStyle=gl;ctx.fillRect(hd.x-PT*3,hd.y-PT*3,PT*6,PT*6);
ctx.beginPath();ctx.arc(hd.x,hd.y,PT,0,Math.PI*2);ctx.fillStyle='rgba(57,255,20,0.9)';ctx.fill();}
requestAnimationFrame(draw);}draw();return function(){alive=false;};}
var s=go();setInterval(function(){if(!p.getElementById('ecg-bg')){s&&s();s=go();}},2000);
p.addEventListener('visibilitychange',function(){if(!p.hidden){s&&s();s=go();}});})();
</script>
""", height=0)

# ── En-tete ───────────────────────────────────────────────────────────────────
st.markdown('<div style="text-align:center"><div class="kpi-tag">KPI 2</div></div>', unsafe_allow_html=True)
st.markdown('<div class="page-title">Suivi des mots-clés</div>', unsafe_allow_html=True)
st.markdown("""
<div class="desc-box">
    Cliquez sur un point du lollipop pour afficher les articles associés avec leurs liens.<br>
    Chaque ligne montre les occurrences, articles et sources distinctes.
</div>
""", unsafe_allow_html=True)

# ── Refresh + badge ───────────────────────────────────────────────────────────
_, col_r, col_b, _ = st.columns([2, 1, 2, 2])
with col_r:
    if st.button("Actualiser", use_container_width=True):
        force_refresh()
        st.rerun()

# ── Chargement ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_mart_k2():
    return get_mart_k2()

try:
    df_raw  = load_mart_k2()
    load_ok = True
    load_ts = time.strftime("%H:%M:%S")
except Exception as e:
    load_ok  = False
    load_err = str(e)

with col_b:
    if load_ok:
        st.markdown(f'<div class="badge-live"><span class="dot-live"></span>{load_ts}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="badge-err">Erreur de connexion</div>', unsafe_allow_html=True)

if not load_ok:
    st.error(f"Impossible de charger mart_k2 : {load_err}")
    st.stop()
if df_raw.empty:
    st.warning("mart_k2 est vide. Vérifiez votre pipeline dbt.")
    st.stop()

# ── Categories & mappings ─────────────────────────────────────────────────────
CATEGORIES = {
    "failles": {
        "label": "Vulnerabilities & Exploits", "color": "#ef4444",
        "subcats": {
            "Vulnerabilities": ["zero-day","0-day","cve","rce","remote code execution","lpe","privilege escalation"],
            "Techniques": ["sql injection","xss","cross-site scripting","buffer overflow","man-in-the-middle","mitm","supply chain attack","supply chain"],
            "Data Leaks": ["data breach","database dump","leaked credentials","exfiltration","data leak","exposed credentials"],
        },
    },
    "infra": {
        "label": "Infrastructures", "color": "#3b82f6",
        "subcats": {
            "Cloud": ["aws","s3 bucket","azure","azure ad","google cloud","gcp","kubernetes","docker"],
            "Systems": ["active directory","windows server","linux kernel","macos","tcc"],
            "Networks": ["vpn","firewall","sd-wan","dns tunneling","firewall bypass","vpn gateway"],
        },
    },
    "editeurs": {
        "label": "Critical Vendors", "color": "#f59e0b",
        "subcats": {
            "Hardware": ["cisco","fortinet","palo alto","check point","juniper","ubiquiti","f5"],
            "Software": ["microsoft 365","exchange","vmware","esxi","citrix","sap","salesforce","atlassian","confluence","jira"],
        },
    },
    "menaces": {
        "label": "Threats & APT", "color": "#a855f7",
        "subcats": {
            "Malware": ["ransomware","infostealer","trojan","rat","botnet","wiper","malware"],
            "APT Groups": ["apt28","lazarus","lockbit","revil","fancy bear","scattered spider","volt typhoon"],
            "Indicators": ["ioc","indicator of compromise","ttp","threat intelligence","threat actor"],
        },
    },
}

PERIODS    = {3: "3j", 7: "7j", 15: "15j", 30: "30j"}
CAT_COLORS = {k: v["color"] for k, v in CATEGORIES.items()}

kw_cat_map = {
    kw: cat_key
    for cat_key, cat in CATEGORIES.items()
    for kws in cat["subcats"].values()
    for kw in kws
}


def _counts_by_period(df, col="occurrences"):
    return {
        p: dict(zip(
            df[df["period_days"] == p]["keyword"],
            df[df["period_days"] == p][col].fillna(0).astype(int),
        ))
        for p in PERIODS
    }


counts_all     = _counts_by_period(df_raw, "occurrences")
art_counts_all = _counts_by_period(df_raw, "article_count")
src_counts_all = (
    _counts_by_period(df_raw, "source_count")
    if "source_count" in df_raw.columns
    else {p: {} for p in PERIODS}
)

# ── Slider periode ────────────────────────────────────────────────────────────
col_sl, _ = st.columns([1, 3])
with col_sl:
    n_days = st.slider("Période d'affichage (jours)", min_value=3, max_value=30, value=7, step=1, key="k2_days")

_avail     = sorted(PERIODS.keys())
period_sel = min(_avail, key=lambda p: abs(p - n_days))

counts     = counts_all[period_sel]
art_counts = art_counts_all[period_sel]
src_counts = src_counts_all[period_sel]

# ── Metriques animees ─────────────────────────────────────────────────────────
top_kw            = max(counts, key=counts.get) if any(counts.values()) else "—"
total_occ         = sum(counts.values())
nb_detect         = sum(1 for v in counts.values() if v > 0)
nb_articles_total = int(df_raw[df_raw["period_days"] == period_sel]["article_count"].sum())
period_label      = PERIODS[period_sel]

components.html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;700&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}body{{background:transparent;font-family:'Roboto',sans-serif}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.card{{background:rgba(15,20,34,0.85);border:1px solid #1e2a42;border-radius:10px;
padding:28px 20px;text-align:center;position:relative;overflow:hidden;
transition:border-color 0.2s,transform 0.2s,box-shadow 0.2s;cursor:default}}
.card::before{{content:'';position:absolute;top:0;left:0;width:100%;height:3px;background:#a855f7;border-radius:10px 10px 0 0}}
.card:hover{{border-color:#a855f7;transform:translateY(-3px);box-shadow:0 8px 28px rgba(168,85,247,0.18)}}
.val{{font-family:'Roboto Mono',monospace;font-size:3rem;font-weight:700;color:#e2e8f0}}
.lbl{{font-size:0.9rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.08em;margin-top:10px}}
</style>
<div class="grid">
  <div class="card"><div class="val" id="v1">0</div><div class="lbl">Mots-clés détectés ({period_label})</div></div>
  <div class="card"><div class="val" style="font-size:2rem">{top_kw}</div><div class="lbl">Mot-clé le plus recherché ({period_label})</div></div>
  <div class="card"><div class="val" id="v3">0</div><div class="lbl">Total occurrences ({period_label})</div></div>
  <div class="card"><div class="val" id="v4">0</div><div class="lbl">Articles correspondants ({period_label})</div></div>
</div>
<script>
function animCount(id,t,d){{var el=document.getElementById(id);if(!el||isNaN(t))return;
var s=t/(d/16),c=0;var ti=setInterval(function(){{c+=s;if(c>=t){{c=t;clearInterval(ti);}}
el.textContent=Math.floor(c).toLocaleString('fr-FR');}},16);}}
animCount('v1',{nb_detect},1000);animCount('v3',{total_occ},1200);animCount('v4',{nb_articles_total},1000);
</script>
""", height=150)

st.markdown("<br>", unsafe_allow_html=True)

# ── Bar chart top N ───────────────────────────────────────────────────────────
top_n = 20

col_title, col_cat = st.columns([3, 1])
with col_cat:
    cat_filter = st.selectbox("Catégorie", ["Toutes","Vulnerabilities","Infra","Vendors","Menaces"], key="k2_cat")

cat_filter_map = {"Toutes": None, "Vulnerabilities": "failles", "Infra": "infra", "Vendors": "editeurs", "Menaces": "menaces"}

df_chart = (
    pd.DataFrame(sorted(counts.items(), key=lambda x: x[1], reverse=True), columns=["keyword", "occurrences"])
    .assign(category=lambda d: d["keyword"].map(kw_cat_map))
)
if cat_filter_map[cat_filter]:
    df_chart = df_chart[df_chart["category"] == cat_filter_map[cat_filter]]
df_chart = df_chart.head(top_n).sort_values("occurrences")

with col_title:
    st.markdown(
        f"<div style='text-align:center;font-size:2.2rem;color:#a855f7;font-weight:700;padding-top:24px'>"
        f"Top {top_n} mots-clés — {n_days}j</div>",
        unsafe_allow_html=True,
    )

fig = px.bar(
    df_chart, x="occurrences", y="keyword", orientation="h", color="category",
    color_discrete_map=CAT_COLORS,
    labels={"occurrences": "Cas", "keyword": "", "category": "Catégorie"},
    text="occurrences",
)
fig.update_traces(
    textposition="outside",
    textfont=dict(size=14, color="#cbd5e1", family="Roboto Mono"),
    marker_line_width=0,
)
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,10,20,0.6)",
    font=dict(family="Roboto", color="#94a3b8", size=18),
    xaxis=dict(gridcolor="#1e2a42", tickfont=dict(size=16, color="#94a3b8"), title_font=dict(size=18), showgrid=False),
    yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=16, color="#cbd5e1")),
    legend=dict(font=dict(size=16), title_text="Catégorie", title_font=dict(size=16)),
    margin=dict(l=20, r=60, t=60, b=20), height=max(500, top_n * 40),
)
st.plotly_chart(fig, use_container_width=True)

# ── Heatmap categorie x periode ───────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;font-size:2.2rem;color:#a855f7;font-weight:700;padding-bottom:12px'>"
    "Intensité des menaces par catégorie</div>",
    unsafe_allow_html=True,
)

cat_keys    = list(CATEGORIES.keys())
cat_labels  = [CATEGORIES[k]["label"] for k in cat_keys]
period_keys = sorted(PERIODS.keys())
period_lbls = [PERIODS[p] for p in period_keys]

heat_z = []
for ck in cat_keys:
    kws = [kw for sub in CATEGORIES[ck]["subcats"].values() for kw in sub]
    heat_z.append([sum(counts_all[p].get(kw, 0) for kw in kws) for p in period_keys])

# Delta acceleration
delta_col = []
for ck in cat_keys:
    kws      = [kw for sub in CATEGORIES[ck]["subcats"].values() for kw in sub]
    v3       = sum(counts_all[3].get(kw, 0) for kw in kws)
    v7       = sum(counts_all[7].get(kw, 0) for kw in kws)
    baseline = (v7 / 7) * 3
    delta_col.append(round((v3 / baseline) - 1, 2) if baseline > 0 else 0.0)

fig_heat = go.Figure(go.Heatmap(
    z=heat_z, x=period_lbls, y=cat_labels,
    colorscale=[[0,"#0f1422"],[.25,"#1e3a5f"],[.55,"#6d28d9"],[.8,"#a855f7"],[1,"#f0abfc"]],
    text=[[f"{v:,}" for v in row] for row in heat_z],
    texttemplate="%{text}",
    textfont=dict(size=20, family="Roboto Mono", color="#ffffff"),
    hoverongaps=False, showscale=True,
    colorbar=dict(tickfont=dict(color="#94a3b8", size=14), outlinewidth=0, bgcolor="rgba(0,0,0,0)"),
))

for i, (label, delta) in enumerate(zip(cat_labels, delta_col)):
    arrow, color = ("↑","#22c55e") if delta > 0.1 else ("↓","#ef4444") if delta < -0.1 else ("→","#94a3b8")
    fig_heat.add_annotation(
        x=4.55, y=i, text=f"<b>{arrow} {abs(delta)*100:.0f}%</b>",
        showarrow=False, font=dict(size=16, color=color, family="Roboto Mono"),
        xanchor="left", yanchor="middle",
    )

fig_heat.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,10,20,0.6)",
    font=dict(family="Roboto", color="#94a3b8", size=16),
    xaxis=dict(tickfont=dict(size=18, color="#cbd5e1"), title_font=dict(size=18), range=[-0.5, 5.2]),
    yaxis=dict(tickfont=dict(size=16, color="#cbd5e1")),
    margin=dict(l=20, r=80, t=20, b=20), height=340,
)
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown(
    "<div style='text-align:center;font-size:0.95rem;color:#64748b;margin-top:-10px;margin-bottom:24px'>"
    "Somme des occurrences par famille — plus c'est violet, plus l'activité est intense. "
    "La flèche compare le rythme des 3 derniers jours à la moyenne des 7 derniers jours.</div>",
    unsafe_allow_html=True,
)

# ── Lollipop : fiabilite du signal ─────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f"<div style='text-align:center;font-size:2.2rem;color:#a855f7;font-weight:700;padding-bottom:12px'>"
    f"Fiabilité du signal — {n_days}j</div>",
    unsafe_allow_html=True,
)

lollipop_rows = [
    {"keyword": kw, "occurrences": v, "article_count": art_counts.get(kw, 0),
     "source_count": src_counts.get(kw, 0), "category": kw_cat_map.get(kw, "inconnu")}
    for kw, v in counts.items() if v > 0
]
df_lp = pd.DataFrame(lollipop_rows).sort_values("occurrences", ascending=True)

if not df_lp.empty:
    # Top 25 pour lisibilite
    df_lp = df_lp.tail(25)
    max_occ = df_lp["occurrences"].max()

    fig_lp = go.Figure()

    # Tiges horizontales (lignes fines)
    for _, row in df_lp.iterrows():
        cat_color = CAT_COLORS.get(row["category"], "#495b73")
        fig_lp.add_trace(go.Scatter(
            x=[0, row["occurrences"]],
            y=[row["keyword"], row["keyword"]],
            mode="lines",
            line=dict(color=cat_color, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Points (cercles) au bout + hover detaille
    for cat_key, cat_color in CAT_COLORS.items():
        sub = df_lp[df_lp["category"] == cat_key]
        if sub.empty:
            continue
        fig_lp.add_trace(go.Scatter(
            x=sub["occurrences"],
            y=sub["keyword"],
            mode="markers",
            name=CATEGORIES[cat_key]["label"],
            marker=dict(size=14, color=cat_color,
                        line=dict(width=1.5, color="rgba(255,255,255,0.2)")),
            customdata=list(zip(
                sub["keyword"].tolist(),
                sub["article_count"].tolist(),
                sub["source_count"].tolist(),
                sub["category"].tolist(),
            )),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Occurrences : %{x}<br>"
                "Articles : %{customdata[1]}<br>"
                "Sources : %{customdata[2]}<br>"
                "Catégorie : %{customdata[3]}"
                "<extra></extra>"
            ),
        ))

    # Annotations chiffres a droite de chaque point
    for _, row in df_lp.iterrows():
        cat_color = CAT_COLORS.get(row["category"], "#64748b")
        occ = int(row["occurrences"])
        art = int(row["article_count"])
        src = int(row["source_count"])
        fig_lp.add_annotation(
            x=row["occurrences"],
            y=row["keyword"],
            text=f"<b>{occ}</b> <span style='color:#94a3b8'>· {art} art · {src} src</span>",
            showarrow=False,
            xanchor="left",
            xshift=14,
            font=dict(size=12, color="#cbd5e1", family="Roboto Mono"),
        )

    fig_lp.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,10,20,0.6)",
        font=dict(family="Roboto", color="#94a3b8", size=14),
        xaxis=dict(
            gridcolor="#1e2a42", tickfont=dict(size=14, color="#94a3b8"),
            title="Occurrences (mentions)", title_font=dict(size=16, color="#94a3b8"),
            zeroline=False, range=[0, max_occ * 1.45],
        ),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)", tickfont=dict(size=14, color="#cbd5e1"),
        ),
        legend=dict(
            font=dict(size=14), title_text="Catégorie", title_font=dict(size=14),
            bgcolor="rgba(15,20,34,0.8)", bordercolor="#1e2a42", borderwidth=1,
            orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
        ),
        margin=dict(l=20, r=120, t=50, b=40),
        height=max(500, len(df_lp) * 32),
    )

    event = st.plotly_chart(fig_lp, use_container_width=True, on_select="rerun", key="lollipop_k2")

    st.markdown(
        "<div style='text-align:center;font-size:0.85rem;color:#64748b;margin-top:-10px'>"
        "Longueur = occurrences · <b>art</b> = articles distincts · <b>src</b> = sources distinctes. "
        "Plus un mot-clé est couvert par des sources variées, plus le signal est fiable. "
        "Cliquez sur un point pour voir les articles.</div>",
        unsafe_allow_html=True,
    )

    # ── Panel articles au clic ────────────────────────────────────────────────
    points     = (event.selection or {}).get("points", [])
    clicked_kw = ""
    if points:
        cd = points[0].get("customdata", "")
        if isinstance(cd, (list, tuple)) and len(cd) > 0:
            clicked_kw = cd[0]
        elif isinstance(cd, str):
            clicked_kw = cd

    if clicked_kw:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:1.6rem;font-weight:700;color:#a855f7;margin-bottom:12px'>"
            f"Articles mentionnant <span style='color:#22c55e'>{clicked_kw}</span> — {n_days}j</div>",
            unsafe_allow_html=True,
        )

        try:
            df_arts = get_articles_by_keyword(clicked_kw, n_days)
        except Exception as e:
            st.error(f"Erreur chargement articles : {e}")
            df_arts = pd.DataFrame()

        if df_arts.empty:
            st.info(f"Aucun article trouvé pour « {clicked_kw} » sur {n_days}j.")
        else:
            st.markdown(
                f"<div style='color:#64748b;font-size:0.9rem;margin-bottom:16px'>"
                f"{len(df_arts)} article(s) trouvé(s)</div>",
                unsafe_allow_html=True,
            )
            for _, row in df_arts.iterrows():
                pub       = str(row.get("published_date", ""))[:10]
                src       = row.get("source", "")
                cat       = row.get("category", "")
                url       = row.get("url", "")
                title     = row.get("title", "Sans titre")
                cat_color = CAT_COLORS.get(cat, "#64748b")
                title_html = f'<a href="{url}" target="_blank" style="color:#e2e8f0;text-decoration:none">{title}</a>' if url else title
                cat_html   = f"&nbsp;·&nbsp;<span style='color:{cat_color}'>{cat}</span>" if cat else ""
                st.markdown(f"""
<div style="background:rgba(15,20,34,0.85);border:1px solid #1e2a42;border-left:3px solid {cat_color};
border-radius:8px;padding:14px 18px;margin-bottom:10px">
    <div style="font-size:1.05rem;font-weight:600;color:#e2e8f0;margin-bottom:6px">{title_html}</div>
    <div style="font-size:0.85rem;color:#64748b">{src}&nbsp;·&nbsp;{pub}{cat_html}</div>
</div>""", unsafe_allow_html=True)

else:
    st.info("Aucune donnée disponible pour cette période.")
