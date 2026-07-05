# -*- coding: utf-8 -*-
"""
Word raporu grafik motoru — modern tasarim dili.

Tasarim sistemi (dashboard ile ortak):
  BRAND   #2563EB  canli mavi (sektor / son yil)
  NAVY    #1E3A5F  derin lacivert
  MUTED   #64748B  kiyas serileri (imalat geneli)
  POS     #059669  buyume     NEG #DC2626  daralma
  Grid: noktali #E2E8F0 · Fontlar: Arial · Etiketler: uc nokta + bold deger
"""
import os, pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np

# ─── TASARIM SABITLERI (örnek Borsan raporu paleti) ──────────────────────────
BRAND    = '#0070C0'   # örnek belgedeki ana mavi (çizgi/çubuk)
BRAND_DK = '#002060'   # koyu lacivert (ihracat)
NAVY     = '#002060'
SKY      = '#0070C0'
TEAL     = '#00538F'
AMBER    = '#8895B6'
POS      = '#00538F'
NEG      = '#C00000'
INK      = '#000000'
INK_SOFT = '#333333'
MUTED    = '#595959'
LINE_CLR = '#D9D9D9'
GRID_CLR = '#E7E6E6'

# Çok serili gerektiğinde: mavi tonları + gri
SERIES_PAL = ['#0070C0', '#002060', '#8895B6', '#00538F', '#5B9BD5', '#7F7F7F', '#333333']
# Yillik bar gradyani: gecmis soluk gri → son yil mavi (örnek belge tarzı)
BAR_FADE   = ['#BFBFBF', '#A6A6A6', '#7F9FBF', BRAND]
TRADE_EXP  = '#002060'   # İhracat — koyu lacivert
TRADE_IMP  = '#8895B6'   # İthalat — gri-mavi

FONT     = 'Arial'
LABEL_PT = 8
TICK_PT  = 7.5

plt.rcParams.update({
    'font.family':        FONT,
    'font.size':          TICK_PT,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.spines.left':   False,
    'axes.spines.bottom': True,
    'axes.edgecolor':     LINE_CLR,
    'axes.linewidth':     0.8,
    'axes.grid':          False,
    'xtick.color':        MUTED,
    'ytick.color':        MUTED,
    'xtick.labelsize':    TICK_PT,
    'ytick.labelsize':    TICK_PT,
    'xtick.major.size':   0,
    'ytick.major.size':   0,
    'legend.fontsize':    7,
    'legend.frameon':     False,
    'figure.dpi':         170,
})

TR_MONTHS = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz',
             'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']

# ─── NACE ISIMLERI (cache'ten) ────────────────────────────────────────────────
_NAMES = None
def nace_name(code):
    global _NAMES
    if _NAMES is None:
        try:
            cf = os.path.join(os.path.dirname(__file__), 'data_cache.pkl')
            with open(cf, 'rb') as f:
                _NAMES = pickle.load(f).get('nace_names', {})
        except Exception:
            _NAMES = {}
    return _NAMES.get(code, code)

def short_name(code, n=36):
    s = nace_name(code)
    return s if len(s) <= n else s[:n-1].rstrip() + '…'

def _tr_month_label(period_str):
    try:
        yr, mo = period_str.split('-')
        return f'{TR_MONTHS[int(mo)-1]} {yr[2:]}'
    except Exception:
        return period_str

def _annual_avg(series_dict, min_months=6):
    by_year = {}
    for p, v in series_dict.items():
        if v is None: continue
        by_year.setdefault(p.split('-')[0], []).append(v)
    return {yr: round(sum(vs)/len(vs), 2)
            for yr, vs in sorted(by_year.items())
            if len(vs) >= min_months or yr == max(by_year)}

def _figax(w=6.3, h=2.6):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    return fig, ax

def _save(fig, ax, path):
    plt.tight_layout(pad=0.35)
    plt.savefig(path, bbox_inches='tight', facecolor='white', dpi=170)
    plt.close()

def _hgrid(ax):
    """Yatay noktali izgara (cizgi grafikler icin)."""
    ax.grid(axis='y', color=GRID_CLR, linewidth=0.7, linestyle=(0, (1, 3)), zorder=0)
    ax.set_axisbelow(True)

