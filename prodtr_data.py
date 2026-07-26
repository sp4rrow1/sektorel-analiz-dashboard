# -*- coding: utf-8 -*-
"""
TÜİK Sanayi Ürün İstatistikleri (PRODTR) 2005-2025 veri modülü.

Ürün bazlı üretim miktarı, satış değeri, satış miktarı ve girişim sayısını
NACE sektörüyle eşleştirir (PRODTR kodunun ilk 2 hanesi = NACE bölümü).
Ayrıca GTİP↔PRODTR eşleme tablosunu sağlar.

Onbellek (prodtr_cache.pkl) repo ile gelir; ham xlsx dosyaları yalnızca
onbelleği yeniden üretmek için gerekir (prodtr_source/ klasörü).

Kullanım:
  from prodtr_data import sector_products
  agg = sector_products('C13')   # sektörün ürün özeti
"""
import os, re, pickle, warnings
import pandas as pd
import numpy as np

warnings.filterwarnings('ignore')

BASE = os.path.dirname(__file__)
CACHE = os.path.join(BASE, 'prodtr_cache.pkl')
SRC   = os.path.join(BASE, 'prodtr_source', 'prodtr.xlsx')
GTIP  = os.path.join(BASE, 'prodtr_source', 'gtip_prodtr.xlsx')

METRICS = {
    'uretim': 'Üretim Miktarı',
    'satis_deger': 'Satış Değeri',
    'satis_miktar': 'Satış Miktarı',
    'girisim': 'Girişim Sayısı',
}


def _num(v):
    """'c' (gizli), '-', boş → None; sayısal → float."""
    if v is None: return None
    s = str(v).strip()
    if s in ('', 'c', 'C', '-', 'nan', 'None', ':'):
        return None
    try:
        return float(str(v).replace(',', '.'))
    except Exception:
        return None


def _nace_of(code):
    """'13.10.10.00.00' → 'C13' (imalat 10-33), aksi halde None."""
    try:
        d2 = int(str(code).split('.')[0])
        return f'C{d2}' if 10 <= d2 <= 33 else None
    except Exception:
        return None


def nace4_of(code):
    """'13.93.12.00.00' → 'C1393' (4 haneli NACE sınıfı)."""
    p = str(code).split('.')
    if len(p) < 2:
        return None
    try:
        d2 = int(p[0])
        if not (10 <= d2 <= 33):
            return None
        return f'C{p[0]}{p[1]}'
    except Exception:
        return None


def products_by_nace4(nace4, top_n=None):
    """
    Belirli bir 4 haneli NACE sınıfına (ör. 'C1393') ait PRODTR ürünlerini döner.
    Satış değerine göre sıralı: [{kod, tanim, birim, satis_deger, uretim, girisim, seri_*}]
    """
    c = _load()
    desc, data = c['desc'], c['data']
    sd = data.get('satis_deger', {}); ur = data.get('uretim', {}); gr = data.get('girisim', {})
    target = str(nace4).upper().strip()
    rows = []
    for k, meta in desc.items():
        if meta.get('duzey') != 'PRODTR':
            continue
        if nace4_of(k) != target:
            continue
        _, sval = _last_val(sd.get(k, {}))
        _, uval = _last_val(ur.get(k, {}))
        _, gval = _last_val(gr.get(k, {}))
        rows.append({
            'kod': k, 'tanim': meta.get('tanim', ''), 'birim': meta.get('birim', ''),
            'satis_deger': sval, 'uretim': uval,
            'girisim': int(gval) if gval else None,
            'seri_satis': dict(sorted(sd.get(k, {}).items())),
            'seri_uretim': dict(sorted(ur.get(k, {}).items())),
        })
    rows.sort(key=lambda r: (r['satis_deger'] is None, -(r['satis_deger'] or 0)))
    return rows[:top_n] if top_n else rows


def nace4_list(nace2=None):
    """
    PRODTR verisinde bulunan 4 haneli NACE sınıflarını döner.
    nace2 ('C13') verilirse yalnızca onun altındakiler.
    Döner: [{kod, urun_sayisi, toplam_satis}]
    """
    c = _load()
    sd = c['data'].get('satis_deger', {})
    agg = {}
    for k, meta in c['desc'].items():
        if meta.get('duzey') != 'PRODTR':
            continue
        n4 = nace4_of(k)
        if not n4:
            continue
        if nace2 and nace2 != 'C' and not n4.startswith(nace2):
            continue
        a = agg.setdefault(n4, {'kod': n4, 'urun_sayisi': 0, 'toplam_satis': 0.0})
        a['urun_sayisi'] += 1
        _, sv = _last_val(sd.get(k, {}))
        if sv:
            a['toplam_satis'] += sv
    return sorted(agg.values(), key=lambda r: -r['toplam_satis'])


