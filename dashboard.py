# -*- coding: utf-8 -*-
"""
TÜİK + TCMB Sektörel Analiz Dashboard
Kullanim: streamlit run dashboard.py
"""
import os, sys, pickle, re, html as _html
import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
from datetime import datetime

# ─── SAYFA YAPISI ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sektörel Analiz | TÜİK · TCMB",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════════════════════
#  ERİŞİM ŞİFRESİ
# ════════════════════════════════════════════════════════════════════════════════
# Streamlit Cloud'da Advanced settings > Secrets içine APP_PASSWORD = "..." ekleyerek
# değiştirilebilir. Secret tanımlı değilse varsayılan "1" kullanılır.
try:
    _APP_PASSWORD = st.secrets.get("APP_PASSWORD", "1")
except Exception:
    # secrets.toml yoksa st.secrets erişimi hata fırlatır → varsayılana düş
    _APP_PASSWORD = "1"

if not st.session_state.get("_authed", False):
    st.markdown("""
    <style>
    .stApp { background:#0F1729; }
    [data-testid="stAppViewContainer"] { background:#0F1729; }
    </style>
    """, unsafe_allow_html=True)
    _c1, _c2, _c3 = st.columns([1, 1.1, 1])
    with _c2:
        st.markdown("<div style='height:14vh'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center;margin-bottom:1.2rem;'>
          <div style='font-size:1.4rem;font-weight:800;color:#fff;'>📊 Sektörel Analiz</div>
          <div style='font-size:.8rem;color:#94A3B8;margin-top:.2rem;'>Devam etmek için şifre girin</div>
        </div>
        """, unsafe_allow_html=True)
        _pw = st.text_input("Şifre", type="password", label_visibility="collapsed",
                            placeholder="Şifre")
        if st.button("Giriş", use_container_width=True):
            if _pw == _APP_PASSWORD:
                st.session_state["_authed"] = True
                st.rerun()
            else:
                st.error("Hatalı şifre.")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════════
#  TASARIM SİSTEMİ
# ════════════════════════════════════════════════════════════════════════════════
INK        = "#0F1729"   # Ana metin
INK_SOFT   = "#334155"   # İkincil metin
MUTED      = "#64748B"   # Soluk metin
LINE       = "#E2E8F0"   # Kenarlık
PANEL      = "#F8FAFC"   # Panel arkaplan
WHITE      = "#FFFFFF"

BRAND      = "#2563EB"   # Ana marka
BRAND_DK   = "#1D4ED8"
NAVY       = "#1E3A5F"
SKY        = "#0EA5E9"
TEAL       = "#0D9488"
AMBER      = "#F59E0B"

POS        = "#059669"
NEG        = "#DC2626"
ROSE       = "#F43F5E"

SERIES_PAL = [BRAND, "#7C3AED", SKY, TEAL, AMBER, "#DB2777", NAVY]
YEAR_PAL   = ["#BFDBFE", "#93C5FD", "#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8"]
TRADE_EXP  = "#1D4ED8"
TRADE_IMP  = "#94A3B8"

FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
        "'Helvetica Neue', Arial, sans-serif")

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&display=swap');

:root {{
  --ink:{INK}; --ink-soft:{INK_SOFT}; --muted:{MUTED};
  --line:{LINE}; --panel:{PANEL}; --brand:{BRAND};
  --pos:{POS}; --neg:{NEG};
}}

html, body, [class*="css"], .stApp {{
  font-family: 'Outfit', 'Inter', {FONT};
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}}
/* Zengin, çok katmanlı arkaplan — düz beyaz yerine hafif ışıltılı doku */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  background:
    radial-gradient(1100px 500px at 12% -8%, rgba(37,99,235,.05), transparent 60%),
    radial-gradient(900px 460px at 100% 0%, rgba(13,148,136,.04), transparent 55%),
    {WHITE};
}}
.main .block-container {{
  padding: 1.2rem 2.2rem 3rem 2.2rem;
  max-width: 1500px;
}}

/* ── Özel kaydırma çubuğu (premium sinyal) ── */
* {{ scrollbar-width: thin; scrollbar-color: #CBD5E1 transparent; }}
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
  background: linear-gradient(180deg, #CBD5E1, #B4C0D0);
  border-radius: 99px; border: 2px solid transparent; background-clip: padding-box;
}}
::-webkit-scrollbar-thumb:hover {{ background: {BRAND}; background-clip: padding-box; }}

/* ── Metin seçimi & odak halkası ── */
::selection {{ background: rgba(37,99,235,.18); color: {INK}; }}
:focus-visible {{ outline: 2px solid rgba(37,99,235,.5); outline-offset: 2px; border-radius: 6px; }}
/* NOT: stHeader'i tamamen gizlemek sidebar'i acip-kapatan oku (collapsedControl)
   da yok ediyordu -> "sidebar kayboldu" hatasi. Sadece menu/footer'i gizle,
   header'i seffaf ama islevsel birak; toggle her zaman erisilebilir kalsin. */
#MainMenu, footer {{ visibility: hidden; height:0; }}
header[data-testid="stHeader"] {{
  background: transparent;
  box-shadow: none;
  height: 3.2rem;
}}
header[data-testid="stHeader"] * {{ visibility: visible; }}
button[kind="header"], [data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"], [data-testid="stSidebarCollapseButton"] {{
  visibility: visible !important;
  opacity: 1 !important;
  z-index: 999999 !important;
}}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="collapsedControl"] button {{
  background: {WHITE} !important;
  border: 1px solid {LINE} !important;
  border-radius: 8px !important;
  box-shadow: 0 2px 8px rgba(15,23,41,.12) !important;
}}

/* ── Header ── */
.app-header {{
  background:
    radial-gradient(700px 300px at 88% -30%, rgba(14,165,233,.45), transparent 60%),
    radial-gradient(600px 260px at 10% 130%, rgba(13,148,136,.35), transparent 60%),
    linear-gradient(120deg, {NAVY} 0%, {BRAND_DK} 52%, {BRAND} 100%);
  border-radius: 18px;
  padding: 1.6rem 2.1rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 18px 40px -18px rgba(29,78,216,.55),
              inset 0 1px 0 rgba(255,255,255,.14);
  position: relative;
  overflow: hidden;
}}
/* dönen ışıltı sweep — sürekli, yeniden başlamadan */
.app-header::before {{
  content:""; position:absolute; inset:0;
  background: linear-gradient(105deg, transparent 30%, rgba(255,255,255,.10) 46%,
              rgba(255,255,255,.04) 54%, transparent 70%);
  transform: translateX(-100%);
  animation: hdrShine 7s ease-in-out infinite;
}}
@keyframes hdrShine {{
  0% {{ transform: translateX(-120%); }}
  55%,100% {{ transform: translateX(120%); }}
}}
.app-header::after {{
  content:""; position:absolute; right:-40px; top:-40px;
  width:240px; height:240px; border-radius:50%;
  background: radial-gradient(circle, rgba(255,255,255,.14), transparent 70%);
}}
.app-header > * {{ position: relative; z-index: 2; }}
.app-header .eyebrow {{
  color: rgba(255,255,255,.75); font-size:.72rem; font-weight:700;
  letter-spacing:.2em; text-transform:uppercase; margin-bottom:.4rem;
}}
.app-header h1 {{
  color:#fff; font-size:1.75rem; font-weight:800; margin:0; line-height:1.12;
  letter-spacing:-.025em; text-shadow: 0 1px 12px rgba(0,0,0,.15);
}}
.app-header .sub {{
  color: rgba(255,255,255,.88); font-size:.92rem; font-weight:500; margin-top:.4rem;
}}
.app-header .meta {{
  position:absolute; right:2.1rem; top:50%; transform:translateY(-50%);
  text-align:right; z-index:3;
}}
.app-header .meta .chip {{
  display:inline-block; background:rgba(255,255,255,.16);
  border:1px solid rgba(255,255,255,.28); backdrop-filter:blur(10px);
  color:#fff; font-size:.74rem; font-weight:600; padding:.38rem .85rem;
  border-radius:999px; margin-left:.45rem;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
  transition: transform .2s ease, background .2s ease;
}}
.app-header .meta .chip:hover {{ transform:translateY(-1px); background:rgba(255,255,255,.24); }}

/* ── KPI ── */
.kpi {{
  background: linear-gradient(180deg, {WHITE} 0%, #FCFDFF 100%);
  border:1px solid var(--line);
  border-radius:16px; padding:1rem 1.15rem .95rem 1.25rem;
  position:relative; overflow:hidden; height:100%;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.05);
  transition: transform .22s cubic-bezier(.2,.7,.3,1),
              box-shadow .22s ease, border-color .22s ease;
}}
.kpi:hover {{
  transform:translateY(-4px);
  box-shadow:0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);
  border-color:#D3DEEC;
}}
/* renkli, parıltılı vurgu çubuğu */
.kpi::before {{
  content:""; position:absolute; left:0; top:0; bottom:0; width:4px;
  background:linear-gradient(180deg, var(--brand), #60A5FA);
  box-shadow: 0 0 14px rgba(37,99,235,.5);
}}
.kpi.pos::before {{ background:linear-gradient(180deg, var(--pos), #34D399); box-shadow:0 0 14px rgba(5,150,105,.45); }}
.kpi.neg::before {{ background:linear-gradient(180deg, var(--neg), #F87171); box-shadow:0 0 14px rgba(220,38,38,.4); }}
/* hover'da ışık süpürme */
.kpi::after {{
  content:""; position:absolute; top:0; left:-60%; width:45%; height:100%;
  background:linear-gradient(105deg, transparent, rgba(37,99,235,.06), transparent);
  transform:skewX(-18deg); transition:left .55s ease;
}}
.kpi:hover::after {{ left:130%; }}
.kpi .k-label {{
  font-size:.7rem; font-weight:700; color:var(--muted);
  text-transform:uppercase; letter-spacing:.07em; margin-bottom:.4rem;
  display:flex; align-items:center; gap:.35rem;
}}
.kpi .k-value {{
  font-size:1.9rem; font-weight:800; letter-spacing:-.025em;
  line-height:1; color:var(--ink);
  font-variant-numeric: tabular-nums;
}}
.kpi.pos .k-value {{ color:var(--pos); }}
.kpi.neg .k-value {{ color:var(--neg); }}
.kpi .k-sub {{
  font-size:.72rem; color:var(--muted); margin-top:.5rem; font-weight:500;
}}
.kpi .k-badge {{
  display:inline-flex; align-items:center; gap:.2rem;
  font-size:.72rem; font-weight:800; padding:.14rem .5rem;
  border-radius:999px; margin-left:auto;
  font-variant-numeric: tabular-nums;
}}
.badge-pos {{ background:rgba(5,150,105,.12); color:var(--pos); }}
.badge-neg {{ background:rgba(220,38,38,.12); color:var(--neg); }}
.badge-neu {{ background:rgba(100,116,139,.14); color:var(--muted); }}

/* ── Bölüm başlığı ── */
.sec-title {{
  display:flex; align-items:center; gap:.6rem;
  font-size:1.05rem; font-weight:800; color:var(--ink);
  margin:.3rem 0 .25rem 0; letter-spacing:-.015em;
}}
.sec-title .dot {{
  width:9px; height:9px; border-radius:3px; flex:none;
  background:linear-gradient(135deg, var(--brand), #60A5FA);
  box-shadow: 0 0 10px rgba(37,99,235,.55);
}}
.sec-sub {{
  font-size:.82rem; color:var(--muted); font-weight:500;
  margin:0 0 1rem 1.35rem;
}}

/* ── Grafik başlığı ── */
.chart-h {{
  font-size:.8rem; font-weight:700; color:var(--ink-soft);
  text-transform:uppercase; letter-spacing:.05em;
  margin:.2rem 0 .1rem .1rem;
}}
.chart-hs {{
  font-size:.72rem; font-weight:500; color:var(--muted);
  margin:0 0 .3rem .1rem;
}}

/* ── Kaynak ── */
.src {{
  font-size:.72rem; color:{MUTED}; font-weight:500;
  margin-top:.4rem; border-left:2px solid var(--line); padding-left:.6rem;
}}

/* ── Rapor ── */
.report {{
  background:
    linear-gradient(180deg, rgba(37,99,235,.03), transparent 90px),
    {WHITE};
  border:1px solid var(--line);
  border-radius:16px; padding:1.5rem 1.85rem; margin-top:.5rem;
  font-size:.9rem; line-height:1.78; color:var(--ink-soft);
  box-shadow:0 2px 4px rgba(15,23,41,.04), 0 18px 40px -28px rgba(15,23,41,.25);
  position:relative;
}}
.report::before {{
  content:""; position:absolute; left:0; right:0; top:0; height:3px;
  border-radius:16px 16px 0 0;
  background:linear-gradient(90deg, var(--brand), {TEAL}, {AMBER});
  opacity:.85;
}}
.report b {{ color:var(--ink); font-weight:700; }}
.report .r-head {{
  font-size:.78rem; font-weight:700; color:var(--brand);
  text-transform:uppercase; letter-spacing:.06em;
  margin:1.15rem 0 .5rem 0; padding-bottom:.35rem;
  border-bottom:1px solid var(--line);
}}
.report .r-head:first-child {{ margin-top:0; }}
.report ul {{ margin:.2rem 0 .4rem 0; padding-left:1.15rem; }}
.report li {{ margin-bottom:.4rem; padding-left:.15rem; }}
.report li::marker {{ color:var(--brand); }}
.report .r-intro {{
  font-size:.92rem; line-height:1.8; color:var(--ink-soft);
  background:rgba(37,99,235,.035); border-left:3px solid var(--brand);
  padding:.7rem .95rem; border-radius:0 8px 8px 0; margin-bottom:.4rem;
}}
.report .r-para {{
  font-size:.9rem; line-height:1.8; color:var(--ink-soft);
  text-align:justify; margin:.1rem 0 .3rem 0;
}}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
  background: rgba(248,250,252,0.65); backdrop-filter: blur(24px);
  border-right: 1px solid var(--line);
  box-shadow: 1px 0 0 rgba(15,23,41,.02);
  min-width: 320px !important;
}}
[data-testid="stSidebar"] > div:first-child {{ padding-top: 0; }}
[data-testid="stSidebar"] .block-container {{ padding: 1.4rem 1.3rem 2rem 1.3rem; }}

/* Marka bloğu */
.side-brand {{
  font-size: 1.12rem; font-weight: 800; color: var(--ink);
  letter-spacing: -.01em; margin-bottom: .2rem;
  display: flex; align-items: center; gap: .4rem;
}}
.side-brand .accent {{ color: var(--brand); }}
.side-tag {{
  font-size: .7rem; color: var(--muted); font-weight: 600;
  margin-bottom: 1.1rem; letter-spacing: .02em;
  padding-bottom: 1rem; border-bottom: 1px dashed var(--line);
}}

/* Bölüm etiketleri — küçük ikonlu kapsül başlıklar */
.side-label {{
  font-size: .68rem; font-weight: 800; color: {BRAND_DK};
  text-transform: uppercase; letter-spacing: .08em;
  margin: 1.35rem 0 .5rem 0;
  display: flex; align-items: center; gap: .35rem;
}}
.side-label::before {{
  content: ""; width: 3px; height: 12px; border-radius: 2px;
  background: var(--brand); display: inline-block;
}}
.side-label.first {{ margin-top: .2rem; }}

/* Sidebar içi kart grupları — hafif cam */
.side-card {{
  background: rgba(255,255,255,.7); backdrop-filter: blur(8px);
  border: 1px solid var(--line); border-radius: 13px;
  padding: .85rem .95rem; margin-bottom: .7rem;
  box-shadow: 0 2px 8px -4px rgba(15,23,41,.1);
}}

/* Sidebar form elemanları — ortak dokunuş */
[data-testid="stSidebar"] label p {{
  font-size: .78rem !important; font-weight: 600 !important; color: var(--ink-soft) !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{
  border-radius: 9px !important; border-color: var(--line) !important;
  font-size: .84rem !important;
}}
[data-testid="stSidebar"] [data-baseweb="select"] > div:hover {{ border-color: var(--brand) !important; }}
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {{ margin-top: .3rem; }}
[data-testid="stSidebar"] .stCaption {{ font-size: .72rem !important; }}
[data-testid="stSidebar"] hr {{ margin: .9rem 0; border-color: var(--line); }}
[data-testid="stSidebar"] .stButton > button {{
  font-size: .82rem; padding: .5rem 1rem;
}}
[data-testid="stSidebar"] .stDownloadButton > button {{ font-size: .8rem; }}
[data-testid="stSidebar"] .stTextInput input {{
  border-radius: 9px; font-size: .82rem; border-color: var(--line);
}}
[data-testid="stSidebar"] .stTextInput input:focus {{ border-color: var(--brand); box-shadow: 0 0 0 1px var(--brand); }}

/* Küçük bilgi rozet grubu (footer) */
.side-meta-row {{
  display: flex; align-items: center; justify-content: space-between;
  font-size: .72rem; color: var(--muted); font-weight: 500; padding: .15rem 0;
}}
.side-meta-row b {{ color: var(--ink-soft); font-weight: 700; }}
.side-pill {{
  display: inline-block; background: rgba(37,99,235,.08); color: var(--brand);
  font-size: .68rem; font-weight: 700; padding: .12rem .5rem; border-radius: 999px;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
  gap:.15rem; padding:.32rem; border-radius:14px;
  background: linear-gradient(180deg, #F1F5FB, {PANEL});
  border:1px solid var(--line);
  box-shadow: inset 0 1px 2px rgba(15,23,41,.03);
  flex-wrap: wrap;
}}
.stTabs [data-baseweb="tab"] {{
  font-size:.82rem; font-weight:600; color:var(--muted);
  border-radius:10px; padding:.5rem .95rem; background:transparent;
  transition: color .18s ease, background .18s ease, transform .18s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{ color:var(--ink-soft); background:rgba(255,255,255,.6); }}
.stTabs [aria-selected="true"] {{
  background:{WHITE} !important; color:var(--brand) !important;
  box-shadow:0 2px 8px -2px rgba(37,99,235,.28), 0 1px 2px rgba(15,23,41,.06);
  transform: translateY(-1px);
}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top:1.15rem; }}

/* ── Butonlar ── */
.stButton > button {{
  background:linear-gradient(180deg, #3B82F6, {BRAND}); color:#fff; border:none;
  border-radius:11px; padding:.6rem 1.5rem; font-weight:700; font-size:.88rem;
  box-shadow:0 6px 16px -6px rgba(37,99,235,.6), inset 0 1px 0 rgba(255,255,255,.25);
  transition:transform .18s cubic-bezier(.2,.7,.3,1), box-shadow .18s ease, filter .18s ease;
  position:relative; overflow:hidden;
}}
.stButton > button:hover {{
  transform:translateY(-2px); filter:saturate(1.08);
  box-shadow:0 12px 24px -8px rgba(37,99,235,.6), inset 0 1px 0 rgba(255,255,255,.3);
}}
.stButton > button:active {{ transform:translateY(0); }}
.stDownloadButton > button {{
  background:{WHITE}; color:var(--brand); border:1.5px solid #BFD3F5;
  border-radius:11px; font-weight:700; font-size:.84rem; transition:all .18s ease;
}}
.stDownloadButton > button:hover {{
  background:rgba(37,99,235,.06); border-color:var(--brand); transform:translateY(-1px);
}}

hr {{ border-color:var(--line); margin:1.5rem 0; }}
.stRadio [role="radiogroup"] {{ gap:.3rem; }}
.stRadio [role="radiogroup"] label p {{ font-size:.82rem; font-weight:600; }}

/* ── Expander ── */
[data-testid="stExpander"] {{
  border:1px solid var(--line); border-radius:14px; overflow:hidden;
  box-shadow: 0 1px 2px rgba(15,23,41,.03); transition: box-shadow .2s ease;
}}
[data-testid="stExpander"]:hover {{ box-shadow: 0 6px 18px -12px rgba(15,23,41,.2); }}
[data-testid="stExpander"] summary {{ font-weight:600; font-size:.85rem; }}
[data-testid="stExpander"] summary:hover {{ color:var(--brand); }}

/* ── DataFrame ── */
[data-testid="stDataFrame"] {{
  border-radius:12px; overflow:hidden; border:1px solid var(--line);
}}

/* ── Metric / caption ── */
.stCaption, [data-testid="stCaptionContainer"] {{ color:var(--muted); }}

/* ── Spinner marka rengi ── */
.stSpinner > div {{ border-top-color: var(--brand) !important; }}

/* ── Plotly kabı — yumuşak çerçeve ── */
[data-testid="stPlotlyChart"] {{
  border-radius:14px;
}}

/* ── Genel giriş: sadece ilk yüklemede yumuşak açılış (rerun'da replay olmaz) ── */
.app-header {{ animation: fadeSlide .5s ease both; }}
@keyframes fadeSlide {{ from {{ opacity:0; transform:translateY(-6px); }} to {{ opacity:1; transform:none; }} }}

.app-foot {{
  text-align:center; color:{MUTED}; font-size:.72rem; font-weight:500;
  margin-top:2.5rem; padding-top:1.2rem; border-top:1px solid var(--line);
}}
.app-foot .sep {{ margin:0 .5rem; opacity:.5; }}
</style>
""", unsafe_allow_html=True)

# ─── PLOTLY TEMASI ───────────────────────────────────────────────────────────────
pio.templates["tuik"] = go.layout.Template(
    layout=dict(
        font=dict(family="Outfit, Inter, sans-serif", size=13, color=INK_SOFT),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=SERIES_PAL,
        margin=dict(l=16, r=80, t=24, b=45),
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.95)", bordercolor=LINE,
                        font=dict(family="Inter, sans-serif", size=14, color=INK)),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0,
                    font=dict(size=12, color=INK_SOFT), bgcolor="rgba(0,0,0,0)", itemwidth=30),
        xaxis=dict(showgrid=False, showline=True, linecolor=LINE, linewidth=1.5,
                   ticks="outside", tickcolor=LINE, ticklen=6,
                   tickfont=dict(size=12, color=MUTED)),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", griddash="solid",
                   zeroline=True, zerolinecolor="#94A3B8", zerolinewidth=1.5,
                   tickfont=dict(size=12, color=MUTED), hoverformat=".1f"),
    )
)
LAYOUT   = dict(template="tuik")
NOBAR    = {"displayModeBar": False}

# ════════════════════════════════════════════════════════════════════════════════
#  VERİ
# ════════════════════════════════════════════════════════════════════════════════
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data_cache.pkl")

@st.cache_resource(show_spinner="Veriler yükleniyor…")
def load_data():
    if not os.path.exists(CACHE_FILE):
        st.error("data_cache.pkl bulunamadı. Önce 'python cache_all.py' çalıştırın.")
        st.stop()
    with open(CACHE_FILE, "rb") as f:
        return pickle.load(f)