# ═══════════════════════════════════════════════════════════════════════════════
# ŞEKİL 1 — Üretim: yıllık çubuk (soluk geçmiş → marka mavisi son yıl)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_sekil1(data_dict, out_path):
    if not data_dict:
        return
    if len(data_dict) == 1:
        raw = next(iter(data_dict.values()))
    else:
        all_periods = sorted({p for d in data_dict.values() for p in d})
        raw = {}
        for p in all_periods:
            vals = [d[p] for d in data_dict.values() if p in d and d[p] is not None]
            if vals: raw[p] = sum(vals) / len(vals)

    annual = _annual_avg(raw)
    if not annual: return

    years, vals = list(annual.keys()), list(annual.values())
    n = len(years)
    colors = ['#B7C3D7'] * n
    if n >= 3: colors[-3] = '#8FA8CF'
    if n >= 2: colors[-2] = '#5C85D6'
    if n >= 1: colors[-1] = BRAND

    fig, ax = _figax(w=6.0, h=2.5)
    bars = ax.bar(range(n), vals, color=colors, width=0.56, zorder=3)
    ax.axhline(0, color='#CBD5E1', linewidth=0.9, zorder=4)

    for patch, v, c in zip(bars, vals, colors):
        x = patch.get_x() + patch.get_width() / 2
        y = patch.get_height()
        va = 'bottom' if y >= 0 else 'top'
        off = max(abs(max(vals) - min(vals)) * 0.03, 0.25)
        ax.text(x, y + (off if y >= 0 else -off), f'{v:+.1f}%',
                ha='center', va=va, fontsize=LABEL_PT,
                color=INK if c == BRAND else INK_SOFT,
                fontweight='bold' if c == BRAND else 'normal')

    ax.yaxis.set_visible(False)
    ax.set_xticks(range(n))
    ax.set_xticklabels(years, fontsize=TICK_PT, color=MUTED)
    ax.set_xlim(-0.55, n - 0.45)
    rng = max(vals) - min(vals) or 1
    ax.set_ylim(min(min(vals), 0) - rng * 0.18, max(max(vals), 0) + rng * 0.22)
    _save(fig, ax, out_path)

# ═══════════════════════════════════════════════════════════════════════════════
# ŞEKİL 2 — Alt kırılımlar: son yıl sıralı YATAY çubuk, gerçek isimler, +yeşil/−kırmızı
# ═══════════════════════════════════════════════════════════════════════════════
def chart_sekil2(data_dict, out_path):
    if not data_dict:
        return
    sectors = sorted(data_dict.keys())
    annual_by = {s: _annual_avg(data_dict[s]) for s in sectors}
    all_years = sorted({yr for a in annual_by.values() for yr in a})
    if not all_years: return
    latest = all_years[-1]
    prev   = all_years[-2] if len(all_years) >= 2 else None

    order = sorted(sectors,
                   key=lambda s: annual_by[s].get(latest) if annual_by[s].get(latest) is not None else -999)
    vals  = [annual_by[s].get(latest) or 0 for s in order]
    prevs = [annual_by[s].get(prev) if prev else None for s in order]
    names = [f"{s.lstrip('C')} · {short_name(s, 34)}" for s in order]
    cols  = [POS if v >= 0 else NEG for v in vals]

    h = max(2.2, 0.42 * len(order) + 0.7)
    fig, ax = _figax(w=6.3, h=h)

    bars = ax.barh(range(len(order)), vals, height=0.5, color=cols, zorder=3)

    # Onceki yil: ince dikey tick isareti (kiyas noktasi)
    if prev:
        for i, pv in enumerate(prevs):
            if pv is None: continue
            ax.plot([pv], [i], marker='|', markersize=13,
                    markeredgewidth=1.8, color='#64748B', zorder=4)

    vmax = max((abs(v) for v in vals), default=1)
    for i, (b, v) in enumerate(zip(bars, vals)):
        off = vmax * 0.04 + 0.2
        ha = 'left' if v >= 0 else 'right'
        ax.text(v + (off if v >= 0 else -off), i, f'{v:+.1f}%',
                ha=ha, va='center', fontsize=LABEL_PT, color=cols[i], fontweight='bold')

    ax.axvline(0, color='#CBD5E1', linewidth=0.9, zorder=2)
    ax.xaxis.set_visible(False)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(names, fontsize=TICK_PT, color=INK_SOFT)
    ax.set_ylim(-0.6, len(order) - 0.4)
    allx = vals + [p for p in prevs if p is not None]
    pad = (max(abs(v) for v in allx) if allx else 1) * 0.28 + 1
    ax.set_xlim(min(min(allx), 0) - pad, max(max(allx), 0) + pad)

    handles = [mpatches.Patch(color=POS, label=f'{latest} büyüme'),
               mpatches.Patch(color=NEG, label=f'{latest} daralma')]
    if prev:
        handles.append(Line2D([0], [0], marker='|', color='#64748B',
                              linestyle='none', markersize=9,
                              markeredgewidth=1.8, label=f'{prev} ortalaması'))
    ax.legend(handles=handles, loc='lower right', fontsize=6.5,
              frameon=False, handlelength=1.1)
    _save(fig, ax, out_path)