def build_cache(force=False):
    if os.path.exists(CACHE) and not force:
        return
    if not os.path.exists(SRC):
        raise FileNotFoundError(f'PRODTR kaynak yok: {SRC}')

    kl = pd.read_excel(SRC, sheet_name='Kod Listesi', header=0)
    kod_c = kl.columns[0]
    kl = kl.rename(columns={kod_c: 'kod'})
    kl['kod'] = kl['kod'].astype(str).str.strip()
    desc = {r['kod']: {'duzey': r['Düzey'], 'tanim': str(r['Tanım']).strip(),
                       'birim': str(r.get('Ölçü Birimi', '')).strip()}
            for _, r in kl.iterrows()}

    # Metrik sayfaları → {kod: {yil: deger}}
    data = {}
    years_all = set()
    for key, sheet in METRICS.items():
        df = pd.read_excel(SRC, sheet_name=sheet, header=0)
        code_col = df.columns[0]
        year_cols = [c for c in df.columns if str(c).strip().isdigit()]
        years_all |= {int(str(c).strip()) for c in year_cols}
        m = {}
        for _, row in df.iterrows():
            code = str(row[code_col]).strip()
            series = {}
            for yc in year_cols:
                v = _num(row[yc])
                if v is not None:
                    series[int(str(yc).strip())] = v
            if series:
                m[code] = series
        data[key] = m

    # GTİP ↔ PRODTR eşleme (header satır 0: kol1=GTİP, kol2=Tanım, kol3=PRODTR, kol4=Tanım)
    gtip_map = {}    # {prodtr: [gtip,...]}   ileri yön
    gtip_rev = {}    # {gtip: prodtr}          geri yön
    gtip_desc = {}   # {gtip: tanim}
    try:
        g = pd.read_excel(GTIP, sheet_name=0, header=0)
        cols = list(g.columns)
        gtip_col, gtip_tan, prod_col = cols[1], cols[2], cols[3]
        for _, r in g.iterrows():
            gt = str(r[gtip_col]).strip()
            pr = str(r[prod_col]).strip()
            if not gt or gt in ('-', 'nan') or not pr or pr == 'nan':
                continue
            gtip_map.setdefault(pr, []).append(gt)
            gtip_rev[gt] = pr
            td = str(r.get(gtip_tan, '')).strip()
            if td and td != 'nan':
                gtip_desc[gt] = td
    except Exception as e:
        print(f'[prodtr] GTİP eşleme atlandı: {e}')

    cache = {
        'desc': desc,
        'data': data,
        'gtip_map': gtip_map,
        'gtip_rev': gtip_rev,
        'gtip_desc': gtip_desc,
        'years': sorted(years_all),
        'meta': {'built': pd.Timestamp.now().isoformat()},
    }
    with open(CACHE, 'wb') as f:
        pickle.dump(cache, f)
    print(f'[prodtr] cache yazıldı: {len(desc)} kod, {len(years_all)} yıl')


_C = None
def _load():
    global _C
    if _C is None:
        build_cache()
        with open(CACHE, 'rb') as f:
            _C = pickle.load(f)
    return _C


def _last_val(series):
    if not series: return None, None
    y = max(series)
    return y, series[y]


def sector_products(nace, top_n=12):
    """
    Sektörün (PRODTR düzeyi) ürün özeti.
    Döner: dict — yoksa None.
    """
    c = _load()
    if nace == 'C':
        prefixes = [f'{i:02d}' for i in range(10, 34)]
    else:
        prefixes = [nace.lstrip('C')]

    desc, data = c['desc'], c['data']
    sd = data.get('satis_deger', {})
    sm = data.get('satis_miktar', {})
    ur = data.get('uretim', {})
    gr = data.get('girisim', {})

    # PRODTR düzeyi + sektöre ait kodlar
    codes = [k for k, meta in desc.items()
             if meta.get('duzey') == 'PRODTR'
             and any(k.startswith(p + '.') or k.startswith(p) and _nace_of(k) ==
                     (nace if nace != 'C' else _nace_of(k)) for p in prefixes)
             and _nace_of(k) is not None
             and (nace == 'C' or _nace_of(k) == nace)]
    if not codes:
        return None

    # Sektörün kendi son veri yılı (global son yıldan eski olabilir)
    son_yil = max((y for k in codes for y in sd.get(k, {})),
                  default=max(c['years']) if c['years'] else None)

    # Ürünleri son yıl satış değerine göre sırala
    rows = []
    for k in codes:
        sv = sd.get(k, {})
        uv = ur.get(k, {})
        gv = gr.get(k, {})
        sy, sval = _last_val(sv)
        _, uval = _last_val(uv)
        _, gval = _last_val(gv)
        rows.append({
            'kod': k,
            'tanim': desc[k]['tanim'],
            'birim': desc[k].get('birim', ''),
            'satis_deger': sval,
            'satis_yil': sy,
            'uretim': uval,
            'girisim': int(gval) if gval else None,
            'seri_satis': sv,
            'seri_miktar': sm.get(k, {}),
            'seri_uretim': uv,
            'seri_girisim': gv,
        })

    with_sales = [r for r in rows if r['satis_deger'] is not None]
    with_sales.sort(key=lambda r: r['satis_deger'], reverse=True)

    # Sektör toplam satış trendi (yıllara göre, tüm ürünler toplamı)
    trend = {}
    for k in codes:
        for y, v in sd.get(k, {}).items():
            trend[y] = trend.get(y, 0.0) + v
    trend = dict(sorted(trend.items()))

    # Son yıl bazlı sıralama: farklı yılların değerleri karışmasın diye
    # top listesi ve toplamlar yalnızca son yılda veri beyan eden ürünlerden gelir.
    son_rows = sorted((r for r in rows if r['seri_satis'].get(son_yil) is not None),
                      key=lambda r: r['seri_satis'][son_yil], reverse=True)

    out = {
        'nace': nace,
        'yil': son_yil,
        'urun_sayisi': len(codes),
        'veri_urun': len(with_sales),
        'veri_urun_son': len(son_rows),
        'toplam_satis': trend.get(son_yil, 0.0),
        'toplam_girisim': sum(r['seri_girisim'].get(son_yil) or 0 for r in rows),
        'top': son_rows[:top_n] if son_rows else with_sales[:top_n],
        'all_rows': rows,
        'satis_trend': trend,
    }
    return out