sys.path.insert(0, os.path.dirname(__file__))
from nace_config import (SECTOR_NAMES, SITC_MAP, ALL_MANUFACTURING,
                         SECTOR_SELECT_OPTIONS, TOTAL_MANUFACTURING)
from generate_report import (
    build_sekil1, build_sekil2, build_sekil3,
    build_sekil4, build_sekil5, build_sekil6, build_sekil7,
    build_dis_ticaret_fiyat, build_saat_ucret, build_ydufe, build_tufe
)

cache = load_data()
cache_date = cache.get("meta", {}).get("created_at", "bilinmiyor")[:10]
NACE_NAMES = cache.get("nace_names", {})

# ─── YARDIMCILAR ─────────────────────────────────────────────────────────────────
TR_MONTHS = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]

def nace_name(code):
    """C1391 -> resmi Türkçe isim (codelist'ten)."""
    return NACE_NAMES.get(code, code)

def short_name(code, n=42):
    s = nace_name(code)
    return s if len(s) <= n else s[:n-1].rstrip() + "…"

def wrap_name(code, width=26):
    """Uzun isimleri <br> ile 2 satıra böler (y ekseni etiketleri için)."""
    s = nace_name(code)
    if len(s) <= width: return s
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur: lines.append(cur)
    return "<br>".join(lines[:2]) + ("…" if len(lines) > 2 else "")

def annual_avg(series_dict, min_m=4):
    by_year = {}
    for p, v in series_dict.items():
        if v is None: continue
        by_year.setdefault(p.split("-")[0], []).append(v)
    if not by_year: return {}
    # 1 ondalık → çubuk/ısı haritası hover'larında hep temiz görünüm (ör. 36.2)
    return {yr: round(sum(vs)/len(vs), 1)
            for yr, vs in sorted(by_year.items())
            if len(vs) >= min_m or yr == max(by_year)}

def last_n_months(series_dict, n=48):
    return dict(sorted(series_dict.items())[-n:])

def tr_month(p):
    try:
        yr, mo = p.split("-")
        return f"{TR_MONTHS[int(mo)-1]} {yr[2:]}"
    except Exception:
        return p

def series_xy(s, n):
    pts = sorted(last_n_months(s, n).items())
    xs = [tr_month(p) for p, v in pts if v is not None]
    # Grafiğe çizilen değerleri 1 ondalığa yuvarla → hover/etiketler her zaman
    # temiz görünür (ör. -36.277... yerine -36.3), unified-hover fallback'te bile.
    ys = [round(v, 1) for _, v in pts if v is not None]
    return xs, ys

def end_label(fig, xs, ys, color, fmt="{:+.1f}%"):
    """Tek serinin uç noktası — çakışma yoksa doğrudan kullan."""
    if not xs: return
    fig.add_trace(go.Scatter(
        x=[xs[-1]], y=[ys[-1]], mode="markers+text",
        marker=dict(color=color, size=8, line=dict(color=WHITE, width=1.5)),
        text=[fmt.format(ys[-1])], textposition="middle right",
        textfont=dict(size=11.5, color=color, family="Inter"),
        showlegend=False, hoverinfo="skip", cliponaxis=False,
    ))

def add_end_labels(fig, ends, gap_frac=0.07):
    """
    ends: [(x_last, y_last, color, fmt_str)] — çok serili çizgilerde uç etiketleri
    dikey olarak yayarak üst üste binmelerini önler. İşaretçi gerçek noktada kalır,
    değer etiketi çakışmayacak şekilde kaydırılır.
    """
    ends = [e for e in ends if e[0] is not None and e[1] is not None]
    if not ends: return
    ys = [e[1] for e in ends]
    rng = (max(ys) - min(ys)) or (abs(max(ys)) or 1)
    gap = rng * gap_frac
    order = sorted(range(len(ends)), key=lambda i: ends[i][1])
    adj = {}
    prev = None
    for i in order:
        y = ends[i][1]
        if prev is not None and y - prev < gap:
            y = prev + gap
        adj[i] = y
        prev = y
    for i, (x, yv, color, fmt) in enumerate(ends):
        fig.add_trace(go.Scatter(
            x=[x], y=[yv], mode="markers",
            marker=dict(color=color, size=7, line=dict(color=WHITE, width=1.4)),
            showlegend=False, hoverinfo="skip", cliponaxis=False))
        fig.add_annotation(
            x=x, y=adj[i], text=fmt.format(yv),
            xref="x", yref="y", xanchor="left", xshift=9, showarrow=False,
            font=dict(size=11, color=color, family="Inter"), align="left")

def fmt_val(v, suffix="%", signed=True):
    if v is None: return "—"
    if suffix == "%":
        return f"{v:+.1f}%" if signed else f"{v:.1f}%"
    return f"{v:.1f}{suffix}"

def first_series(fig_dict):
    if not fig_dict: return None
    return next(iter(fig_dict.values()), None)

def spark_svg(series, color, w=124, h=30, n=24):
    """KPI kartı içi mini eğri (son n ay) — gradyan dolgulu."""
    if not series: return ""
    ys = [v for _, v in sorted(series.items())[-n:] if v is not None]
    if len(ys) < 3: return ""
    mn, mx = min(ys), max(ys)
    rng = (mx - mn) or 1
    step = w / (len(ys) - 1)
    coords = [(i*step, h - (y-mn)/rng*(h-8) - 4) for i, y in enumerate(ys)]
    line_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area_pts = f"0,{h} " + line_pts + f" {w},{h}"
    lx, ly = coords[-1]
    gid = f"sg{abs(hash((color, len(ys), round(ys[-1], 2)))) % 100000}"
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'preserveAspectRatio="none" style="display:block;margin-top:.5rem;width:100%">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{color}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
        f'<polygon points="{area_pts}" fill="url(#{gid})"/>'
        f'<polyline points="{line_pts}" fill="none" stroke="{color}" stroke-width="1.8" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" fill="{color}" '
        f'stroke="#fff" stroke-width="1.2"/></svg>')

def kpi_card(col, label, value, sub, tone=None, badge=None, icon="", spark=""):
    cls = {"pos": "pos", "neg": "neg"}.get(tone, "")
    badge_html = ""
    if badge is not None:
        b_cls = "badge-pos" if tone == "pos" else "badge-neg" if tone == "neg" else "badge-neu"
        arrow = "▲" if tone == "pos" else "▼" if tone == "neg" else "•"
        badge_html = f'<span class="k-badge {b_cls}">{arrow} {badge}</span>'
    col.markdown(f"""
    <div class="kpi {cls}">
      <div class="k-label">{icon} {label} {badge_html}</div>
      <div class="k-value">{value}</div>
      <div class="k-sub">{sub}</div>
      {spark}
    </div>""", unsafe_allow_html=True)

def sec_title(text, sub=None):
    st.markdown(f'<div class="sec-title"><span class="dot"></span>{text}</div>',
                unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="sec-sub">{sub}</div>', unsafe_allow_html=True)

def chart_head(title, sub=None):
    st.markdown(f'<div class="chart-h">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="chart-hs">{sub}</div>', unsafe_allow_html=True)

def source(text):
    st.markdown(f'<div class="src">{text}</div>', unsafe_allow_html=True)

# ─── ANALİST TÜREVLERİ (reel, verimlilik, momentum) ──────────────────────────────
def first_serie_sorted(fig_dict):
    """İlk serinin {period: value} sözlüğünü döner (None temizlenmez)."""
    if not fig_dict: return {}
    return dict(sorted(next(iter(fig_dict.values())).items()))

def merged_avg_series(fig_dict):
    """Çok serili bir fig'in dönem-bazında ortalama serisini döner."""
    merged = {}
    for _, s in (fig_dict or {}).items():
        for p, v in s.items():
            if v is not None: merged.setdefault(p, []).append(v)
    return {p: sum(vs)/len(vs) for p, vs in merged.items()}

def real_growth(nom_series, defl_series):
    """Nominal YoY %'yi ÜFE YoY % ile deflate eder: (1+n)/(1+d)-1. Ortak dönemler.
    (Ulusal hesaplar deflasyon pratiği — Eurostat 2016, SNA 2008.)"""
    out = {}
    for p, n in nom_series.items():
        d = defl_series.get(p)
        if n is None or d is None: continue
        try:
            out[p] = ((1 + n/100.0) / (1 + d/100.0) - 1) * 100.0
        except ZeroDivisionError:
            continue
    return out

# Verimlilik = (1+g_Y)/(1+g_L)−1: kesikli zamanda doğru form (OECD 2001,
# Measuring Productivity). Aritmetik fark (g_Y−g_L) yalnız küçük oranlarda
# geçerli bir yaklaşımdır; Türkiye ölçeğindeki oranlarda sapma büyür.
ratio_growth = real_growth

def diff_series(a, b):
    """İki YoY serisinin aritmetik farkı (betimleyici makas): a - b, ortak dönem."""
    return {p: a[p] - b[p] for p in a if p in b and a[p] is not None and b[p] is not None}

def momentum(series, win=3):
    """Son `win` ay ort. ile önceki `win` ay ort. farkı → ivme (puan)."""
    pts = [v for _, v in sorted(series.items()) if v is not None]
    if len(pts) < 2 * win: return None
    return sum(pts[-win:]) / win - sum(pts[-2*win:-win]) / win

def vol_std(series, n=24):
    """Son n ayın standart sapması (oynaklık göstergesi)."""
    pts = [v for _, v in sorted(series.items())[-n:] if v is not None]
    if len(pts) < 4: return None
    m = sum(pts) / len(pts)
    return (sum((x - m) ** 2 for x in pts) / (len(pts) - 1)) ** 0.5

def last_value(series):
    pts = [(p, v) for p, v in sorted(series.items()) if v is not None]
    return pts[-1] if pts else (None, None)

# ════════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown('<div class="side-brand">📊 Sektörel<span class="accent"> Analiz</span></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="side-tag">TÜİK SDMX · TCMB EVDS · İSO 500</div>', unsafe_allow_html=True)

    # ── Sektör seçimi + hızlı arama ──────────────────────────────────────────
    st.markdown('<div class="side-label first">🏭 Sektör</div>', unsafe_allow_html=True)
    nace_options_full = {f"{k} · {SECTOR_NAMES.get(k, k)}": k for k in SECTOR_SELECT_OPTIONS}

    arama = st.text_input("Sektör ara", value="", placeholder="🔍 İsim veya kod ile ara (örn. tekstil, C29)",
                          label_visibility="collapsed")
    if arama.strip():
        q = arama.strip().lower()
        filtered = {lbl: k for lbl, k in nace_options_full.items() if q in lbl.lower()}
        nace_options = filtered or nace_options_full
        if not filtered:
            st.caption("⚠️ Eşleşme yok — tüm liste gösteriliyor")
    else:
        nace_options = nace_options_full

    _default = "C13 · Tekstil Urunleri Imalati"
    _default_key = _default if _default in nace_options else next(iter(nace_options))
    default_idx = list(nace_options.keys()).index(_default_key)
    selected_label = st.selectbox("NACE", list(nace_options.keys()),
                                  index=default_idx, label_visibility="collapsed")
    nace = nace_options[selected_label]

    # ── Karşılaştırma sektörü ────────────────────────────────────────────────
    st.markdown('<div class="side-label">⚖️ Karşılaştırma</div>', unsafe_allow_html=True)
    cmp_choices = ["— Karşılaştırma yok —"] + [f"{k} · {SECTOR_NAMES.get(k, k)}"
                                                for k in SECTOR_SELECT_OPTIONS if k != nace]
    cmp_label = st.selectbox("Kıyas sektörü", cmp_choices, index=0,
                             label_visibility="collapsed",
                             help="Üretim sekmesindeki aylık grafiğe ikinci bir sektörü kesikli çizgi olarak ekler")
    compare_nace = None if cmp_label == cmp_choices[0] else cmp_label.split(" · ")[0]

    # ── Zaman aralığı: hızlı presetler + ince ayar ──────────────────────────
    st.markdown('<div class="side-label">📅 Zaman Aralığı</div>', unsafe_allow_html=True)
    if "ay_sayisi" not in st.session_state:
        st.session_state["ay_sayisi"] = 48
    preset_cols = st.columns(4)
    presets = [("1Y", 12), ("2Y", 24), ("4Y", 48), ("6Y", 72)]
    for pc, (lbl, val) in zip(preset_cols, presets):
        active = st.session_state["ay_sayisi"] == val
        if pc.button(lbl, key=f"preset_{val}", use_container_width=True,
                    type="primary" if active else "secondary"):
            st.session_state["ay_sayisi"] = val
            st.rerun()
    ay_sayisi = st.slider("Ay", 12, 72, step=6, key="ay_sayisi",
                          label_visibility="collapsed",
                          help="Çizgi grafiklerde gösterilecek son ay sayısı")
    st.caption(f"Son **{ay_sayisi} ay** gösteriliyor")

    # ── Para birimi (TL değer taşıyan grafikler için) ────────────────────────
    _kur_ay = cache.get("usdtry") or {}
    if _kur_ay:
        st.markdown('<div class="side-label">💱 Para Birimi</div>', unsafe_allow_html=True)
        _para_sec = st.radio("Para birimi", ["₺ TL", "$ USD"], horizontal=True,
                             label_visibility="collapsed", key="para_birimi",
                             help="Ürün Detayı ve İSO 500'deki TL tutarlarını yıllık "
                                  "ortalama USD/TRY kuruyla dolara çevirir (TCMB)")
        usd_mode = _para_sec.startswith("$")
    else:
        usd_mode = False

    # ── Haber & Risk arama override ──────────────────────────────────────────
    st.markdown('<div class="side-label">📰 Haber Sorgusu</div>', unsafe_allow_html=True)
    news_query = st.text_input("Özel arama terimi", value="",
                               placeholder="Boş bırakılırsa sektör adı kullanılır",
                               label_visibility="collapsed",
                               help="Haber & Risk sekmesinde Google News araması için özel anahtar kelime")

    # ── Veri & önbellek ───────────────────────────────────────────────────────
    st.markdown('<div class="side-label">🗂️ Veri</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="side-card">
      <div class="side-meta-row"><span>Güncelleme</span><b>{cache_date}</b></div>
      <div class="side-meta-row"><span>Kapsam</span><b>C10–C33</b></div>
      <div class="side-meta-row"><span>Kaynaklar</span>
        <span class="side-pill">9 set</span></div>
    </div>""", unsafe_allow_html=True)
    if st.button("🔄 Önbelleği Yenile", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

    # LLM durumu: kendi anahtar mı, ücretsiz havuz mu?
    try:
        from llm_client import _primary_key
        _has_key = _primary_key() is not None
    except Exception:
        _has_key = False
    _llm_txt = ("🟢 Kendi API anahtarı" if _has_key
                else "🟡 Ücretsiz havuz (yoğunsa verilerden yazılır)")
    st.markdown(f'<div class="side-meta-row" style="margin-top:.5rem">'
                f'<span>LLM</span><b style="font-size:.68rem">{_llm_txt}</b></div>',
                unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  VERİ HAZIRLA
# ════════════════════════════════════════════════════════════════════════════════
sector    = SECTOR_NAMES.get(nace, nace)
sector_tr = nace_name(nace) if nace in NACE_NAMES else sector

with st.spinner("Hesaplanıyor…"):
    _ana_c = cache.get("ana_c")
    f1 = build_sekil1(nace, cache["alt_c"], ana_c_series=_ana_c)
    f2 = build_sekil2(nace, cache["sinif_o"], ana_c_series=_ana_c)
    f3 = build_sekil3(nace, cache["dis_ticaret"])
    f4 = build_sekil4(nace, cache["kko"])
    f5 = build_sekil5(nace, cache["ufe"])
    f6 = build_sekil6(nace, cache["ciro"])    if "ciro"    in cache else {}
    f7 = build_sekil7(nace, cache["ucretli"]) if "ucretli" in cache else {}
    
    f_fiyat = build_dis_ticaret_fiyat(nace, cache.get("dis_ticaret_fiyat", {}))
    f_su    = build_saat_ucret(nace, cache.get("saat_ucret", {}))
    f_ydufe = build_ydufe(nace, cache.get("ydufe", []))
    f_tufe  = build_tufe(cache.get("tufe", []))
    try:
        from iso_data import sector_iso
        f8 = sector_iso(nace)
    except Exception:
        f8 = None
    try:
        from prodtr_data import sector_products
        f9 = sector_products(nace)
    except Exception:
        f9 = None

# ── Para birimi türevleri: yıllık ortalama USD/TRY + dönüşüm yardımcıları ──────
_kur_yil = {}
if _kur_ay:
    _kby = {}
    for _p, _v in _kur_ay.items():
        _kby.setdefault(int(_p[:4]), []).append(_v)
    _kur_yil = {y: sum(vs)/len(vs) for y, vs in sorted(_kby.items())}

PARA_SIM = "$" if usd_mode else "₺"

def to_cur_yillik(series_tl):
    """{yıl: TL} serisini seçili para birimine çevirir (USD: yıllık ort. kur)."""
    if not usd_mode:
        return dict(series_tl or {})
    return {y: v / _kur_yil[y] for y, v in (series_tl or {}).items()
            if y in _kur_yil and _kur_yil[y]}

def tl_to_cur(v, yil):
    """Tek TL tutarı seçili para birimine çevirir; kur yoksa None."""
    if v is None: return None
    if not usd_mode: return v
    k = _kur_yil.get(yil)
    return v / k if k else None

# ─── SIDEBAR: VERI INDIR (figler hazir olduktan sonra) ──────────────────────────
with st.sidebar:
    import io
    def _xlsx_bytes():
        buf = io.BytesIO()
        sheets = [("Uretim", f1), ("AltKirilim", f2), ("DisTicaret", f3),
                  ("KKO", {k: (dict(v) if not isinstance(v, dict) else v) for k, v in f4.items()}),
                  ("UFE", f5), ("Ciro", f6), ("Istihdam", f7)]
        with pd.ExcelWriter(buf, engine="openpyxl") as xw:
            for name, fd in sheets:
                if not fd: continue
                df = pd.DataFrame(fd)
                df.index.name = "Donem"
                df.sort_index().round(2).to_excel(xw, sheet_name=name[:31])
            if f8 is not None:
                f8["firmalar"].to_excel(xw, sheet_name="ISO500", index=False)
            if f9 is not None and f9.get("all_rows"):
                pdf = pd.DataFrame([{
                    "PRODTR": r["kod"], "Urun": r["tanim"],
                    "Satis_TL": r["satis_deger"], "Uretim": r["uretim"],
                    "Birim": r["birim"], "Girisim": r["girisim"],
                } for r in f9["all_rows"]])
                pdf.to_excel(xw, sheet_name="Urunler_PRODTR", index=False)
        return buf.getvalue()
    st.markdown('<div class="side-label">Dışa Aktar</div>', unsafe_allow_html=True)
    st.download_button("⬇ Excel Veri (.xlsx)", data=_xlsx_bytes(),
                       file_name=f"{nace}_veri.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)

# ─── HEADER ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
  <div class="eyebrow">Sektörel Araştırmalar</div>
  <h1>{sector_tr}</h1>
  <div class="sub">{nace} · İmalat Sanayii · NACE Rev.2</div>
  <div class="meta">
    <span class="chip">TÜİK SDMX v1.5</span>
    <span class="chip">TCMB EVDS</span>
    <span class="chip">📅 {cache_date}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  KPI KARTLARI
# ════════════════════════════════════════════════════════════════════════════════
def last_val(fig):
    if not fig: return None, None
    for _, series in fig.items():
        pts = sorted(series.items())
        if pts: return pts[-1][1], pts[-1][0]
    return None, None

prod_val, prod_per = last_val(f1)
ih_series = {k: v for k, v in f3.items() if "hracat" in k and "thalat" not in k}
it_series = {k: v for k, v in f3.items() if "thalat" in k}
ih_val, ih_per = last_val(ih_series)
it_val, it_per = last_val(it_series)
kko_sec = {k: v for k, v in f4.items() if "anayii" not in k}
kko_val, kko_per = last_val(kko_sec if kko_sec else f4)
ufe_val, ufe_per = last_val(f5)
ciro_val, ciro_per = last_val(f6)

def tone_of(v, invert=False):
    if v is None: return None
    if invert: return "neg" if v >= 0 else "pos"
    return "pos" if v >= 0 else "neg"

def tr_per(p):
    return tr_month(p) if p else "—"

def _tone_color(t):
    return POS if t == "pos" else NEG if t == "neg" else BRAND

# Badge dönem bilgisi taşır (değerin tekrarı değil); değer büyük rakamda bir kez yazılır.
cols = st.columns(6)
kpi_card(cols[0], "Üretim", fmt_val(prod_val), "YoY, takvim arındırılmış",
         tone=tone_of(prod_val), badge=tr_per(prod_per) if prod_val is not None else None,
         icon="🏭", spark=spark_svg(first_series(f1), _tone_color(tone_of(prod_val))))
kpi_card(cols[1], "İhracat", fmt_val(ih_val), "miktar endeksi YoY",
         tone=tone_of(ih_val), badge=tr_per(ih_per) if ih_val is not None else None,
         icon="🌍", spark=spark_svg(first_series(ih_series), _tone_color(tone_of(ih_val))))
kpi_card(cols[2], "İthalat", fmt_val(it_val), "miktar endeksi YoY",
         tone=tone_of(it_val), badge=tr_per(it_per) if it_val is not None else None,
         icon="📦", spark=spark_svg(first_series(it_series), _tone_color(tone_of(it_val))))
kpi_card(cols[3], "Ciro", fmt_val(ciro_val), "nominal YoY, arındırılmış",
         tone=tone_of(ciro_val), badge=tr_per(ciro_per) if ciro_val is not None else None,
         icon="📈", spark=spark_svg(first_series(f6), _tone_color(tone_of(ciro_val))))
kpi_card(cols[4], "KKO", fmt_val(kko_val, suffix="%", signed=False),
         "kapasite kullanım oranı", tone=None, icon="⚙️",
         badge=tr_per(kko_per) if kko_val is not None else None,
         spark=spark_svg(first_series({k: (dict(v) if not isinstance(v, dict) else v)
                                       for k, v in kko_sec.items()}), BRAND))
kpi_card(cols[5], "ÜFE", fmt_val(ufe_val), "yıllık üretici enflasyonu",
         tone="neg" if (ufe_val or 0) > 20 else "pos",
         badge=tr_per(ufe_per) if ufe_val is not None else None, icon="💰",
         spark=spark_svg(first_series(f5), _tone_color("neg" if (ufe_val or 0) > 20 else "pos")))

# ── TÜREV (ANALİST) GÖSTERGELERİ ────────────────────────────────────────────────
# Reel ciro = nominal ciro YoY, ÜFE ile deflate edilmiş
_prod_ser  = merged_avg_series(f1)                    # üretim YoY (alt grup ort.)
_ciro_ser  = first_serie_sorted(f6)                   # nominal ciro YoY
_ufe_ser   = first_serie_sorted(f5)                   # sektör ÜFE YoY
_emp_ser   = first_serie_sorted(f7)                   # istihdam YoY
_maas_ser  = dict(sorted((f_su.get("Brüt Maaş YoY %") or {}).items()))  # ücret-maaş YoY
_reel_ciro = real_growth(_ciro_ser, _ufe_ser)         # reel ciro YoY
_verim     = ratio_growth(_prod_ser, _emp_ser)        # verimlilik = (1+gY)/(1+gL)−1
_ulc       = ratio_growth(_maas_ser, _prod_ser)       # ULC = ücret kütlesi / reel üretim
_ih_ser    = first_series(ih_series) or {}
_it_ser    = first_series(it_series) or {}
_net_trade = diff_series(_ih_ser, _it_ser)            # dış ticaret makası (ihr - ith)

reel_p, reel_v   = last_value(_reel_ciro)   # last_value → (dönem, değer)
verim_p, verim_v = last_value(_verim)
ulc_p, ulc_v     = last_value(_ulc)
net_p, net_v     = last_value(_net_trade)
prod_mom         = momentum(_prod_ser)

st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
_dkpis = [
    ("Reel Ciro", fmt_val(reel_v), "ÜFE'den arındırılmış YoY",
     tone_of(reel_v), _reel_ciro, "💵", tr_per(reel_p)),
    ("İşgücü Verimliliği", fmt_val(verim_v),
     "üretim/istihdam bileşik oranı (OECD 2001)",
     tone_of(verim_v), _verim, "⚡", tr_per(verim_p)),
]
if ulc_v is not None:  # ücret verisi önbellekte varsa gerçek ULC göster
    _dkpis.append(("Birim İşgücü Maliyeti", fmt_val(ulc_v),
                   "ücret kütlesi / üretim hacmi",
                   tone_of(ulc_v, invert=True), _ulc, "🧾", tr_per(ulc_p)))
_dkpis += [
    ("Dış Ticaret Makası", fmt_val(net_v), "ihracat − ithalat (YoY farkı)",
     tone_of(net_v), _net_trade, "⚖️", tr_per(net_p)),
    ("Üretim Momentumu", fmt_val(prod_mom) if prod_mom is not None else "—",
     "son 3 ay − önceki 3 ay ivme", tone_of(prod_mom), _prod_ser, "🚀", "3a/3a"),
]
dcols = st.columns(len(_dkpis))
for _dc, (_lbl, _val, _sub, _tn, _spk, _ic, _bdg) in zip(dcols, _dkpis):
    kpi_card(_dc, _lbl, _val, _sub, tone=_tn,
             badge=_bdg if _val != "—" else None, icon=_ic,
             spark=spark_svg(_spk, _tone_color(_tn)))

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

# ── 24 SEKTÖR PANELİ (bileşik skor ve yüzdelik konumlanma için) ─────────────────
@st.cache_data(show_spinner=False)
def cross_sector_panel(cache_key):
    """24 sektörün son değerlerini türev metriklerle birlikte döner (yüzdelik için)."""
    rows = {}
    for k in ALL_MANUFACTURING:
        try:
            g1 = build_sekil1(k, cache["alt_c"], ana_c_series=_ana_c)
            g3 = build_sekil3(k, cache["dis_ticaret"])
            g4 = build_sekil4(k, cache["kko"])
            g5 = build_sekil5(k, cache["ufe"])
            g6 = build_sekil6(k, cache["ciro"])    if "ciro"    in cache else {}
            g7 = build_sekil7(k, cache["ucretli"]) if "ucretli" in cache else {}
            prod = merged_avg_series(g1)
            ciro = first_serie_sorted(g6)
            ufe  = first_serie_sorted(g5)
            emp  = first_serie_sorted(g7)
            ihd  = {p: v for lbl, s in g3.items()
                    if "hracat" in lbl and "thalat" not in lbl for p, v in s.items()}
            reel = real_growth(ciro, ufe)
            verim = ratio_growth(prod, emp)
            kko_s = {kk: vv for kk, vv in g4.items() if "anayii" not in kk}
            rows[k] = {
                "uretim":    last_value(prod)[1],
                "reel_ciro": last_value(reel)[1],
                "ihracat":   last_value(ihd)[1] if ihd else None,
                "verim":     last_value(verim)[1],
                "istihdam":  last_value(emp)[1],
                "ufe":       last_value(ufe)[1],
                "kko":       last_value(first_serie_sorted(kko_s))[1] if kko_s else None,
            }
        except Exception:
            continue
    return rows

def _pct_rank(values, target):
    """target'ın values içindeki yüzdelik dilimi (0-100)."""
    vals = [v for v in values if v is not None]
    if target is None or len(vals) < 2: return None
    below = sum(1 for v in vals if v < target)
    return round(below / (len(vals) - 1) * 100)

# ════════════════════════════════════════════════════════════════════════════════
#  SEKMELER
# ════════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📌  Genel Bakış",
    "🏭  Üretim", "🌍  Dış Ticaret",
    "⚙️  Kapasite", "💰  Maliyet Baskısı", "📈  Ciro", "👥  İstihdam",
    "🏆  İSO 500", "📰  Haber & Risk", "📐  Analist Görünümü",
    "🧴  Ürün Detayı", "📘  Metodoloji",
])