# ═══════════════════════════════════════════════════════════════════════════════
# ŞEKİL 3 — Dış ticaret: yıllık yatay gruplu çubuk (ihracat mavi / ithalat gri)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_sekil3(data_dict, out_path):
    if not data_dict:
        return
    annual = {lbl: _annual_avg(s) for lbl, s in data_dict.items()}
    all_years = sorted({yr for a in annual.values() for yr in a})[-6:]
    labels = list(data_dict.keys())
    n_l, n_y = len(labels), len(all_years)
    if n_y == 0: return

    def _col(lbl):
        if 'hracat' in lbl and 'thalat' not in lbl: return TRADE_EXP
        if 'thalat' in lbl: return TRADE_IMP
        return BRAND
    def _nm(lbl):
        return 'İhracat' if ('hracat' in lbl and 'thalat' not in lbl) else 'İthalat'

    fig, ax = _figax(w=5.9, h=2.7)
    bar_h  = 0.68 / n_l
    offs   = np.linspace(-(0.68 - bar_h) / 2, (0.68 - bar_h) / 2, n_l)

    all_vals = []
    for li, lbl in enumerate(labels):
        vals = [annual[lbl].get(yr) for yr in all_years]
        all_vals += [v for v in vals if v is not None]
        ys = [yi + offs[li] for yi in range(n_y)]
        pv = [v if v is not None else 0 for v in vals]
        bars = ax.barh(ys, pv, height=bar_h, color=_col(lbl), zorder=3, label=_nm(lbl))
        for b, v in zip(bars, vals):
            if v is None: continue
            x = b.get_width()
            off = (max(abs(min(pv)), abs(max(pv))) or 1) * 0.03 + 0.2
            ax.text(x + (off if x >= 0 else -off), b.get_y() + b.get_height()/2,
                    f'{v:+.1f}%', ha='left' if x >= 0 else 'right', va='center',
                    fontsize=7, color=_col(lbl), fontweight='bold')

    ax.axvline(0, color='#CBD5E1', linewidth=0.9, zorder=4)
    ax.xaxis.set_visible(False)
    ax.set_yticks(range(n_y))
    ax.set_yticklabels(all_years, fontsize=TICK_PT, color=MUTED)
    ax.set_ylim(-0.6, n_y - 0.4)
    ax.invert_yaxis()                      # en yeni yil ustte
    if all_vals:
        pad = max(abs(v) for v in all_vals) * 0.28 + 1.5
        ax.set_xlim(min(min(all_vals), 0) - pad, max(max(all_vals), 0) + pad)
    ax.legend(loc='lower right', fontsize=7, frameon=False)
    _save(fig, ax, out_path)

# ═══════════════════════════════════════════════════════════════════════════════
# ŞEKİL 4/5 — Çizgi: sektör=marka, kıyas=gri kesikli, uç nokta + bold değer
# ═══════════════════════════════════════════════════════════════════════════════
def _is_comparator(lbl):
    l = lbl.lower()
    return ('sanayii' in l or 'toplam' in l
            or (' c ' in f' {l} ' and 'yillik' in l))

