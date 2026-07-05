# -*- coding: utf-8 -*-
"""
Sektorel LLM Analiz Modulu — Kimteks Word formati icin yeniden yazildi.
LLM'den [TAG] bolumlu yapi beklenir; report_word.py parse eder.
"""
import re
from llm_client import call_llm
from nace_config import SECTOR_NAMES, SITC_MAP


def summarize_data(nace, fig1, fig2, fig3, fig4, fig5):
    """5 sekildeki veriyi LLM icin ozet metin haline getirir."""
    def last_n(data_dict, n=12):
        out = {}
        for lbl, series in (data_dict or {}).items():
            pts = [(p, v) for p, v in sorted(series.items()) if v is not None][-n:]
            out[lbl] = pts
        return out

    def fmt_son(pts):
        """Son nokta metni — veri yoksa guvenli."""
        if not pts:
            return 'veri yok'
        p, v = pts[-1]
        return f'{v:.1f}% ({p})'

    def trend(pts):
        if len(pts) < 2: return 'belirsiz'
        vals = [v for _, v in pts if v is not None]
        if not vals: return 'veri yok'
        a = sum(vals[:3]) / max(len(vals[:3]), 1)
        b = sum(vals[-3:]) / max(len(vals[-3:]), 1)
        diff = b - a
        if diff > 3:  return 'yukari yonlu'
        if diff < -3: return 'asagi yonlu'
        return 'yatay seyir'

    def fmt(pts):
        return ', '.join(f'{p}: {v:.1f}%' for p, v in pts[-6:] if v is not None)

    lines = []
    sector = SECTOR_NAMES.get(nace, nace)
    lines.append(f'SEKTOR: {nace} - {sector}')
    lines.append(f'SITC eslesmesi: {SITC_MAP.get(nace, "T")}\n')

    if fig1:
        lines.append('=== SEKIL 1: Uretim Endeksi (YoY %) ===')
        for lbl, pts in last_n(fig1, 12).items():
            lines.append(f'  {lbl}: son={fmt_son(pts)}, trend={trend(pts)}')
            lines.append(f'  Son 6 ay: {fmt(pts)}')

    if fig2:
        lines.append('\n=== SEKIL 2: Alt Kirilimlar (YoY %) ===')
        for lbl, pts in last_n(fig2, 12).items():
            lines.append(f'  {lbl}: son={fmt_son(pts)}, trend={trend(pts)}')

    if fig3:
        lines.append('\n=== SEKIL 3: Dis Ticaret (YoY %) ===')
        for lbl, pts in last_n(fig3, 12).items():
            lines.append(f'  {lbl}: son={fmt_son(pts)}, trend={trend(pts)}')

    if fig4:
        lines.append('\n=== SEKIL 4: Kapasite Kullanim Orani (%) ===')
        for lbl, v in (fig4 or {}).items():
            d = v if isinstance(v, dict) else dict(v)
            pts_list = [(p, x) for p, x in sorted(d.items()) if x is not None][-12:]
            lines.append(f'  {lbl}: son={fmt_son(pts_list)}, trend={trend(pts_list)}')

    if fig5:
        lines.append('\n=== SEKIL 5: UFE Yillik Degisim (%) ===')
        for lbl, pts in last_n(fig5, 6).items():
            lines.append(f'  {lbl}: son={fmt_son(pts)}')

    return '\n'.join(lines)


SYSTEM_PROMPT = """Sen Türkiye'nin önde gelen bir kalkınma ve yatırım bankasının Sektörel
Araştırmalar biriminde çalışan kıdemli bir ekonomistsin. Bankacılık standardında,
resmi ve akıcı Türkçe ile sektör raporları yazarsın.

YAZIM KURALLARI (kesinlikle uy):
- Madde işareti (-) KULLANMA. Her bölümü AKICI PARAGRAF olarak yaz (2-4 cümle).
- Sayıları Türkçe biçimde yaz: ondalık ayırıcı VİRGÜL (%3,4 — %3.4 DEĞİL),
  binlik ayırıcı nokta (17.782). Yüzde işareti sayıdan önce (%12,1).
- Somut değerlere daima atıf yap; hem yıllık (ör. "2025 yılında") hem son ay
  (ör. "2026 Mart ayında") karşılaştırması ver.
- Tipik kalıpları kullan: "... bir önceki yıla göre %X oranında artış/azalış
  kaydetmiştir", "... geçen yılın aynı ayına göre %Y arttığı gözlemlenmektedir",
  "... düzeyinde gerçekleşmiştir", "... paralel seyretmektedir".
- Abartısız, olgusal, rasyonel. Başlık, etiket, markdown yıldızı KULLANMA."""