# ── TAB 0: GENEL BAKIŞ ───────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def sector_league(cache_key):
    """24 imalat sektörünün son üretim YoY değeri (alt grup ortalaması)."""
    out = {}
    for k in ALL_MANUFACTURING:
        fk = build_sekil1(k, cache["alt_c"])
        if not fk: continue
        merged = {}
        for _, s in fk.items():
            for p, v in s.items():
                if v is not None: merged.setdefault(p, []).append(v)
        if not merged: continue
        lp = max(merged)
        out[k] = (round(sum(merged[lp]) / len(merged[lp]), 1), lp)
    return out

with tabs[0]:
    # ── Makro Bağlam — Türkiye geneli (sektörü konumlandıran çerçeve) ──────────
    _tufe_ser  = first_serie_sorted(f_tufe)
    _tufe_p, _tufe_v = last_value(_tufe_ser)
    ufe_imalat_series = {k: v for k, v in f5.items()
                         if " c " in (" " + k.lower() + " ")}
    _uimal_ser = first_serie_sorted(ufe_imalat_series)
    _uimal_p, ufe_imalat_val = last_value(_uimal_ser)
    _redk_ser  = dict(sorted((cache.get("redk") or {}).items()))
    _redk_p, _redk_v = last_value(_redk_ser)
    _kur_p = max(_kur_ay) if _kur_ay else None
    _kur_v = _kur_ay.get(_kur_p) if _kur_p else None
    _kur_yoy = None
    if _kur_p and _kur_ay:
        _oy = f"{int(_kur_p[:4])-1}{_kur_p[4:]}"
        if _kur_ay.get(_oy):
            _kur_yoy = (_kur_v / _kur_ay[_oy] - 1) * 100

    _kur_sub = "TCMB kur arşivi, ay ortası"
    if _kur_yoy is not None:
        _yon = "TL değer kaybı" if _kur_yoy >= 0 else "TL değer kazancı"
        _kur_sub = f"yıllık {_kur_yoy:+.1f}% ({_yon})".replace(".", ",")
    # Verisi olan makro kartlar (TÜFE/REDK önbelleğe eklendiğinde kendiliğinden görünür)
    _mk_items = []
    if _tufe_v is not None:
        _mk_items.append(("TÜFE", fmt_val(_tufe_v), "tüketici enflasyonu, yıllık",
                          "neg" if _tufe_v > 20 else None, tr_per(_tufe_p), "🛒",
                          spark_svg(_tufe_ser, AMBER)))
    if ufe_imalat_val is not None:
        _mk_items.append(("Yİ-ÜFE (İmalat)", fmt_val(ufe_imalat_val),
                          "üretici enflasyonu, imalat geneli",
                          "neg" if ufe_imalat_val > 20 else None, tr_per(_uimal_p), "🏭",
                          spark_svg(_uimal_ser, ROSE)))
    if _kur_v is not None:
        _mk_items.append(("USD/TRY", f"{_kur_v:,.2f}".replace(".", ","), _kur_sub,
                          "neg" if (_kur_yoy or 0) > 20 else None, tr_per(_kur_p), "💱",
                          spark_svg(_kur_ay, NAVY)))
    if _redk_v is not None:
        _mk_items.append(("REDK", f"{_redk_v:,.1f}".replace(".", ","),
                          "reel efektif kur · düşük = rekabetçi TL",
                          None, tr_per(_redk_p), "⚖️", spark_svg(_redk_ser, TEAL)))
    if _mk_items:
        sec_title("Makro Bağlam",
                  "Türkiye geneli fiyat ve kur ortamı · sektörel verilerin okunduğu çerçeve")
        mc0 = st.columns(len(_mk_items))
        for _col, (_l, _v, _s, _t, _b, _i, _sp) in zip(mc0, _mk_items):
            kpi_card(_col, _l, _v, _s, tone=_t, badge=_b, icon=_i, spark=_sp)
        st.markdown("<div style='height:1.1rem'></div>", unsafe_allow_html=True)

    ov_l, ov_r = st.columns([5, 4], gap="large")

    # ── Sektör Ligi ──
    with ov_l:
        sec_title("Sektör Ligi", "24 imalat sektörünün son üretim performansı (YoY %)")
        league = sector_league(cache_date)
        if league:
            items = sorted(league.items(), key=lambda kv: kv[1][0])
            codes  = [k for k, _ in items]
            l_vals = [v for _, (v, _) in items]
            l_cols = [BRAND if k == nace else ("#C7D6EE" if v >= 0 else "#F3C1C1")
                      for k, (v, _) in items]
            fig_lg = go.Figure()
            fig_lg.add_trace(go.Bar(
                y=[f"{k.lstrip('C')} · {short_name(k, 26)}" for k in codes],
                x=l_vals, orientation="h",
                marker_color=l_cols, marker_line_width=0, marker=dict(cornerradius=3),
                text=[f"{v:+.1f}" for v in l_vals],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=9.5, family="Inter"),
                hovertext=[f"{k} · {nace_name(k)} — {tr_month(p)}" for k, (v, p) in items],
                hovertemplate="%{hovertext}<br><b>%{x:+.1f}%</b><extra></extra>",
                width=0.62,
            ))
            fig_lg.update_layout(**LAYOUT, height=620, showlegend=False,
                                 hovermode="closest",
                                 margin=dict(l=8, r=46, t=8, b=36))
            fig_lg.update_xaxes(ticksuffix="%")
            fig_lg.update_yaxes(showgrid=False,
                                tickfont=dict(size=10,
                                              color=INK_SOFT))
            fig_lg.add_vline(x=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig_lg, use_container_width=True, config=NOBAR)
            source("Her sektörün alt grup ortalaması, son yayımlanan ay · mavi = seçili sektör")
        else:
            st.info("Lig verisi hesaplanamadı.")

    with ov_r:
        # ── Sektör Bileşik Skoru (yüzdelik tabanlı) ──
        sec_title("Sektör Bileşik Skoru",
                  "24 imalat sektörü içindeki yüzdelik konumların eşit ağırlıklı ortalaması (0–100)")

        imalat_kko = {k: v for k, v in f4.items() if "anayii" in k}
        imalat_kko_val, _ = last_val({k: (dict(v) if not isinstance(v, dict) else v)
                                      for k, v in imalat_kko.items()})
        emp_val, _ = last_val(f7)

        panel0 = cross_sector_panel(cache_date)
        comp_ok = {}
        if panel0 and nace in panel0:
            _cur0 = panel0[nace]
            for _lbl, _key, _inv in [("Üretim", "uretim", False),
                                     ("Reel Ciro", "reel_ciro", False),
                                     ("İhracat", "ihracat", False),
                                     ("Verimlilik", "verim", False),
                                     ("İstihdam", "istihdam", False),
                                     ("KKO", "kko", False),
                                     ("Maliyet (ÜFE)", "ufe", True)]:
                _allv = [panel0[k].get(_key) for k in panel0]
                _tgt = _cur0.get(_key)
                if _inv:  # yüksek = kötü → işaret çevir
                    _allv = [-v if v is not None else None for v in _allv]
                    _tgt = -_tgt if _tgt is not None else None
                _pr = _pct_rank(_allv, _tgt)
                if _pr is not None:
                    comp_ok[_lbl] = _pr
        score = round(sum(comp_ok.values()) / len(comp_ok)) if comp_ok else None

        if score is not None:
            g_col = POS if score >= 60 else AMBER if score >= 40 else NEG
            g_txt = ("üst dilim" if score >= 66 else
                     "orta dilim" if score >= 33 else "alt dilim")
            st.markdown(f"""
            <div class="report" style="text-align:center;padding:.9rem 1rem;margin-bottom:.6rem">
              <span style="font-size:2.6rem;font-weight:800;color:{g_col};
                    font-variant-numeric:tabular-nums">{score}</span>
              <span style="color:{MUTED};font-size:1rem">/100</span>
              <div style="color:{MUTED};font-size:.75rem;margin-top:.15rem">
                24 sektör arasında {g_txt}</div>
            </div>""", unsafe_allow_html=True)

            # Bileşen yüzdelik çubukları
            fig_c = go.Figure()
            c_names = list(comp_ok.keys())[::-1]
            c_vals  = [comp_ok[k] for k in c_names]
            fig_c.add_trace(go.Bar(
                y=c_names, x=c_vals, orientation="h",
                marker_color=[POS if v >= 66 else AMBER if v >= 33 else NEG for v in c_vals],
                marker_line_width=0, marker=dict(cornerradius=3),
                text=[f"P{v:.0f}" for v in c_vals],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=10, family="Inter"),
                hovertemplate="%{y}: 24 sektör içinde <b>%{x:.0f}. yüzdelik</b><extra></extra>",
                width=0.55,
            ))
            fig_c.update_layout(**LAYOUT, height=250, showlegend=False,
                                hovermode="closest",
                                margin=dict(l=8, r=40, t=4, b=20))
            fig_c.update_xaxes(range=[0, 115], showticklabels=False, showline=False)
            fig_c.add_vline(x=50, line_width=1, line_dash="dot", line_color="#CBD5E1")
            fig_c.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK_SOFT))
            st.plotly_chart(fig_c, use_container_width=True, config=NOBAR)
            source("Sıra-tabanlı normalizasyon (yüzdelik dilim, OECD & JRC 2008) · "
                   "eşit ağırlık · kesik çizgi = medyan sektör · P100 = en iyi")
        elif nace == TOTAL_MANUFACTURING:
            st.info("Bileşik skor tekil sektörler için hesaplanır — 24 sektör "
                    "karşılaştırmasında toplam imalat referans evrenin kendisidir.")
        else:
            st.info("Skor için yeterli veri yok.")

        # ── Erken Uyarı — sinyal yaklaşımı (KLR 1998) ──
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        chart_head("Erken Uyarı Sistemi",
                   "Sinyal yaklaşımı: son değerin kendi tarihsel dağılımındaki yüzdeliği")

        def _tarihsel_pr(series, invert=False, min_n=24):
            """Son gözlemin kendi geçmişi içindeki yüzdeliği (KLR 1998 sinyal eşiği)."""
            pts = [v for _, v in sorted((series or {}).items()) if v is not None]
            if len(pts) < min_n:
                return None, None
            cur, hist = pts[-1], pts[:-1]
            if invert:   # yüksek değer = kötü (ör. maliyet makası)
                pr = sum(1 for v in hist if v > cur) / len(hist) * 100
            else:
                pr = sum(1 for v in hist if v < cur) / len(hist) * 100
            return cur, round(pr)

        def _isik(pr):
            return "🔴" if pr <= 10 else "🟡" if pr <= 25 else "🟢"

        _kko_ser0 = dict(sorted((first_series(
            {k: (dict(v) if not isinstance(v, dict) else v)
             for k, v in kko_sec.items()}) or {}).items()))
        _maliyet_makas = diff_series(_ufe_ser, _uimal_ser)  # sektör − imalat ÜFE

        warnings = []
        # Üretim: yüzdelik + Bry–Boschan tarzı ardışıklık kuralı
        _pc, _ppr = _tarihsel_pr(_prod_ser)
        if _ppr is not None:
            _son3 = [v for v in list(_prod_ser.values())[-3:] if v is not None]
            if len(_son3) == 3 and all(v < 0 for v in _son3):
                warnings.append(("Üretim", "🔴",
                                 f"3 ay üst üste daralma (ardışıklık kuralı) · son %{_pc:.1f}"))
            else:
                warnings.append(("Üretim", _isik(_ppr),
                                 f"%{_pc:+.1f} · tarihsel P{_ppr}"))
        for _ad, _ser, _inv in [("Reel Ciro", _reel_ciro, False),
                                ("İhracat", _ih_ser, False),
                                ("İstihdam", first_serie_sorted(f7), False),
                                ("Kapasite", _kko_ser0, False),
                                ("Maliyet", _maliyet_makas, True)]:
            _c, _pr = _tarihsel_pr(_ser, invert=_inv)
            if _pr is None:
                continue
            _fmt = (f"{_c:.1f} puan makas" if _ad == "Maliyet"
                    else f"%{_c:.1f}" if _ad == "Kapasite" else f"%{_c:+.1f}")
            warnings.append((_ad, _isik(_pr), f"{_fmt} · tarihsel P{_pr}"))

        if warnings:
            html = '<div style="display:flex; flex-direction:column; gap:0.4rem;">'
            for w_name, w_icon, w_desc in warnings:
                bg = "#FEE2E2" if w_icon=="🔴" else "#FEF3C7" if w_icon=="🟡" else "#D1FAE5"
                text_col = "#991B1B" if w_icon=="🔴" else "#92400E" if w_icon=="🟡" else "#065F46"
                html += f'''<div style="background:{bg}; padding:0.5rem 0.75rem; border-radius:6px; font-size:0.85rem; display:flex; align-items:center;">
<span style="font-size:1.1rem; margin-right:0.6rem;">{w_icon}</span>
<strong style="margin-right:0.4rem; color:{text_col}; width:75px;">{w_name}</strong>
<span style="color:#475569;">{w_desc}</span>
</div>'''
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            st.markdown('<div class="src">🔴 tarihsel P10 altı · 🟡 P25 altı · 🟢 normal — '
                        'gösterge kendi geçmişine göre değerlendirilir (Kaminsky, Lizondo '
                        '&amp; Reinhart 1998); üretimde ek ardışıklık kuralı Bry &amp; '
                        'Boschan (1971) döngü tarihlemesine dayanır.</div>',
                        unsafe_allow_html=True)
        else:
            st.info("Uyarı sistemi için yeterli veri yok.")

        # ── Mevsimsellik ısı takvimi ──
        sec_title("Mevsimsellik Takvimi", "Üretim YoY % · yıl × ay deseni")
        if f1:
            merged_m = {}
            for _, s in f1.items():
                for p, v in s.items():
                    if v is not None: merged_m.setdefault(p, []).append(v)
            mavg = {p: sum(vs)/len(vs) for p, vs in merged_m.items()}
            yrs_h = sorted({p.split("-")[0] for p in mavg})[-6:]
            z_h, t_h = [], []
            for yr in yrs_h[::-1]:
                row = [mavg.get(f"{yr}-{m:02d}") for m in range(1, 13)]
                z_h.append(row)
                t_h.append([f"{v:.0f}" if v is not None else "" for v in row])
            zm = max((abs(v) for r in z_h for v in r if v is not None), default=1)
            fig_s = go.Figure(go.Heatmap(
                z=z_h, x=TR_MONTHS, y=yrs_h[::-1],
                text=t_h, texttemplate="%{text}",
                textfont=dict(size=9.5, family="Inter"),
                colorscale=[[0, "#DC2626"], [0.42, "#FEE2E2"], [0.5, "#FFFFFF"],
                            [0.58, "#DBEAFE"], [1, BRAND]],
                zmid=0, zmin=-zm, zmax=zm,
                xgap=3, ygap=3, showscale=False,
                hovertemplate="%{y} %{x}: <b>%{z:+.1f}%</b><extra></extra>",
            ))
            fig_s.update_layout(**LAYOUT, height=200, hovermode="closest",
                                margin=dict(l=8, r=8, t=4, b=28))
            fig_s.update_xaxes(showline=False, ticks="", tickfont=dict(size=9.5))
            fig_s.update_yaxes(showgrid=False, tickfont=dict(size=10))
            st.plotly_chart(fig_s, use_container_width=True, config=NOBAR)

