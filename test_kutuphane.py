import pytest
import sqlite3
from models import Kitap, Kullanici, Kutuphane
from database import VeritabaniYoneticisi
from exceptions import ISBNZatenMevcutError, KitapBulunamadiError
import os
import uuid
import tempfile
import gc
from unittest.mock import patch
from raporlama import istatistikleri_olustur
from unittest.mock import patch, MagicMock
import pandas as pd
from raporlama import istatistikleri_olustur
from exceptions import RaporlamaHatasi


@pytest.fixture
def gecici_db():
    db_isim = f"test_{uuid.uuid4()}.db"
    db = VeritabaniYoneticisi()
    db.db_yolu = db_isim
    db._tablolari_olustur()

    yield db

    # Bağlantıların kapanması için çöp toplayıcıyı zorla
    gc.collect()

    # Dosyaları sil
    for file in [db_isim, db_isim + "-wal", db_isim + "-shm", db_isim + "-journal"]:
        if os.path.exists(file):
            try:
                os.remove(file)
            except PermissionError:
                # Hala silinmiyorsa küçük bir bekleme (opsiyonel)
                pass


@pytest.fixture
def ornek_kitap_admin():
    """Geçerli bir Kitap nesnesi fixture'ı döndürür.

    Returns:
        Kitap: Admin kullanıcısına atanmış kitap modeli.
    """
    return Kitap(
        isbn="9789750719387",
        baslik="Dönüşüm",
        yazar="Franz Kafka",
        tur="Roman",
        sayfa_sayisi=100,
        kullanici_adi="admin",
    )


def test_1_kitap_basariyla_ekleniyor(gecici_db, ornek_kitap_admin):
    """Yeni bir kitabın sisteme sorunsuz eklenip eklenmediğini kontrol eder."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert len(kitaplar) == 1
    assert kitaplar[0][0] == "9789750719387"


def test_2_ayni_isbn_ile_kitap_eklenemez(gecici_db, ornek_kitap_admin):
    """Mükerrer ISBN numarası girildiğinde özel hata sınıfının fırlatıldığını doğrular."""
    gecici_db.kitap_ekle(ornek_kitap_admin)

    # pytest.raises bloğu, kodun çökmesi yerine bilinçli olarak fırlatılan
    # doğru Exception sınıfını yakalayıp yakalayamadığını (Hata Yönetimi) test eder.
    with pytest.raises(ISBNZatenMevcutError):
        gecici_db.kitap_ekle(ornek_kitap_admin)


def test_3_kitap_basariyla_siliniyor(gecici_db, ornek_kitap_admin):
    """Var olan bir kitabın ISBN ile sistemden silinebildiğini doğrular."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kitap_sil(ornek_kitap_admin.isbn, "admin")
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert len(kitaplar) == 0


def test_4_olmayan_kitap_silinmeye_calisildiginda_hata_firlatir(gecici_db):
    """Sistemde olmayan bir ISBN silindiğinde hata fırlatıldığını doğrular."""
    with pytest.raises(KitapBulunamadiError):
        gecici_db.kitap_sil("9999999999999", "admin")


def test_5_kitap_durumu_basariyla_guncelleniyor(gecici_db, ornek_kitap_admin):
    """Kitabın okuma durumunun güncellenebilirliğini kontrol eder."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kitap_durum_guncelle(
        ornek_kitap_admin.isbn, "admin", "okunuyor", bitis_tarihi=None
    )
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert kitaplar[0][6] == "okunuyor"


def test_6_kitap_arama_dogru_calisiyor(gecici_db, ornek_kitap_admin):
    """Anahtar kelime ile arama işleminin doğru sonuç verdiğini doğrular."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    sonuclar = gecici_db.kitap_ara("admin", "Kafka")
    assert len(sonuclar) == 1
    assert sonuclar[0][2] == "Franz Kafka"


def test_7_arama_bos_doner(gecici_db, ornek_kitap_admin):
    """Arama sonucu bulunamadığında çökme olmadan boş liste dönüldüğünü doğrular."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    sonuclar = gecici_db.kitap_ara("admin", "canavar")
    assert len(sonuclar) == 0


def test_8_negatif_sayfa_sayisi_engellenir():
    """Sınıf başlatılırken property setter'ın negatif sayfa sayılarını reddettiğini doğrular."""
    with pytest.raises(ValueError):
        Kitap(isbn="123", baslik="T", yazar="T", tur="T", sayfa_sayisi=-5)


def test_9_bos_kutuphane_listelendiginde_bos_liste_doner(gecici_db):
    """Boş kütüphane listelendiğinde listenin boş döndüğünü kontrol eder."""
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert len(kitaplar) == 0


