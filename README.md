# Sektörel Analiz Dashboard — TÜİK · TCMB · İSO 500

Türkiye imalat sanayii (NACE C10–C33 + toplam) için interaktif sektörel araştırma
dashboard'u. TÜİK SDMX API, TCMB EVDS, İSO 500/İkinci 500 ve güncel haber akışını
tek ekranda birleştirir; yapay zekâ destekli Word raporu üretir.

## Özellikler

- **9 sekme**: Genel Bakış, Üretim, Alt Kırılımlar, Dış Ticaret, Kapasite Kullanımı,
  Enflasyon (ÜFE), Ciro, İstihdam, İSO 500, Haber & Risk
- 24 imalat sektörü + **"C — İmalat Sanayii (Toplam)"** agrega görünümü
- Sektör karşılaştırma, hızlı dönem presetleri, canlı sektör arama
- Otomatik Word raporu (grafikler + LLM analizi + İSO 500 + haber risk sentezi)
- Excel veri indirme

## Çalıştırma

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

`data_cache.pkl` ve `iso_cache.pkl` repo ile birlikte gelir — ilk çalıştırmada
ekstra kurulum gerekmez.

## Veriyi yenilemek (opsiyonel, yerel)

```bash
set TUIK_API_KEY=...
set EVDS_API_KEY=...
python cache_all.py
```

## Güvenilir LLM (opsiyonel)

Otomatik rapor varsayılan olarak ücretsiz paylaşımlı key havuzunu kullanır; havuz
tükendiğinde rapor verilerden deterministik olarak yazılır. Her raporun tam LLM
kalitesinde gelmesi için kendi (OpenAI-uyumlu) anahtarınızı verin:

Streamlit Cloud → **Settings → Secrets**:
```toml
LLM_API_KEY  = "sk-..."
LLM_BASE_URL = "https://api.openai.com/v1/chat/completions"   # veya DeepSeek/Groq
LLM_MODEL    = "gpt-4o-mini"
```
Yerelde ortam değişkeni olarak da verilebilir (`LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`).
Tanımlıysa bu anahtar havuzdan önce, öncelikli denenir.

## Kaynaklar

- TÜİK SDMX REST API v1.5
- TCMB EVDS
- İstanbul Sanayi Odası — Türkiye'nin 500 Büyük Sanayi Kuruluşu / İkinci 500
- Google News RSS