# ── TAB 1: ÜRETİM ────────────────────────────────────────────────────────────────
with tabs[1]:
    sec_title(f"Üretim Endeksi", "Sanayi üretim endeksi, önceki yıla göre değişim (%) · alt gruplar")
    if f1:
        merged = {}
        for _, s in f1.items():
            for p, v in s.items():
                if v is not None: merged.setdefault(p, []).append(v)
        ann = annual_avg({p: sum(vs)/len(vs) for p, vs in merged.items()})
        years, vals = list(ann.keys()), list(ann.values())
        n = len(years)
        colors = ["#B7C3D7"]*n          # geçmiş yıllar: soluk
        if n >= 3: colors[-3] = "#8FA8CF"
        if n >= 2: colors[-2] = "#5C85D6"
        if n >= 1: colors[-1] = BRAND   # son yıl: marka

        c1, c2 = st.columns([2, 3], gap="large")
        with c1:
            chart_head("Yıllık Ortalama", "Alt grupların ortalaması")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=years, y=vals, marker_color=colors, marker_line_width=0,
                marker=dict(cornerradius=5),
                text=[f"{v:+.1f}" for v in vals],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=11.5, color=INK, family="Inter"),
                hovertemplate="%{x}: <b>%{y:.1f}%</b><extra></extra>",
                width=0.58,
            ))
            fig.update_layout(**LAYOUT, height=430, bargap=0.3, showlegend=False,
                              margin=dict(l=8, r=8, t=24, b=36))
            fig.update_yaxes(visible=False)
            fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        with c2:
            cmp_sub = f" · kıyas: {compare_nace}" if compare_nace else ""
            chart_head("Aylık Seyir", f"Son {ay_sayisi} ay · YoY %{cmp_sub}")
            fig2 = go.Figure()
            _ends = []
            for i, (lbl, s) in enumerate(f1.items()):
                xs, ys = series_xy(s, ay_sayisi)
                col = SERIES_PAL[i % len(SERIES_PAL)]
                disp = lbl if nace == TOTAL_MANUFACTURING else f"{lbl.lstrip('C')} · {short_name(lbl, 30)}"
                fig2.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines", name=disp,
                    line=dict(color=col, width=2, shape="spline", smoothing=.8),
                    hovertemplate="<b>%{y:.1f}%</b><extra>" + disp[:26] + "</extra>"))
    
            if xs: _ends.append((xs[-1], ys[-1], col, "{:+.1f}%"))

        if compare_nace:
            f7_cmp = build_sekil7(compare_nace, cache.get("ucretli", []))
            if f7_cmp:
                for lbl, s in f7_cmp.items():
                    if compare_nace in lbl:
                        cx, cy = series_xy(s, ay_sayisi)
                        if cx:
                            fig.add_trace(go.Scatter(
                                x=cx, y=cy, mode="lines", name=f"⚖ {compare_nace} İstihdam",
                                line=dict(color=ROSE, width=2.4, dash="dashdot", shape="spline", smoothing=.8),
                                hovertemplate="<b>%{y:+.2f}%</b><extra>Kıyas: " + compare_nace + "</extra>"))
                            _ends.append((cx[-1], cy[-1], ROSE, "{:+.1f}%"))


            if compare_nace:
                f1_cmp = build_sekil1(compare_nace, cache["alt_c"], ana_c_series=_ana_c)
                if f1_cmp:
                    merged_c = {}
                    for _, s in f1_cmp.items():
                        for p, v in s.items():
                            if v is not None: merged_c.setdefault(p, []).append(v)
                    cmp_avg = {p: sum(vs)/len(vs) for p, vs in merged_c.items()}
                    xs_c, ys_c = series_xy(cmp_avg, ay_sayisi)
                    fig2.add_trace(go.Scatter(
                        x=xs_c, y=ys_c, mode="lines",
                        name=f"⚖ {compare_nace} · {short_name(compare_nace, 26)}",
                        line=dict(color=INK_SOFT, width=2.2, dash="dash", shape="spline", smoothing=.8),
                        hovertemplate="<b>%{y:.1f}%</b><extra>Kıyas: " + short_name(compare_nace, 22) + "</extra>"))
                    if xs_c: _ends.append((xs_c[-1], ys_c[-1], INK_SOFT, "{:+.1f}%"))
            add_end_labels(fig2, _ends)

            fig2.update_layout(**LAYOUT, height=450,
                               margin=dict(l=8, r=64, t=8, b=64),
                               legend=dict(orientation="h", y=-0.28, x=0, font=dict(size=10)))
            fig2.update_xaxes(dtick=6)
            fig2.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig2, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Sanayi Üretim Endeksi [2021=100], mevsim ve takvim etkisinden arındırılmış" +
              (" · kesikli çizgi: karşılaştırma sektörü" if compare_nace else ""))
    else:
        st.info("Bu sektör için üretim endeksi alt grup verisi bulunamadı.")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    with st.expander("🔍 Alt Kırılım Detayları (Sınıf Düzeyi)", expanded=False):
        if nace == TOTAL_MANUFACTURING:
            sec_title("İmalat Sanayii Alt Sektörleri",
                      "Ana sektörler (2 haneli NACE, C10–C33) düzeyinde üretim performansı · yıl ortalaması, YoY %")
        else:
            sec_title("Alt Sektör Kırılımları",
                      "Sınıf (4 haneli NACE) düzeyinde üretim performansı · yıl ortalaması, YoY %")
        if f2:
            secs   = sorted(f2.keys())
            ann_by = {s: annual_avg(f2[s]) for s in secs}
            yrs    = sorted({y for a in ann_by.values() for y in a})[-5:]
            latest = yrs[-1]

            # Son yıla göre sırala (büyükten küçüğe)
            order  = sorted(secs, key=lambda s: ann_by[s].get(latest) if ann_by[s].get(latest) is not None else -999,
                            reverse=False)  # yatay bar: en büyük üstte olsun diye ascending

            c1, c2 = st.columns([5, 4], gap="large")

            with c1:
                chart_head(f"{latest} Performansı", "Son yıl ortalaması · sıralı")
                vals_l  = [ann_by[s].get(latest, 0) or 0 for s in order]
                bar_col = [POS if v >= 0 else NEG for v in vals_l]
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=[wrap_name(s, 30) for s in order],
                    x=vals_l, orientation="h",
                    marker_color=bar_col, marker_line_width=0,
                    marker=dict(cornerradius=4),
                    text=[f"{v:+.1f}%" for v in vals_l],
                    textposition="outside", cliponaxis=False,
                    textfont=dict(size=11, family="Inter"),
                    hovertext=[f"{s} · {nace_name(s)}" for s in order],
                    hovertemplate="%{hovertext}<br><b>%{x:+.1f}%</b><extra></extra>",
                    width=0.6,
                ))
                h2 = max(300, 66 * len(order))
                fig.update_layout(**LAYOUT, height=h2, showlegend=False, hovermode="closest",
                                  margin=dict(l=8, r=54, t=8, b=36), bargap=0.32)
                fig.update_xaxes(ticksuffix="%", zeroline=True, zerolinecolor="#CBD5E1")
                fig.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK_SOFT))
                fig.add_vline(x=0, line_width=1, line_color="#CBD5E1")
                st.plotly_chart(fig, use_container_width=True, config=NOBAR)

            with c2:
                chart_head("Yıllara Göre Isı Haritası", "Kırmızı: daralma · Mavi: büyüme")
                z, txt = [], []
                for s in order:
                    row  = [ann_by[s].get(y) for y in yrs]
                    z.append(row)
                    txt.append([f"{v:+.1f}" if v is not None else "" for v in row])
                zmax = max((abs(v) for r in z for v in r if v is not None), default=1)
                fig_h = go.Figure(go.Heatmap(
                    z=z, x=yrs, y=[wrap_name(s, 30) for s in order],
                    text=txt, texttemplate="%{text}",
                    textfont=dict(size=10.5, family="Inter"),
                    colorscale=[[0, "#DC2626"], [0.42, "#FEE2E2"], [0.5, "#FFFFFF"],
                                [0.58, "#DBEAFE"], [1, BRAND]],
                    zmid=0, zmin=-zmax, zmax=zmax,
                    xgap=4, ygap=4, showscale=False,
                    hovertemplate="%{y}<br>%{x}: <b>%{z:+.1f}%</b><extra></extra>",
                ))
                fig_h.update_layout(**LAYOUT, height=h2, hovermode="closest",
                                    margin=dict(l=8, r=8, t=8, b=36))
                fig_h.update_xaxes(side="bottom", showline=False, ticks="")
                fig_h.update_yaxes(showticklabels=False, showgrid=False)
                st.plotly_chart(fig_h, use_container_width=True, config=NOBAR)

            if nace == TOTAL_MANUFACTURING:
                source("Kaynak: TÜİK — Sanayi Üretim Endeksi, Ana Endeksler (2 haneli NACE, C10–C33)")
            else:
                source("Kaynak: TÜİK — Sanayi Üretim Endeksi, sınıf düzeyi · endeksten hesaplanan yıllık değişim")

            with st.expander("📋 Detay tablosu — tüm yıllar"):
                rows = []
                for s in order[::-1]:
                    r = {"Kod": s, "Alt Sektör": nace_name(s)}
                    for yr in yrs:
                        v = ann_by[s].get(yr)
                        r[str(yr)] = f"{v:+.1f}%" if v is not None else "—"
                    rows.append(r)
                st.dataframe(pd.DataFrame(rows).set_index("Kod"), use_container_width=True)
        else:
            st.info("Bu sektör için sınıf düzeyi kırılım verisi bulunamadı.")



# ── TAB 2: DIŞ TİCARET ───────────────────────────────────────────────────────────
with tabs[2]:
    sec_title("Dış Ticaret",
              f"Miktar endeksi, önceki yıla göre değişim (%) · SITC bölüm {SITC_MAP.get(nace, 'T')}")
    if f3:
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            cmp_sub = f" · kıyas: {compare_nace}" if compare_nace else ""
            chart_head("Aylık Seyir", f"Son {ay_sayisi} ay{cmp_sub}")
            fig = go.Figure()
            _ends = []
            
            # Seçili Sektör
            for lbl, s in f3.items():
                is_exp = "hracat" in lbl and "thalat" not in lbl
                xs, ys = series_xy(s, ay_sayisi)
                col = TRADE_EXP if is_exp else TRADE_IMP
                fig.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines", name="İhracat" if is_exp else "İthalat",
                    line=dict(color=col, width=2.4 if is_exp else 1.8,
                              shape="spline", smoothing=.8),
                    fill="tozeroy",
                    fillcolor="rgba(29,78,216,.06)" if is_exp else "rgba(148,163,184,.08)",
                    hovertemplate="<b>%{y:+.1f}%</b><extra>" + ("İhracat" if is_exp else "İthalat") + "</extra>"))
                if xs: _ends.append((xs[-1], ys[-1], col, "{:+.1f}%"))
                
            # Kıyaslama Sektörü Overlay
            if compare_nace:
                f3_cmp = build_sekil3(compare_nace, cache["dis_ticaret"])
                if f3_cmp:
                    for lbl, s in f3_cmp.items():
                        is_exp = "hracat" in lbl and "thalat" not in lbl
                        cx, cy = series_xy(s, ay_sayisi)
                        col = TRADE_EXP if is_exp else TRADE_IMP
                        if cx:
                            fig.add_trace(go.Scatter(
                                x=cx, y=cy, mode="lines", name=f"⚖ {compare_nace} ({'İhr.' if is_exp else 'İth.'})",
                                line=dict(color=col, width=1.5, dash="dot", shape="spline", smoothing=.8),
                                hovertemplate="<b>%{y:+.1f}%</b><extra>Kıyas: " + compare_nace + "</extra>"))
            
            add_end_labels(fig, _ends)
            fig.update_layout(**LAYOUT, height=450)
            fig.update_xaxes(dtick=6)
            fig.update_yaxes(ticksuffix="%")
            fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig, use_container_width=True, config=NOBAR)
            
        with c2:
            chart_head("Yıllık Ortalama", "YoY %")
            ann_t = {lbl: annual_avg(s) for lbl, s in f3.items()}
            yrs = sorted({y for a in ann_t.values() for y in a})[-6:]
            fig2 = go.Figure()
            for lbl, ann in ann_t.items():
                is_exp = "hracat" in lbl and "thalat" not in lbl
                vals = [ann.get(yr, 0) for yr in yrs]
                fig2.add_trace(go.Bar(
                    y=yrs, x=vals, orientation="h",
                    name="İhracat" if is_exp else "İthalat",
                    marker_color=TRADE_EXP if is_exp else TRADE_IMP,
                    marker_line_width=0, marker=dict(cornerradius=3),
                    text=[f"{v:+.1f}" for v in vals],
                    textposition="outside", cliponaxis=False,
                    textfont=dict(size=10, family="Inter"),
                    hovertemplate="%{y}: <b>%{x:+.1f}%</b><extra></extra>"))
            fig2.update_layout(**LAYOUT, barmode="group", height=450, bargap=0.25,
                               margin=dict(l=8, r=44, t=8, b=36))
            fig2.update_xaxes(ticksuffix="%")
            fig2.update_yaxes(showgrid=False, autorange="reversed")
            fig2.add_vline(x=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig2, use_container_width=True, config=NOBAR)

        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        
        # ── Dış Ticaret Makası Alt Grafik ──
        if _net_trade:
            chart_head("Dış Ticaret Makası", "İhracat büyümesi − İthalat büyümesi (Puan) · net ticaret yönelimi")
            m_xs, m_ys = series_xy(_net_trade, ay_sayisi)
            fig_m = go.Figure()
            fig_m.add_trace(go.Scatter(
                x=m_xs, y=m_ys, mode="lines", name="Ticaret Makası",
                line=dict(color=BRAND, width=2, shape="spline", smoothing=.8),
                fill="tozeroy",
                fillcolor="rgba(16,185,129,.15)", # default green
                hovertemplate="<b>%{y:+.1f} pn</b><extra>Makas</extra>"
            ))
            # Dinamik dolgu rengi (pozitif yeşil, negatif kırmızı)
            # Plotly scatter ile sıfır altına farklı renk zor olduğu için bar chart alternatifi kullanalım:
            fig_m.data = [] # clear line
            fig_m.add_trace(go.Bar(
                x=m_xs, y=m_ys, name="Ticaret Makası",
                marker_color=["rgba(16,185,129,.7)" if v >= 0 else "rgba(239,68,68,.7)" for v in m_ys],
                marker_line_width=0,
                hovertemplate="<b>%{y:+.1f} pn</b><extra>Makas</extra>"
            ))
            fig_m.update_layout(**LAYOUT, height=320, margin=dict(l=8, r=32, t=8, b=32))
            fig_m.update_xaxes(dtick=6)
            fig_m.update_yaxes(ticksuffix=" pn")
            fig_m.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig_m, use_container_width=True, config=NOBAR)


        # ── Dış Ticaret Fiyat (Birim Değer) Makası ──
        if f_fiyat:
            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            sec_title("Birim Değer (Fiyat) Endeksi", "İhracat Fiyatı vs İthalat Fiyatı Yıllık Değişim (%) · Rekabetçilik ve Katma Değer")
            
            p_xs, _ = series_xy(list(f_fiyat.values())[0], ay_sayisi) if f_fiyat else ([], [])
            if p_xs:
                fig_p = go.Figure()
                _p_ends = []
                for lbl, s in f_fiyat.items():
                    is_exp = "hracat" in lbl and "thalat" not in lbl
                    cx, cy = series_xy(s, ay_sayisi)
                    col = TRADE_EXP if is_exp else TRADE_IMP
                    fig_p.add_trace(go.Scatter(
                        x=cx, y=cy, mode="lines", name="İhracat Fiyatı" if is_exp else "İthalat Fiyatı",
                        line=dict(color=col, width=2.4 if is_exp else 1.8, shape="spline", smoothing=.8),
                        hovertemplate="<b>%{y:+.1f}%</b><extra>" + ("İhr. Fiyatı" if is_exp else "İth. Fiyatı") + "</extra>"
                    ))
                    if cx: _p_ends.append((cx[-1], cy[-1], col, "{:+.1f}%"))
                
                # Fiyat Makası Overlay (İhracat Fiyatı - İthalat Fiyatı)
                if "İhracat Fiyat YoY %" in f_fiyat and "İthalat Fiyat YoY %" in f_fiyat:
                    s_exp = dict(f_fiyat["İhracat Fiyat YoY %"])
                    s_imp = dict(f_fiyat["İthalat Fiyat YoY %"])
                    m_xs, m_ys = calc_diff(s_exp, s_imp, ay_sayisi)
                    if m_xs:
                        fig_p.add_trace(go.Bar(
                            x=m_xs, y=m_ys, name="Fiyat Makası",
                            marker_color=["rgba(16,185,129,.5)" if v >= 0 else "rgba(239,68,68,.5)" for v in m_ys],
                            marker_line_width=0,
                            hovertemplate="<b>%{y:+.1f} pn</b><extra>Fiyat Makası</extra>"
                        ))

                add_end_labels(fig_p, _p_ends)
                fig_p.update_layout(**LAYOUT, height=420)
                fig_p.update_xaxes(dtick=6)
                fig_p.update_yaxes(ticksuffix="%")
                fig_p.add_hline(y=0, line_width=1, line_color="#CBD5E1")
                st.plotly_chart(fig_p, use_container_width=True, config=NOBAR)
                source("Kaynak: TÜİK — Dış Ticaret Birim Değer Endeksi")

        source("Kaynak: TÜİK — Dış Ticaret Miktar Endeksi" + 
              (" · kesikli çizgi: karşılaştırma sektörü" if compare_nace else ""))
    else:
        st.info("Bu sektör için dış ticaret verisi bulunamadı.")

# ── TAB 3: KAPASİTE ──────────────────────────────────────────────────────────────
with tabs[3]:
    sec_title("Kapasite Kullanım Oranı", "TCMB imalat sanayi KKO · sektör vs. imalat geneli (%)")
    if f4:
        all_v = [v for s in f4.values()
                 for v in (dict(s) if not isinstance(s, dict) else s).values() if v is not None]
        lo = min(all_v) - 3 if all_v else 50
        hi = max(all_v) + 3 if all_v else 90

        fig = go.Figure()
        _ends = []
        for lbl, s in f4.items():
            is_tot = "anayii" in lbl and nace != TOTAL_MANUFACTURING
            d = dict(s) if not isinstance(s, dict) else s
            xs, ys = series_xy(d, ay_sayisi)
            col = MUTED if is_tot else BRAND
            disp_name = ("İmalat Geneli" if is_tot
                        else "İmalat Sanayii Geneli" if nace == TOTAL_MANUFACTURING
                        else f"{nace} · {short_name(nace, 30)}")
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", name=disp_name,
                line=dict(color=col, width=1.8 if is_tot else 2.6,
                          dash="dot" if is_tot else "solid", shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:.1f}%</b><extra>" + disp_name[:22] + "</extra>"))


            if xs: _ends.append((xs[-1], ys[-1], col, "{:.1f}%"))

        if compare_nace:
            f5_cmp = build_sekil5(compare_nace, cache["ufe"])
            if f5_cmp:
                for lbl, s in f5_cmp.items():
                    if compare_nace in lbl:
                        cx, cy = series_xy(s, ay_sayisi)
                        if cx:
                            fig.add_trace(go.Scatter(
                                x=cx, y=cy, mode="lines", name=f"⚖ {compare_nace} ÜFE",
                                line=dict(color=AMBER, width=2.4, dash="dashdot", shape="spline", smoothing=.8),
                                hovertemplate="<b>%{y:.1f}%</b><extra>Kıyas: " + compare_nace + "</extra>"))
                            _ends.append((cx[-1], cy[-1], AMBER, "{:.1f}%"))

            
        if compare_nace:
            f4_cmp = build_sekil4(compare_nace, cache["kko"])
            if f4_cmp:
                for lbl, s in f4_cmp.items():
                    if "anayii" not in lbl:
                        cx, cy = series_xy(s, ay_sayisi)
                        if cx:
                            fig.add_trace(go.Scatter(
                                x=cx, y=cy, mode="lines", name=f"⚖ {compare_nace} KKO",
                                line=dict(color=TEAL, width=2.4, dash="dashdot", shape="spline", smoothing=.8),
                                hovertemplate="<b>%{y:.1f}%</b><extra>Kıyas: " + compare_nace + "</extra>"))
                            _ends.append((cx[-1], cy[-1], TEAL, "{:.1f}%"))

        add_end_labels(fig, _ends, gap_frac=0.06)
        fig.update_layout(**LAYOUT, height=480)
        fig.update_xaxes(dtick=6)
        fig.update_yaxes(ticksuffix="%", range=[lo, hi], zeroline=False)
        st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        source("Kaynak: TCMB EVDS — İmalat Sanayi Kapasite Kullanım Oranı (NACE Rev.2)")
    else:
        st.info("KKO verisi bulunamadı.")

# ── TAB 5: ENFLASYON / ÜFE ───────────────────────────────────────────────────────
with tabs[4]:
    sec_title("Üretici Fiyat Endeksi (ÜFE)", "Yıllık değişim (%) · sektör maliyet baskısı")
    if f5:
        def ufe_label(lbl):
            m = re.search(r'UFE\s+(\S+)\s+Yillik', lbl)
            code = m.group(1) if m else ""
            if code == "C": return "İmalat Geneli"
            return f"{code.lstrip('C')} · {short_name(code, 30)}" if code else lbl[:30]

        fig = go.Figure()
        _ends = []
        for i, (lbl, s) in enumerate(f5.items()):
            is_tot = (" c " in (" " + lbl.lower() + " ") and "yillik" in lbl.lower()
                     and nace != TOTAL_MANUFACTURING)
            xs, ys = series_xy(s, ay_sayisi)
            col = MUTED if is_tot else SERIES_PAL[i % len(SERIES_PAL)]
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", name=ufe_label(lbl),
                line=dict(color=col, width=1.8 if is_tot else 2.2,
                          dash="dot" if is_tot else "solid", shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:.1f}%</b><extra>" + ufe_label(lbl)[:24] + "</extra>"))
            if xs: _ends.append((xs[-1], ys[-1], col, "{:.0f}%"))
        add_end_labels(fig, _ends, gap_frac=0.075)
        fig.update_layout(**LAYOUT, height=430,
                          margin=dict(l=8, r=64, t=8, b=68),
                          legend=dict(orientation="h", y=-0.26, x=0, font=dict(size=10)))
        fig.update_xaxes(dtick=6)
        fig.update_yaxes(ticksuffix="%")
        fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
        st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Yurt İçi Üretici Fiyat Endeksi (Yİ-ÜFE)")
    else:
        st.info("ÜFE verisi bulunamadı.")

# ── TAB 5: CİRO ──────────────────────────────────────────────────────────────────
with tabs[5]:
    sec_title("Ciro Endeksi", "Önceki yıla göre değişim (%) · nominal, mevsim etkisinden arındırılmış")
    if f6:
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            chart_head("Aylık Seyir", f"Son {ay_sayisi} ay")
            fig = go.Figure()
            _ends = []
            for i, (lbl, s) in enumerate(f6.items()):
                is_tot = "Toplam" in lbl and nace != TOTAL_MANUFACTURING
                xs, ys = series_xy(s, ay_sayisi)
                col = MUTED if is_tot else BRAND
                disp_name = ("İmalat Geneli" if is_tot
                            else "İmalat Sanayii Geneli" if nace == TOTAL_MANUFACTURING
                            else f"{nace} · {short_name(nace, 26)}")
                fig.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines", name=disp_name,
                    line=dict(color=col, width=1.8 if is_tot else 2.6,
                              dash="dot" if is_tot else "solid", shape="spline", smoothing=.8),
                    hovertemplate="<b>%{y:+.1f}%</b><extra>" + disp_name[:22] + "</extra>"))
                if xs: _ends.append((xs[-1], ys[-1], col, "{:+.1f}%"))
            add_end_labels(fig, _ends)
            fig.update_layout(**LAYOUT, height=450)
            fig.update_xaxes(dtick=6)
            fig.update_yaxes(ticksuffix="%")
            fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        with c2:
            chart_head("Yıllık Ortalama", "YoY %")
            ann6 = {lbl: annual_avg(s) for lbl, s in f6.items()}
            yrs = sorted({y for a in ann6.values() for y in a})[-6:]
            fig2 = go.Figure()
            for i, (lbl, ann) in enumerate(ann6.items()):
                is_tot = "Toplam" in lbl and nace != TOTAL_MANUFACTURING
                vals = [ann.get(yr, 0) for yr in yrs]
                fig2.add_trace(go.Bar(
                    x=yrs, y=vals,
                    name="İmalat Geneli" if is_tot else ("İmalat Sanayii Geneli" if nace == TOTAL_MANUFACTURING else nace),
                    marker_color=TRADE_IMP if is_tot else BRAND,
                    marker_line_width=0, marker=dict(cornerradius=3),
                    text=[f"{v:+.0f}" for v in vals],
                    textposition="outside", cliponaxis=False,
                    textfont=dict(size=10, family="Inter"),
                    hovertemplate="%{x}: <b>%{y:+.1f}%</b><extra></extra>"))
            fig2.update_layout(**LAYOUT, barmode="group", height=450, bargap=0.3,
                               margin=dict(l=8, r=8, t=24, b=36))
            fig2.update_yaxes(visible=False)
            fig2.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig2, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Ciro Endeksleri [2021=100], mevsim ve takvim etkisinden arındırılmış")
    else:
        st.info("Ciro verisi için 'python cache_all.py' çalıştırın.")

