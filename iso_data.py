# -*- coding: utf-8 -*-
"""
İSO 500 / İSO İkinci 500 veri modülü.

Onbellek (iso_cache.pkl) repo ile birlikte gelir; asagidaki ham xlsx dosyalari
sadece onbellegi SIFIRDAN yeniden olusturmak icin gereklidir (build_iso_cache(force=True)).
Ham dosyalari 'iso_source/' klasorune koyup calistirin:
  2024 (3).xlsx : İSO 500, 2024
  2024 (2).xlsx : İSO İkinci 500, 2024
  2025.xlsx     : İSO 500, 2025

Kullanım:
  from iso_data import load_iso, sector_iso
  df   = load_iso()          # tidy DataFrame (tüm listeler)
  agg  = sector_iso('C13')   # sektörel özet sözlüğü
"""
import os, pickle, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

BASE = os.path.dirname(__file__)
ISO_CACHE = os.path.join(BASE, 'iso_cache.pkl')

_SRC_DIR = os.path.join(BASE, 'iso_source')
SOURCES = [
    (os.path.join(_SRC_DIR, '2024 (3).xlsx'),       'İSO 500',        2024),
    (os.path.join(_SRC_DIR, '2024 (2).xlsx'),       'İSO İkinci 500', 2024),
    (os.path.join(_SRC_DIR, '2025.xlsx'),           'İSO 500',        2025),
    (os.path.join(_SRC_DIR, '2025_ikinci500.xlsx'), 'İSO İkinci 500', 2025),
]

COLS = {
    'Genel Sıra No':                            'sira',
    'Genel Sıra No (Önceki Yıl)':               'sira_onceki',
    'Kuruluş Adı':                              'firma',
    'Üretimden Satışlar (Net) (TL)':            'uretim_satis',
    'Net Satışlar (TL)':                        'net_satis',
    'Brüt Katma Değer (TL)':                    'bkd',
    'Özkaynak (TL)':                            'ozkaynak',
    'Aktif Toplamı (TL)':                       'aktif',
    'Dönem Karı/Zararı (Vergi Öncesi) (TL)':    'kar',
    'FAVÖK (TL)':                               'favok',
    'İhracat (Bin $)':                          'ihracat_bin_usd',
    'Ücretle Çalışanlar Ortalaması (Kişi)':     'calisan',
    'Sermaye Payı / Yabancı':                   'pay_yabanci',
    'Sermaye Payı / Halka Açık':                'pay_halka',
    'NACE Kodu':                                'nace_raw',
    'NACE':                                     'nace_tanim',
    'İl':                                       'il',
}

NUM_COLS = ['uretim_satis', 'net_satis', 'bkd', 'ozkaynak', 'aktif',
            'kar', 'favok', 'ihracat_bin_usd', 'calisan',
            'pay_yabanci', 'pay_halka']


def _norm_nace(v):
    """13.0 → 'C13' | '32.1' → 'C32' | NaN → None"""
    try:
        n = int(float(v))
        return f'C{n}' if 10 <= n <= 33 else f'X{n}'
    except Exception:
        return None


def build_iso_cache(force=False):
    """Kaynak xlsx'leri okuyup tidy pickle üretir."""
    if os.path.exists(ISO_CACHE) and not force:
        return
    frames = []
    for path, liste, yil in SOURCES:
        if not os.path.exists(path):
            print(f'[iso] atlandi (yok): {path}')
            continue
        raw = pd.read_excel(path, sheet_name=0)
        df = raw[[c for c in COLS if c in raw.columns]].rename(columns=COLS)
        df['liste'] = liste
        df['yil']   = yil
        frames.append(df)
    if not frames:
        raise FileNotFoundError('Hicbir ISO kaynak dosyasi bulunamadi.')

    df = pd.concat(frames, ignore_index=True)
    df = df[df['firma'].notna()].copy()

    for c in NUM_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['sira'] = pd.to_numeric(df['sira'], errors='coerce')
    df['nace2'] = df['nace_raw'].map(_norm_nace)
    df['ihracat_musd'] = df['ihracat_bin_usd'] / 1000.0   # milyon $
    df['favok_marj'] = np.where(
        (df['favok'].notna()) & (df['net_satis'].notna()) & (df['net_satis'] > 0),
        df['favok'] / df['net_satis'] * 100, np.nan)
    df['kar_marj'] = np.where(
        (df['kar'].notna()) & (df['net_satis'].notna()) & (df['net_satis'] > 0),
        df['kar'] / df['net_satis'] * 100, np.nan)

    with open(ISO_CACHE, 'wb') as f:
        pickle.dump(df, f)
    print(f'[iso] cache yazildi: {len(df)} satir')