def _pretty_label(lbl):
    """'UFE C131 Yillik %' → '131 · Tekstil elyafının hazırlanması…'"""
    import re as _re
    m = _re.match(r'UFE\s+(\S+)\s+Yillik', lbl)
    if m:
        code = m.group(1)
        if code == 'C':
            return 'İmalat Geneli'
        return f"{code.lstrip('C')} · {short_name(code, 24)}"
    if _is_comparator(lbl):
        return 'İmalat Geneli'
    return lbl[:32]

def chart_line(data_dict, out_path, smooth=True):
    if not data_dict:
        return
    all_periods = sorted({p for d in data_dict.values() for p in d})
    periods = all_periods[-48:]
    n = len(periods)
    if n == 0: return

    labels = list(data_dict.keys())
    styles, pi = [], 0
    for lbl in labels:
        if _is_comparator(lbl):
            styles.append((MUTED, 1.3, (0, (3, 2))))         # gri kesikli
        else:
            styles.append((SERIES_PAL[pi % len(SERIES_PAL)], 1.9, 'solid'))
            pi += 1

    fig, ax = _figax(w=6.3, h=2.6)
    _hgrid(ax)

    all_vals = [v for d in data_dict.values() for p, v in d.items()
                if p in periods and v is not None]

    ends = []   # (x_son, y_son, renk) — etiket çakışma önleme için
    for lbl, (color, lw, ls) in zip(labels, styles):
        raw = [data_dict[lbl].get(p) for p in periods]
        xi = [i for i, v in enumerate(raw) if v is not None]
        yi = [raw[i] for i in xi]
        if not xi: continue

        if smooth and len(xi) >= 4:
            try:
                from scipy.interpolate import make_interp_spline
                xnew = np.linspace(xi[0], xi[-1], 400)
                ynew = make_interp_spline(xi, yi, k=3)(xnew)
                ax.plot(xnew, ynew, color=color, linewidth=lw, linestyle=ls, zorder=3)
            except Exception:
                ax.plot(xi, yi, color=color, linewidth=lw, linestyle=ls, zorder=3)
        else:
            ax.plot(xi, yi, color=color, linewidth=lw, linestyle=ls, zorder=3)

        ends.append((xi[-1], yi[-1], color))

    # Uç işaretçiler + çakışmayan değer etiketleri
    if ends and all_vals:
        rng = (max(all_vals) - min(all_vals)) or 1
        min_gap = rng * 0.075
        order_i = sorted(range(len(ends)), key=lambda i: ends[i][1])
        adj = [ends[i][1] for i in order_i]
        for k in range(1, len(adj)):
            if adj[k] - adj[k-1] < min_gap:
                adj[k] = adj[k-1] + min_gap
        for k, i in enumerate(order_i):
            x, y, color = ends[i]
            ax.scatter([x], [y], s=22, color=color, zorder=5,
                       edgecolors='white', linewidths=1.2)
            ax.annotate(f'{y:.1f}', xy=(x, adj[k]),
                        xytext=(7, 0), textcoords='offset points',
                        fontsize=7.5, color=color, ha='left', va='center',
                        fontweight='bold')

    # Y aralığı: veriye sıkı (uç etiketler için pay)
    if all_vals:
        vmin, vmax = min(all_vals), max(all_vals)
        if ends:
            _tops = [ends[i][1] for i in range(len(ends))]
            vmax = max(vmax, max(_tops) + (vmax - vmin or 1) * 0.075 * len(ends))
        rng = (vmax - vmin) or 1
        ax.set_ylim(vmin - rng * 0.12, vmax + rng * 0.14)
        if vmin < 0 < vmax:
            ax.axhline(0, color='#CBD5E1', linewidth=0.7, zorder=2)

    step = max(1, n // 9)
    ticks = list(range(0, n, step))
    if (n - 1) not in ticks: ticks.append(n - 1)
    ax.set_xticks(ticks)
    ax.set_xticklabels([_tr_month_label(periods[i]) for i in ticks],
                       rotation=45, ha='right', fontsize=TICK_PT - 1, color=MUTED)
    ax.set_xlim(-0.5, n + 3.5)

    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', labelsize=TICK_PT - 1, colors=MUTED)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.0f'))

    handles = [Line2D([0], [0], color=c, linewidth=lw2,
                      linestyle=ls if isinstance(ls, str) else (0, (3, 2)),
                      label=_pretty_label(l))
               for (c, lw2, ls), l in zip(styles, labels)]
    ax.legend(handles=handles, loc='upper left', bbox_to_anchor=(0, 1.06),
              ncol=min(len(labels), 2), fontsize=6.5, frameon=False)
    _save(fig, ax, out_path)