# ── TAB 6: İSTİHDAM ──────────────────────────────────────────────────────────────
with tabs[6]:
    sec_title("Ücretli Çalışan Sayısı", "İstihdam, önceki yıla göre değişim (%)")
    if f7:
        fig = go.Figure()
        _ends = []
        for i, (lbl, s) in enumerate(f7.items()):
            is_tot = "Toplam" in lbl and nace != TOTAL_MANUFACTURING
            xs, ys = series_xy(s, ay_sayisi)
            col = MUTED if is_tot else TEAL
            disp_name = ("İmalat Geneli" if is_tot
                        else "İmalat Sanayii Geneli" if nace == TOTAL_MANUFACTURING
                        else f"{nace} · {short_name(nace, 30)}")
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="lines", name=disp_name,
                line=dict(color=col, width=1.8 if is_tot else 2.6,
                          dash="dot" if is_tot else "solid", shape="spline", smoothing=.8),
                fill="tozeroy" if not is_tot else "none",
                fillcolor="rgba(13,148,136,.07)" if not is_tot else None,
                hovertemplate="<b>%{y:+.2f}%</b><extra>" + disp_name[:22] + "</extra>"))
            if xs: _ends.append((xs[-1], ys[-1], col, "{:+.1f}%"))
        add_end_labels(fig, _ends)
        fig.update_layout(**LAYOUT, height=480)
        fig.update_xaxes(dtick=6)
        fig.update_yaxes(ticksuffix="%")
        fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
        st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Ücretli Çalışan İstatistikleri, takvim etkisinden arındırılmış")

        with st.expander("📋 Son 24 ay"):
            periods = sorted({p for s in f7.values() for p in s})[-24:]
            rows = []
            for p in periods:
                r = {"Dönem": tr_month(p)}
                for lbl, s in f7.items():
                    v = s.get(p)
                    key = "İmalat Geneli" if "Toplam" in lbl else nace
                    r[key] = f"{v:+.2f}%" if v is not None else "—"
                rows.append(r)
            st.dataframe(pd.DataFrame(rows).set_index("Dönem"), use_container_width=True)
    else:
        st.info("İstihdam verisi için 'python cache_all.py' çalıştırın.")

# ── TAB 7: İSO 500 ───────────────────────────────────────────────────────────────
with tabs[7]:
    if f8:
        # Fragment: yıl seçimi yalnızca bu bölümü yeniden çalıştırır — tüm
        # script'in yeniden koşup aktif sekmenin ilk sekmeye dönmesini önler.
        @st.fragment
        def _iso_tab():
            # ── Yıl seçimi ──
            _years = f8.get("available_years") or [f8["yil"]]

            ty1, ty2 = st.columns([3, 1])
            with ty2:
                sel_year = st.selectbox("İSO yılı", _years,
                                        format_func=lambda y: f"{y} listesi",
                                        key=f"iso_yil_{nace}",
                                        label_visibility="collapsed")
            # Seçilen yıl en güncelden farklıysa o yılın kesitini yeniden hesapla
            if sel_year != f8["yil"]:
                try:
                    from iso_data import sector_iso as _sec_iso
                    f8i = _sec_iso(nace, year=sel_year) or f8
                except Exception:
                    f8i = f8
            else:
                f8i = f8
            yil8 = f8i["yil"]
            with ty1:
                sec_title(f"İSO 500 & İkinci 500'de {sector_tr}",
                          f"Türkiye'nin en büyük sanayi kuruluşları içindeki sektör fotoğrafı · {yil8}")

            # Seçili para birimi (₺/$) — yıllık ortalama kurla dönüştürme
            _kur8 = _kur_yil.get(yil8) if usd_mode else None
            def _cur8(v):
                """TL tutarı seçili para birimine çevirir (USD modunda yıl kuru)."""
                if v is None: return None
                return v / _kur8 if _kur8 else (None if usd_mode else v)

            # ── KPI satırı ──
            ic = st.columns(5)
            kpi_card(ic[0], "Listedeki Firma", f"{f8i['firma_sayisi']}",
                     f"İSO 500: {f8i['firma_500']} · İkinci 500: {f8i['firma_2_500']}",
                     icon="🏢")
            _sat8 = _cur8(f8i['toplam_uretim_satis'])
            kpi_card(ic[1], "Üretimden Satışlar",
                     (f"{PARA_SIM}{_sat8/1e9:,.0f} mlr".replace(",", ".") if _sat8 is not None else "—"),
                     f"{yil8} toplamı" + (f" · pay %{f8i['pay_uretim']:.1f}"
                                          if f8i.get('pay_uretim') and nace != TOTAL_MANUFACTURING else ""),
                     icon="💼")
            kpi_card(ic[2], "İhracat", f"${f8i['toplam_ihracat_musd']:,.0f} mn".replace(",", "."),
                     f"{yil8} · beyan eden firmalar", icon="🌍")
            kpi_card(ic[3], "İstihdam", f"{f8i['toplam_calisan']:,.0f}".replace(",", "."),
                     "ücretli çalışan ort.", icon="👥")
            marj = f8i.get("favok_marj_med")
            kpi_card(ic[4], "FAVÖK Marjı (medyan)",
                     f"%{marj:.1f}" if marj is not None else "—",
                     "beyan eden firmalar", icon="📐",
                     tone="pos" if (marj or 0) >= 10 else None)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            il_l, il_r = st.columns([5, 4], gap="large")

            # ── Top 15 firma ──
            with il_l:
                _kdiv = _kur8 if (usd_mode and _kur8) else 1.0
                chart_head(f"En Büyük 15 Kuruluş",
                           f"Üretimden satışlar, milyar {PARA_SIM} · {yil8}")
                fdf = f8i["firmalar"].head(15).iloc[::-1]
                bar_c = [BRAND if l == "İSO 500" else "#93C5FD" for l in fdf["liste"]]
                fig_i = go.Figure()
                fig_i.add_trace(go.Bar(
                    y=[n[:36] + ("…" if len(n) > 36 else "") for n in fdf["firma"]],
                    x=fdf["uretim_satis"] / _kdiv / 1e9,
                    orientation="h", marker_color=bar_c, marker_line_width=0,
                    marker=dict(cornerradius=3),
                    text=[f"{v/_kdiv/1e9:,.1f}".replace(",", ".") for v in fdf["uretim_satis"]],
                    textposition="outside", cliponaxis=False,
                    textfont=dict(size=10, family="Inter"),
                    customdata=[[il, f"{e:,.0f}" if pd.notna(e) else "—",
                                 f"{int(c):,}".replace(",", ".") if pd.notna(c) else "—"]
                                for il, e, c in zip(fdf["il"], fdf["ihracat_musd"], fdf["calisan"])],
                    hovertemplate="<b>%{y}</b><br>Satış: " + PARA_SIM + "%{x:.1f} mlr<br>"
                                  "İhracat: $%{customdata[1]} mn · Çalışan: %{customdata[2]}"
                                  "<br>%{customdata[0]}<extra></extra>",
                    width=0.62,
                ))
                fig_i.update_layout(**LAYOUT, height=max(360, 30 * len(fdf) + 60),
                                    showlegend=False, hovermode="closest",
                                    margin=dict(l=8, r=52, t=8, b=36))
                fig_i.update_xaxes(title=None, showticklabels=False, showline=False)
                fig_i.update_yaxes(showgrid=False, tickfont=dict(size=10, color=INK_SOFT))
                st.plotly_chart(fig_i, use_container_width=True, config=NOBAR)
                st.markdown(
                    f'<div class="src">Koyu mavi: İSO 500 · Açık mavi: İSO İkinci 500</div>',
                    unsafe_allow_html=True)

            with il_r:
                # ── Yıllara göre sektör (İSO 500) ──
                y500 = [r for r in f8i["yearly"] if r["liste"] == "İSO 500"]
                if len(y500) >= 2:
                    chart_head("İSO 500'de Sektör Trendi",
                               f"Üretimden satışlar ({'USD, yıl ort. kur' if usd_mode else 'nominal ₺'}) ve firma sayısı")
                    def _tcur(r):
                        k = _kur_yil.get(r["yil"]) if usd_mode else 1.0
                        return (r["uretim_satis"] / k / 1e9) if k else None
                    _tv = [_tcur(r) for r in y500]
                    fig_t = go.Figure()
                    fig_t.add_trace(go.Bar(
                        x=[str(r["yil"]) for r in y500],
                        y=_tv,
                        marker_color=[TRADE_IMP, BRAND][-len(y500):],
                        marker_line_width=0, marker=dict(cornerradius=4),
                        text=[(f"{PARA_SIM}{v:,.0f} mlr<br>{r['firma']} firma".replace(",", ".")
                               if v is not None else "—")
                              for r, v in zip(y500, _tv)],
                        textposition="inside",
                        textfont=dict(size=11, color="white", family="Inter"),
                        hovertemplate="%{x}: <b>" + PARA_SIM + "%{y:.0f} mlr</b><extra></extra>",
                        width=0.5,
                    ))
                    fig_t.update_layout(**LAYOUT, height=240, showlegend=False,
                                        margin=dict(l=8, r=8, t=8, b=32))
                    fig_t.update_yaxes(visible=False)
                    st.plotly_chart(fig_t, use_container_width=True, config=NOBAR)
                    if f8i.get("yoy") and f8i["yoy"].get("uretim_satis") is not None:
                        y = f8i["yoy"]
                        ihr_txt = (f" · İhracat %{y['ihracat']:+.1f}"
                                   if y.get("ihracat") is not None else "")
                        st.markdown(
                            f'<div class="src">{y["donem"]}: satışlar nominal '
                            f'%{y["uretim_satis"]:+.1f}{ihr_txt} · '
                            f'firma sayısı {y["firma"]:+d}</div>', unsafe_allow_html=True)

                # ── İl dağılımı ──
                if f8i.get("iller"):
                    chart_head("Coğrafi Yoğunlaşma", "Firma sayısına göre ilk iller")
                    ils = f8i["iller"][::-1]
                    fig_il = go.Figure()
                    fig_il.add_trace(go.Bar(
                        y=[i["il"] for i in ils], x=[i["firma"] for i in ils],
                        orientation="h", marker_color=TEAL, marker_line_width=0,
                        marker=dict(cornerradius=3),
                        text=[f"{i['firma']}" for i in ils],
                        textposition="outside", cliponaxis=False,
                        textfont=dict(size=10, family="Inter"),
                        hovertemplate="%{y}: <b>%{x} firma</b><extra></extra>",
                        width=0.55,
                    ))
                    fig_il.update_layout(**LAYOUT, height=max(200, 26 * len(ils) + 50),
                                         showlegend=False, hovermode="closest",
                                         margin=dict(l=8, r=28, t=4, b=24))
                    fig_il.update_xaxes(showticklabels=False, showline=False)
                    fig_il.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK_SOFT))
                    st.plotly_chart(fig_il, use_container_width=True, config=NOBAR)

            # ── Firma Heterojenliği — dağılım analizi ──────────────────────────
            # "Sektör iyi ama kim iyi?" — firma içi dağılım (Syverson 2011)
            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            chart_head("Firma Heterojenliği",
                       f"Sektör içi dağılımlar · {yil8} · kutu = çeyrekler arası aralık, çizgi = medyan")
            _fh = f8i["firmalar"]
            hh1, hh2, hh3 = st.columns(3, gap="medium")

            def _box(col, seri_by_liste, baslik, alt, suffix="%"):
                with col:
                    st.markdown(f'<div class="chart-h" style="font-size:.78rem">{baslik}</div>'
                                f'<div class="chart-hs">{alt}</div>', unsafe_allow_html=True)
                    figb = go.Figure()
                    for _lst, _vals, _renk in seri_by_liste:
                        if len(_vals) >= 5:
                            figb.add_trace(go.Box(
                                y=_vals, name=_lst, marker_color=_renk,
                                boxpoints="outliers", marker=dict(size=3, opacity=.5),
                                line=dict(width=1.6), width=0.5,
                                hovertemplate="%{y:.1f}" + suffix + "<extra>" + _lst + "</extra>"))
                    if figb.data:
                        figb.update_layout(**LAYOUT, height=280, showlegend=False,
                                           margin=dict(l=8, r=8, t=6, b=26))
                        figb.update_yaxes(ticksuffix=suffix)
                        st.plotly_chart(figb, use_container_width=True, config=NOBAR)
                    else:
                        st.caption("Yeterli firma verisi yok (min. 5 beyan).")

            def _liste_vals(seri):
                out = []
                for _lst, _renk in [("İSO 500", BRAND), ("İSO İkinci 500", "#93C5FD")]:
                    v = seri[_fh["liste"] == _lst].dropna()
                    v = v[(v > v.quantile(0.02)) & (v < v.quantile(0.98))] if len(v) >= 20 else v
                    out.append((_lst, v.tolist(), _renk))
                return out

            _box(hh1, _liste_vals(_fh["favok_marj"]),
                 "FAVÖK Marjı", "FAVÖK / net satış · kârlılık dağılımı")
            _kur8y = _kur_yil.get(yil8)
            if _kur8y and "net_satis" in _fh.columns:
                _ihy = (_fh["ihracat_musd"] * 1e6 * _kur8y / _fh["net_satis"] * 100)
                _ihy = _ihy.where((_fh["net_satis"] > 0))
                _box(hh2, _liste_vals(_ihy),
                     "İhracat Yoğunluğu", "ihracat (₺ karşılığı) / net satış")
            else:
                with hh2:
                    st.caption("İhracat yoğunluğu için USD/TRY kuru gerekli "
                               "(cache_all.py ile eklenir).")
            if "aktif" in _fh.columns:
                _adh = (_fh["net_satis"] / _fh["aktif"]).where(_fh["aktif"] > 0)
                _box(hh3, _liste_vals(_adh),
                     "Aktif Devir Hızı", "net satış / aktif toplamı · sermaye verimliliği",
                     suffix="x")
            st.markdown('<div class="src">Firma-içi dağılım: aynı sektörde kârlılık ve '
                        'verimlilik farkları kalıcı ve büyüktür (Syverson 2011) — medyan '
                        'sektörü, kutu genişliği rekabet heterojenliğini anlatır. Uç %2 '
                        'kırpılmıştır.</div>', unsafe_allow_html=True)

            # ── Tam firma tablosu ──
            with st.expander(f"📋 Tüm sektör firmaları ({f8i['firma_sayisi']})"):
                tdf = f8i["firmalar"].copy()
                _sat_col = f"Satış (mlr {PARA_SIM})"
                _tdiv = _kur8 if (usd_mode and _kur8) else 1.0
                tdf[_sat_col] = (tdf["uretim_satis"] / _tdiv / 1e9).round(2)
                tdf["İhracat (mn $)"] = tdf["ihracat_musd"].round(1)
                tdf["FAVÖK %"] = tdf["favok_marj"].round(1)

                # Safe parsing for PyArrow to avoid crashes
                tdf["sira"] = tdf["sira"].fillna(-1).astype(int).astype(str).replace("-1", "-")
                tdf["il"] = tdf["il"].fillna("-").astype(str)

                tdf = tdf.rename(columns={"sira": "Sıra", "liste": "Liste",
                                          "firma": "Kuruluş", "il": "İl",
                                          "calisan": "Çalışan"})
                st.dataframe(
                    tdf[["Sıra", "Liste", "Kuruluş", "İl", _sat_col,
                         "İhracat (mn $)", "Çalışan", "FAVÖK %"]],
                    hide_index=True,
                    use_container_width=True, height=420)

            _nace_etiketi = "tüm imalat sanayii (C10–C33)" if nace == TOTAL_MANUFACTURING else f"NACE {nace.lstrip('C')}"
            source(f"Kaynak: İstanbul Sanayi Odası — Türkiye'nin 500 Büyük Sanayi Kuruluşu "
                   f"ve İkinci 500 · {_nace_etiketi} eşleşmesi")

        _iso_tab()
    else:
        st.info("Bu sektörde İSO 500 / İkinci 500 listesine giren kuruluş bulunmuyor "
                "veya İSO kaynak dosyaları okunamadı.")

# ── TAB 8: HABER & RİSK ──────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_news(nace_code, query_override="", time_range=""):
    from news_analysis import fetch_sector_news
    try:
        return fetch_sector_news(nace_code, query_override=query_override or None,
                                 time_range=time_range)
    except Exception:
        return []

with tabs[8]:
    from news_analysis import TIME_RANGES
    th1, th2 = st.columns([3, 1])
    with th1:
        sec_title(f"Haber Akışı & Risk Analizi",
                  f"{sector_tr} · Google News taraması + yapay zekâ sentezi")
    with th2:
        tr_label = st.selectbox("Zaman aralığı", list(TIME_RANGES.keys()), index=2,
                                label_visibility="collapsed")
        if not tr_label:
            tr_label = list(TIME_RANGES.keys())[2]
            
    if news_query.strip():
        st.caption(f"🔍 Özel arama terimi kullanılıyor: **{news_query.strip()}**")

    news_items = get_news(nace, news_query, TIME_RANGES.get(tr_label, ""))

    nl, nr = st.columns([2, 3], gap="large")

    with nl:
        chart_head("Güncel Haber Akışı", f"{len(news_items)} başlık · {tr_label.lower()}")
        if news_items:
            import html as html_lib
            news_html = ""
            for it in news_items:
                safe_title = html_lib.escape(it['title'])
                safe_source = html_lib.escape(it['source'])
                safe_date = html_lib.escape(it['date'])
                news_html += f"""
                <div style="padding:.55rem 0;border-bottom:1px solid {LINE};">
                  <a href="{it['link']}" target="_blank" style="font-size:.83rem;font-weight:600;
                     color:{INK};text-decoration:none;line-height:1.4;">{safe_title}</a>
                  <div style="font-size:.7rem;color:{MUTED};font-weight:500;margin-top:.15rem;">
                    {safe_source} · {safe_date}</div>
                </div>"""
            st.markdown(f'<div style="max-height:520px;overflow-y:auto;padding-right:.5rem;">{news_html}</div>',
                        unsafe_allow_html=True)
        else:
            st.info("Haber akışı alınamadı (bağlantı ya da sorgu sorunu).")

    with nr:
        chart_head("Sektörel Beklentiler ve Risk Analizi",
                   "Yatırım komitesi formatında yapay zekâ sentezi")

        risk_key_ok = (st.session_state.get("news_nace") == nace
                       and st.session_state.get("news_analysis"))

        if st.button("🧠 Risk Analizi Üret", use_container_width=False,
                     disabled=not news_items):
            from news_analysis import analyze_news
            with st.spinner("Haberler sentezleniyor (30–60 sn)…"):
                try:
                    res = analyze_news(nace, news_items)
                    if res and res.strip():
                        st.session_state["news_analysis"] = res
                        st.session_state["news_nace"] = nace
                        risk_key_ok = True
                    else:
                        st.error("Sentez boş döndü — tekrar deneyin.")
                except Exception as e:
                    st.error(f"Sentez hatası: {e}")

        if risk_key_ok:
            from report_word import bullets_from_text
            bl = bullets_from_text(st.session_state["news_analysis"])
            items_html = "".join(f"<li>{b}</li>" for b in bl)
            st.markdown(f'<div class="report"><ul>{items_html}</ul></div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="src">Görüşler haber sentezidir; yatırım tavsiyesi '
                        f'değildir. Word raporuna otomatik eklenir.</div>',
                        unsafe_allow_html=True)
        elif news_items:
            st.markdown(f'<div class="src">Soldaki haber akışını yatırım komitesi '
                        f'formatında risk-fırsat maddelerine dönüştürmek için butona basın.</div>',
                        unsafe_allow_html=True)

