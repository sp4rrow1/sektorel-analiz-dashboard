# -*- coding: utf-8 -*-
"""
TUIK SDMX + TCMB EVDS - Tum Imalat Verisi Onbellekleme
Calistirilma: python -X utf8 cache_all.py
Cikti:        data_cache.pkl (~50-150 MB, tum NACE C10-C33 verisi)
"""
import urllib.request, urllib.parse, json, re, os, time, pickle
from datetime import datetime, timedelta
from nace_config import ALL_MANUFACTURING, get_kko_code

# Onbellek yenileme (bu script) icin gerekli anahtarlar; ortam degiskeninden okunur.
# Deploy edilen dashboard.py bu dosyayi CALISTIRMAZ (sadece hazir data_cache.pkl'yi
# okur) -> bu anahtarlar canli sistemde kullanilmaz, sadece yerel yenileme icindir.
def _tuik_key():
    return os.environ.get("TUIK_API_KEY", "").strip()

def _evds_key():
    return os.environ.get("EVDS_API_KEY", "").strip()

# Geriye dönük uyumluluk (bazı fetch fonksiyonları modül sabitini kullanıyor)
TUIK_KEY  = _tuik_key()
EVDS_KEY  = _evds_key()
BASE_URL  = "https://nsiws.tuik.gov.tr/rest"
TOKEN_URL = "https://giris.tuik.gov.tr/realms/web/protocol/openid-connect/token"
EVDS_BASE = "https://evds3.tcmb.gov.tr/igmevdsms-dis"
START     = "2015-01"
# END dinamik: içinde bulunulan ay (TÜİK yayınladıkça yeni dönemler otomatik gelir)
END       = datetime.now().strftime("%Y-%m")
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data_cache.pkl")

_token = None
_expiry = None