# ═══════════════════════════════════════════════════════════════════════════════
# ŞEKİL 6 — İSO 500: Top 10 firma (üretimden satışlar, mlr TL)
# ═══════════════════════════════════════════════════════════════════════════════
def chart_iso_top10(iso_agg, out_path):
    """iso_agg: iso_data.sector_iso() çıktısı."""
    if not iso_agg or not iso_agg.get('top10'):
        return
    top = iso_agg['top10'][::-1]           # en büyük üstte (barh ters çizer)
    names = [t['firma'][:34] + ('…' if len(t['firma']) > 34 else '') for t in top]
    vals  = [(t['uretim_satis'] or 0) / 1e9 for t in top]
    cols  = [BRAND if t['liste'] == 'İSO 500' else '#93C5FD' for t in top]

    h = max(2.4, 0.34 * len(top) + 0.8)
    fig, ax = _figax(w=6.3, h=h)
    bars = ax.barh(range(len(top)), vals, height=0.55, color=cols, zorder=3)

    vmax = max(vals) if vals else 1
    for i, (b, t) in enumerate(zip(bars, top)):
        v = vals[i]
        extra = ''
        if t.get('ihracat_musd'):
            extra = f"  ·  {t['ihracat_musd']:.0f} mn$ ihr."
        ax.text(v + vmax * 0.015, i, f'{v:.1f}{extra}',
                ha='left', va='center', fontsize=7,
                color=INK_SOFT, fontweight='bold')

    ax.xaxis.set_visible(False)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(names, fontsize=TICK_PT, color=INK_SOFT)
    ax.set_ylim(-0.6, len(top) - 0.4)
    ax.set_xlim(0, vmax * 1.42)

    handles = [mpatches.Patch(color=BRAND, label='İSO 500'),
               mpatches.Patch(color='#93C5FD', label='İSO İkinci 500')]
    ax.legend(handles=handles, loc='lower right', fontsize=6.5, frameon=False)
    _save(fig, ax, out_path)

# ─── ANA FONKSIYON ────────────────────────────────────────────────────────────
def generate_all_charts(nace, fig1, fig2, fig3, fig4, fig5, tmpdir, iso_agg=None):
    charts = {}

    if iso_agg:
        p = os.path.join(tmpdir, 'sekil6.png')
        try:
            chart_iso_top10(iso_agg, p); charts['sekil6'] = p
        except Exception as e:
            print(f'   [chart] Sekil6 (ISO) hatasi: {e}')

    if fig1:
        p = os.path.join(tmpdir, 'sekil1.png')
        try:
            chart_sekil1(fig1, p); charts['sekil1'] = p
        except Exception as e:
            print(f'   [chart] Sekil1 hatasi: {e}')

    if fig2:
        p = os.path.join(tmpdir, 'sekil2.png')
        try:
            chart_sekil2(fig2, p); charts['sekil2'] = p
        except Exception as e:
            print(f'   [chart] Sekil2 hatasi: {e}')

    if fig3:
        p = os.path.join(tmpdir, 'sekil3.png')
        try:
            chart_sekil3(fig3, p); charts['sekil3'] = p
        except Exception as e:
            print(f'   [chart] Sekil3 hatasi: {e}')

    if fig4:
        fig4_norm = {lbl: (dict(v) if not isinstance(v, dict) else v)
                     for lbl, v in fig4.items()}
        p = os.path.join(tmpdir, 'sekil4.png')
        try:
            chart_line(fig4_norm, p, smooth=True); charts['sekil4'] = p
        except Exception as e:
            print(f'   [chart] Sekil4 hatasi: {e}')

    if fig5:
        p = os.path.join(tmpdir, 'sekil5.png')
        try:
            chart_line(fig5, p, smooth=False); charts['sekil5'] = p
        except Exception as e:
            print(f'   [chart] Sekil5 hatasi: {e}')

    return charts