# ── TAB 9: ANALİST GÖRÜNÜMÜ ─────────────────────────────────────────────────────
with tabs[9]:
    sec_title("Analist Görünümü",
              "Reel büyüme, verimlilik, momentum ve karşılaştırmalı konumlanma · türev göstergeler")

    # ── Reel vs Nominal Ciro + Momentum ──
    a1, a2 = st.columns([3, 2], gap="large")
    with a1:
        chart_head("Reel vs Nominal Ciro",
                   "Nominal ciro ÜFE ile deflate edildi · reel = gerçek büyüme")
        if _ciro_ser and _reel_ciro:
            fig = go.Figure()
            _ends = []
            xs_n, ys_n = series_xy(_ciro_ser, ay_sayisi)
            fig.add_trace(go.Scatter(x=xs_n, y=ys_n, mode="lines", name="Nominal Ciro",
                line=dict(color="#94A3B8", width=1.8, shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:+.1f}%</b><extra>Nominal</extra>"))
            if xs_n: _ends.append((xs_n[-1], ys_n[-1], "#94A3B8", "{:+.0f}%"))
            xs_u, ys_u = series_xy(_ufe_ser, ay_sayisi)
            fig.add_trace(go.Scatter(x=xs_u, y=ys_u, mode="lines", name="ÜFE (maliyet)",
                line=dict(color=AMBER, width=1.6, dash="dot", shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:+.1f}%</b><extra>ÜFE</extra>"))
            if xs_u: _ends.append((xs_u[-1], ys_u[-1], AMBER, "{:+.0f}%"))
            xs_r, ys_r = series_xy(_reel_ciro, ay_sayisi)
            fig.add_trace(go.Scatter(x=xs_r, y=ys_r, mode="lines", name="Reel Ciro",
                line=dict(color=BRAND, width=2.8, shape="spline", smoothing=.8),
                fill="tozeroy", fillcolor="rgba(37,99,235,.06)",
                hovertemplate="<b>%{y:+.1f}%</b><extra>Reel</extra>"))
            if xs_r: _ends.append((xs_r[-1], ys_r[-1], BRAND, "{:+.0f}%"))
            add_end_labels(fig, _ends, gap_frac=0.08)
            fig.update_layout(**LAYOUT, height=450)
            fig.update_xaxes(dtick=6)
            fig.update_yaxes(ticksuffix="%")
            fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig, use_container_width=True, config=NOBAR)
            if reel_v is not None:
                _msg = ("reel daralma — nominal büyüme enflasyonun altında" if reel_v < 0
                        else "reel büyüme — nominal artış enflasyonu aştı")
                st.markdown(f'<div class="src">Son dönem reel ciro <b>{reel_v:+.1f}%</b> · {_msg}</div>',
                            unsafe_allow_html=True)
        else:
            st.info("Reel ciro için ciro ve ÜFE verisi gerekli.")

    with a2:
        chart_head("Oynaklık / Risk Profili", "Son 24 ayın standart sapması (düşük = istikrarlı)")
        vol_items = [
            ("Üretim",   vol_std(_prod_ser)),
            ("Ciro",     vol_std(_ciro_ser)),
            ("İhracat",  vol_std(_ih_ser)),
            ("İstihdam", vol_std(_emp_ser)),
            ("ÜFE",      vol_std(_ufe_ser)),
        ]
        vol_items = [(n, round(v, 1)) for n, v in vol_items if v is not None]
        if vol_items:
            names = [n for n, _ in vol_items][::-1]
            vvals = [v for _, v in vol_items][::-1]
            fig = go.Figure(go.Bar(
                y=names, x=vvals, orientation="h",
                marker_color=AMBER, marker_line_width=0, marker=dict(cornerradius=3),
                text=[f"{v:.1f}" for v in vvals], textposition="outside",
                cliponaxis=False, textfont=dict(size=11, family="Inter"),
                hovertemplate="%{y}: <b>σ = %{x:.1f}</b><extra></extra>", width=0.58))
            fig.update_layout(**LAYOUT, height=450, showlegend=False, hovermode="closest",
                              margin=dict(l=8, r=36, t=8, b=30))
            fig.update_xaxes(showticklabels=False, showline=False,
                             range=[0, max(vvals) * 1.35 or 1])
            fig.update_yaxes(showgrid=False, tickfont=dict(size=11, color=INK_SOFT))
            st.plotly_chart(fig, use_container_width=True, config=NOBAR)
            st.markdown('<div class="src">Yüksek σ = öngörülemez talep/fiyat · '
                        'planlama ve nakit akışı riski</div>', unsafe_allow_html=True)
        else:
            st.info("Oynaklık için yeterli veri yok.")

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    # ── Verimlilik + Oynaklık ──
    b1 = st.container()
    with b1:
        chart_head("İşgücü Verimliliği",
                   "Üretim ve istihdam YoY · çubuklar = verimlilik büyümesi (1+gY)/(1+gL)−1")
        if _prod_ser and _emp_ser and _verim:
            # Üç seriyi ortak döneme hizala → unified hover düzgün çalışsın
            _common = sorted(set(_prod_ser) & set(_emp_ser))[-ay_sayisi:]
            _cx = [tr_month(p) for p in _common]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=_cx, y=[round(_prod_ser[p], 1) for p in _common],
                mode="lines", name="Üretim",
                line=dict(color=BRAND, width=2, shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:+.1f}%</b><extra>Üretim</extra>"))
            fig.add_trace(go.Scatter(x=_cx, y=[round(_emp_ser[p], 1) for p in _common],
                mode="lines", name="İstihdam",
                line=dict(color=TEAL, width=2, shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:+.1f}%</b><extra>İstihdam</extra>"))
            _yv = [round(_verim.get(p, 0), 1) for p in _common]
            fig.add_trace(go.Bar(x=_cx, y=_yv, name="Verimlilik",
                marker_color=["rgba(5,150,105,.35)" if v >= 0 else "rgba(220,38,38,.35)" for v in _yv],
                marker_line_width=0,
                hovertemplate="<b>%{y:+.1f}%</b><extra>Verimlilik</extra>"))
            fig.update_layout(**LAYOUT, height=340)
            fig.update_xaxes(dtick=6)
            fig.update_yaxes(ticksuffix="%")
            fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig, use_container_width=True, config=NOBAR)
            st.markdown('<div class="src">Verimlilik büyümesi = (1+g<sub>üretim</sub>)/(1+g<sub>istihdam</sub>)−1 '
                        '(OECD 2001, Measuring Productivity). Çıktı hacim endeksi, işgücü girdisi '
                        'ücretli çalışan endeksiyle temsil edilir; çalışılan saat farkları yansımaz. '
                        'Kaynak: TÜİK üretim + ücretli çalışan endeksleri</div>',
                        unsafe_allow_html=True)
        else:
            st.info("Verimlilik için üretim ve istihdam verisi gerekli.")



    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    # ── REDK Overlay ──
    chart_head("Reel Efektif Döviz Kuru & İhracat",
               "REDK (ÜFE bazlı) vs ihracat büyümesi · rekabet etkisi")
    _redk = cache.get("redk")
    if _redk and _ih_ser:
        _r_common = sorted(set(_redk) & set(_ih_ser))[-ay_sayisi:]
        if len(_r_common) >= 6:
            xs_rd = [tr_month(p) for p in _r_common]
            fig_rd = go.Figure()
            fig_rd.add_trace(go.Scatter(
                x=xs_rd, y=[round(_ih_ser.get(p, 0), 1) for p in _r_common],
                mode="lines", name="İhracat YoY%", yaxis="y",
                line=dict(color=TRADE_EXP, width=2.2, shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:+.1f}%</b><extra>İhracat</extra>"))
            fig_rd.add_trace(go.Scatter(
                x=xs_rd, y=[round(_redk[p], 1) for p in _r_common],
                mode="lines", name="REDK", yaxis="y2",
                line=dict(color=AMBER, width=2, dash="dot", shape="spline", smoothing=.8),
                hovertemplate="<b>%{y:.1f}</b><extra>REDK</extra>"))
            fig_rd.update_layout(
                **LAYOUT, height=420,
                yaxis=dict(title=None, ticksuffix="%", side="left"),
                yaxis2=dict(title=None, overlaying="y", side="right",
                            showgrid=False, tickfont=dict(size=9, color=AMBER)),
            )
            fig_rd.update_xaxes(dtick=6)
            st.plotly_chart(fig_rd, use_container_width=True, config=NOBAR)
            st.markdown('<div class="src">REDK düşerken (TL değer kaybı) ihracat artışı '
                        'beklenir · Ters korelasyon = kur duyarlılığı yüksek sektör</div>',
                        unsafe_allow_html=True)
        else:
            st.info("REDK verisi yetersiz (cache_all.py yeniden çalıştırılmalı).")
    else:
        st.info("REDK verisi için `python cache_all.py` çalıştırın — TCMB EVDS'den çekilir.")

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    # ── İYA Güven Endeksi ──
    sec_title("Öncü Göstergeler — Sektörel Güven Endeksi", "TCMB İktisadi Yönelim Anketi (İYA) · İmalat sanayi beklentileri (Denge değeri)")
    _iya = cache.get("iya")
    if _iya:
        fig_iya = go.Figure()
        cols_iya = [BRAND, AMBER, TEAL, NEG]
        for idx, (k, info) in enumerate(_iya.items()):
            series = info['data']
            label = info['label']
            xs, ys = series_xy(series, ay_sayisi)
            if xs:
                fig_iya.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines", name=label,
                    line=dict(color=cols_iya[idx % len(cols_iya)], width=2.2, shape="spline", smoothing=.8),
                    hovertemplate="<b>%{y:+.1f}</b><extra>" + label + "</extra>"))
        fig_iya.update_layout(**LAYOUT, height=450, margin=dict(l=8, r=8, t=8, b=30))
        fig_iya.update_xaxes(dtick=6)
        fig_iya.update_yaxes(ticksuffix="")
        fig_iya.add_hline(y=0, line_width=1.5, line_color="#94A3B8")
        st.plotly_chart(fig_iya, use_container_width=True, config=NOBAR)
        source("Kaynak: TCMB EVDS · Denge = (Artacak/İyileşecek diyenler %) − (Azalacak/Kötüleşecek diyenler %)")
    else:
        st.info("İYA Güven Endeksi verisi için `python cache_all.py` çalıştırın.")

    st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)

    # ── Sektörler Arası Korelasyon Matrisi ──
    sec_title("Sektörler Arası Korelasyon",
              "24 imalat sektörünün üretim YoY serileri arasındaki Pearson korelasyonu (son 24 ay)")

    @st.cache_data(show_spinner=False)
    def _corr_matrix(cache_key):
        import numpy as np
        sector_data = {}
        for k in ALL_MANUFACTURING:
            fk = build_sekil1(k, cache["alt_c"], ana_c_series=_ana_c)
            if not fk: continue
            merged = {}
            for _, s in fk.items():
                for p, v in s.items():
                    if v is not None: merged.setdefault(p, []).append(v)
            if merged:
                sector_data[k] = {p: sum(vs)/len(vs) for p, vs in merged.items()}
        if len(sector_data) < 3:
            return None, None
        # Son 24 ay, ortak dönemler
        all_periods = sorted(set.intersection(*[set(s.keys()) for s in sector_data.values()]))[-24:]
        if len(all_periods) < 6:
            return None, None
        codes = sorted(sector_data.keys())
        matrix = []
        for k in codes:
            matrix.append([sector_data[k].get(p, 0) for p in all_periods])
        corr = np.corrcoef(matrix)
        return corr, codes

    corr, corr_codes = _corr_matrix(cache_date)
    if corr is not None:
        corr_labels = [f"{c.lstrip('C')}·{short_name(c, 12)}" for c in corr_codes]
        fig_corr = go.Figure(go.Heatmap(
            z=corr.tolist(), x=corr_labels, y=corr_labels,
            text=[[f"{v:.2f}" for v in row] for row in corr.tolist()],
            texttemplate="%{text}", textfont=dict(size=7.5, family="Inter"),
            colorscale=[[0, "#DC2626"], [0.35, "#FEE2E2"], [0.5, "#F8FAFC"],
                        [0.65, "#DBEAFE"], [1, BRAND]],
            zmid=0, zmin=-1, zmax=1, xgap=2, ygap=2, showscale=True,
            colorbar=dict(thickness=12, len=0.5, tickfont=dict(size=8)),
            hovertemplate="%{x} ↔ %{y}<br><b>r = %{z:.2f}</b><extra></extra>",
        ))
        fig_corr.update_layout(**LAYOUT, height=520, hovermode="closest",
                               margin=dict(l=8, r=8, t=8, b=8))
        fig_corr.update_xaxes(showline=False, ticks="", tickfont=dict(size=8),
                              tickangle=45)
        fig_corr.update_yaxes(showgrid=False, tickfont=dict(size=8), autorange="reversed")
        st.plotly_chart(fig_corr, use_container_width=True, config=NOBAR)
        source("Pearson korelasyonu · son 24 aylık üretim YoY% ortalaması · "
               "koyu mavi = güçlü pozitif (birlikte hareket) · kırmızı = negatif (ters yönlü)")
    else:
        st.info("Korelasyon matrisi için yeterli veri yok.")

    st.markdown('<div class="src">Sektörün 24 imalat sektörü içindeki yüzdelik konumlanması '
                'Genel Bakış sekmesindeki <b>Sektör Bileşik Skoru</b>nda gösterilir '
                '(sıra-tabanlı normalizasyon, tek bileşik gösterge).</div>',
                unsafe_allow_html=True)

# ── TAB 10: ÜRÜN DETAYI (PRODTR) ─────────────────────────────────────────────────
with tabs[10]:
    if f9:
        from prodtr_data import (gtip_for_product, product_detail,
                                  prodtr_for_gtip, search_products)
        yil9   = f9["yil"]
        trend9 = f9.get("satis_trend", {})
        toplam_son = trend9.get(yil9, 0.0)

        # ── Türev yardımcılar: deflatör (YİÜFE), reel seri, YoY, fiziksel CAGR ──
        def _trnum(v, nd=1):
            return f"{v:,.{nd}f}".replace(",", "§").replace(".", ",").replace("§", ".")

        def _para(v, sym=None):
            sym = sym if sym is not None else PARA_SIM
            if v is None: return "—"
            a = abs(v)
            if a >= 1e9: return f"{sym}{_trnum(v/1e9, 1)} mlr"
            if a >= 1e6: return f"{sym}{_trnum(v/1e6, 1)} mn"
            if a >= 1e3: return f"{sym}{_trnum(v/1e3, 1)} bin"
            return f"{sym}{_trnum(v, 2)}"

        # Seçili para birimi: TL serilerini yıllık ortalama kurla çevirir.
        # Reel (YİÜFE) arındırma yalnız TL modunda gösterilir — USD serisi
        # zaten ortak paydadadır, iki kez arındırma yanıltıcı olur.
        _c9 = to_cur_yillik

        def _birim_kisa(b):
            m = re.search(r"\(([^)]+)\)", b or "")
            return m.group(1) if m else (b or "birim")

        def _yiufe_yillik(code):
            """Sektörün yurt içi ÜFE endeksi (2003=100) → yıllık ortalama seviye."""
            for s_ in cache.get("ufe", []):
                k_ = s_.get("key", {})
                if (k_.get("INDICATOR") == "F_YIUFE" and k_.get("DEGISIM") == "1"
                        and k_.get("URUN_UFE_NACE_CPA") == code):
                    by = {}
                    for p_, v_ in s_.get("data", {}).items():
                        if v_ is not None:
                            by.setdefault(int(p_[:4]), []).append(v_)
                    return {y: sum(vs)/len(vs) for y, vs in sorted(by.items())}
            return {}

        defl9 = _yiufe_yillik(nace) or _yiufe_yillik("C")

        def _reel9(nom, base=None):
            """Nominal yıllık seriyi baz yıl fiyatlarına çevirir (sektörel YİÜFE)."""
            ok = [y for y in (nom or {}) if y in defl9 and defl9[y]]
            if not ok: return {}
            b = base if (base in defl9 and defl9.get(base)) else max(ok)
            return {y: nom[y] * defl9[b] / defl9[y] for y in sorted(ok)}

        def _yoy9(series, y):
            v1, v0 = (series or {}).get(y), (series or {}).get(y - 1)
            if v1 is None or not v0: return None
            return (v1 / v0 - 1) * 100

        def _reel_yoy9(series, y):
            n = _yoy9(series, y)
            if n is None or not defl9.get(y) or not defl9.get(y - 1): return None
            pi = (defl9[y] / defl9[y - 1] - 1) * 100
            return ((1 + n/100) / (1 + pi/100) - 1) * 100

        def _cagr9(series, span=5):
            """Seride ~span yıllık bileşik büyüme (%). Son yıl güncel olmalı."""
            ys = sorted(y for y, v in (series or {}).items() if v)
            if not ys: return None
            y1 = ys[-1]
            if y1 < yil9 - 1: return None
            cands = [y for y in ys if y1 - span - 1 <= y <= y1 - span + 1 and y < y1]
            if not cands: return None
            y0 = min(cands, key=lambda y: abs(y - (y1 - span)))
            v0, v1 = series[y0], series[y1]
            if v0 <= 0 or v1 <= 0: return None
            return ((v1 / v0) ** (1 / (y1 - y0)) - 1) * 100

        def _lbl9(r, n=34):
            p_ = r["kod"].split(".")
            kisa = f"{p_[0]}.{p_[1]}" if len(p_) > 1 else p_[0]
            return f"{kisa} · {r['tanim'][:n]}" + ("…" if len(r["tanim"]) > n else "")

        # Son yılda veri beyan eden ürünler (pay/yoğunlaşma bu küme üstünden)
        son_rows9 = sorted((r for r in f9["all_rows"]
                            if r["seri_satis"].get(yil9) is not None),
                           key=lambda r: r["seri_satis"][yil9], reverse=True)
        paylar9 = ([r["seri_satis"][yil9] / toplam_son * 100 for r in son_rows9]
                   if toplam_son else [])
        cr5_9  = sum(paylar9[:5])
        hhi9   = sum(p*p for p in paylar9)
        hhi_lbl = ("düşük" if hhi9 < 1000 else "ılımlı" if hhi9 < 1800 else "yüksek")

        sec_title(f"Ürün Detayı — {sector_tr}",
                  f"TÜİK Sanayi Ürün İstatistikleri (PRODTR) · fiziksel ürün bazında üretim ve satış · {yil9}")

        trend9c = _c9(trend9)               # seçili para biriminde trend
        _yn9 = _yoy9(trend9, yil9)          # nominal ₺ büyüme
        _yu9 = _yoy9(trend9c, yil9) if usd_mode else None   # USD bazlı büyüme
        _yr9 = _reel_yoy9(trend9, yil9)     # YİÜFE ile arındırılmış büyüme
        _tone9 = (None if _yr9 is None and _yn9 is None
                  else ("pos" if (_yr9 if _yr9 is not None else _yn9) >= 0 else "neg"))

        pc = st.columns(4)
        kpi_card(pc[0], "Ürün Çeşidi", f"{f9['urun_sayisi']}",
                 f"{len(son_rows9)} üründe {yil9} verisi · {f9['veri_urun']} üründe tarihsel seri",
                 icon="🧴")
        if usd_mode:
            _ts_sub = (f"USD bazında {_yu9:+.1f}".replace(".", ",") + "% YoY (yıl ort. kur)"
                       if _yu9 is not None else f"{yil9} · yıl ort. kurla USD")
        else:
            _ts_sub = (f"reel {_yr9:+.1f}% (YİÜFE arındırılmış)".replace(".", ",")
                       if _yr9 is not None else f"{yil9} · ürün satış değeri")
        kpi_card(pc[1], "Toplam Satış", _para(trend9c.get(yil9)),
                 _ts_sub, tone=_tone9,
                 badge=(f"{_yn9:+.1f}".replace(".", ",") + "% nominal ₺" if _yn9 is not None else None),
                 icon="💰")
        kpi_card(pc[2], "Ürün Yoğunlaşması", f"%{cr5_9:,.0f}",
                 f"CR5 · HHI {hhi9:,.0f} ({hhi_lbl}) · {yil9} ürün sepeti".replace(",", "."),
                 icon="🎯")
        _top1 = son_rows9[0] if son_rows9 else None
        kpi_card(pc[3], "En Büyük Ürün",
                 _para(tl_to_cur(_top1["seri_satis"][yil9], yil9)) if _top1 else "—",
                 (_top1["tanim"][:38] + "…" if _top1 and len(_top1["tanim"]) > 38
                  else (_top1["tanim"] if _top1 else "—")),
                 badge=(f"%{paylar9[0]:.1f} pay".replace(".", ",") if paylar9 else None),
                 icon="🥇")

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        pl, pr = st.columns([5, 4], gap="large")

        with pl:
            chart_head(f"En Büyük 12 Ürün", f"Satış değeri, milyar {PARA_SIM} · {yil9}")
            top = son_rows9[:12][::-1]
            _kd9 = _kur_yil.get(yil9, 1.0) if usd_mode else 1.0
            if top and _kd9:
                fig = go.Figure(go.Bar(
                    y=[_lbl9(t) for t in top],
                    x=[t["seri_satis"][yil9]/_kd9/1e9 for t in top],
                    orientation="h", marker_color=BRAND, marker_line_width=0,
                    marker=dict(cornerradius=3),
                    text=[f"{t['seri_satis'][yil9]/_kd9/1e9:,.1f}".replace(",", ".") for t in top],
                    textposition="outside", cliponaxis=False,
                    textfont=dict(size=10, family="Inter"),
                    customdata=[[t["tanim"],
                                 t["seri_girisim"].get(yil9) or "—",
                                 f"{t['seri_satis'][yil9]/toplam_son*100:.1f}" if toplam_son else "—"]
                                for t in top],
                    hovertemplate="<b>%{customdata[0]}</b><br>Satış: " + PARA_SIM + "%{x:.2f} mlr · "
                                  "Pay: %%{customdata[2]} · Girişim: %{customdata[1]}<extra></extra>",
                    width=0.7,
                ))
                fig.update_layout(**LAYOUT, height=max(360, 30*len(top)+60),
                                  showlegend=False, hovermode="closest",
                                  margin=dict(l=8, r=52, t=8, b=30))
                fig.update_xaxes(showticklabels=False, showline=False)
                fig.update_yaxes(showgrid=False, tickfont=dict(size=9.5, color=INK_SOFT))
                st.plotly_chart(fig, use_container_width=True, config=NOBAR)
            source("Kaynak: TÜİK — Sanayi Ürün İstatistikleri Veri Tabanı (PRODTR, 2005–2025)")

        with pr:
            chart_head("Sektör Satış Değeri Trendi",
                       (f"Tüm ürünler toplamı · milyar $ · yıllık ort. kurla" if usd_mode else
                        f"Tüm ürünler toplamı · milyar ₺ · nominal ve reel ({yil9} fiyatlarıyla)"))
            if trend9c:
                yrs = sorted(trend9c.keys())
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=[str(y) for y in yrs], y=[trend9c[y]/1e9 for y in yrs],
                    name=("USD" if usd_mode else "Nominal"), mode="lines",
                    line=dict(color=BRAND, width=2.6, shape="spline", smoothing=.6),
                    fill="tozeroy", fillcolor="rgba(37,99,235,.07)",
                    hovertemplate="<b>" + PARA_SIM + "%{y:.1f} mlr</b><extra></extra>"))
                reel_tr = {} if usd_mode else _reel9(trend9, yil9)
                if len(reel_tr) >= 2:
                    ry = sorted(reel_tr)
                    fig2.add_trace(go.Scatter(
                        x=[str(y) for y in ry], y=[reel_tr[y]/1e9 for y in ry],
                        name=f"Reel ({yil9} fiy.)", mode="lines",
                        line=dict(color=NAVY, width=2, dash="dot"),
                        hovertemplate="Reel: <b>₺%{y:.0f} mlr</b><extra></extra>"))
                fig2.update_layout(**LAYOUT, height=300, showlegend=len(reel_tr) >= 2)
                fig2.update_yaxes(ticksuffix="")
                st.plotly_chart(fig2, use_container_width=True, config=NOBAR)
                _src2 = ('USD serisi yıllık ortalama USD/TRY ile çevrilmiştir (TCMB); '
                         'kur hareketleri seriye yansır, birim değer yorumunda dikkat. '
                         if usd_mode else
                         'Reel seri sektörel yurt içi ÜFE ile arındırılmıştır (YİÜFE 2015+). ')
                st.markdown(f'<div class="src">{_src2}Gizli (c) beyan edilen ürünler '
                            'toplama dahil edilmez; seriler alt sınır niteliğindedir.</div>',
                            unsafe_allow_html=True)

        # ── Yapı & dinamikler: fiziksel momentum + Pareto yoğunlaşması ──────────
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        dl9, dr9 = st.columns([5, 4], gap="large")

        with dl9:
            chart_head("Yükselen & Gerileyen Ürünler",
                       "Satış miktarı, ~5 yıllık bileşik büyüme (fiziksel — enflasyondan bağımsız)")
            movers = []
            for r in son_rows9[:80]:
                g = _cagr9(r.get("seri_miktar"))
                if g is None or abs(g) > 80:   # veri kırılması / birim değişimi filtresi
                    continue
                movers.append((r, g))
            if len(movers) >= 4:
                movers.sort(key=lambda t: t[1], reverse=True)
                secilen = movers[:6] + movers[-6:] if len(movers) > 12 else movers
                secilen = sorted(secilen, key=lambda t: t[1])
                figm = go.Figure(go.Bar(
                    y=[_lbl9(r, 30) for r, _ in secilen],
                    x=[g for _, g in secilen],
                    orientation="h",
                    marker_color=[POS if g >= 0 else NEG for _, g in secilen],
                    marker_line_width=0, marker=dict(cornerradius=3),
                    text=[f"{g:+.1f}%".replace(".", ",") for _, g in secilen],
                    textposition="outside", cliponaxis=False,
                    textfont=dict(size=10, family="Inter"),
                    customdata=[[r["tanim"], _birim_kisa(r["birim"])] for r, _ in secilen],
                    hovertemplate="<b>%{customdata[0]}</b><br>Miktar CAGR: %{x:+.1f}%/yıl "
                                  "(%{customdata[1]})<extra></extra>",
                    width=0.68,
                ))
                figm.update_layout(**LAYOUT, height=max(320, 28*len(secilen)+60),
                                   showlegend=False, hovermode="closest",
                                   margin=dict(l=8, r=60, t=8, b=30))
                figm.update_xaxes(ticksuffix="%", zeroline=True,
                                  zerolinecolor="#94A3B8", zerolinewidth=1.2)
                figm.update_yaxes(showgrid=False, tickfont=dict(size=9.5, color=INK_SOFT))
                st.plotly_chart(figm, use_container_width=True, config=NOBAR)
                st.markdown('<div class="src">Miktar bazlı büyüme fiyat etkisi içermez; ürün '
                            'portföyünün gerçek kayma yönünü gösterir. |CAGR| &gt; %80 olan '
                            'seriler (olası birim/kapsam değişimi) elenmiştir.</div>',
                            unsafe_allow_html=True)
            else:
                st.caption("Momentum taraması için yeterli satış miktarı serisi yok.")

        with dr9:
            chart_head("Ürün Yoğunlaşması — Pareto",
                       f"Kümülatif satış payı, ilk N ürün · {yil9}")
            if paylar9:
                cum, s_ = [], 0.0
                for p in paylar9:
                    s_ += p; cum.append(min(s_, 100.0))
                figp = go.Figure(go.Scatter(
                    x=list(range(1, len(cum)+1)), y=cum, mode="lines",
                    line=dict(color=BRAND, width=2.4),
                    fill="tozeroy", fillcolor="rgba(37,99,235,.06)",
                    customdata=[r["tanim"][:60] for r in son_rows9],
                    hovertemplate="İlk %{x} ürün: <b>%%{y:.1f}</b><br>"
                                  "%{x}. ürün: %{customdata}<extra></extra>"))
                for n_ in (5, 10, 20):
                    if n_ <= len(cum):
                        figp.add_trace(go.Scatter(
                            x=[n_], y=[cum[n_-1]], mode="markers+text",
                            marker=dict(color=NAVY, size=8,
                                        line=dict(color=WHITE, width=1.5)),
                            text=[f"CR{n_} %{cum[n_-1]:.0f}"], textposition="bottom right",
                            textfont=dict(size=10.5, color=NAVY, family="Inter"),
                            showlegend=False, hoverinfo="skip"))
                figp.update_layout(**LAYOUT, height=300, showlegend=False,
                                   hovermode="closest")
                figp.update_xaxes(title=None)
                figp.update_yaxes(range=[0, 105], ticksuffix="%")
                st.plotly_chart(figp, use_container_width=True, config=NOBAR)
                _hhi_txt = f"{hhi9:,.0f}".replace(",", ".")
                st.markdown(f'<div class="src">HHI {_hhi_txt} (ürün sepeti, firma değil; '
                            f'Herfindahl 1950, Hirschman 1964) — {hhi_lbl} yoğunlaşma. '
                            f'Eşikler ABD DOJ &amp; FTC 2023 Birleşme Rehberi ile uyumlu: '
                            f'1.000 altı çeşitlenmiş, 1.800 üzeri yoğunlaşmış.</div>',
                            unsafe_allow_html=True)

        st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
        sub1, sub2, sub3 = st.tabs(["📋  Ürün Tablosu", "🔬  Ürün İncelemesi",
                                    "🔄  GTİP ↔ PRODTR Dönüştürücü"])

        # ── Alt 1: Aranabilir ürün tablosu (pay, büyüme, birim değer analitiği) ──
        with sub1:
            idx9 = {r["kod"]: r for r in f9["all_rows"]}
            q = st.text_input("Ürün ara", value="",
                              placeholder="🔍 Ürün adı veya PRODTR kodu (ör. halı, 13.93, dokuma)",
                              key="prod_search", label_visibility="collapsed")
            if q.strip():
                # search_products yalnız kod/tanım döner → tam satırı all_rows'tan al
                base_rows = [idx9[s_["kod"]] for s_ in search_products(q, nace=nace)
                             if s_["kod"] in idx9]
            else:
                base_rows = sorted(f9["all_rows"],
                                   key=lambda r: (r["seri_satis"].get(yil9) is not None,
                                                  r["satis_deger"] or 0),
                                   reverse=True)
            _satcol9 = f"Satış (mlr {PARA_SIM})"
            _bdcol9  = f"Birim Değer {PARA_SIM}"
            rows = []
            for r in base_rows:
                ss, smk = r["seri_satis"], r.get("seri_miktar") or {}
                sv = tl_to_cur(r.get("satis_deger"), r.get("satis_yil"))
                pay = (ss[yil9] / toplam_son * 100
                       if toplam_son and ss.get(yil9) is not None else None)
                yoy = _yoy9(ss, yil9)
                mg  = _cagr9(smk)
                bd  = (tl_to_cur(ss[yil9], yil9) / smk[yil9]
                       if ss.get(yil9) and smk.get(yil9)
                       and tl_to_cur(ss[yil9], yil9) is not None else None)
                rows.append({
                    "PRODTR": r["kod"],
                    "Ürün": r.get("tanim", ""),
                    _satcol9: round(sv/1e9, 3) if sv else None,
                    "Yıl": r.get("satis_yil"),
                    "Pay %": round(pay, 2) if pay is not None else None,
                    "YoY %": round(yoy, 1) if yoy is not None else None,
                    "Miktar CAGR₅ %": round(mg, 1) if mg is not None else None,
                    _bdcol9: round(bd, 2) if bd is not None else None,
                    "Üretim": r.get("uretim"),
                    "Birim": _birim_kisa(r.get("birim", "")),
                    "Girişim": r.get("girisim"),
                    "GTİP": len(gtip_for_product(r["kod"])),
                })
            st.caption(f"{len(rows)} ürün gösteriliyor"
                       + (f" · '{q}' araması" if q.strip() else "")
                       + f" · Pay/YoY/Birim Değer yalnız {yil9} verisi olan ürünlerde hesaplanır")
            df9 = pd.DataFrame(rows)
            _maxpay = max((r["Pay %"] for r in rows if r["Pay %"] is not None), default=100.0)
            st.dataframe(
                df9.set_index("PRODTR"), use_container_width=True, height=440,
                column_config={
                    "Ürün": st.column_config.TextColumn("Ürün", width="large"),
                    _satcol9: st.column_config.NumberColumn(
                        _satcol9, format="%.3f",
                        help="Ürünün son veri yılındaki satış değeri"),
                    "Yıl": st.column_config.NumberColumn(
                        "Yıl", format="%d", help="Son veri yılı — eski yıllar nominal TL "
                        "olduğundan güncel ürünlerle doğrudan kıyaslanamaz"),
                    "Pay %": st.column_config.ProgressColumn(
                        "Pay %", format="%.1f%%", min_value=0.0, max_value=float(_maxpay),
                        help=f"Sektör {yil9} ürün satışları içindeki pay"),
                    "YoY %": st.column_config.NumberColumn(
                        "YoY %", format="%+.1f%%",
                        help=f"{yil9-1}→{yil9} nominal satış değişimi"),
                    "Miktar CAGR₅ %": st.column_config.NumberColumn(
                        "Miktar CAGR₅", format="%+.1f%%",
                        help="Satış miktarının ~5 yıllık bileşik büyümesi "
                             "(fiziksel — enflasyondan bağımsız)"),
                    _bdcol9: st.column_config.NumberColumn(
                        _bdcol9, format="%.2f",
                        help=f"{yil9} satış değeri ÷ satış miktarı ({PARA_SIM}/birim)"),
                })
            st.download_button(
                "⬇ Tabloyu CSV indir", df9.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{nace}_urun_tablosu_{yil9}.csv", mime="text/csv",
                key=f"dl_prod_{nace}")

        # ── Alt 2: Tekil ürün derin incelemesi ──
        with sub2:
            prod_opts = {f"{r['kod']} · {r['tanim'][:55]}": r['kod']
                         for r in sorted(f9["all_rows"],
                                         key=lambda r: (r["seri_satis"].get(yil9) or 0),
                                         reverse=True)}
            # key sektöre bağlı: sektör değişince seçenek listesi değişir,
            # sabit key eski değeri taşıyıp rerun hatası üretebilir
            sc1, sc2 = st.columns([3, 2], gap="medium")
            sel = sc1.selectbox("Ürün seçin", list(prod_opts.keys()), index=0,
                                key=f"prod_detail_sel_{nace}")
            manual = sc2.text_input("… veya PRODTR kodu girin", value="",
                                    placeholder="ör. 13.93.12.00.00",
                                    key="prod_detail_manual")
            code = manual.strip() if manual.strip() else prod_opts.get(sel)
            det = product_detail(code) if code else None
            if not det:
                st.warning(f"'{code}' için PRODTR kaydı bulunamadı.")
            else:
                sdd, smm = det["satis_deger"], det["satis_miktar"]
                udd, grr = det["uretim"], det["girisim"]
                sdd_c = _c9(sdd)          # seçili para biriminde satış değeri
                bk = _birim_kisa(det["birim"])
                tum_yil = sorted(set(sdd) | set(smm) | set(udd) | set(grr))
                aralik = f"{tum_yil[0]}–{tum_yil[-1]}" if tum_yil else "—"
                y_son = max(sdd) if sdd else (max(udd) if udd else None)

                # Birim değer serisi: satış değeri ÷ satış miktarı (₺ bazlı; görünüm için çevrilir)
                bd_seri = {y: sdd[y]/smm[y] for y in sdd
                           if smm.get(y) and sdd[y] is not None}
                bd_seri_c = {y: sdd_c[y]/smm[y] for y in sdd_c
                             if smm.get(y) and sdd_c[y] is not None}

                st.markdown(f"""<div class="report" style="padding:1rem 1.2rem;margin-bottom:.8rem">
                    <b style="font-size:1rem">{det['tanim']}</b><br>
                    <span style="color:{MUTED};font-size:.8rem">PRODTR {det['kod']} ·
                    {det['nace']} · Ölçü birimi: {det['birim'] or '—'} ·
                    Veri aralığı: {aralik} · Eşleşen GTİP: {len(det['gtip'])}</span></div>""",
                    unsafe_allow_html=True)

                if y_son is not None:
                    mk = st.columns(4)
                    _ys  = _yoy9(sdd, y_son); _yrr = _reel_yoy9(sdd, y_son)
                    _yus = _yoy9(sdd_c, y_son) if usd_mode else None
                    if usd_mode:
                        _sd_sub = (f"USD bazında {_yus:+.1f}% YoY".replace(".", ",")
                                   if _yus is not None else "yıl ort. kurla USD")
                    else:
                        _sd_sub = (f"reel {_yrr:+.1f}%".replace(".", ",") + " (YİÜFE arınd.)"
                                   if _yrr is not None else "nominal satış değeri")
                    kpi_card(mk[0], f"Satış Değeri ({y_son})", _para(sdd_c.get(y_son)),
                             _sd_sub,
                             tone=(None if _yrr is None and _ys is None
                                   else ("pos" if (_yrr if _yrr is not None else _ys) >= 0 else "neg")),
                             badge=(f"{_ys:+.1f}".replace(".", ",") + "% nominal ₺" if _ys is not None else None),
                             icon="💰")
                    _ym = _yoy9(smm, y_son)
                    kpi_card(mk[1], f"Satış Miktarı ({y_son})",
                             (f"{_trnum(smm[y_son], 0)} {bk}" if smm.get(y_son) else "—"),
                             (f"üretim: {_trnum(udd[y_son], 0)} {bk}"
                              if udd.get(y_son) else "üretim verisi gizli/yok"),
                             tone=(None if _ym is None else ("pos" if _ym >= 0 else "neg")),
                             badge=(f"{_ym:+.1f}%".replace(".", ",") if _ym is not None else None),
                             icon="📦")
                    _yb = _yoy9(bd_seri_c, y_son)
                    kpi_card(mk[2], "Birim Değer",
                             (f"{_para(bd_seri_c[y_son])}/{bk}" if bd_seri_c.get(y_son) else "—"),
                             "satış değeri ÷ satış miktarı",
                             badge=(f"{_yb:+.1f}%".replace(".", ",") if _yb is not None else None),
                             tone=(None if _yb is None else ("pos" if _yb >= 0 else "neg")),
                             icon="🏷️")
                    _g1 = grr.get(y_son); _g0 = grr.get(y_son - 1)
                    kpi_card(mk[3], f"Girişim ({y_son})",
                             (f"{_g1:.0f}" if _g1 else "—"),
                             "bu ürünü üreten girişim sayısı",
                             badge=(f"{_g1-_g0:+.0f}" if _g1 and _g0 else None),
                             tone=(None if not (_g1 and _g0)
                                   else ("pos" if _g1 >= _g0 else "neg")),
                             icon="🏢")
                    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

                dc1, dc2 = st.columns(2, gap="large")
                with dc1:
                    if sd_ys := sorted(sdd_c):
                        chart_head("Satış Değeri",
                                   (f"milyar $ · {sd_ys[0]}–{sd_ys[-1]} · yıl ort. kurla" if usd_mode
                                    else f"milyar ₺ · {sd_ys[0]}–{sd_ys[-1]} · nominal + reel"))
                        figd = go.Figure()
                        figd.add_trace(go.Bar(
                            x=[str(y) for y in sd_ys], y=[sdd_c[y]/1e9 for y in sd_ys],
                            name=("USD" if usd_mode else "Nominal"), marker_color=BRAND,
                            marker_line_width=0, marker=dict(cornerradius=3),
                            hovertemplate="<b>" + PARA_SIM + "%{y:.3f} mlr</b><extra></extra>"))
                        sd_reel = {} if usd_mode else _reel9(sdd, y_son)
                        if len(sd_reel) >= 2:
                            r_ys = sorted(sd_reel)
                            figd.add_trace(go.Scatter(
                                x=[str(y) for y in r_ys], y=[sd_reel[y]/1e9 for y in r_ys],
                                name=f"Reel ({y_son} fiy.)", mode="lines",
                                line=dict(color=NAVY, width=2, dash="dot"),
                                hovertemplate="Reel: <b>₺%{y:.3f} mlr</b><extra></extra>"))
                        figd.update_layout(**LAYOUT, height=270,
                                           showlegend=len(sd_reel) >= 2)
                        st.plotly_chart(figd, use_container_width=True, config=NOBAR)
                    else:
                        chart_head("Satış Değeri", f"milyar {PARA_SIM}")
                        st.caption("Satış değeri verisi gizli/yok.")
                with dc2:
                    if udd or smm:
                        u_ys = sorted(set(udd) | set(smm))
                        chart_head("Üretim & Satış Miktarı",
                                   f"{bk} · {u_ys[0]}–{u_ys[-1]} · aradaki fark stok/fason göstergesi")
                        figu = go.Figure()
                        if udd:
                            uy = sorted(udd)
                            figu.add_trace(go.Scatter(
                                x=[str(y) for y in uy], y=[udd[y] for y in uy],
                                name="Üretim", mode="lines",
                                line=dict(color=TEAL, width=2.4, shape="spline", smoothing=.6),
                                fill="tozeroy", fillcolor="rgba(13,148,136,.07)",
                                hovertemplate="Üretim: <b>%{y:,.0f}</b><extra></extra>"))
                        if smm:
                            my = sorted(smm)
                            figu.add_trace(go.Scatter(
                                x=[str(y) for y in my], y=[smm[y] for y in my],
                                name="Satış miktarı", mode="lines",
                                line=dict(color=SKY, width=2, dash="dash"),
                                hovertemplate="Satış: <b>%{y:,.0f}</b><extra></extra>"))
                        figu.update_layout(**LAYOUT, height=270,
                                           showlegend=bool(udd and smm))
                        st.plotly_chart(figu, use_container_width=True, config=NOBAR)
                    else:
                        chart_head("Üretim & Satış Miktarı", bk)
                        st.caption("Miktar verisi gizli/yok.")

                dc3, dc4 = st.columns(2, gap="large")
                with dc3:
                    if len(bd_seri_c) >= 2:
                        b_ys = sorted(bd_seri_c)
                        chart_head("Birim Değer",
                                   f"{PARA_SIM}/{bk} · {b_ys[0]}–{b_ys[-1]} · ürünün ortalama fiyat düzeyi")
                        figb = go.Figure()
                        figb.add_trace(go.Scatter(
                            x=[str(y) for y in b_ys], y=[bd_seri_c[y] for y in b_ys],
                            name=("USD" if usd_mode else "Nominal"), mode="lines+markers",
                            line=dict(color=AMBER, width=2.2),
                            marker=dict(size=5),
                            hovertemplate="<b>" + PARA_SIM + "%{y:,.2f}</b><extra></extra>"))
                        bd_reel = {} if usd_mode else _reel9(bd_seri, y_son)
                        if len(bd_reel) >= 2:
                            br_ys = sorted(bd_reel)
                            figb.add_trace(go.Scatter(
                                x=[str(y) for y in br_ys], y=[bd_reel[y] for y in br_ys],
                                name=f"Reel ({y_son} fiy.)", mode="lines",
                                line=dict(color=NAVY, width=2, dash="dot"),
                                hovertemplate="Reel: <b>₺%{y:,.2f}</b><extra></extra>"))
                        figb.update_layout(**LAYOUT, height=250,
                                           showlegend=len(bd_reel) >= 2)
                        st.plotly_chart(figb, use_container_width=True, config=NOBAR)
                        _bd_src = ('USD birim değer, dolar bazlı ihraç fiyatı kıyası için '
                                   'uygundur; kur oynaklığı seriye yansır.'
                                   if usd_mode else
                                   'Reel birim değerdeki düşüş fiyat rekabetine/değer '
                                   'kaybına, artış premiumlaşmaya işaret eder (sektörel '
                                   'YİÜFE ile arındırılmış).')
                        st.markdown(f'<div class="src">{_bd_src}</div>',
                                    unsafe_allow_html=True)
                    else:
                        chart_head("Birim Değer", f"{PARA_SIM}/{bk}")
                        st.caption("Birim değer için yeterli satış değeri+miktarı çifti yok.")
                with dc4:
                    if grr:
                        gy = sorted(grr)
                        chart_head("Girişim Sayısı",
                                   f"üretici girişim · {gy[0]}–{gy[-1]} · giriş-çıkış dinamiği")
                        figg = go.Figure(go.Scatter(x=[str(y) for y in gy],
                            y=[grr[y] for y in gy], mode="lines+markers",
                            line=dict(color=NAVY, width=2),
                            hovertemplate="%{x}: <b>%{y:.0f} girişim</b><extra></extra>"))
                        figg.update_layout(**LAYOUT, height=250, showlegend=False)
                        st.plotly_chart(figg, use_container_width=True, config=NOBAR)
                    else:
                        chart_head("Girişim Sayısı", "üretici girişim")
                        st.caption("Girişim sayısı verisi gizli/yok.")

                chart_head("Eşleşen GTİP Kodları",
                           "gümrük tarife satırları — dış ticaret istatistiklerine köprü")
                if det["gtip"]:
                    gdf = pd.DataFrame([{"GTİP": g["kod"], "Tanım": g["tanim"]}
                                       for g in det["gtip"]])
                    st.dataframe(gdf.set_index("GTİP"), use_container_width=True,
                                 height=min(320, 42 + 35*len(gdf)))
                else:
                    st.caption("Bu ürün için GTİP eşlemesi bulunamadı.")

        # ── Alt 3: GTİP ↔ PRODTR çift yönlü dönüştürücü ──
        with sub3:
            cv1, cv2 = st.columns(2, gap="large")
            with cv1:
                st.markdown('<div class="chart-h">GTİP → PRODTR</div>'
                            '<div class="chart-hs">Gümrük tarife kodundan üretim koduna</div>',
                            unsafe_allow_html=True)
                gq = st.text_input("GTİP kodu", value="",
                                   placeholder="ör. 5208 veya 520811100000",
                                   key="conv_gtip", label_visibility="collapsed")
                if gq.strip():
                    res = prodtr_for_gtip(gq)
                    if res:
                        st.caption(f"{len(res)} eşleşme")
                        st.dataframe(pd.DataFrame([{
                            "GTİP": r["gtip"], "GTİP Tanım": r["gtip_tanim"][:45],
                            "PRODTR": r["prodtr"], "PRODTR Ürün": r["prodtr_tanim"][:45],
                        } for r in res]).set_index("GTİP"),
                            use_container_width=True, height=360)
                    else:
                        st.info("Bu GTİP kodu için PRODTR eşleşmesi bulunamadı.")
            with cv2:
                st.markdown('<div class="chart-h">PRODTR → GTİP</div>'
                            '<div class="chart-hs">Üretim kodundan gümrük tarife kodlarına</div>',
                            unsafe_allow_html=True)
                pq = st.text_input("PRODTR kodu", value="",
                                   placeholder="ör. 13.93.12.00.00",
                                   key="conv_prodtr", label_visibility="collapsed")
                if pq.strip():
                    det2 = product_detail(pq.strip())
                    if det2 and det2["gtip"]:
                        st.caption(f"{det2['tanim'][:50]} → {len(det2['gtip'])} GTİP")
                        st.dataframe(pd.DataFrame([{
                            "GTİP": g["kod"], "Tanım": g["tanim"]}
                            for g in det2["gtip"]]).set_index("GTİP"),
                            use_container_width=True, height=360)
                    elif det2:
                        st.info("Bu ürün için GTİP eşlemesi yok.")
                    else:
                        st.info("PRODTR kodu bulunamadı.")

        source(f"Kaynak: TÜİK Sanayi Ürün İstatistikleri (PRODTR, 2005–2025) + "
               f"GTİP↔PRODTR 2018 eşleme tablosu (17.167 GTİP) · 'c' = gizli değer")
    else:
        st.info("Bu sektör için PRODTR ürün istatistiği bulunamadı "
                "(veya prodtr_cache.pkl eksik).")

# ── TAB 11: METODOLOJİ ──────────────────────────────────────────────────────────
with tabs[11]:
    sec_title("Metodoloji & Veri Kaynakları",
              "Dashboard'ta kullanılan tüm veri kaynakları, hesaplama yöntemleri ve türev göstergeler")

    met_l, met_r = st.columns([1, 1], gap="large")

    with met_l:
        # ── Veri Kaynakları ──
        chart_head("Veri Kaynakları", "7 temel + 2 tamamlayıcı kaynak")
        st.markdown(f"""
        <div class="report" style="font-size:.82rem;line-height:1.7;">
        <div class="r-head">1. TÜİK — Sanayi Üretim Endeksi</div>
        <p class="r-para">Kaynak: TÜİK SDMX REST API v1.5 · <code>DF_SANAYI_URETIM_ENDEKS_ALT_C</code> (3 haneli NACE)
        ve <code>DF_SANAYI_URETIM_ENDEKS_SINIF_O</code> (4 haneli sınıf düzeyi).<br>
        Endeks bazı: 2021=100. Üç düzeltme türü: ham, takvim arındırılmış, mevsim+takvim arındırılmış.
        Dashboard'da gösterilen YoY %: bir önceki yılın aynı ayına göre değişim oranı.
        Mevsim arındırılmış seri tercih edilir; yoksa takvim arındırılmış kullanılır.</p>

        <div class="r-head">2. TÜİK — Dış Ticaret Miktar Endeksi</div>
        <p class="r-para">İhracat: <code>DF_TAKVIM_ETKISINDEN_ARINDIRILMIS_IHRACAT_V2</code><br>
        İthalat: <code>DF_TAKVIM_ETKISINDEN_ARINDIRILMIS_ITHALAT_V2</code><br>
        Sektör eşlemesi NACE → SITC tablonuza göre yapılır (örn. C13 Tekstil → SITC 6).
        Gösterilen metrik: takvim arındırılmış miktar endeksinin YoY % değişimi.</p>

        <div class="r-head">3. TCMB EVDS — Kapasite Kullanım Oranı (KKO)</div>
        <p class="r-para">Kaynak: TCMB Elektronik Veri Dağıtım Sistemi · <code>TP.KKO2.IS.*</code> seri grubu.<br>
        İmalat sanayii toplam + 24 alt sektör bazında aylık KKO (%).
        TCMB anketi ile elde edilen yüzde, sektörün kurulu kapasitesinin ne kadarını kullandığını ölçer.
        İmalat ortalamasıyla fark, sektörün göreli durumunu gösterir.</p>

        <div class="r-head">4. TÜİK — Yurt İçi Üretici Fiyat Endeksi (Yİ-ÜFE)</div>
        <p class="r-para">Kaynak: <code>DF_UFE_SANAYI_V2</code><br>
        Sektör bazında ve imalat geneli yıllık değişim (%). Sektörün maliyet baskısını ölçer.
        İmalat ÜFE'sinden yüksekse → sektörde ortalamanın üzerinde girdi maliyeti baskısı var.</p>

        <div class="r-head">5. TÜİK — Ciro Endeksi</div>
        <p class="r-para">Kaynak: <code>DF_CIRO_ENDEKS_DEGISIM_C</code> · Bazı: 2021=100<br>
        Mevsim ve takvim etkisinden arındırılmış sektörel ciro değişimi (YoY %).
        Nominal büyümeyi gösterir; reel büyüme için ÜFE ile deflate edilir.</p>

        <div class="r-head">6. TÜİK — Ücretli Çalışan İstatistikleri</div>
        <p class="r-para">Kaynak: <code>DF_UCRETLI_CALISAN_ISTATISTIKLERI_C</code><br>
        Takvim arındırılmış ücretli çalışan endeksi (YoY %). Sektördeki istihdam dinamiğini ölçer.</p>

        <div class="r-head">7. İSO 500 & İkinci 500</div>
        <p class="r-para">Kaynak: İstanbul Sanayi Odası yıllık yayınları (Excel).<br>
        NACE kodu eşlemesiyle sektöre ait firmalar filtrelenir. Üretimden satışlar (₺),
        ihracat ($), çalışan sayısı, FAVÖK marjı gibi kurumsal metrikler hesaplanır.</p>

        <div class="r-head">8. TÜİK — Sanayi Ürün İstatistikleri (PRODTR)</div>
        <p class="r-para">Kaynak: TÜİK Sanayi Ürün İstatistikleri Veri Tabanı (2005–2025, Excel).<br>
        PRODTR ürün kodunun ilk 2 hanesi NACE bölümüne eşlenir (örn. 13.xx → C13).
        Ürün bazında üretim miktarı, satış değeri (₺) ve girişim sayısı gösterilir;
        GTİP↔PRODTR 2018 tablosuyla gümrük tarife kodlarına bağlanır.
        <code>c</code> = gizli (açıklanmayan) değer; toplamlar alt sınır niteliğindedir.</p>

        <div class="r-head">9. Google News RSS</div>
        <p class="r-para">Sektöre özel anahtar kelimelerle Google News RSS akışından son haberler çekilir.
        Zaman filtresi (24 saat – 1 yıl) Google'ın <code>when:</code> operatörüyle sunucu tarafında uygulanır.</p>

        <div class="r-head">10. TCMB — Kur Arşivi (USD/TRY)</div>
        <p class="r-para">Kaynak: TCMB günlük gösterge kurları arşivi (<code>tcmb.gov.tr/kurlar</code>).<br>
        2005'ten bugüne aylık USD satış kuru (ayın ortasındaki ilk iş günü). Makro Bağlam
        şeridinde ve ₺/$ para birimi dönüşümünde (yıllık ortalama) kullanılır.
        EVDS anahtarı tanımlıysa önbellek yenilemede aylık ortalama seriye geçilir.</p>
        </div>
        """, unsafe_allow_html=True)

    with met_r:
        # ── Türev Göstergeler ──
        chart_head("Türev Göstergeler & Hesaplama Yöntemleri",
                   "Temel verilerden türetilen analitik metrikler · literatür atıflı")
        st.markdown(f"""
        <div class="report" style="font-size:.82rem;line-height:1.7;">
        <div class="r-head">Reel Ciro Büyümesi</div>
        <p class="r-para">Formül: <code>g_reel = (1 + g_nominal) / (1 + π_ÜFE) − 1</code><br>
        Nominal ciro artışı sektörel Yİ-ÜFE ile deflate edilir — ulusal hesaplardaki
        hacim ölçümü pratiği (SNA 2008; Eurostat 2016). Aritmetik fark
        (<code>nominal − enflasyon</code>) yalnız küçük oranlarda geçerli bir yaklaşımdır;
        yüksek enflasyonda oransal form kullanılması gerekir. Pozitifse sektör
        gerçek anlamda büyüyor, negatifse nominal artış enflasyonun altında (reel daralma).</p>

        <div class="r-head">İşgücü Verimliliği Büyümesi</div>
        <p class="r-para">Formül: <code>g_verim = (1 + g_üretim) / (1 + g_istihdam) − 1</code><br>
        Emek verimliliği = çıktı hacmi / işgücü girdisi; büyüme oranı kesikli zamanda
        oransal formla hesaplanır (OECD 2001; kuramsal temel: Solow 1957 büyüme muhasebesi).
        Çıktı sanayi üretim (hacim) endeksi, işgücü girdisi ücretli çalışan endeksiyle
        temsil edilir — çalışılan saat değişimleri yansımadığından kişi-başı verimlilik
        proxy'sidir.</p>

        <div class="r-head">Birim İşgücü Maliyeti (ULC) Büyümesi</div>
        <p class="r-para">Formül: <code>g_ULC = (1 + g_ücret&nbsp;kütlesi) / (1 + g_üretim&nbsp;hacmi) − 1</code><br>
        Nominal ULC = işgücüne yapılan toplam ödeme / reel çıktı (OECD 2007 ULC
        göstergeleri sistemi). Burada pay TÜİK brüt ücret-maaş endeksi, payda üretim
        hacim endeksidir. Ücret artışı verimlilik artışını aşarsa ULC yükselir →
        maliyet kaynaklı rekabet gücü kaybı. <i>Not: önceki sürümdeki
        <code>ÜFE − verimlilik</code> tanımı çıktı fiyatını işgücü maliyeti yerine
        koyduğu için terk edilmiştir.</i></p>

        <div class="r-head">Dış Ticaret Makası</div>
        <p class="r-para">Formül: <code>Makas = İhracat miktar YoY% − İthalat miktar YoY%</code><br>
        Betimleyici bir ivme farkıdır (büyüme muhasebesi anlamında bir oran değildir).
        Pozitifse ihracat hacmi ithalattan hızlı büyüyor → net ticaret pozisyonu
        iyileşme eğiliminde.</p>

        <div class="r-head">Üretim Momentumu</div>
        <p class="r-para">Formül: <code>Momentum = Ort(son 3 ay) − Ort(önceki 3 ay)</code><br>
        Konjonktür izlemede yaygın 3 ay/3 ay karşılaştırması (merkez bankası kısa
        vadeli izleme pratiği; bkz. OECD 2008 kompozit öncü gösterge yaklaşımı).
        Trendin yönünü değil, ivmesini ölçer.</p>

        <div class="r-head">Oynaklık (Volatilite)</div>
        <p class="r-para">Formül: son 24 aylık YoY serisinin örneklem standart sapması (σ, n−1 payda).<br>
        Yüksek σ = öngörülemez talep/fiyat ortamı → planlama ve nakit akışı riski.
        Ham seriler yerine YoY değişimler üzerinden hesaplandığından trend etkisi
        büyük ölçüde arındırılmıştır.</p>

        <div class="r-head">Ürün Yoğunlaşması — CR<sub>k</sub> & HHI</div>
        <p class="r-para">Formüller: <code>CR_k = Σ ilk k ürün payı</code> ·
        <code>HHI = Σ s_i²</code> (paylar %, ölçek 0–10.000; Herfindahl 1950,
        Hirschman 1964). Eşikler ABD DOJ &amp; FTC 2023 Birleşme Rehberi'yle uyumlu:
        &lt;1.000 çeşitlenmiş, 1.000–1.800 ılımlı, &gt;1.800 yoğunlaşmış. Burada birim
        <i>ürün sepeti</i>dir (firma değil) → portföy çeşitlenmesi okuması yapılır.</p>

        <div class="r-head">Birim Değer (Unit Value)</div>
        <p class="r-para">Formül: <code>BD = satış değeri (₺) / satış miktarı (fiziksel birim)</code><br>
        Ürünün ortalama fiyat düzeyi proxy'si (Kravis &amp; Lipsey 1971; UN IMTS 2010).
        Ürün karması ve kalite değişimlerini fiyattan ayıramaz — yorumda bu sınırlılık
        gözetilmelidir. Reel birim değer sektörel Yİ-ÜFE ile arındırılır.</p>

        <div class="r-head">Miktar CAGR (5 yıl)</div>
        <p class="r-para">Formül: <code>CAGR = (V_t / V_0)^(1/t) − 1</code> — geometrik ortalama büyüme.<br>
        Satış <i>miktarı</i> üzerinden hesaplandığından fiyat/enflasyon etkisi içermez;
        |CAGR| &gt; %80 gözlemler olası birim/kapsam kırılması nedeniyle elenir.</p>

        <div class="r-head">Sektör Bileşik Skoru (0–100, yüzdelik tabanlı)</div>
        <p class="r-para">7 gösterge (üretim, reel ciro, ihracat, verimlilik, istihdam, KKO,
        maliyet) için sektörün 24 imalat sektörü içindeki yüzdelik dilimi hesaplanır:
        <code>PR = (altında kalan sektör sayısı) / (n−1) × 100</code>; skor bu yüzdeliklerin
        eşit ağırlıklı ortalamasıdır. Sıra-tabanlı normalizasyon, kompozit gösterge
        el kitabındaki standart yöntemlerdendir (OECD &amp; JRC 2008) ve keyfî bant
        seçimini ortadan kaldırır — <i>önceki sürümdeki uzman-yargısı bantları
        ([−15,+15] vb.) bu gerekçeyle terk edilmiştir.</i> Maliyet göstergesinde işaret
        çevrilir (düşük ÜFE = iyi). Dağılım varsayımı gerektirmez, aykırı değere dayanıklıdır.</p>

        <div class="r-head">Erken Uyarı — Sinyal Yaklaşımı</div>
        <p class="r-para">Her gösterge, son değerinin <i>kendi tarihsel dağılımı</i> içindeki
        yüzdeliğiyle değerlendirilir (sinyal eşiği yaklaşımı; Kaminsky, Lizondo &amp;
        Reinhart 1998): P10 altı 🔴 alarm, P25 altı 🟡 dikkat, üstü 🟢 normal
        (min. 24 gözlem). Üretimde ek kural: 3 ay üst üste negatif YoY → 🔴 —
        aylık konjonktür tarihlemesindeki minimum evre süresi geleneğine dayanır
        (Bry &amp; Boschan 1971). Maliyet makası (sektör−imalat ÜFE) ters işaretle
        değerlendirilir.</p>

        <div class="r-head">Firma Heterojenliği (İSO 500)</div>
        <p class="r-para">FAVÖK marjı, ihracat yoğunluğu (ihracat ₺ karşılığı / net satış) ve
        aktif devir hızı (net satış / aktif) dağılımları kutu grafiğiyle gösterilir.
        Aynı dar sektörde bile firmalar arası verimlilik/kârlılık farklarının büyük ve
        kalıcı olduğu bulgusuna dayanır (Syverson 2011). Uç %2 kırpılır (winsorizasyon).</p>

        <div class="r-head">USD Dönüşümü (₺/$ Görünümü)</div>
        <p class="r-para">Yıllık TL tutarlar, TCMB kur arşivinden derlenen aylık USD/TRY
        satış kurunun <i>yıllık ortalamasıyla</i> çevrilir (ayın ortasındaki ilk iş günü
        gözlemi). Dolar bazlı seri, yüksek enflasyon ortamında kaba bir reel/uluslararası
        kıyas sağlar; ancak kur oynaklığı seriye yansıdığından YİÜFE ile arındırılmış
        reel serinin yerine geçmez — USD modunda reel çizgi bu nedenle gösterilmez.</p>

        <div class="r-head">Korelasyon Matrisi</div>
        <p class="r-para">24 sektörün son 24 aylık üretim YoY serileri arasındaki Pearson
        korelasyonu (<code>numpy.corrcoef</code>). Yüksek r: ortak konjonktür/tedarik
        zinciri bağı; negatif r: çeşitlendirme potansiyeli. <i>Ortak makro şoklar
        korelasyonu yukarı yanlı ölçtürebilir; nedensellik okunamaz.</i></p>

        <div class="r-head">REDK & İhracat</div>
        <p class="r-para">TCMB reel efektif döviz kuru endeksi (Yİ-ÜFE bazlı; Saygılı,
        Saygılı &amp; Yılmaz 2010). REDK artışı = TL reel değerlenmesi → fiyat
        rekabetçiliği aleyhine; düşüşü ihracat hacmini destekler (klasik Marshall–Lerner
        çerçevesi).</p>
        </div>
        """, unsafe_allow_html=True)

    # ── Kaynakça ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    chart_head("Kaynakça", "Metodolojide atıf yapılan literatür")
    st.markdown("""
    <div class="report" style="font-size:.78rem;line-height:1.85;">
    <p class="r-para">
    Bry, G. &amp; Boschan, C. (1971). <i>Cyclical Analysis of Time Series: Selected
    Procedures and Computer Programs</i>. New York: NBER.<br>
    Eurostat (2016). <i>Handbook on Prices and Volume Measures in National Accounts</i>.
    Luxembourg: Publications Office of the European Union.<br>
    Herfindahl, O. C. (1950). <i>Concentration in the U.S. Steel Industry</i>.
    Doktora tezi, Columbia University.<br>
    Kaminsky, G., Lizondo, S. &amp; Reinhart, C. M. (1998). "Leading Indicators of
    Currency Crises." <i>IMF Staff Papers</i>, 45(1), 1–48.<br>
    Hirschman, A. O. (1964). "The Paternity of an Index."
    <i>American Economic Review</i>, 54(5), 761–762.<br>
    Kravis, I. B. &amp; Lipsey, R. E. (1971). <i>Price Competitiveness in World Trade</i>.
    New York: NBER / Columbia University Press.<br>
    OECD (2001). <i>Measuring Productivity — OECD Manual: Measurement of Aggregate
    and Industry-Level Productivity Growth</i>. Paris: OECD Publishing.<br>
    OECD (2007). <i>OECD System of Unit Labour Cost and Related Indicators</i>.
    Paris: OECD Publishing.<br>
    OECD &amp; European Commission JRC (2008). <i>Handbook on Constructing Composite
    Indicators: Methodology and User Guide</i>. Paris: OECD Publishing.<br>
    Saygılı, H., Saygılı, M. &amp; Yılmaz, G. (2010). "Türkiye İçin Yeni Reel Efektif
    Döviz Kuru Endeksleri." <i>TCMB Çalışma Tebliği</i> No. 10/12.<br>
    Solow, R. M. (1957). "Technical Change and the Aggregate Production Function."
    <i>Review of Economics and Statistics</i>, 39(3), 312–320.<br>
    Syverson, C. (2011). "What Determines Productivity?"
    <i>Journal of Economic Literature</i>, 49(2), 326–365.<br>
    United Nations (2011). <i>International Merchandise Trade Statistics:
    Concepts and Definitions 2010 (IMTS 2010)</i>. New York: UN Statistics Division.<br>
    U.S. Department of Justice &amp; Federal Trade Commission (2023).
    <i>Merger Guidelines</i>. Washington, DC.<br>
    European Commission (2008). <i>NACE Rev. 2 — Statistical Classification of
    Economic Activities in the European Community</i>. Eurostat Methodologies and
    Working Papers.<br>
    TÜİK (2025). <i>Sanayi Üretim Endeksi, Yurt İçi Üretici Fiyat Endeksi ve Sanayi
    Ürün İstatistikleri Metaverileri</i>. Ankara: Türkiye İstatistik Kurumu.
    </p></div>
    """, unsafe_allow_html=True)

    # ── NACE-SITC Eşleme Tablosu ──
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    chart_head("NACE → SITC Eşleme Tablosu", "Dış ticaret verisi sektör eşlemesi")
    sitc_rows = []
    for code in sorted(ALL_MANUFACTURING):
        sitc_rows.append({
            "NACE": code,
            "Sektör": nace_name(code) if code in NACE_NAMES else SECTOR_NAMES.get(code, code),
            "SITC Bölüm": SITC_MAP.get(code, "T"),
        })
    st.dataframe(pd.DataFrame(sitc_rows).set_index("NACE"), use_container_width=True, height=420)
    source("Eşleme: 2 haneli NACE Rev.2 → SITC Rev.4 bölüm kodu · T = Toplam dış ticaret")

# ════════════════════════════════════════════════════════════════════════════════
#  OTOMATİK RAPOR
# ════════════════════════════════════════════════════════════════════════════════
st.divider()
sec_title(f"Otomatik Rapor", f"{sector_tr} · yapay zekâ destekli sektörel değerlendirme")

cb, co = st.columns([1, 3])
with co:
    rapor_stili = st.radio("stil", ["Detaylı Analiz", "Kısa Özet"], horizontal=True,
                           label_visibility="collapsed", key="rapor_stili")
with cb:
    uret = st.button("✨ Rapor Üret", use_container_width=True)

def _clean_inline(s):
    """LLM metnini HTML-güvenli hale getir + markdown (**kalın**) dönüştür."""
    s = s.strip()
    s = _html.escape(s)                                  # <, >, & kaçışla
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)        # **kalın** → <b>
    s = s.replace('**', '').replace('*', '')             # artık/tek yıldızları temizle
    s = re.sub(r'^#{1,6}\s*', '', s)                     # markdown başlık işareti
    s = re.sub(r'\s{2,}', ' ', s)                        # fazla boşluk
    return s.strip()