# ─── AUTH / FETCH ─────────────────────────────────────────────────────────────
def get_token():
    global _token, _expiry
    if _token and _expiry and datetime.now() < _expiry:
        return _token
    data = urllib.parse.urlencode({
        "grant_type": "password", "client_id": "nsi-ws-consumer", "api_key": _tuik_key()
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data,
          headers={"Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req) as r:
        _token = json.loads(r.read())["access_token"]
    _expiry = datetime.now() + timedelta(seconds=240)
    return _token

def fetch_tuik(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {get_token()}"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read().decode("utf-8-sig", errors="replace")
        except Exception as e:
            if i == retries - 1: raise
            print(f"   Retry {i+1}: {e}")
            time.sleep(5)

def fetch_evds(path):
    req = urllib.request.Request(f"{EVDS_BASE}/{path}", headers={"key": _evds_key()})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def parse_series(content):
    out = []
    for s in re.findall(r'<generic:Series>(.*?)</generic:Series>', content, re.DOTALL):
        kp  = s.split('</generic:SeriesKey>')[0]
        key = dict(re.findall(r'<generic:Value id="([^"]+)" value="([^"]+)"', kp))
        obs = re.findall(
            r'<generic:ObsDimension id="TIME_PERIOD" value="([^"]+)"\s*/>\s*<generic:ObsValue value="([^"]+)"', s)
        out.append({'key': key, 'data': {p: float(v) for p, v in obs}})
    return out

# ─── VERI CEKME ──────────────────────────────────────────────────────────────
def fetch_alt_c():
    print("[1/5] ALT_C - Uretim endeksi (Alt gruplar, 3 hane NACE)...")
    content = fetch_tuik(
        f"{BASE_URL}/data/TR,DF_SANAYI_URETIM_ENDEKS_ALT_C,1.0"
        f"?startPeriod={START}&endPeriod={END}")
    series = parse_series(content)
    print(f"      {len(series)} seri yuklendi")
    return series

def fetch_ana_c():
    print("[1b] ANA_C - Uretim endeksi (Ana Endeksler, C toplam + 2 hane NACE)...")
    content = fetch_tuik(
        f"{BASE_URL}/data/TR,DF_SANAYI_URETIM_ENDEKS_ANA_C,1.0"
        f"?startPeriod={START}&endPeriod={END}")
    series = parse_series(content)
    print(f"      {len(series)} seri yuklendi")
    return series

def fetch_sinif_o():
    print("[2/5] SINIF_O - Uretim endeksi (Sinif duzeyi, 4 hane NACE)...")
    content = fetch_tuik(
        f"{BASE_URL}/data/TR,DF_SANAYI_URETIM_ENDEKS_SINIF_O,1.0"
        f"?startPeriod=2015-01&endPeriod={END}")
    series = parse_series(content)
    print(f"      {len(series)} seri yuklendi")
    return series

def fetch_ufe():
    print("[3/5] UFE - Uretici Fiyat Endeksi (tum NACE)...")
    content = fetch_tuik(
        f"{BASE_URL}/data/TR,DF_UFE_SANAYI_V2,1.0"
        f"?startPeriod={START}&endPeriod={END}")
    series = parse_series(content)
    print(f"      {len(series)} seri yuklendi")
    return series

def fetch_dis_ticaret():
    print("[4/5] Dis Ticaret - Takvim arindirilmis ihracat + ithalat...")
    result = {}
    for label, df_id in [
        ("ihracat", "DF_TAKVIM_ETKISINDEN_ARINDIRILMIS_IHRACAT_V2"),
        ("ithalat", "DF_TAKVIM_ETKISINDEN_ARINDIRILMIS_ITHALAT_V2"),
    ]:
        content = fetch_tuik(
            f"{BASE_URL}/data/TR,{df_id},1.0"
            f"?startPeriod=2015-01&endPeriod={END}")
        result[label] = parse_series(content)
        print(f"      {label}: {len(result[label])} seri")
    return result

def fetch_ciro():
    print("[6] Ciro Endeksi (DF_CIRO_ENDEKS_DEGISIM_C)...")
    content = fetch_tuik(
        f"{BASE_URL}/data/TR,DF_CIRO_ENDEKS_DEGISIM_C,1.0"
        f"?startPeriod={START}&endPeriod={END}")
    series = parse_series(content)
    print(f"      {len(series)} seri yuklendi")
    return series

def fetch_ucretli():
    print("[7] Ucretli Calisan (DF_UCRETLI_CALISAN_ISTATISTIKLERI_C)...")
    content = fetch_tuik(
        f"{BASE_URL}/data/TR,DF_UCRETLI_CALISAN_ISTATISTIKLERI_C,1.0"
        f"?startPeriod={START}&endPeriod={END}")
    series = parse_series(content)
    print(f"      {len(series)} seri yuklendi")
    return series

def fetch_kko():
    print("[5/5] TCMB EVDS - KKO (tum imalat sektorleri)...")
    result = {}
    toplam_url = (f"series=TP.KKO2.IS.TOP"
                  f"&startDate=01-01-2015&endDate=01-06-2030"
                  f"&type=json&frequency=5&aggregationTypes=avg")
    data = fetch_evds(toplam_url)
    items = data.get('items', [])
    parsed = {}
    for item in items:
        tarih = item.get('Tarih', '')
        val   = item.get('TP_KKO2_IS_TOP')
        if not val: continue
        try:
            yr, mo = tarih.split('-')
            parsed[f"{yr}-{int(mo):02d}"] = float(val)
        except: continue
    result['TOPLAM'] = parsed
    print(f"      Toplam imalat: {len(parsed)} obs")

    for nace in ALL_MANUFACTURING:
        code = get_kko_code(nace)
        key_field = code.replace('.', '_')
        try:
            url = (f"series={code}"
                   f"&startDate=01-01-2015&endDate=01-06-2030"
                   f"&type=json&frequency=5&aggregationTypes=avg")
            data = fetch_evds(url)
            items = data.get('items', [])
            parsed = {}
            for item in items:
                tarih = item.get('Tarih', '')
                val   = item.get(key_field)
                if not val: continue
                try:
                    yr, mo = tarih.split('-')
                    parsed[f"{yr}-{int(mo):02d}"] = float(val)
                except: continue
            if parsed:
                result[nace] = parsed
                print(f"      {nace} ({code}): {len(parsed)} obs")
        except Exception as e:
            print(f"      {nace}: HATA - {e}")
        time.sleep(0.2)

    return result

def fetch_redk():
    """TCMB Reel Efektif Döviz Kuru (ÜFE bazlı)."""
    print("[8] TCMB EVDS - Reel Efektif Kur (ÜFE bazlı)...")
    try:
        url = (f"series=TP.REELKUR.U2"
               f"&startDate=01-01-2015&endDate=01-06-2030"
               f"&type=json&frequency=5&aggregationTypes=avg")
        data = fetch_evds(url)
        items = data.get('items', [])
        parsed = {}
        for item in items:
            tarih = item.get('Tarih', '')
            val = item.get('TP_REELKUR_U2')
            if not val: continue
            try:
                yr, mo = tarih.split('-')
                parsed[f"{yr}-{int(mo):02d}"] = float(val)
            except: continue
        print(f"      REDK: {len(parsed)} obs")
        return parsed
    except Exception as e:
        print(f"      REDK: HATA - {e}")
        return {}

def fetch_iya():
    """TCMB İktisadi Yönelim Anketi — imalat sanayi beklenti göstergeleri."""
    print("[9] TCMB EVDS - İYA Güven Endeksi...")
    series_map = {
        'uretim_beklenti': ('TP.IYA2.Y4', 'Üretim hacmi gelecek 3 ay'),
        'genel_gidisat': ('TP.IYA2.Y2', 'Genel gidişat gelecek 3 ay'),
        'siparis': ('TP.IYA2.Y5', 'Toplam sipariş miktarı son 3 ay'),
        'ihracat_siparis': ('TP.IYA2.Y6', 'İhracat sipariş miktarı son 3 ay'),
    }
    result = {}
    for key, (code, desc) in series_map.items():
        try:
            field = code.replace('.', '_')
            url = (f"series={code}"
                   f"&startDate=01-01-2015&endDate=01-06-2030"
                   f"&type=json&frequency=5&aggregationTypes=avg")
            data = fetch_evds(url)
            items = data.get('items', [])
            parsed = {}
            for item in items:
                tarih = item.get('Tarih', '')
                val = item.get(field)
                if not val: continue
                try:
                    yr, mo = tarih.split('-')
                    parsed[f"{yr}-{int(mo):02d}"] = float(val)
                except: continue
            if parsed:
                result[key] = {'data': parsed, 'label': desc}
                print(f"      {desc}: {len(parsed)} obs")
        except Exception as e:
            print(f"      {desc}: HATA - {e}")
    return result

# ─── ANA ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("TUIK + TCMB - Tum Imalat Verisi Onbellekleniyor")
    print(f"Donem: {START} - {END}")
    print("=" * 60)

def fetch_dis_ticaret_fiyat():
    print("[8] Dis Ticaret - Birim Deger Endeksi...")
    result = {}
    for label, df_id in [
        ("ihracat_fiyat", "DF_IHRACAT_BIRIM_DEGER_ENDEKSI"),
        ("ithalat_fiyat", "DF_ITHALAT_BIRIM_DEGER_ENDEKSI"),
    ]:
        try:
            content = fetch_tuik(f"{BASE_URL}/data/TR,{df_id},1.0?startPeriod=2015-01&endPeriod={END}")
            result[label] = parse_series(content)
            print(f"      {label}: {len(result[label])} seri")
        except:
            pass
    return result

def fetch_saat_ucret():
    print("[9] Calisilan Saat ve Brut Maas Endeksleri...")
    result = {}
    for label, df_id in [
        ("saat", "DF_CALISILAN_SAAT_ISTATISTIKLERI_C"),
        ("maas", "DF_BRUT_UCRET_MAAS_ISTATISTIKLERI_C"),
    ]:
        try:
            content = fetch_tuik(f"{BASE_URL}/data/TR,{df_id},1.0?startPeriod={START}&endPeriod={END}")
            result[label] = parse_series(content)
            print(f"      {label}: {len(result[label])} seri")
        except:
            pass
    return result

def fetch_ydufe():
    print("[10] YD-UFE (Yurt Disi Uretici Fiyat Endeksi)...")
    try:
        content = fetch_tuik(f"{BASE_URL}/data/TR,DF_YDUFE_SANAYI_V2,1.0?startPeriod={START}&endPeriod={END}")
        s = parse_series(content)
        print(f"      YD-UFE: {len(s)} seri yuklendi")
        return s
    except:
        return []

def fetch_tufe():
    print("[11] TUFE (Tuketici Fiyat Endeksi - Harcama Gruplari)...")
    try:
        content = fetch_tuik(f"{BASE_URL}/data/TR,DF_TUFE_COICOP_V2,1.0?startPeriod={START}&endPeriod={END}")
        s = parse_series(content)
        print(f"      TUFE: {len(s)} seri yuklendi")
        return s
    except:
        return []

def fetch_usdtry():
    """Aylik USD/TRY: EVDS anahtari varsa aylik ortalama, yoksa TCMB kur
    arsivinden ayin ortasindaki ilk gecerli is gunu satis kuru (2005-01+)."""
    print("[12] USD/TRY kuru...")
    if _evds_key():
        try:
            url = ("series=TP.DK.USD.S.YTL&startDate=01-01-2005&endDate=01-06-2030"
                   "&type=json&frequency=5&aggregationTypes=avg")
            data = fetch_evds(url)
            parsed = {}
            for item in data.get('items', []):
                val = item.get('TP_DK_USD_S_YTL')
                if not val: continue
                try:
                    yr, mo = item.get('Tarih', '').split('-')
                    parsed[f"{yr}-{int(mo):02d}"] = float(val)
                except: continue
            if parsed:
                print(f"      EVDS: {len(parsed)} ay")
                return parsed
        except Exception as e:
            print(f"      EVDS basarisiz ({e}), TCMB arsivine dusuluyor...")
    def _gun(y, m, d):
        u = f"https://www.tcmb.gov.tr/kurlar/{y}{m:02d}/{d:02d}{m:02d}{y}.xml"
        try:
            with urllib.request.urlopen(u, timeout=12) as r:
                xml = r.read().decode('utf-8', 'replace')
            mt = re.search(r'CurrencyCode="USD".*?<ForexSelling>([\d.]+)</ForexSelling>',
                           xml, re.DOTALL)
            return float(mt.group(1)) if mt else None
        except Exception:
            return None
    out, today = {}, datetime.now()
    y, m = 2005, 1
    while (y, m) <= (today.year, today.month):
        for d in (15, 16, 17, 14, 18, 13, 19, 12, 20):
            v = _gun(y, m, d)
            if v:
                out[f"{y}-{m:02d}"] = v
                break
        m += 1
        if m > 12: y, m = y + 1, 1
    print(f"      TCMB arsivi: {len(out)} ay")
    return out


# ─── VERİ SETİ TANIMLARI (sıra + fetch fonksiyonu) ────────────────────────────
FETCH_STEPS = [
    ('alt_c',            fetch_alt_c),
    ('ana_c',            fetch_ana_c),
    ('sinif_o',          fetch_sinif_o),
    ('ufe',              fetch_ufe),
    ('dis_ticaret',      fetch_dis_ticaret),
    ('kko',              fetch_kko),
    ('ciro',             fetch_ciro),
    ('ucretli',          fetch_ucretli),
    ('redk',             fetch_redk),
    ('iya',              fetch_iya),
    ('dis_ticaret_fiyat', fetch_dis_ticaret_fiyat),
    ('saat_ucret',       fetch_saat_ucret),
    ('ydufe',            fetch_ydufe),
    ('tufe',             fetch_tufe),
    ('usdtry',           fetch_usdtry),
]


def latest_period(cache):
    """Cache'teki en güncel aylık dönemi (YYYY-MM) döndürür — veri güncelliği göstergesi."""
    best = ''
    for key in ('alt_c', 'ana_c', 'ufe'):
        for s in cache.get(key, []) or []:
            if isinstance(s, dict) and 'data' in s:
                for p in s['data']:
                    if len(str(p)) == 7 and str(p) > best:
                        best = str(p)
    return best or None


def refresh_all_data(progress_cb=None):
    """
    Tüm veri setlerini API'lerden TAZE çeker, data_cache.pkl'yi güncelin end tarihiyle
    yeniden yazar. Mevcut (yeniden çekilmeyen) anahtarları korur (ör. nace_names).
    progress_cb(i, n, key) verilirse her adımda çağrılır (UI ilerleme çubuğu için).
    Döner: {'ok': [...], 'fail': [...], 'created_at', 'end', 'latest', 'elapsed', 'size_mb'}
    """
    if not _tuik_key():
        raise RuntimeError("TUIK_API_KEY tanımlı değil — taze veri çekilemez.")

    t0 = datetime.now()
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
        except Exception:
            cache = {}

    ok, fail = [], []
    n = len(FETCH_STEPS)
    for i, (key, func) in enumerate(FETCH_STEPS):
        if progress_cb:
            try: progress_cb(i, n, key)
            except Exception: pass
        try:
            res = func()
            if res:
                cache[key] = res
                ok.append(key)
            else:
                fail.append(key)
        except Exception as e:
            print(f"   [HATA] {key}: {e}")
            fail.append(key)

    cache['meta'] = {
        'created_at': datetime.now().isoformat(),
        'start':      START,
        'end':        END,
        'nace_codes': ALL_MANUFACTURING,
    }
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

    return {
        'ok': ok, 'fail': fail,
        'created_at': cache['meta']['created_at'],
        'end': END,
        'latest': latest_period(cache),
        'elapsed': (datetime.now() - t0).seconds,
        'size_mb': os.path.getsize(CACHE_FILE) / 1024 / 1024,
    }


if __name__ == "__main__":
    print("=" * 60)
    print(f"TÜİK + TCMB — Tüm veri yenileniyor (dönem: {START} → {END})")
    print("=" * 60)
    r = refresh_all_data(lambda i, n, k: print(f"[{i+1}/{n}] {k} ..."))
    print(f"\nBitti — başarılı: {len(r['ok'])}, hatalı: {len(r['fail'])} "
          f"({', '.join(r['fail']) if r['fail'] else 'yok'})")
    print(f"En güncel dönem: {r['latest']} | Süre: {r['elapsed']}s | "
          f"Boyut: {r['size_mb']:.1f} MB")
