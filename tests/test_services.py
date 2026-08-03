import pytest
from unittest.mock import patch
import pandas as pd
from services.raporlama import istatistikleri_olustur
from models.exceptions import RaporlamaHatasi

def test_15_raporlama_dosya_mevcutsa_cik():
    with patch("os.path.exists", return_value=True):
        istatistikleri_olustur("admin", force_update=False)

def test_17_raporlama_verisiz_durum():
    with patch("pandas.read_sql_query", return_value=pd.DataFrame()):
        istatistikleri_olustur("admin", force_update=True)

def test_18_raporlama_hata_yakalama():
    with patch("pandas.read_sql_query", return_value=pd.DataFrame({'tur': ['A'], 'adet': [1]})), \
            patch("matplotlib.pyplot.savefig", side_effect=Exception("Çizim Hatası")):
        with pytest.raises(RaporlamaHatasi):
            istatistikleri_olustur("admin", force_update=True)