if uret:
    from sector_analysis import generate_analysis
    with st.spinner("Rapor hazırlanıyor… (yapay zekâ erişilemezse verilerden otomatik yazılır)"):
        try:
            analysis = generate_analysis(nace, f1, f2, f3, f4, f5, iso_agg=f8,
                                         fig6=f6, fig7=f7,
                                         kisa=(st.session_state.get("rapor_stili") == "Kısa Özet"),
                                         f_fiyat=f_fiyat, f_su=f_su, f_ydufe=f_ydufe, f_tufe=f_tufe)
            if not analysis or not analysis.strip():
                st.error("Rapor üretilemedi. Lütfen tekrar deneyin.")
            else:
                st.session_state["rapor_text"] = analysis
                st.session_state["rapor_nace"] = nace
        except Exception as e:
            st.error(f"Rapor üretilemedi: {e}")

if "rapor_text" in st.session_state and st.session_state.get("rapor_nace") == nace:
    analysis = st.session_state["rapor_text"]
    from report_word import parse_llm_sections, bullets_from_text
    secs = parse_llm_sections(analysis)
    labels = {
        "GIRIS": "Genel Değerlendirme", "SEKIL1": "Üretim Endeksi",
        "SEKIL2": "Alt Kırılımlar", "SEKIL3": "Dış Ticaret",
        "SEKIL4": "Kapasite Kullanımı", "SEKIL5": "ÜFE · Maliyet",
        "SEKIL6": "İSO 500 · Kurumsal Görünüm",
        "SEKIL7": "Ciro Endeksi", "SEKIL8": "İstihdam",
    }
    html = ""
    any_section = False
    for tag, tl in labels.items():
        text = secs.get(tag, "")
        if not text or not text.strip(): continue
        paras = [p for p in re.split(r'\n+', text) if p.strip()]
        body = "<br>".join(_clean_inline(p) for p in paras)
        if tag == "GIRIS":
            html += f'<div class="r-head">{tl}</div><div class="r-intro">{body}</div>'
        else:
            html += f'<div class="r-head">{tl}</div><p class="r-para">{body}</p>'
        any_section = True
    if any_section:
        st.markdown(f'<div class="report">{html}</div>', unsafe_allow_html=True)
    else:
        # Etiket parse edilemediyse ham metni yine de temiz göster
        safe = "<br>".join(_clean_inline(l) for l in analysis.split("\n") if l.strip())
        st.markdown(f'<div class="report">{safe}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)
    d1, d2, _ = st.columns([1, 1, 3])
    with d1:
        import tempfile, shutil, glob
        try:
            tmp = tempfile.mkdtemp()
            from report_charts import generate_all_charts
            from report_word import build_word_report
            news_txt = (st.session_state.get("news_analysis")
                        if st.session_state.get("news_nace") == nace else None)
            chart_paths = generate_all_charts(nace, f1, f2, f3, f4, f5, tmp, iso_agg=f8)
            build_word_report(nace, f1, f2, f3, f4, f5,
                              analysis_text=analysis, chart_paths=chart_paths,
                              out_dir=tmp, iso_agg=f8, news_analysis=news_txt,
                              prodtr_agg=f9)
            docs = glob.glob(os.path.join(tmp, "*.docx"))
            if docs:
                with open(docs[0], "rb") as fh:
                    st.download_button("⬇  Word (.docx)", data=fh.read(),
                        file_name=f"{nace}_{sector[:20].replace(' ','_')}_Rapor.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True)
        except Exception as e:
            st.caption(f"Word oluşturulamadı: {e}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    with d2:
        st.download_button("⬇  Metin (.txt)", data=analysis.encode("utf-8"),
            file_name=f"{nace}_analiz.txt", mime="text/plain", use_container_width=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-foot">
  TÜİK SDMX REST API v1.5<span class="sep">·</span>TCMB EVDS<span class="sep">·</span>
  Önbellek: {cache_date}<span class="sep">·</span>9 veri seti · 24 sektör · PRODTR ürün detayı
</div>
""", unsafe_allow_html=True)
