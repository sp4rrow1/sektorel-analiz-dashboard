# -*- coding: utf-8 -*-
"""
Sektörel haber taraması + yapay zekâ risk sentezi.

Kaynak: Google News RSS (https://news.google.com/rss/search) — API anahtarı
gerektirmez; oxylabs/google-news-scraper yaklaşımının RSS tabanlı sağlam muadili.

Kullanım:
  from news_analysis import fetch_sector_news, analyze_news
  items = fetch_sector_news('C13')
  text  = analyze_news('C13', items)   # LLM — [madde] listesi döner
"""
import re, html, urllib.request, urllib.parse
from datetime import datetime

from nace_config import SECTOR_NAMES
from llm_client import call_llm

# ─── Sektöre özel arama anahtar kelimeleri ────────────────────────────────────
SECTOR_KEYWORDS = {
    'C':   'Türkiye imalat sanayi',
    'C10': 'gıda sanayi',
    'C11': 'içecek sektörü',
    'C12': 'tütün sektörü',
    'C13': 'tekstil sektörü',
    'C14': 'hazır giyim sektörü',
    'C15': 'deri sektörü ayakkabı',
    'C16': 'orman ürünleri ahşap sanayi',
    'C17': 'kağıt sanayi ambalaj',
    'C18': 'basım matbaa sektörü',
    'C19': 'rafineri petrol ürünleri',
    'C20': 'kimya sanayi petrokimya',
    'C21': 'ilaç sanayi',
    'C22': 'plastik kauçuk sanayi',
    'C23': 'çimento cam seramik sektörü',
    'C24': 'demir çelik sektörü',
    'C25': 'metal sanayi',
    'C26': 'elektronik sanayi',
    'C27': 'beyaz eşya elektrikli teçhizat',
    'C28': 'makine imalat sanayi',
    'C29': 'otomotiv sanayi',
    'C30': 'savunma sanayi gemi raylı sistem',
    'C31': 'mobilya sektörü',
    'C32': 'medikal imalat sanayi',
    'C33': 'makine bakım onarım sanayi',
}

_UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
       '(KHTML, like Gecko) Chrome/124.0 Safari/537.36')


def _strip_html(s):
    s = re.sub(r'<[^>]+>', ' ', s or '')
    return html.unescape(re.sub(r'\s+', ' ', s)).strip()


def fetch_sector_news(nace, max_items=14, query_override=None):
    """
    Google News RSS'ten sektör haberleri.
    query_override verilirse varsayılan sektör anahtar kelimesi yerine kullanılır.
    Döner: [{'title','source','date','link','summary'}, ...]
    """
    kw = (query_override or '').strip() or SECTOR_KEYWORDS.get(nace, SECTOR_NAMES.get(nace, nace))
    q = urllib.parse.quote(kw)
    url = (f'https://news.google.com/rss/search?q={q}'
           f'&hl=tr&gl=TR&ceid=TR:tr')
    req = urllib.request.Request(url, headers={'User-Agent': _UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        xml = r.read().decode('utf-8', 'replace')

    items = []
    for m in re.finditer(r'<item>(.*?)</item>', xml, re.DOTALL):
        blk = m.group(1)
        def tag(t):
            mm = re.search(rf'<{t}[^>]*>(.*?)</{t}>', blk, re.DOTALL)
            return mm.group(1).strip() if mm else ''
        title = _strip_html(re.sub(r'^<!\[CDATA\[|\]\]>$', '', tag('title')))
        src   = _strip_html(tag('source'))
        # Google News basligi "Başlık - Kaynak" formatında; kaynak sondaysa ayıkla
        if src and title.endswith(f' - {src}'):
            title = title[: -len(src) - 3].strip()
        pub = tag('pubDate')
        try:
            dt = datetime.strptime(pub[:25].strip(), '%a, %d %b %Y %H:%M:%S')
            date = dt.strftime('%d.%m.%Y')
        except Exception:
            date = pub[:16]
        items.append({
            'title':   title,
            'source':  src,
            'date':    date,
            'link':    _strip_html(tag('link')),
            'summary': _strip_html(tag('description'))[:260],
        })
        if len(items) >= max_items:
            break
    return items


def news_to_text(items):
    lines = []
    for i, it in enumerate(items, 1):
        base = f"{i}. [{it['source']} · {it['date']}] {it['title']}"
        if it['summary'] and it['summary'].lower() != it['title'].lower():
            base += f" — {it['summary']}"
        lines.append(base)
    return '\n'.join(lines)


# ─── LLM PROMPT ───────────────────────────────────────────────────────────────
NEWS_ANALYSIS_PROMPT = """Sen, Kalkınma ve Yatırım Bankacılığı alanında çalışan, dünyanın en iyi
Sektörel Araştırmalar Analisti ve Uzman Ekonomistisin. Kusursuz durum tespiti
(due diligence) yapar, piyasa sinyallerini en iyi sen okursun. Bütünüyle
özgürsün ve tüm analitik yaratıcılığını kullanmalısın.

GÖREV:
Aşağıda, {sektor_adi} sektörüne ait en güncel haber başlıkları ve özetleri yer
almaktadır. Senden bu ham haber verilerini sentezleyerek, üst düzey yatırım
komitesine sunulacak derinlikte bir "Sektörel Beklentiler ve Risk Analizi"
metni oluşturmanı istiyorum.

FORMAT VE DİL BEKLENTİSİ:
1. Sadece madde imleri (bullet points) kullan. Paragraf yazma. Her madde "-" ile başlasın.
2. Kurumsal araştırma raporları kalitesinde; net, vurucu, rasyonel ve profesyonel bir dil kullan.
3. Her maddede mutlaka şu unsurlardan en az birini barındır:
   - Geleceğe dair bir "beklenti" veya "öngörü"
   - Makro/Mikro bir "risk" veya "fırsat"
   - Gelişmenin gerçekleşme veya sektörü etkileme "olasılığı" (örn: "Yüksek olasılıklı daralma riski", "Kısa vadeli marj baskısı")
4. Haberleri olduğu gibi tekrar etme; haberin *sektörün üretimi, kapasitesi,
   maliyetleri veya ihracatı üzerindeki olası etkisini* yorumla.
5. 6-9 madde yaz; en kritik sinyalleri öne al. Başlık, giriş, sonuç yazma — sadece maddeler.

Örnek Madde Formatı:
- Küresel tedarik zincirindeki aksamaların devam etmesi nedeniyle, sektörde hammadde maliyetlerinde kısa vadede yukarı yönlü risklerin sürmesi (%70 olasılık) ve kar marjlarında daralma beklenmektedir.
- Avrupa pazarındaki regülasyon değişikliklerinin, yeşil dönüşüme yatırım yapan firmalar için orta vadede rekabet avantajı ve pazar payı artışı yaratması öngörülmektedir.

GÜNCEL HABER VERİSİ:
{news_data}"""


def analyze_news(nace, items):
    """Haberleri LLM ile sentezler; '-' maddeli metin döner."""
    if not items:
        return None
    sektor = SECTOR_NAMES.get(nace, nace)
    prompt = NEWS_ANALYSIS_PROMPT.format(
        sektor_adi=f'{nace} — {sektor}',
        news_data=news_to_text(items),
    )
    return call_llm(prompt, max_tokens=1800)


if __name__ == '__main__':
    items = fetch_sector_news('C13')
    print(f'{len(items)} haber bulundu:')
    for it in items[:6]:
        print(f"  [{it['source']} · {it['date']}] {it['title'][:75]}")
