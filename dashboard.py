# -*- coding: utf-8 -*-
"""
TÜİK + TCMB Sektörel Analiz Dashboard
Kullanim: streamlit run dashboard.py
"""
import os, sys, pickle, re
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

SERIES_PAL = [BRAND, "#7C3AED", SKY, TEAL, AMBER, "#DB2777", NAVY]
YEAR_PAL   = ["#BFDBFE", "#93C5FD", "#60A5FA", "#3B82F6", "#2563EB", "#1D4ED8"]
TRADE_EXP  = "#1D4ED8"
TRADE_IMP  = "#94A3B8"

FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
        "'Helvetica Neue', Arial, sans-serif")

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {{
  --ink:{INK}; --ink-soft:{INK_SOFT}; --muted:{MUTED};
  --line:{LINE}; --panel:{PANEL}; --brand:{BRAND};
  --pos:{POS}; --neg:{NEG};
}}

html, body, [class*="css"], .stApp {{
  font-family: 'Inter', {FONT};
  color: var(--ink);
}}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
  background: {WHITE};
}}
.main .block-container {{
  padding: 1.2rem 2.2rem 3rem 2.2rem;
  max-width: 1500px;
}}
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
  background: linear-gradient(120deg, {NAVY} 0%, {BRAND_DK} 55%, {BRAND} 100%);
  border-radius: 16px;
  padding: 1.5rem 2rem;
  margin-bottom: 1.4rem;
  box-shadow: 0 10px 30px -12px rgba(29,78,216,.45);
  position: relative;
  overflow: hidden;
}}
.app-header::after {{
  content:""; position:absolute; right:-40px; top:-40px;
  width:220px; height:220px; border-radius:50%;
  background: radial-gradient(circle, rgba(255,255,255,.12), transparent 70%);
}}
.app-header .eyebrow {{
  color: rgba(255,255,255,.72); font-size:.72rem; font-weight:600;
  letter-spacing:.18em; text-transform:uppercase; margin-bottom:.35rem;
}}
.app-header h1 {{
  color:#fff; font-size:1.7rem; font-weight:800; margin:0; line-height:1.15;
  letter-spacing:-.02em;
}}
.app-header .sub {{
  color: rgba(255,255,255,.85); font-size:.92rem; font-weight:500; margin-top:.35rem;
}}
.app-header .meta {{
  position:absolute; right:2rem; top:50%; transform:translateY(-50%);
  text-align:right; z-index:2;
}}
.app-header .meta .chip {{
  display:inline-block; background:rgba(255,255,255,.14);
  border:1px solid rgba(255,255,255,.22); backdrop-filter:blur(6px);
  color:#fff; font-size:.74rem; font-weight:600; padding:.35rem .8rem;
  border-radius:999px; margin-left:.4rem;
}}

/* ── KPI ── */
.kpi {{
  background:{WHITE}; border:1px solid var(--line);
  border-radius:14px; padding:1rem 1.15rem .95rem 1.15rem;
  position:relative; overflow:hidden; height:100%;
  box-shadow: 0 1px 2px rgba(15,23,41,.04);
  transition: transform .15s ease, box-shadow .15s ease;
}}
.kpi:hover {{ transform:translateY(-2px); box-shadow:0 8px 24px -12px rgba(15,23,41,.22); }}
.kpi::before {{
  content:""; position:absolute; left:0; top:0; bottom:0; width:4px;
  background:var(--brand);
}}
.kpi.pos::before {{ background:var(--pos); }}
.kpi.neg::before {{ background:var(--neg); }}
.kpi .k-label {{
  font-size:.7rem; font-weight:600; color:var(--muted);
  text-transform:uppercase; letter-spacing:.07em; margin-bottom:.35rem;
  display:flex; align-items:center; gap:.35rem;
}}
.kpi .k-value {{
  font-size:1.85rem; font-weight:800; letter-spacing:-.02em;
  line-height:1; color:var(--ink);
}}
.kpi.pos .k-value {{ color:var(--pos); }}
.kpi.neg .k-value {{ color:var(--neg); }}
.kpi .k-sub {{
  font-size:.72rem; color:var(--muted); margin-top:.45rem; font-weight:500;
}}
.kpi .k-badge {{
  display:inline-flex; align-items:center; gap:.2rem;
  font-size:.72rem; font-weight:700; padding:.12rem .45rem;
  border-radius:6px; margin-left:auto;
}}
.badge-pos {{ background:rgba(5,150,105,.1); color:var(--pos); }}
.badge-neg {{ background:rgba(220,38,38,.1); color:var(--neg); }}
.badge-neu {{ background:rgba(100,116,139,.12); color:var(--muted); }}

