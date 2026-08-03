import pytest
import os
import uuid
import gc
from models.models import Kitap
from models.database import VeritabaniYoneticisi
from models.exceptions import ISBNZatenMevcutError, KitapBulunamadiError


@pytest.fixture
def gecici_db():
    db_isim = f"test_{uuid.uuid4()}.db"
    db = VeritabaniYoneticisi()
    db.db_yolu = db_isim
    db._tablolari_olustur()

    yield db

    # Bağlantıyı kapatıp dosyayı sil
    db.close()
    gc.collect()

    for file in [db_isim, db_isim + "-wal", db_isim + "-shm", db_isim + "-journal"]:
        if os.path.exists(file):
            try:
                os.remove(file)
            except PermissionError:
                pass


@pytest.fixture
def ornek_kitap_admin():
    return Kitap("9789750719387", "Dönüşüm", "Franz Kafka", "Roman", 100, "admin")


def test_1_kitap_basariyla_ekleniyor(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert len(kitaplar) == 1
    assert kitaplar[0][0] == "9789750719387"


def test_2_ayni_isbn_ile_kitap_eklenemez(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    with pytest.raises(ISBNZatenMevcutError):
        gecici_db.kitap_ekle(ornek_kitap_admin)


def test_3_kitap_basariyla_siliniyor(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kitap_sil(ornek_kitap_admin.isbn, "admin")
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert len(kitaplar) == 0


def test_4_olmayan_kitap_silinmeye_calisildiginda_hata_firlatir(gecici_db):
    with pytest.raises(KitapBulunamadiError):
        gecici_db.kitap_sil("9999999999999", "admin")


def test_5_kitap_durumu_basariyla_guncelleniyor(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kitap_durum_guncelle(ornek_kitap_admin.isbn, "admin", "okunuyor", bitis_tarihi=None)
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert kitaplar[0][6] == "okunuyor"


def test_6_kitap_arama_dogru_calisiyor(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    sonuclar = gecici_db.kitap_ara("admin", "Kafka")
    assert len(sonuclar) == 1
    assert sonuclar[0][2] == "Franz Kafka"


def test_7_arama_bos_doner(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    sonuclar = gecici_db.kitap_ara("admin", "canavar")
    assert len(sonuclar) == 0


def test_8_negatif_sayfa_sayisi_engellenir():
    with pytest.raises(ValueError):
        Kitap(isbn="123", baslik="T", yazar="T", tur="T", sayfa_sayisi=-5)


def test_9_bos_kutuphane_listelendiginde_bos_liste_doner(gecici_db):
    kitaplar = gecici_db.kitaplari_listele("admin")
    assert len(kitaplar) == 0


def test_10_istatistik_ozeti_dogru_hesaplanir(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kitap_durum_guncelle(ornek_kitap_admin.isbn, "admin", "okundu", bitis_tarihi="2026-07-17")
    ozet = gecici_db.istatistik_ozet_getir("admin")
    assert ozet["okunan"] == 1
    assert ozet["sayfa"] == 100


def test_11_gecersiz_isbn_engellenir():
    with pytest.raises(ValueError, match="Geçersiz ISBN"):
        Kitap("123", "Test", "Test", "Test", 100)


def test_12_kitap_guncelle_tur_ve_sayfa(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kitap_guncelle(ornek_kitap_admin.isbn, "admin", tur="Bilim Kurgu")
    kitap = gecici_db.kitap_getir_isbn(ornek_kitap_admin.isbn)
    assert kitap[3] == "Bilim Kurgu"
    gecici_db.kitap_guncelle(ornek_kitap_admin.isbn, "admin", sayfa=200)
    kitap = gecici_db.kitap_getir_isbn(ornek_kitap_admin.isbn)
    assert kitap[4] == 200


def test_13_kitaplari_listele_filtreler(gecici_db):
    k1 = Kitap("9780000000001", "A", "Y", "Roman", 100, "admin", "okundu")
    k2 = Kitap("9780000000002", "B", "Y", "Bilim Kurgu", 100, "admin", "okunacak")
    gecici_db.kitap_ekle(k1)
    gecici_db.kitap_ekle(k2)
    sonuc = gecici_db.kitaplari_listele("admin", tur="Roman")
    assert len(sonuc) == 1
    assert sonuc[0][3] == "Roman"
    sonuc = gecici_db.kitaplari_listele("admin", durum="okunacak")
    assert len(sonuc) == 1
    assert sonuc[0][6] == "okunacak"


def test_14_kullanici_silme_cascade(gecici_db, ornek_kitap_admin):
    gecici_db.kitap_ekle(ornek_kitap_admin)
    gecici_db.kullanici_sil("admin")
    kitaplar = gecici_db.tum_kitaplari_getir()
    assert len(kitaplar) == 0


def test_16_hatali_veritabani_baglantisi():
    db = VeritabaniYoneticisi()
    db.db_yolu = "/gecersiz/yol/test.db"
    with pytest.raises(Exception):
        db._tablolari_olustur()