_DF = None
def load_iso():
    global _DF
    if _DF is None:
        build_iso_cache()
        with open(ISO_CACHE, 'rb') as f:
            _DF = pickle.load(f)
    return _DF


def sector_years(nace):
    """Sektör için İSO verisinde mevcut yıllar (büyükten küçüğe)."""
    df = load_iso()
    if nace == 'C':
        sec = df[df['nace2'].str.startswith('C', na=False)]
    else:
        sec = df[df['nace2'] == nace]
    if sec.empty:
        return []
    return sorted({int(y) for y in sec['yil'].dropna().unique()}, reverse=True)


def sector_iso(nace, year=None):
    """
    Sektörün İSO evrenindeki tam fotoğrafı.
    nace == 'C' (ana imalat sanayii toplamı) verilirse tüm imalat sektörlerinin
    (C10..C33) birleşik evreni döner — İSO 500 + İkinci 500'ün tamamı.
    year verilirse o yılın kesiti; None ise en güncel yıl.
    Döner: dict — yoksa None.
    """
    df = load_iso()
    if nace == 'C':
        sec = df[df['nace2'].str.startswith('C', na=False)].copy()
    else:
        sec = df[df['nace2'] == nace].copy()
    if sec.empty:
        return None

    out = {'nace': nace}

    # ── Yıl/liste bazında özet ────────────────────────────────────────────────
    yearly = []
    for (yil, liste), g in sec.groupby(['yil', 'liste']):
        yearly.append({
            'yil': int(yil), 'liste': liste,
            'firma': int(len(g)),
            'uretim_satis': float(g['uretim_satis'].sum(skipna=True)),
            'ihracat_musd': float(g['ihracat_musd'].sum(skipna=True)),
            'calisan': float(g['calisan'].sum(skipna=True)),
            'favok_marj_med': float(g['favok_marj'].median()) if g['favok_marj'].notna().any() else None,
        })
    out['yearly'] = sorted(yearly, key=lambda r: (r['yil'], r['liste']))

    # ── Seçilen (ya da en güncel) yıl — İSO 500 öncelikli firma tablosu ───────
    avail_years = sorted({int(y) for y in sec['yil'].dropna().unique()})
    last_yr = int(year) if (year is not None and int(year) in avail_years) else int(sec['yil'].max())
    cur = sec[sec['yil'] == last_yr].sort_values('uretim_satis', ascending=False)
    out['yil'] = last_yr
    out['available_years'] = sorted(avail_years, reverse=True)
    out['firma_sayisi'] = int(len(cur))
    out['firma_500']    = int((cur['liste'] == 'İSO 500').sum())
    out['firma_2_500']  = int((cur['liste'] == 'İSO İkinci 500').sum())
    out['toplam_uretim_satis'] = float(cur['uretim_satis'].sum(skipna=True))
    out['toplam_ihracat_musd'] = float(cur['ihracat_musd'].sum(skipna=True))
    out['toplam_calisan'] = float(cur['calisan'].sum(skipna=True))
    out['favok_marj_med'] = (float(cur['favok_marj'].median())
                             if cur['favok_marj'].notna().any() else None)
    out['kar_marj_med'] = (float(cur['kar_marj'].median())
                           if cur['kar_marj'].notna().any() else None)
    out['yabanci_pay_ort'] = (float(cur['pay_yabanci'].mean())
                              if cur['pay_yabanci'].notna().any() else None)

    # Sektörün İSO evreni içindeki payı (aynı yıl, tüm listeler)
    uni = df[df['yil'] == last_yr]
    tot = uni['uretim_satis'].sum(skipna=True)
    out['pay_uretim'] = float(out['toplam_uretim_satis'] / tot * 100) if tot else None

    # ── YoY (İSO 500 kesişimi: her iki yılda listede olan sektör toplamı) ────
    y500 = {r['yil']: r for r in yearly if r['liste'] == 'İSO 500'}
    if len(y500) >= 2:
        yrs = sorted(y500)
        a, b = y500[yrs[-2]], y500[yrs[-1]]
        out['yoy'] = {
            'donem': f"{yrs[-2]}→{yrs[-1]}",
            'uretim_satis': (b['uretim_satis']/a['uretim_satis']-1)*100 if a['uretim_satis'] else None,
            'ihracat': (b['ihracat_musd']/a['ihracat_musd']-1)*100 if a['ihracat_musd'] else None,
            'firma': b['firma'] - a['firma'],
        }
    else:
        out['yoy'] = None

    # ── Top 10 firma (son yıl, üretimden satışlara göre) ─────────────────────
    top = cur.head(10)
    out['top10'] = [{
        'sira': int(r['sira']) if pd.notna(r['sira']) else None,
        'liste': r['liste'],
        'firma': str(r['firma']),
        'uretim_satis': float(r['uretim_satis']) if pd.notna(r['uretim_satis']) else None,
        'ihracat_musd': float(r['ihracat_musd']) if pd.notna(r['ihracat_musd']) else None,
        'calisan': int(r['calisan']) if pd.notna(r['calisan']) else None,
        'favok_marj': float(r['favok_marj']) if pd.notna(r['favok_marj']) else None,
        'il': str(r['il']) if pd.notna(r['il']) else '',
    } for _, r in top.iterrows()]

    # ── İl dağılımı (son yıl) ─────────────────────────────────────────────────
    il = (cur.groupby('il')
             .agg(firma=('firma', 'count'),
                  satis=('uretim_satis', 'sum'))
             .sort_values('firma', ascending=False).head(8))
    out['iller'] = [{'il': str(i), 'firma': int(r['firma']), 'satis': float(r['satis'])}
                    for i, r in il.iterrows()]

    # ── Tam firma listesi (dashboard tablosu + dağılım analizi için) ─────────
    out['firmalar'] = cur[['sira', 'liste', 'firma', 'il', 'uretim_satis',
                           'net_satis', 'aktif', 'ihracat_musd', 'calisan',
                           'favok_marj']].copy()
    return out