/* ── Bölüm başlığı ── */
.sec-title {{
  display:flex; align-items:center; gap:.55rem;
  font-size:1.02rem; font-weight:700; color:var(--ink);
  margin:.3rem 0 .25rem 0; letter-spacing:-.01em;
}}
.sec-title .dot {{
  width:8px; height:8px; border-radius:3px; background:var(--brand); flex:none;
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
  background:{WHITE}; border:1px solid var(--line);
  border-radius:14px; padding:1.5rem 1.75rem; margin-top:.5rem;
  font-size:.9rem; line-height:1.75; color:var(--ink-soft);
  box-shadow:0 1px 2px rgba(15,23,41,.04);
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
.report li {{ margin-bottom:.3rem; }}
.report li::marker {{ color:var(--brand); }}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {PANEL} 0%, #F4F7FB 100%);
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

/* Sidebar içi kart grupları */
.side-card {{
  background: {WHITE}; border: 1px solid var(--line); border-radius: 12px;
  padding: .85rem .9rem; margin-bottom: .7rem;
  box-shadow: 0 1px 2px rgba(15,23,41,.03);
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
  gap:.15rem; background:{PANEL}; padding:.3rem; border-radius:12px;
  border:1px solid var(--line);
}}
.stTabs [data-baseweb="tab"] {{
  font-size:.82rem; font-weight:600; color:var(--muted);
  border-radius:9px; padding:.5rem .9rem; background:transparent;
}}
.stTabs [aria-selected="true"] {{
  background:{WHITE} !important; color:var(--brand) !important;
  box-shadow:0 1px 3px rgba(15,23,41,.1);
}}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}
.stTabs [data-baseweb="tab-panel"] {{ padding-top:1.1rem; }}

/* ── Butonlar ── */
.stButton > button {{
  background:var(--brand); color:#fff; border:none; border-radius:10px;
  padding:.6rem 1.4rem; font-weight:700; font-size:.88rem;
  box-shadow:0 4px 12px -4px rgba(37,99,235,.5); transition:all .15s;
}}
.stButton > button:hover {{ background:{BRAND_DK}; transform:translateY(-1px); }}
.stDownloadButton > button {{
  background:{WHITE}; color:var(--brand); border:1.5px solid var(--brand);
  border-radius:10px; font-weight:700; font-size:.84rem;
}}
.stDownloadButton > button:hover {{ background:rgba(37,99,235,.06); }}

hr {{ border-color:var(--line); margin:1.5rem 0; }}
.stRadio [role="radiogroup"] label p {{ font-size:.82rem; font-weight:600; }}
[data-testid="stExpander"] {{ border:1px solid var(--line); border-radius:12px; }}

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
        font=dict(family="Inter, sans-serif", size=12, color=INK_SOFT),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=SERIES_PAL,
        margin=dict(l=8, r=70, t=8, b=40),
        hoverlabel=dict(bgcolor=WHITE, bordercolor=LINE,
                        font=dict(family="Inter, sans-serif", size=12, color=INK)),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="left", x=0,
                    font=dict(size=11, color=INK_SOFT), bgcolor="rgba(0,0,0,0)",
                    itemwidth=30),
        xaxis=dict(showgrid=False, showline=True, linecolor=LINE, linewidth=1,
                   ticks="outside", tickcolor=LINE, ticklen=4,
                   tickfont=dict(size=10.5, color=MUTED)),
        yaxis=dict(showgrid=True, gridcolor="#EDF1F6", griddash="dot",
                   zeroline=True, zerolinecolor="#CBD5E1", zerolinewidth=1.2,
                   tickfont=dict(size=10.5, color=MUTED)),
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
    return {yr: round(sum(vs)/len(vs), 2)
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
    ys = [v for _, v in pts if v is not None]
    return xs, ys

def end_label(fig, xs, ys, color, fmt="{:+.1f}%"):
    """Serinin son noktasına işaretçi + değer etiketi koyar."""
    if not xs: return
    fig.add_trace(go.Scatter(
        x=[xs[-1]], y=[ys[-1]], mode="markers+text",
        marker=dict(color=color, size=8, line=dict(color=WHITE, width=1.5)),
        text=[fmt.format(ys[-1])], textposition="middle right",
        textfont=dict(size=11.5, color=color, family="Inter"),
        showlegend=False, hoverinfo="skip", cliponaxis=False,
    ))

def fmt_val(v, suffix="%", signed=True):
    if v is None: return "—"
    if suffix == "%":
        return f"{v:+.1f}%" if signed else f"{v:.1f}%"
    return f"{v:.1f}{suffix}"

def first_series(fig_dict):
    if not fig_dict: return None
    return next(iter(fig_dict.values()), None)

def spark_svg(series, color, w=120, h=26, n=24):
    """KPI kartı içi mini eğri (son n ay)."""
    if not series: return ""
    ys = [v for _, v in sorted(series.items())[-n:] if v is not None]
    if len(ys) < 3: return ""
    mn, mx = min(ys), max(ys)
    rng = (mx - mn) or 1
    step = w / (len(ys) - 1)
    pts = " ".join(f"{i*step:.1f},{h - (y-mn)/rng*(h-6) - 3:.1f}" for i, y in enumerate(ys))
    lx, ly = (len(ys)-1)*step, h - (ys[-1]-mn)/rng*(h-6) - 3
    return (f'<svg width="{w}" height="{h}" style="display:block;margin-top:.45rem">'
            f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.6" '
            f'stroke-linejoin="round" stroke-linecap="round" opacity=".8"/>'
            f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.4" fill="{color}"/></svg>')

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
        <span class="side-pill">7 set</span></div>
    </div>""", unsafe_allow_html=True)
    if st.button("🔄 Önbelleği Yenile", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()

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
    try:
        from iso_data import sector_iso
        f8 = sector_iso(nace)
    except Exception:
        f8 = None

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

cols = st.columns(6)
kpi_card(cols[0], "Üretim", fmt_val(prod_val), f"YoY · {tr_per(prod_per)}",
         tone=tone_of(prod_val), badge=fmt_val(prod_val) if prod_val is not None else None,
         icon="🏭", spark=spark_svg(first_series(f1), _tone_color(tone_of(prod_val))))
kpi_card(cols[1], "İhracat", fmt_val(ih_val), f"Miktar · {tr_per(ih_per)}",
         tone=tone_of(ih_val), badge=fmt_val(ih_val) if ih_val is not None else None,
         icon="🌍", spark=spark_svg(first_series(ih_series), _tone_color(tone_of(ih_val))))
kpi_card(cols[2], "İthalat", fmt_val(it_val), f"Miktar · {tr_per(it_per)}",
         tone=tone_of(it_val), badge=fmt_val(it_val) if it_val is not None else None,
         icon="📦", spark=spark_svg(first_series(it_series), _tone_color(tone_of(it_val))))
kpi_card(cols[3], "Ciro", fmt_val(ciro_val), f"YoY · {tr_per(ciro_per)}",
         tone=tone_of(ciro_val), badge=fmt_val(ciro_val) if ciro_val is not None else None,
         icon="📈", spark=spark_svg(first_series(f6), _tone_color(tone_of(ciro_val))))
kpi_card(cols[4], "KKO", fmt_val(kko_val, suffix="%", signed=False),
         f"Kapasite · {tr_per(kko_per)}", tone=None, icon="⚙️",
         spark=spark_svg(first_series({k: (dict(v) if not isinstance(v, dict) else v)
                                       for k, v in kko_sec.items()}), BRAND))
kpi_card(cols[5], "ÜFE", fmt_val(ufe_val), f"Yıllık · {tr_per(ufe_per)}",
         tone="neg" if (ufe_val or 0) > 20 else "pos",
         badge=fmt_val(ufe_val) if ufe_val is not None else None, icon="💰",
         spark=spark_svg(first_series(f5), _tone_color("neg" if (ufe_val or 0) > 20 else "pos")))

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  SEKMELER
# ════════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📌  Genel Bakış",
    "🏭  Üretim", "🔍  Alt Kırılımlar", "🌍  Dış Ticaret",
    "⚙️  Kapasite", "💰  Enflasyon", "📈  Ciro", "👥  İstihdam",
    "🏆  İSO 500", "📰  Haber & Risk",
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

def _clamp_score(v, lo, hi):
    if v is None: return None
    return max(0.0, min(100.0, (v - lo) / (hi - lo) * 100.0))

with tabs[0]:
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
        # ── Sektör Sağlık Skoru ──
        sec_title("Sektör Sağlık Skoru", "6 göstergenin bileşik puanı (0–100)")

        imalat_kko = {k: v for k, v in f4.items() if "anayii" in k}
        imalat_kko_val, _ = last_val({k: (dict(v) if not isinstance(v, dict) else v)
                                      for k, v in imalat_kko.items()})
        ufe_imalat_series = {k: v for k, v in f5.items()
                             if " c " in (" " + k.lower() + " ")}
        ufe_imalat_val, _ = last_val(ufe_imalat_series)
        emp_val, _ = last_val(f7)

        comp = {
            "Üretim":   _clamp_score(prod_val, -15, 15),
            "İhracat":  _clamp_score(ih_val, -20, 20),
            "Ciro":     _clamp_score(ciro_val, -25, 40),
            "İstihdam": _clamp_score(emp_val, -10, 10),
            "KKO farkı": _clamp_score(
                (kko_val - imalat_kko_val) if (kko_val is not None and imalat_kko_val is not None) else None,
                -10, 10),
            "Maliyet (ÜFE)": _clamp_score(
                (ufe_imalat_val - ufe_val) if (ufe_val is not None and ufe_imalat_val is not None) else None,
                -15, 15),
        }
        comp_ok = {k: v for k, v in comp.items() if v is not None}
        score = round(sum(comp_ok.values()) / len(comp_ok)) if comp_ok else None

        if score is not None:
            g_col = POS if score >= 60 else AMBER if score >= 40 else NEG
            fig_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number=dict(font=dict(size=44, color=g_col, family="Inter"),
                            suffix="<span style='font-size:.45em;color:#64748B'> /100</span>"),
                gauge=dict(
                    axis=dict(range=[0, 100], tickwidth=0,
                              tickfont=dict(size=9, color=MUTED)),
                    bar=dict(color=g_col, thickness=0.28),
                    bgcolor="#F1F5F9",
                    borderwidth=0,
                    steps=[dict(range=[0, 40],  color="#FEE2E2"),
                           dict(range=[40, 60], color="#FEF3C7"),
                           dict(range=[60, 100], color="#D1FAE5")],
                ),
            ))
            fig_g.update_layout(**LAYOUT, height=210,
                                margin=dict(l=24, r=24, t=18, b=6))
            st.plotly_chart(fig_g, use_container_width=True, config=NOBAR)

            # Bileşen çubukları
            fig_c = go.Figure()
            c_names = list(comp_ok.keys())[::-1]
            c_vals  = [comp_ok[k] for k in c_names]
            fig_c.add_trace(go.Bar(
                y=c_names, x=c_vals, orientation="h",
                marker_color=[POS if v >= 60 else AMBER if v >= 40 else NEG for v in c_vals],
                marker_line_width=0, marker=dict(cornerradius=3),
                text=[f"{v:.0f}" for v in c_vals],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=10, family="Inter"),
                hovertemplate="%{y}: <b>%{x:.0f}/100</b><extra></extra>",
                width=0.55,
            ))
            fig_c.update_layout(**LAYOUT, height=200, showlegend=False,
                                hovermode="closest",
                                margin=dict(l=8, r=34, t=4, b=20))
            fig_c.update_xaxes(range=[0, 112], showticklabels=False, showline=False)
            fig_c.update_yaxes(showgrid=False, tickfont=dict(size=10.5, color=INK_SOFT))
            st.plotly_chart(fig_c, use_container_width=True, config=NOBAR)
            source("Skor: gösterge değerleri sektörel bantlara göre 0–100'e ölçeklenip ortalanır")
        else:
            st.info("Skor için yeterli veri yok.")

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
            fig.update_layout(**LAYOUT, height=330, bargap=0.3, showlegend=False,
                              margin=dict(l=8, r=8, t=24, b=36))
            fig.update_yaxes(visible=False)
            fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        with c2:
            cmp_sub = f" · kıyas: {compare_nace}" if compare_nace else ""
            chart_head("Aylık Seyir", f"Son {ay_sayisi} ay · YoY %{cmp_sub}")
            fig2 = go.Figure()
            for i, (lbl, s) in enumerate(f1.items()):
                xs, ys = series_xy(s, ay_sayisi)
                col = SERIES_PAL[i % len(SERIES_PAL)]
                disp = lbl if nace == TOTAL_MANUFACTURING else f"{lbl.lstrip('C')} · {short_name(lbl, 30)}"
                fig2.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines", name=disp,
                    line=dict(color=col, width=2, shape="spline", smoothing=.8),
                    hovertemplate="<b>%{y:.1f}%</b><extra>" + disp[:26] + "</extra>"))
                end_label(fig2, xs, ys, col)

            if compare_nace:
                f1_cmp = build_sekil1(compare_nace, cache["alt_c"], ana_c_series=_ana_c)
                if f1_cmp:
                    merged_c = {}
                    for _, s in f1_cmp.items():
                        for p, v in s.items():
                            if v is not None: merged_c.setdefault(p, []).append(v)
                    cmp_avg = {p: sum(vs)/len(vs) for p, vs in merged_c.items()}
                    xs_c, ys_c = series_xy(cmp_avg, ay_sayisi)
                    cmp_name = SECTOR_NAMES.get(compare_nace, compare_nace)
                    fig2.add_trace(go.Scatter(
                        x=xs_c, y=ys_c, mode="lines",
                        name=f"⚖ {compare_nace} · {short_name(compare_nace, 26)}",
                        line=dict(color=INK_SOFT, width=2.2, dash="dash", shape="spline", smoothing=.8),
                        hovertemplate="<b>%{y:.1f}%</b><extra>Kıyas: " + short_name(compare_nace, 22) + "</extra>"))
                    end_label(fig2, xs_c, ys_c, INK_SOFT)

            fig2.update_layout(**LAYOUT, height=330,
                               legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=10.5)))
            fig2.update_xaxes(dtick=6)
            fig2.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig2, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Sanayi Üretim Endeksi [2021=100], mevsim ve takvim etkisinden arındırılmış" +
              (" · kesikli çizgi: karşılaştırma sektörü" if compare_nace else ""))
    else:
        st.info("Bu sektör için üretim endeksi alt grup verisi bulunamadı.")

# ── TAB 2: ALT KIRILIMLAR ────────────────────────────────────────────────────────
with tabs[2]:
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

# ── TAB 3: DIŞ TİCARET ───────────────────────────────────────────────────────────
with tabs[3]:
    sec_title("Dış Ticaret",
              f"Miktar endeksi, önceki yıla göre değişim (%) · SITC bölüm {SITC_MAP.get(nace, 'T')}")
    if f3:
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            chart_head("Aylık Seyir", f"Son {ay_sayisi} ay")
            fig = go.Figure()
            for lbl, s in f3.items():
                is_exp = "hracat" in lbl and "thalat" not in lbl
                xs, ys = series_xy(s, ay_sayisi)
                col = TRADE_EXP if is_exp else TRADE_IMP
                fig.add_trace(go.Scatter(
                    x=xs, y=ys, mode="lines", name="İhracat" if is_exp else "İthalat",
                    line=dict(color=col, width=2.4 if is_exp else 1.8,
                              shape="spline", smoothing=.8,
                              dash="solid" if is_exp else "solid"),
                    fill="tozeroy",
                    fillcolor="rgba(29,78,216,.06)" if is_exp else "rgba(148,163,184,.08)",
                    hovertemplate="<b>%{y:+.1f}%</b><extra>" + ("İhracat" if is_exp else "İthalat") + "</extra>"))
                end_label(fig, xs, ys, col)
            fig.update_layout(**LAYOUT, height=360)
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
            fig2.update_layout(**LAYOUT, barmode="group", height=360, bargap=0.25,
                               margin=dict(l=8, r=44, t=8, b=36))
            fig2.update_xaxes(ticksuffix="%")
            fig2.update_yaxes(showgrid=False, autorange="reversed")
            fig2.add_vline(x=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig2, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Dış Ticaret Miktar Endeksi, mevsim ve takvim etkisinden arındırılmış")
    else:
        st.info("Bu sektör için dış ticaret verisi bulunamadı.")

# ── TAB 4: KAPASİTE ──────────────────────────────────────────────────────────────
with tabs[4]:
    sec_title("Kapasite Kullanım Oranı", "TCMB imalat sanayi KKO · sektör vs. imalat geneli (%)")
    if f4:
        all_v = [v for s in f4.values()
                 for v in (dict(s) if not isinstance(s, dict) else s).values() if v is not None]
        lo = min(all_v) - 3 if all_v else 50
        hi = max(all_v) + 3 if all_v else 90

        fig = go.Figure()
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
            end_label(fig, xs, ys, col, fmt="{:.1f}%")
        fig.update_layout(**LAYOUT, height=400)
        fig.update_xaxes(dtick=6)
        fig.update_yaxes(ticksuffix="%", range=[lo, hi], zeroline=False)
        st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        source("Kaynak: TCMB EVDS — İmalat Sanayi Kapasite Kullanım Oranı (NACE Rev.2)")
    else:
        st.info("KKO verisi bulunamadı.")

# ── TAB 5: ENFLASYON / ÜFE ───────────────────────────────────────────────────────
with tabs[5]:
    sec_title("Üretici Fiyat Endeksi (ÜFE)", "Yıllık değişim (%) · sektör maliyet baskısı")
    if f5:
        def ufe_label(lbl):
            m = re.search(r'UFE\s+(\S+)\s+Yillik', lbl)
            code = m.group(1) if m else ""
            if code == "C": return "İmalat Geneli"
            return f"{code.lstrip('C')} · {short_name(code, 30)}" if code else lbl[:30]

        fig = go.Figure()
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
            end_label(fig, xs, ys, col, fmt="{:.1f}%")
        fig.update_layout(**LAYOUT, height=400,
                          legend=dict(orientation="h", y=-0.2, x=0, font=dict(size=10.5)))
        fig.update_xaxes(dtick=6)
        fig.update_yaxes(ticksuffix="%")
        fig.add_hline(y=0, line_width=1, line_color="#CBD5E1")
        st.plotly_chart(fig, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Yurt İçi Üretici Fiyat Endeksi (Yİ-ÜFE)")
    else:
        st.info("ÜFE verisi bulunamadı.")

# ── TAB 6: CİRO ──────────────────────────────────────────────────────────────────
with tabs[6]:
    sec_title("Ciro Endeksi", "Önceki yıla göre değişim (%) · nominal, mevsim etkisinden arındırılmış")
    if f6:
        c1, c2 = st.columns([3, 2], gap="large")
        with c1:
            chart_head("Aylık Seyir", f"Son {ay_sayisi} ay")
            fig = go.Figure()
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
                end_label(fig, xs, ys, col)
            fig.update_layout(**LAYOUT, height=360)
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
            fig2.update_layout(**LAYOUT, barmode="group", height=360, bargap=0.3,
                               margin=dict(l=8, r=8, t=24, b=36))
            fig2.update_yaxes(visible=False)
            fig2.add_hline(y=0, line_width=1, line_color="#CBD5E1")
            st.plotly_chart(fig2, use_container_width=True, config=NOBAR)
        source("Kaynak: TÜİK — Ciro Endeksleri [2021=100], mevsim ve takvim etkisinden arındırılmış")
    else:
        st.info("Ciro verisi için 'python cache_all.py' çalıştırın.")

# ── TAB 7: İSTİHDAM ──────────────────────────────────────────────────────────────
with tabs[7]:
    sec_title("Ücretli Çalışan Sayısı", "İstihdam, önceki yıla göre değişim (%)")
    if f7:
        fig = go.Figure()
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
            end_label(fig, xs, ys, col)
        fig.update_layout(**LAYOUT, height=400)
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

# ── TAB 8: İSO 500 ───────────────────────────────────────────────────────────────
with tabs[8]:
    if f8:
        yil8 = f8["yil"]
        sec_title(f"İSO 500 & İkinci 500'de {sector_tr}",
                  f"Türkiye'nin en büyük sanayi kuruluşları içindeki sektör fotoğrafı · {yil8}")

        # ── KPI satırı ──
        ic = st.columns(5)
        kpi_card(ic[0], "Listedeki Firma", f"{f8['firma_sayisi']}",
                 f"İSO 500: {f8['firma_500']} · İkinci 500: {f8['firma_2_500']}",
                 icon="🏢")
        kpi_card(ic[1], "Üretimden Satışlar", f"₺{f8['toplam_uretim_satis']/1e9:,.0f} mlr".replace(",", "."),
                 f"{yil8} toplamı" + (f" · pay %{f8['pay_uretim']:.1f}"
                                      if f8.get('pay_uretim') and nace != TOTAL_MANUFACTURING else ""),
                 icon="💼")
        kpi_card(ic[2], "İhracat", f"${f8['toplam_ihracat_musd']:,.0f} mn".replace(",", "."),
                 f"{yil8} · beyan eden firmalar", icon="🌍")
        kpi_card(ic[3], "İstihdam", f"{f8['toplam_calisan']:,.0f}".replace(",", "."),
                 "ücretli çalışan ort.", icon="👥")
        marj = f8.get("favok_marj_med")
        kpi_card(ic[4], "FAVÖK Marjı (medyan)",
                 f"%{marj:.1f}" if marj is not None else "—",
                 "beyan eden firmalar", icon="📐",
                 tone="pos" if (marj or 0) >= 10 else None)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        il_l, il_r = st.columns([5, 4], gap="large")

        # ── Top 15 firma ──
        with il_l:
            chart_head(f"En Büyük 15 Kuruluş", f"Üretimden satışlar, milyar ₺ · {yil8}")
            fdf = f8["firmalar"].head(15).iloc[::-1]
            bar_c = [BRAND if l == "İSO 500" else "#93C5FD" for l in fdf["liste"]]
            fig_i = go.Figure()
            fig_i.add_trace(go.Bar(
                y=[n[:36] + ("…" if len(n) > 36 else "") for n in fdf["firma"]],
                x=fdf["uretim_satis"] / 1e9,
                orientation="h", marker_color=bar_c, marker_line_width=0,
                marker=dict(cornerradius=3),
                text=[f"{v/1e9:,.1f}".replace(",", ".") for v in fdf["uretim_satis"]],
                textposition="outside", cliponaxis=False,
                textfont=dict(size=10, family="Inter"),
                customdata=[[il, f"{e:,.0f}" if pd.notna(e) else "—",
                             f"{int(c):,}".replace(",", ".") if pd.notna(c) else "—"]
                            for il, e, c in zip(fdf["il"], fdf["ihracat_musd"], fdf["calisan"])],
                hovertemplate="<b>%{y}</b><br>Satış: ₺%{x:.1f} mlr<br>"
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
            y500 = [r for r in f8["yearly"] if r["liste"] == "İSO 500"]
            if len(y500) >= 2:
                chart_head("İSO 500'de Sektör Trendi", "Üretimden satışlar (nominal) ve firma sayısı")
                fig_t = go.Figure()
                fig_t.add_trace(go.Bar(
                    x=[str(r["yil"]) for r in y500],
                    y=[r["uretim_satis"] / 1e9 for r in y500],
                    marker_color=[TRADE_IMP, BRAND][-len(y500):],
                    marker_line_width=0, marker=dict(cornerradius=4),
                    text=[f"₺{r['uretim_satis']/1e9:,.0f} mlr<br>{r['firma']} firma".replace(",", ".")
                          for r in y500],
                    textposition="inside",
                    textfont=dict(size=11, color="white", family="Inter"),
                    hovertemplate="%{x}: <b>₺%{y:.0f} mlr</b><extra></extra>",
                    width=0.5,
                ))
                fig_t.update_layout(**LAYOUT, height=240, showlegend=False,
                                    margin=dict(l=8, r=8, t=8, b=32))
                fig_t.update_yaxes(visible=False)
                st.plotly_chart(fig_t, use_container_width=True, config=NOBAR)
                if f8.get("yoy") and f8["yoy"].get("uretim_satis") is not None:
                    y = f8["yoy"]
                    ihr_txt = (f" · İhracat %{y['ihracat']:+.1f}"
                               if y.get("ihracat") is not None else "")
                    st.markdown(
                        f'<div class="src">{y["donem"]}: satışlar nominal '
                        f'%{y["uretim_satis"]:+.1f}{ihr_txt} · '
                        f'firma sayısı {y["firma"]:+d}</div>', unsafe_allow_html=True)

            # ── İl dağılımı ──
            if f8.get("iller"):
                chart_head("Coğrafi Yoğunlaşma", "Firma sayısına göre ilk iller")
                ils = f8["iller"][::-1]
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

        # ── Tam firma tablosu ──
        with st.expander(f"📋 Tüm sektör firmaları ({f8['firma_sayisi']})"):
            tdf = f8["firmalar"].copy()
            tdf["Satış (mlr ₺)"] = (tdf["uretim_satis"] / 1e9).round(2)
            tdf["İhracat (mn $)"] = tdf["ihracat_musd"].round(1)
            tdf["FAVÖK %"] = tdf["favok_marj"].round(1)
            tdf = tdf.rename(columns={"sira": "Sıra", "liste": "Liste",
                                      "firma": "Kuruluş", "il": "İl",
                                      "calisan": "Çalışan"})
            st.dataframe(
                tdf[["Sıra", "Liste", "Kuruluş", "İl", "Satış (mlr ₺)",
                     "İhracat (mn $)", "Çalışan", "FAVÖK %"]].set_index("Sıra"),
                use_container_width=True, height=420)

        _nace_etiketi = "tüm imalat sanayii (C10–C33)" if nace == TOTAL_MANUFACTURING else f"NACE {nace.lstrip('C')}"
        source(f"Kaynak: İstanbul Sanayi Odası — Türkiye'nin 500 Büyük Sanayi Kuruluşu "
               f"ve İkinci 500 · {_nace_etiketi} eşleşmesi")
    else:
        st.info("Bu sektörde İSO 500 / İkinci 500 listesine giren kuruluş bulunmuyor "
                "veya İSO kaynak dosyaları okunamadı.")

# ── TAB 9: HABER & RİSK ──────────────────────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def get_news(nace_code, query_override=""):
    from news_analysis import fetch_sector_news
    try:
        return fetch_sector_news(nace_code, query_override=query_override or None)
    except Exception:
        return []

with tabs[9]:
    sec_title(f"Haber Akışı & Risk Analizi",
              f"{sector_tr} · Google News taraması + yapay zekâ sentezi")
    if news_query.strip():
        st.caption(f"🔍 Özel arama terimi kullanılıyor: **{news_query.strip()}**")

    news_items = get_news(nace, news_query)

    nl, nr = st.columns([2, 3], gap="large")

    with nl:
        chart_head("Güncel Haber Akışı", f"{len(news_items)} başlık · son 30 gün ağırlıklı")
        if news_items:
            news_html = ""
            for it in news_items:
                news_html += f"""
                <div style="padding:.55rem 0;border-bottom:1px solid {LINE};">
                  <a href="{it['link']}" target="_blank" style="font-size:.83rem;font-weight:600;
                     color:{INK};text-decoration:none;line-height:1.4;">{it['title']}</a>
                  <div style="font-size:.7rem;color:{MUTED};font-weight:500;margin-top:.15rem;">
                    {it['source']} · {it['date']}</div>
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

# ════════════════════════════════════════════════════════════════════════════════
#  OTOMATİK RAPOR
# ════════════════════════════════════════════════════════════════════════════════
st.divider()
sec_title(f"Otomatik Rapor", f"{sector_tr} · yapay zekâ destekli sektörel değerlendirme")

cb, co = st.columns([1, 3])
with co:
    _ = st.radio("stil", ["Kısa Özet", "Detaylı Analiz"], horizontal=True,
                 label_visibility="collapsed")
with cb:
    uret = st.button("✨ Rapor Üret", use_container_width=True)

if uret:
    from sector_analysis import generate_analysis
    with st.spinner("Yapay zekâ analizi hazırlanıyor (30–90 sn)…"):
        try:
            analysis = generate_analysis(nace, f1, f2, f3, f4, f5, iso_agg=f8)
            st.session_state["rapor_text"] = analysis
            st.session_state["rapor_nace"] = nace
        except Exception as e:
            st.error(f"Analiz hatası: {e}")

if "rapor_text" in st.session_state and st.session_state.get("rapor_nace") == nace:
    analysis = st.session_state["rapor_text"]
    from report_word import parse_llm_sections, bullets_from_text
    secs = parse_llm_sections(analysis)
    labels = {
        "GIRIS": "Genel Değerlendirme", "SEKIL1": "Üretim Endeksi",
        "SEKIL2": "Alt Kırılımlar", "SEKIL3": "Dış Ticaret",
        "SEKIL4": "Kapasite Kullanımı", "SEKIL5": "ÜFE · Maliyet",
        "SEKIL6": "İSO 500 · Kurumsal Görünüm",
    }
    html = ""
    for tag, tl in labels.items():
        text = secs.get(tag, "")
        if not text: continue
        if tag == "GIRIS":
            html += f'<div class="r-head">{tl}</div>{text.replace(chr(10), "<br>")}'
        else:
            items = "".join(f"<li>{b}</li>" for b in bullets_from_text(text))
            html += f'<div class="r-head">{tl}</div><ul>{items}</ul>'
    st.markdown(f'<div class="report">{html}</div>', unsafe_allow_html=True)

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
                              out_dir=tmp, iso_agg=f8, news_analysis=news_txt)
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
  Önbellek: {cache_date}<span class="sep">·</span>7 veri seti · 24 sektör · 1260 NACE kodu
</div>
""", unsafe_allow_html=True)
