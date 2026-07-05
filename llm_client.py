# -*- coding: utf-8 -*-
"""
Free LLM API Key Manager
Her cagirdiginda github.com/alistaitsacle/free-llm-api-keys'dan
guncel key + model ceker, OpenAI-compat proxy uzerinden istek yapar.
"""
import urllib.request, json, re, time

REPO_README = "https://raw.githubusercontent.com/alistaitsacle/free-llm-api-keys/main/README.md"
BASE_URL    = "https://aiapiv2.pekpik.com/v1/chat/completions"

# Model onceligi: en iyi -> en ucuz
PREFERRED_MODELS = [
    "deepseek-chat",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
    "smart-chat",
    "gemini-2.5-flash",
    "claude-opus-4-7",
    "gpt-5.5",
]

_cache_readme   = None
_cache_time     = 0
CACHE_TTL       = 120  # 2 dakika cache — key'ler sik degisiyor

def fetch_readme():
    global _cache_readme, _cache_time
    now = time.time()
    if _cache_readme and (now - _cache_time) < CACHE_TTL:
        return _cache_readme
    try:
        req = urllib.request.Request(REPO_README,
              headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            _cache_readme = r.read().decode("utf-8", "replace")
            _cache_time   = now
            return _cache_readme
    except Exception as e:
        print(f"   [LLM] README cekme hatasi: {e}")
        return _cache_readme or ""

def parse_keys(readme):
    """
    README'deki tablodan key + model bilgisini parse eder.
    Doner: [{'key': 'sk-...', 'model': 'gemini-2.5-flash', 'budget': '$20'}, ...]
    """
    rows = []
    pattern = re.compile(
        r'`(sk-[A-Za-z0-9]{40,})`\s*\|\s*([^\|]+?)\s*\|\s*[🆕✅][^\|]*\|\s*(\$[\d]+)'
    )
    for m in pattern.finditer(readme):
        key    = m.group(1).strip()
        model  = m.group(2).strip()
        budget = m.group(3).strip()
        rows.append({'key': key, 'model': model, 'budget': budget})
    return rows

def pick_best_key(rows):
    """Oncelik sirasina gore en iyi model + key sec."""
    for preferred in PREFERRED_MODELS:
        for row in rows:
            if preferred.lower() in row['model'].lower():
                return row
    # Hicbiri yoksa ilkini donn
    return rows[0] if rows else None

def get_best_key():
    readme = fetch_readme()
    rows   = parse_keys(readme)
    if not rows:
        raise RuntimeError("Hicbir gecerli key bulunamadi (README parse hatasi)")
    chosen = pick_best_key(rows)
    return chosen

def call_llm(prompt, system=None, max_tokens=2000, retries=3):
    """
    En guncel free key ile LLM'e istek gonder.
    Basarisiz olursa siradaki key ile tekrar dener.
    """
    readme = fetch_readme()
    rows   = parse_keys(readme)
    if not rows:
        raise RuntimeError("Hicbir key bulunamadi")

    # Oncelikli modeli bul, olmayan key varsa siradakini dene
    tried = set()
    queue = []
    for preferred in PREFERRED_MODELS:
        for row in rows:
            if preferred.lower() in row['model'].lower() and row['key'] not in tried:
                queue.append(row)
                tried.add(row['key'])
    # Kalanları da ekle
    for row in rows:
        if row['key'] not in tried:
            queue.append(row)
            tried.add(row['key'])

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_err = None
    for attempt, row in enumerate(queue[:retries]):
        try:
            body = json.dumps({
                "model":      row['model'],
                "messages":   messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }).encode("utf-8")
            req = urllib.request.Request(
                BASE_URL, data=body,
                headers={
                    "Content-Type":  "application/json",
                    "Authorization": f"Bearer {row['key']}",
                    "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
                    "Accept":        "application/json",
                })
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.loads(r.read().decode("utf-8","replace"))
                text = resp["choices"][0]["message"]["content"]
                print(f"   [LLM] {row['model']} | budget={row['budget']} | {len(text)} karakter")
                return text
        except Exception as e:
            last_err = e
            status = getattr(e, 'code', '?')
            print(f"   [LLM] deneme {attempt+1} basarisiz ({row['model']} {status}): {e}")
            time.sleep(1)

    raise RuntimeError(f"Tum key'ler basarisiz oldu. Son hata: {last_err}")


if __name__ == "__main__":
    # Test
    print("Key listesi:")
    readme = fetch_readme()
    rows   = parse_keys(readme)
    for r in rows[:5]:
        print(f"  {r['model']:40} | {r['budget']} | {r['key'][:20]}...")
    print(f"\nSec: {pick_best_key(rows)['model']}")
    print("\nTest sorgusu...")
    resp = call_llm("Merhaba! Turkce tek cumleyle selamla.")
    print("Yanit:", resp)