def _derived_metrics_text(fig1, fig5, fig6, fig7):
    """Reel ciro, verimlilik, momentum gibi türev analist metriklerini metne döker."""
    def first_ser(fd):
        if not fd: return {}
        return dict(sorted(next(iter(fd.values())).items()))
    def merged(fd):
        m = {}
        for _, s in (fd or {}).items():
            for p, v in s.items():
                if v is not None: m.setdefault(p, []).append(v)
        return {p: sum(vs)/len(vs) for p, vs in m.items()}
    def last(s):
        pts = [(p, v) for p, v in sorted(s.items()) if v is not None]
        return pts[-1] if pts else (None, None)

    prod = merged(fig1); ciro = first_ser(fig6)
    ufe  = first_ser(fig5); emp = first_ser(fig7)
    lines = []

    cp, cv = last(ciro); up, uv = last(ufe)
    if cv is not None and uv is not None:
        reel = ((1 + cv/100.0) / (1 + uv/100.0) - 1) * 100.0
        lines.append(f"  Reel ciro (nominal %{cv:.1f} - UFE %{uv:.1f}): %{reel:+.1f} "
                     f"({'reel daralma' if reel < 0 else 'reel buyume'})")
    pp, pv = last(prod); ep, ev = last(emp)
    if pv is not None and ev is not None:
        lines.append(f"  Isgucu verimliligi (uretim %{pv:.1f} - istihdam %{ev:.1f}): "
                     f"%{pv - ev:+.1f} puan")
    if not lines:
        return ''
    return "\n=== TUREV ANALIST METRIKLERI ===\n" + "\n".join(lines) + "\n"


def generate_analysis(nace, fig1, fig2, fig3, fig4, fig5, iso_agg=None,
                      fig6=None, fig7=None, kisa=False):
    """
    LLM'e yapılandırılmış sorgu gönderir.
    Dönen metin [TAG] bölümlerine ayrılmış olacak:
      [GIRIS]  — 1-2 paragraf genel değerlendirme
      [SEKIL1] — üretim endeksi maddeleri
      [SEKIL2] — alt kırılım maddeleri
      [SEKIL3] — dış ticaret maddeleri
      [SEKIL4] — KKO maddeleri
      [SEKIL5] — UFE maddeleri
    fig6/fig7 verilirse reel ciro & verimlilik türev metrikleri prompt'a eklenir.
    kisa=True → her bölümde daha az, öz madde (Kısa Özet stili).
    """
    sector = SECTOR_NAMES.get(nace, nace)
    ozet   = summarize_data(nace, fig1, fig2, fig3, fig4, fig5)
    ozet  += _derived_metrics_text(fig1, fig5, fig6, fig7)

    iso_blok = ''
    if iso_agg:
        try:
            from iso_data import iso_summary_text
            iso_txt = iso_summary_text(iso_agg)
            if iso_txt:
                iso_blok = f"\n{iso_txt}\n"
        except Exception:
            pass

    uzunluk = "1-2 cümlelik kısa" if kisa else "2-4 cümlelik"

    prompt = f"""Aşağıdaki TÜİK, TCMB ve İSO verileriyle {nace} - {sector} sektörü için
banka Sektörel Araştırmalar birimi standardında bir rapor yaz.

{ozet}
{iso_blok}

BİÇİM: Yanıtını SADECE aşağıdaki etiketlerle ver. Her etiketin altına, madde
işareti KULLANMADAN, {uzunluk} AKICI BİR PARAGRAF yaz. Sayılarda ondalık ayırıcı
virgül (%3,4), yüzde işareti önde. Örnek üsluba birebir uy.

[GIRIS]
Sektörün stratejik rolünü ve genel görünümünü tanıtan giriş paragrafı.
(Örnek üslup: "Türkiye'de {sector.lower()} sektörü, ... kritik bir rol
oynamaktadır. Sektörün mevcut durumuna ilişkin analizimiz ve temel göstergeler
aşağıda yer almaktadır.")

[SEKIL1]
Üretim endeksi paragrafı. (Örnek üslup: "... sektörü üretimi 2025 yılında bir
önceki yıla göre %X oranında artış kaydetmiştir. 2026 yılı ... ayında ise üretimin
geçen yılın aynı ayına göre %Y arttığı gözlemlenmektedir.")

[SEKIL2]
Alt kırılımlar paragrafı. En yüksek/düşük artış gösteren alt sektörleri isim ve
yüzdeyle belirt. (Örnek üslup: "Seçili alt sektörler incelendiğinde, 2025 yılında
en yüksek artış %X ile '...' alt sektöründe gerçekleşmiştir.")

[SEKIL3]
Dış ticaret paragrafı. İhracat ve ithalatın yıllık değişimini, mümkünse dolar
büyüklüğünü ve dış ticaret dengesini (fazla/açık) yorumla. (Örnek üslup:
"... 2025 yılında yapılan ihracat %X, ithalat ise %Y oranında artış göstermiştir.
2026 ... döneminde ihracatın %Z arttığı, ithalatın ise %W azaldığı görülmektedir.")

[SEKIL4]
Kapasite kullanım oranı paragrafı. Sektörü imalat sanayii ortalamasıyla ve tarihsel
ortalamayla karşılaştır. (Örnek üslup: "... döneminde ortalama kapasite kullanım
oranı imalat sanayiinde %X, ... sektöründe %Y olarak gerçekleşmiştir. ... itibarıyla
... sektöründe kapasite kullanım oranı %Z düzeyinde gerçekleşmiştir.")

[SEKIL5]
ÜFE paragrafı. Sektör ÜFE'sini imalat ÜFE'siyle karşılaştır; varsa reel ciro
etkisine değin. (Örnek üslup: "... ÜFE'si imalat ÜFE'si ile paralel seyretmektedir.
... ayında söz konusu alt endeks değişimi %X, imalat ÜFE değişimi ise %Y düzeyindedir.")
{f'''
[SEKIL6]
İSO 500/İkinci 500 kurumsal görünüm paragrafı. Sektörden listeye giren firma sayısı,
toplam üretimden satışlar ve ihracat büyüklüğü, kârlılık ve yoğunlaşmayı kurumsal
yatırımcı bakışıyla değerlendir.
''' if iso_agg else ''}
Sadece istenen etiketleri döndür. Madde işareti ve markdown yıldızı (**) yasak."""

    # Yanit yeterli DOLU bölüm içermeli; boş/eksik cevaplar elenip sonraki key denenir
    def _valid(t):
        if len(t) < 400:
            return False
        parts = re.split(r'\[[A-Z0-9]+\]', t)
        filled = sum(1 for p in parts if len(p.strip()) > 40)
        return filled >= 4
    return call_llm(prompt, system=SYSTEM_PROMPT,
                    max_tokens=(1200 if kisa else 2000), validate=_valid)


