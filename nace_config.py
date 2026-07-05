# -*- coding: utf-8 -*-
"""
NACE Imalat Sektoru Konfigurasyonu
Tum imalat sektorleri (C10-C33) icin metadata ve eslesme tablosu
"""

# SITC Bolum -> DTE_SEKTOR_KODLARI eslesimi
# TUiK dis ticaret endeksi SITC Rev.3 bolumleri kullanir (0-9, T)
SITC_MAP = {
    'C10': '0',   # Gida - SITC 0 (Gida ve canli hayvanlar)
    'C11': '1',   # Icecek - SITC 1 (Icecekler ve tutun)
    'C12': '1',   # Tutun - SITC 1
    'C13': '6',   # Tekstil - SITC 6 (Uretilen mallar, malzemeye gore siniflandirilmis)
    'C14': '8',   # Giyim - SITC 8 (Cesitli mamul esyalar)
    'C15': '8',   # Deri - SITC 8
    'C16': '2',   # Agac - SITC 2 (Ham maddeler, yakit haric)
    'C17': '6',   # Kagit - SITC 6
    'C18': '8',   # Baski - SITC 8
    'C19': '3',   # Petrol - SITC 3 (Mineral yakit, yaglar)
    'C20': '5',   # Kimya - SITC 5 (Kimyasal maddeler ve urunler)
    'C21': '5',   # Eczacilik - SITC 5
    'C22': '6',   # Kaucuk/Plastik - SITC 6
    'C23': '6',   # Metalik olmayan - SITC 6
    'C24': '6',   # Ana metal - SITC 6
    'C25': '6',   # Fabrikasyon metal - SITC 6
    'C26': '7',   # Elektronik - SITC 7 (Makine ve ulasim araclari)
    'C27': '7',   # Elektrikli - SITC 7
    'C28': '7',   # Makine - SITC 7
    'C29': '7',   # Motorlu arac - SITC 7
    'C30': '7',   # Diger ulasim - SITC 7
    'C31': '8',   # Mobilya - SITC 8
    'C32': '8',   # Diger imalat - SITC 8
    'C33': '7',   # Onarim - SITC 7
}

# Sektör isimleri (rapor basliklari icin)
SECTOR_NAMES = {
    'C10': 'Gida Urunleri Imalati',
    'C11': 'Iceceklerin Imalati',
    'C12': 'Tutun Urunleri Imalati',
    'C13': 'Tekstil Urunleri Imalati',
    'C14': 'Giyim Esyalari Imalati',
    'C15': 'Deri ve Ilgili Urunlerin Imalati',
    'C16': 'Agac ve Agac Urunleri Imalati',
    'C17': 'Kagit ve Kagit Urunleri Imalati',
    'C18': 'Kayitli Medyanin Basilmasi',
    'C19': 'Kok Komuru ve Rafine Petrol Urunleri Imalati',
    'C20': 'Kimyasallar ve Kimyasal Urunlerin Imalati',
    'C21': 'Eczacilik Urunleri ve Malzemeleri Imalati',
    'C22': 'Kaucuk ve Plastik Urunlerin Imalati',
    'C23': 'Metalik Olmayan Mineral Urunlerin Imalati',
    'C24': 'Ana Metal Sanayii',
    'C25': 'Fabrikasyon Metal Urunleri Imalati',
    'C26': 'Bilgisayar Elektronik ve Optik Urunlerin Imalati',
    'C27': 'Elektrikli Techizat Imalati',
    'C28': 'Makine ve Ekipman Imalati',
    'C29': 'Motorlu Kara Tasiti ve Treyler Imalati',
    'C30': 'Diger Ulasim Araclari Imalati',
    'C31': 'Mobilya Imalati',
    'C32': 'Diger Imalatlar',
    'C33': 'Makine ve Ekipmanlarin Kurulum ve Onarimi',
}

# TCMB EVDS KKO seri kodlari (NACE 2 hane)
# TP.KKO2.IS.{iki_haneli_sayi}
def get_kko_code(nace_code):
    """C13 -> TP.KKO2.IS.13"""
    num = nace_code.replace('C', '')
    return f'TP.KKO2.IS.{num}'

def get_nace_number(nace_code):
    """C13 -> 13"""
    return nace_code.replace('C', '')

ALL_MANUFACTURING = [f'C{i}' for i in range(10, 34)]

# Ana imalat sanayii toplami (Bolum C) — tekil sektorlerin ustunde agrega secim
TOTAL_MANUFACTURING = 'C'
SECTOR_NAMES[TOTAL_MANUFACTURING] = 'İmalat Sanayii (Toplam)'
SITC_MAP[TOTAL_MANUFACTURING] = 'T'   # dis ticarette toplam ekonomi karsiligi

# Sektor secim listelerinde (dropdown) kullanilacak: toplam + tum alt sektorler
SECTOR_SELECT_OPTIONS = [TOTAL_MANUFACTURING] + ALL_MANUFACTURING