def gtip_for_product(prodtr_code):
    """PRODTR kodu için eşleşen GTİP kodları."""
    return _load()['gtip_map'].get(str(prodtr_code).strip(), [])


def product_detail(prodtr_code):
    """
    Herhangi bir PRODTR kodunun tam profili: tanım, birim, tüm yıllara ait
    üretim/satış/girişim serileri, eşleşen GTİP kodları.
    Döner: dict — kod yoksa None.
    """
    c = _load()
    code = str(prodtr_code).strip()
    meta = c['desc'].get(code)
    if not meta:
        return None
    d = c['data']
    gtips = c['gtip_map'].get(code, [])
    gd = c.get('gtip_desc', {})
    return {
        'kod': code,
        'tanim': meta.get('tanim', ''),
        'aciklama_en': '',
        'birim': meta.get('birim', ''),
        'duzey': meta.get('duzey', ''),
        'nace': _nace_of(code),
        'uretim': dict(sorted(d.get('uretim', {}).get(code, {}).items())),
        'satis_deger': dict(sorted(d.get('satis_deger', {}).get(code, {}).items())),
        'satis_miktar': dict(sorted(d.get('satis_miktar', {}).get(code, {}).items())),
        'girisim': dict(sorted(d.get('girisim', {}).get(code, {}).items())),
        'gtip': [{'kod': g, 'tanim': gd.get(g, '')} for g in gtips],
    }


def prodtr_for_gtip(gtip_code):
    """
    GTİP kodu → eşleşen PRODTR ürünü (geri yön). Kısmi kod da kabul eder
    (ör. '5208' ile başlayan tüm GTİP'ler). Döner: [{gtip, gtip_tanim, prodtr, prodtr_tanim}]
    """
    c = _load()
    q = re.sub(r'[^0-9]', '', str(gtip_code))
    if not q:
        return []
    rev, gd, desc = c['gtip_rev'], c.get('gtip_desc', {}), c['desc']
    out = []
    for gt, pr in rev.items():
        gt_norm = re.sub(r'[^0-9]', '', gt)
        if gt_norm == q or gt_norm.startswith(q):
            out.append({
                'gtip': gt, 'gtip_tanim': gd.get(gt, ''),
                'prodtr': pr, 'prodtr_tanim': desc.get(pr, {}).get('tanim', ''),
            })
    # tam eşleşmeyi öne al, sonra koda göre sırala
    out.sort(key=lambda r: (re.sub(r'[^0-9]', '', r['gtip']) != q, r['gtip']))
    return out[:50]


def search_products(query, nace=None, level='PRODTR', limit=50):
    """
    PRODTR ürünlerini kod veya tanıma göre arar.
    nace verilirse o sektöre sınırlar. Döner: [{kod, tanim, birim, satis_deger}]
    """
    c = _load()
    q = str(query).strip().lower()
    if not q:
        return []
    sd = c['data'].get('satis_deger', {})
    out = []
    for code, meta in c['desc'].items():
        if level and meta.get('duzey') != level:
            continue
        if nace and nace != 'C' and _nace_of(code) != nace:
            continue
        if nace == 'C' and _nace_of(code) is None:
            continue
        tan = meta.get('tanim', '')
        if q in code.lower() or q in tan.lower():
            _, sval = _last_val(sd.get(code, {}))
            out.append({'kod': code, 'tanim': tan,
                        'birim': meta.get('birim', ''), 'satis_deger': sval})
    out.sort(key=lambda r: (r['satis_deger'] is None, -(r['satis_deger'] or 0)))
    return out[:limit]


if __name__ == '__main__':
    build_cache(force=True)
    for code in ['C13', 'C20', 'C29']:
        a = sector_products(code)
        if a:
            print(f"\n{code}: {a['urun_sayisi']} ürün ({a['veri_urun']} veri), "
                  f"toplam satış {a['toplam_satis']/1e9:.1f} milyar TL ({a['yil']})")
            for t in a['top'][:3]:
                print(f"   {t['kod']} · {t['tanim'][:45]} → {(t['satis_deger'] or 0)/1e9:.2f} mlr TL")