# ─── EXCEL 'Analiz' sayfasi (eski uyumluluk icin tutuluyor) ──────────────────
def add_analysis_sheet(wb, nace, analysis_text):
    """
    Analiz metnini Excel workbook'a 'Analiz' sayfasi olarak ekler.
    (generate_report.py geriye donuk uyumluluk icin kullanir.)
    """
    from openpyxl.styles import Font, Alignment, PatternFill
    sector = SECTOR_NAMES.get(nace, nace)

    ws = wb.create_sheet('Analiz', 1)
    ws.column_dimensions['A'].width = 2
    ws.column_dimensions['B'].width = 100
    ws.column_dimensions['C'].width = 2

    H_FILL = PatternFill('solid', fgColor='44546A')
    S_FILL = PatternFill('solid', fgColor='00538F')

    def title_row(row, text, fill, size=13):
        ws.merge_cells(f'B{row}:B{row}')
        c = ws.cell(row=row, column=2, value=text)
        c.fill = fill
        c.font = Font(name='Arial', bold=True, size=size, color='FFFFFF')
        c.alignment = Alignment(horizontal='left', vertical='center',
                                wrap_text=True, indent=1)
        ws.row_dimensions[row].height = 28
        return row + 1

    def text_row(row, text, bold=False):
        ws.merge_cells(f'B{row}:B{row}')
        c = ws.cell(row=row, column=2, value=text)
        c.font = Font(name='Arial', bold=bold, size=9)
        c.alignment = Alignment(horizontal='left', vertical='top',
                                wrap_text=True, indent=1)
        return row + 1

    r = 2
    r = title_row(r, 'SEKTÖREL ANALİZ RAPORU', H_FILL, 14)
    r = title_row(r, f'{nace} — {sector}', S_FILL, 12)
    r += 1

    if analysis_text:
        for line in analysis_text.splitlines():
            line = line.strip()
            if re.match(r'^\[[A-Z0-9]+\]$', line):
                r += 1
                r = text_row(r, line.strip('[]'), bold=True)
            elif line:
                r = text_row(r, line)
            else:
                r += 1
    return wb
