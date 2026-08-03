from unittest.mock import patch
from models.exceptions import RaporlamaHatasi
import pytest, os, uuid, gc
from models.database import VeritabaniYoneticisi
from controllers.kitap_controller import KitapController
from models.exceptions import VeritabaniHatasi, LibroTrackError

@pytest.fixture
def controller():
    db_isim = f"test_ctrl_{uuid.uuid4()}.db"
    db = VeritabaniYoneticisi()
    db.db_yolu = db_isim
    db._tablolari_olustur()
    ctrl = KitapController(db)
    yield ctrl
    db.close()
    gc.collect()
    for f in [db_isim, db_isim+"-wal", db_isim+"-shm", db_isim+"-journal"]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

def test_controller_kitap_ekleme_basarili(controller):
    s, m = controller.kitap_ekle("9789750719387", "Dönüşüm", "Franz Kafka", "Roman", "100", "admin")
    assert s is True

def test_controller_eksik_veri_hata_verir(controller):
    s, m = controller.kitap_ekle("", "", "Yazar", "Roman", "100", "admin")
    assert s is False

def test_controller_kitap_arama_akisi(controller):
    controller.kitap_ekle("1234567890", "Test", "Yazar", "Roman", "150", "admin")
    assert len(controller.tum_kitaplari_getir()) > 0

def test_controller_durum_guncelleme(controller):
    controller.kitap_ekle("1234567890", "Test", "Yazar", "Roman", "150", "admin")
    s, m = controller.kitap_guncelle("1234567890", "admin", "Tür Seçiniz", "okundu", None)
    assert s is True

def test_controller_not_ekle_gecersiz(controller):
    sonuc, mesaj = controller.not_ekle("9789750719387", "-1", "  ")
    assert sonuc is False
    assert "Geçersiz giriş" in mesaj

def test_controller_rapor_hata_yakalama(controller):
    with patch("controllers.kitap_controller.istatistikleri_olustur", side_effect=RaporlamaHatasi("Rapor Hatası")):
        sonuc, mesaj = controller.rapor_olustur("admin", True)
        assert sonuc is False
        assert "Rapor Hatası" in mesaj

def test_controller_guncelle_hatali_sayfa(controller):
    sonuc, mesaj = controller.kitap_guncelle("9789750719387", "admin", "Roman", "okundu", "abc")
    assert sonuc is False
    assert "tamsayı olmalıdır" in mesaj

def test_controller_sil_bulunamayan_kitap(controller):
    sonuc, mesaj = controller.kitap_sil("0000000000000", "admin")
    assert sonuc is False

def test_controller_kitap_ekle_gecersiz_isbn(controller):
    sonuc, mesaj = controller.kitap_ekle("123", "Baslik", "Yazar", "Roman", "100", "admin")
    assert sonuc is False
    assert "10 veya 13 haneli" in mesaj

def test_controller_kitap_ekle_harf_sayfa(controller):
    sonuc, mesaj = controller.kitap_ekle("9789750719387", "Dönüşüm", "Franz Kafka", "Roman", "yuz", "admin")
    assert sonuc is False
    assert "pozitif bir tamsayı" in mesaj

def test_controller_kullanici_ekle_basarili(controller):
    sonuc, mesaj = controller.kullanici_ekle("yeni_kullanici")
    assert sonuc is True

def test_controller_kitap_ekle_yazar_rakam(controller):
    sonuc, mesaj = controller.kitap_ekle("9781234567890", "Baslik", "12345", "Roman", "100", "admin")
    assert sonuc is False
    assert "harf içermelidir" in mesaj

def test_controller_guncelle_durum_okundu_tarih_atama(controller):
    controller.kitap_ekle("9781234567890", "Baslik", "Yazar", "Roman", "100", "admin")
    sonuc, mesaj = controller.kitap_guncelle("9781234567890", "admin", "Tür Seçiniz", "okundu", None)
    assert sonuc is True

def test_controller_not_ekle_bos_icerik(controller):
    controller.kitap_ekle("9781234567890", "Baslik", "Yazar", "Roman", "100", "admin")
    sonuc, mesaj = controller.not_ekle("9781234567890", "10", "   ")
    assert sonuc is False
    assert "Geçersiz giriş" in mesaj

def test_controller_not_ekle_sayfa_out_of_bounds(controller):
    controller.kitap_ekle("9781234567890", "Baslik", "Yazar", "Roman", "50", "admin")
    sonuc, _ = controller.not_ekle("9781234567890", "999", "Harika not")
    assert sonuc is False

def test_controller_not_ekle_db_hatasi(controller):
    with patch.object(controller.db, 'not_ekle', side_effect=VeritabaniHatasi("DB Hatası")):
        controller.kitap_ekle("9781234567890", "Baslik", "Yazar", "Roman", "50", "admin")
        sonuc, mesaj = controller.not_ekle("9781234567890", "10", "Not")
        assert sonuc is False
        assert "DB Hatası" in mesaj