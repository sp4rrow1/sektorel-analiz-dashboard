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
TUIK_KEY  = os.environ.get("TUIK_API_KEY", "")
EVDS_KEY  = os.environ.get("EVDS_API_KEY", "")
BASE_URL  = "https://nsiws.tuik.gov.tr/rest"
TOKEN_URL = "https://giris.tuik.gov.tr/realms/web/protocol/openid-connect/token"
EVDS_BASE = "https://evds3.tcmb.gov.tr/igmevdsms-dis"
START     = "2015-01"
END       = "2026-06"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data_cache.pkl")

_token = None
_expiry = None

# ─── AUTH / FETCH ─────────────────────────────────────────────────────────────
def get_token():
    global _token, _expiry
    if _token and _expiry and datetime.now() < _expiry:
        return _token
    data = urllib.parse.urlencode({
        "grant_type": "password", "client_id": "nsi-ws-consumer", "api_key": TUIK_KEY
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
    req = urllib.request.Request(f"{EVDS_BASE}/{path}", headers={"key": EVDS_KEY})
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

    t0 = datetime.now()

    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
            print("Mevcut cache yüklendi. Hatalı sorgularda eski veri korunacak.")
        except Exception as e:
            print(f"Eski cache okunamadı: {e}")

    def safe_run(key, func):
        try:
            res = func()
            if res:
                cache[key] = res
        except Exception as e:
            print(f"   [HATA] {key} güncellenemedi: {e}")

    safe_run('alt_c', fetch_alt_c)
    safe_run('ana_c', fetch_ana_c)
    safe_run('sinif_o', fetch_sinif_o)
    safe_run('ufe', fetch_ufe)
    safe_run('dis_ticaret', fetch_dis_ticaret)
    safe_run('kko', fetch_kko)
    safe_run('ciro', fetch_ciro)
    safe_run('ucretli', fetch_ucretli)
    safe_run('redk', fetch_redk)
    safe_run('iya', fetch_iya)

    cache['meta']        = {
        'created_at': datetime.now().isoformat(),
        'start':      START,
        'end':        END,
        'nace_codes': ALL_MANUFACTURING,
    }

    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

    elapsed = (datetime.now() - t0).seconds
    size_mb = os.path.getsize(CACHE_FILE) / 1024 / 1024
    print(f"\nOnbellek kaydedildi: {CACHE_FILE}")
    print(f"Boyut: {size_mb:.1f} MB | Sure: {elapsed}s")
    print(f"Toplam seri: alt_c={len(cache['alt_c'])}, "
          f"sinif_o={len(cache['sinif_o'])}, ufe={len(cache['ufe'])}")