def test_10_istatistik_ozeti_dogru_hesaplanir(gecici_db, ornek_kitap_admin):
    """Veritabanındaki kitap özetlerinin sayısal olarak doğru çekildiğini doğrular."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kitap_durum_guncelle(
        ornek_kitap_admin.isbn, "admin", "okundu", bitis_tarihi="2026-07-17"
    )
    ozet = gecici_db.istatistik_ozet_getir("admin")
    assert ozet["okunan"] == 1
    assert ozet["sayfa"] == 100


def test_11_gecersiz_isbn_engellenir():
    """Hatalı uzunluktaki ISBN'lerin engellendiğini doğrular."""
    with pytest.raises(ValueError, match="Geçersiz ISBN"):
        Kitap(
            isbn="123",  # Hatalı uzunluk
            baslik="Test",
            yazar="Test",
            tur="Test",
            sayfa_sayisi=100,
        )


def test_12_kitap_guncelle_tur_ve_sayfa(gecici_db, ornek_kitap_admin):
    """Kitabın türünün ve sayfa sayısının ayrı ayrı güncellenebildiğini doğrular."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    # Sadece türü güncelle
    gecici_db.kitap_guncelle(ornek_kitap_admin.isbn, "admin", tur="Bilim Kurgu")
    kitap = gecici_db.kitap_getir_isbn(ornek_kitap_admin.isbn)
    assert kitap[3] == "Bilim Kurgu"

    # Sadece sayfayı güncelle
    gecici_db.kitap_guncelle(ornek_kitap_admin.isbn, "admin", sayfa=200)
    kitap = gecici_db.kitap_getir_isbn(ornek_kitap_admin.isbn)
    assert kitap[4] == 200


def test_13_kitaplari_listele_filtreler(gecici_db):
    k1 = Kitap("9780000000001", "A", "Y", "Roman", 100, "admin", "okundu")
    k2 = Kitap("9780000000002", "B", "Y", "Bilim Kurgu", 100, "admin", "okunacak")
    gecici_db.kitap_ekle(k1)
    gecici_db.kitap_ekle(k2)

    # Sadece Roman getir
    sonuc = gecici_db.kitaplari_listele("admin", tur="Roman")
    assert len(sonuc) == 1
    assert sonuc[0][3] == "Roman"

    # Sadece okunacak getir
    sonuc = gecici_db.kitaplari_listele("admin", durum="okunacak")
    assert len(sonuc) == 1
    assert sonuc[0][6] == "okunacak"


def test_14_kullanici_silme_cascade(gecici_db, ornek_kitap_admin):
    """Kullanıcı silindiğinde kitapların da silinip silinmediğini kontrol eder."""
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kullanici_sil("admin")
    kitaplar = gecici_db.tum_kitaplari_getir()
    assert len(kitaplar) == 0


def test_15_raporlama_dosya_mevcutsa_cik():
    """Grafik dosyaları zaten varsa, raporlamanın işlem yapmadan döndüğünü doğrular."""
    # os.path.exists fonksiyonunu True döndürecek şekilde taklit ediyoruz
    with patch("os.path.exists", return_value=True):
        # Bu fonksiyon çalışmalı ve hata vermemeli
        istatistikleri_olustur("admin", force_update=False)


def test_16_hatali_veritabani_baglantisi():
    """Hatalı veritabanı yolu verildiğinde sistemin hata verip vermediğini kontrol eder."""
    from database import VeritabaniYoneticisi

    # Geçersiz bir dosya yolu vererek bir hatayı tetikliyoruz
    db = VeritabaniYoneticisi()
    db.db_yolu = "/gecersiz/yol/test.db"
    with pytest.raises(Exception):  # VeritabaniHatasi fırlatmasını bekliyoruz
        db._tablolari_olustur()


def test_17_raporlama_verisiz_durum():
    """Pandas'tan boş veri gelmesi durumunu test eder."""
    # Veritabanından boş bir DataFrame dönüyormuş gibi taklit ediyoruz (Mock)
    with patch("pandas.read_sql_query", return_value=pd.DataFrame()):
        # Bu durumda fonksiyonun sessizce (hata vermeden) sonlanması beklenir
        istatistikleri_olustur("admin", force_update=True)


def test_18_raporlama_hata_yakalama():
    """Grafik çizimi sırasında hata oluşursa RaporlamaHatasi fırlatıldığını doğrular."""
    # Matplotlib'in savefig metodunu hata verecek şekilde ayarlıyoruz
    with patch("pandas.read_sql_query", return_value=pd.DataFrame({'tur': ['A'], 'adet': [1]})), \
            patch("matplotlib.pyplot.savefig", side_effect=Exception("Çizim Hatası")):
        with pytest.raises(RaporlamaHatasi):
            istatistikleri_olustur("admin", force_update=True)