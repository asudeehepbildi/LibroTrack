import pytest, os, glob, requests, pandas as pd
from unittest.mock import patch, MagicMock
from PIL import Image
from services.api_service import open_library_api_cek, url_to_image
from services.raporlama import istatistikleri_olustur
from models.exceptions import RaporlamaHatasi

@pytest.fixture(autouse=True)
def temizlik():
    yield
    for f in glob.glob("*_istatistik.png") + glob.glob("*_trend.png"):
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

# --- API Servis Testleri ---
def test_open_library_api_cek_basarili():
    mock_data = {
        "ISBN:123": {
            "title": "Test Kitabı",
            "authors": [{"name": "Yazar X"}],
            "number_of_pages": 200,
            "cover": {"large": "http://resim.url"}
        }
    }
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response
        sonuc = open_library_api_cek("123")
        assert sonuc["baslik"] == "Test Kitabı"

def test_open_library_api_cek_hata_durumu():
    with patch("requests.get", side_effect=requests.exceptions.RequestException("Bağlantı Hatası")):
        sonuc = open_library_api_cek("123")
        assert sonuc["aciklama"] == "API'de açıklama bulunamadı."

def test_url_to_image_basarili():
    with patch("requests.get") as mock_get, \
            patch("PIL.Image.open") as mock_open:
        mock_response = MagicMock()
        mock_response.content = b"sahte_resim_verisi"
        mock_get.return_value = mock_response
        mock_open.return_value = Image.new('RGB', (1, 1))
        img = url_to_image("http://resim.url")
        assert img is not None

def test_url_to_image_hata():
    with patch("requests.get", side_effect=requests.exceptions.RequestException("Resim yüklenemedi")):
        img = url_to_image("http://gecersiz.url")
        assert img is None

# --- Raporlama Servis Testleri ---
def test_15_raporlama_dosya_mevcutsa_cik():
    with patch("os.path.exists", return_value=True):
        istatistikleri_olustur("admin", force_update=False)

def test_17_raporlama_verisiz_durum():
    with patch("pandas.read_sql_query", return_value=pd.DataFrame()):
        istatistikleri_olustur("admin", force_update=True)

def test_18_raporlama_hata_yakalama():
    with patch("pandas.read_sql_query", return_value=pd.DataFrame({'tur': ['A'], 'adet': [1]})), \
         patch("matplotlib.pyplot.savefig", side_effect=Exception("Hata")):
        with pytest.raises(RaporlamaHatasi):
            istatistikleri_olustur("admin", force_update=True)

def test_raporlama_pasta_grafigi_hata():
    with patch("sqlite3.connect"), \
            patch("pandas.read_sql_query") as mock_sql:
        mock_sql.side_effect = [pd.DataFrame({'tur': ['Roman'], 'adet': [1]}), pd.DataFrame()]
        with patch("matplotlib.pyplot.savefig", side_effect=Exception("Save hatası")):
            with pytest.raises(RaporlamaHatasi, match="Pasta grafiği çizilemedi"):
                istatistikleri_olustur("admin", force_update=True)

def test_raporlama_bar_grafigi_basarili():
    with patch("sqlite3.connect"), \
            patch("pandas.read_sql_query") as mock_sql, \
            patch("matplotlib.pyplot.savefig") as mock_save:
        mock_sql.side_effect = [pd.DataFrame(), pd.DataFrame({'bitis_tarihi': ['2026-08-01']})]
        istatistikleri_olustur("admin", force_update=True)
        assert mock_save.called

def test_raporlama_bar_grafigi_hata():
    with patch("sqlite3.connect"), \
            patch("pandas.read_sql_query") as mock_sql:
        mock_sql.side_effect = [pd.DataFrame(), pd.DataFrame({'bitis_tarihi': ['2026-08-01']})]
        with patch("matplotlib.pyplot.savefig", side_effect=Exception("Bar save hatası")):
            with pytest.raises(RaporlamaHatasi, match="Bar grafiği çizilemedi"):
                istatistikleri_olustur("admin", force_update=True)