def iso_summary_text(agg):
    """LLM prompt'u için kompakt İSO özeti."""
    if not agg:
        return ''
    L = [f"=== ISO 500 / Ikinci 500 ({agg['yil']}) ==="]
    L.append(f"  Listedeki firma: {agg['firma_sayisi']} "
             f"(ISO 500: {agg['firma_500']}, Ikinci 500: {agg['firma_2_500']})")
    L.append(f"  Toplam uretimden satislar: {agg['toplam_uretim_satis']/1e9:.1f} milyar TL")
    L.append(f"  Toplam ihracat: {agg['toplam_ihracat_musd']:.0f} milyon $")
    L.append(f"  Toplam istihdam: {agg['toplam_calisan']:.0f} kisi")
    if agg.get('favok_marj_med') is not None:
        L.append(f"  Medyan FAVOK marji: %{agg['favok_marj_med']:.1f}")
    if agg.get('pay_uretim') is not None:
        L.append(f"  Sanayi devleri icindeki uretim payi: %{agg['pay_uretim']:.1f}")
    if agg.get('yoy'):
        y = agg['yoy']
        if y.get('uretim_satis') is not None:
            L.append(f"  ISO 500 satis degisimi ({y['donem']}): %{y['uretim_satis']:+.1f} (nominal TL)")
    top3 = agg['top10'][:3]
    L.append('  Ilk 3 firma: ' + '; '.join(
        f"{t['firma']} ({t['uretim_satis']/1e9:.1f} mlr TL)" for t in top3))
    return '\n'.join(L)


if __name__ == '__main__':
    build_iso_cache(force=True)
    for code in ['C13', 'C20', 'C29']:
        agg = sector_iso(code)
        if agg:
            print(f"\n{code}: {agg['firma_sayisi']} firma ({agg['yil']}), "
                  f"satis {agg['toplam_uretim_satis']/1e9:.1f} mlr TL, "
                  f"ihracat {agg['toplam_ihracat_musd']:.0f} mn$, "
                  f"istihdam {agg['toplam_calisan']:.0f}")
            print('  Top3:', [t['firma'][:30] for t in agg['top10'][:3]])
            if agg['yoy']: print('  YoY:', agg['yoy'])
