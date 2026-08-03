import pytest, os, uuid, gc
from models.models import Kitap
from models.database import VeritabaniYoneticisi
from models.exceptions import ISBNZatenMevcutError, KitapBulunamadiError

@pytest.fixture
def db_fixture():
    db_isim = f"test_{uuid.uuid4()}.db"
    db = VeritabaniYoneticisi()
    db.db_yolu = db_isim
    db._tablolari_olustur()
    yield db
    db.close()
    gc.collect()
    for f in [db_isim, db_isim+"-wal", db_isim+"-shm", db_isim+"-journal"]:
        if os.path.exists(f):
            try: os.remove(f)
            except: pass

@pytest.fixture
def ornek_kitap_admin():
    return Kitap("9789750719387", "Dönüşüm", "Franz Kafka", "Roman", 100, "admin")

def test_1_kitap_basariyla_ekleniyor(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    assert len(db_fixture.kitaplari_listele("admin")) == 1

def test_2_ayni_isbn_ile_kitap_eklenemez(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    with pytest.raises(ISBNZatenMevcutError):
        db_fixture.kitap_ekle(ornek_kitap_admin)

def test_3_kitap_basariyla_siliniyor(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    db_fixture.kitap_sil(ornek_kitap_admin.isbn, "admin")
    assert len(db_fixture.kitaplari_listele("admin")) == 0

def test_4_olmayan_kitap_silinmeye_calisildiginda_hata_firlatir(db_fixture):
    with pytest.raises(KitapBulunamadiError):
        db_fixture.kitap_sil("9999999999999", "admin")

def test_5_kitap_durumu_basariyla_guncelleniyor(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    db_fixture.kitap_durum_guncelle(ornek_kitap_admin.isbn, "admin", "okunuyor", None)
    assert db_fixture.kitaplari_listele("admin")[0][6] == "okunuyor"

def test_6_kitap_arama_dogru_calisiyor(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    assert len(db_fixture.kitap_ara("admin", "Kafka")) == 1

def test_7_arama_bos_doner(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    assert len(db_fixture.kitap_ara("admin", "canavar")) == 0

def test_8_negatif_sayfa_sayisi_engellenir():
    with pytest.raises(ValueError):
        Kitap("123", "T", "T", "T", -5, "a")

def test_9_bos_kutuphane_listelendiginde_bos_liste_doner(db_fixture):
    assert len(db_fixture.kitaplari_listele("admin")) == 0

def test_10_istatistik_ozeti_dogru_hesaplanir(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    db_fixture.kitap_durum_guncelle(ornek_kitap_admin.isbn, "admin", "okundu", "2026-07-17")
    ozet = db_fixture.istatistik_ozet_getir("admin")
    assert ozet["okunan"] == 1

def test_11_gecersiz_isbn_engellenir():
    with pytest.raises(ValueError, match="Geçersiz ISBN"):
        Kitap("123", "Test", "Test", "Test", 100, "a")

def test_12_kitap_guncelle_tur_ve_sayfa(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    db_fixture.kitap_guncelle(ornek_kitap_admin.isbn, "admin", "Bilim Kurgu", 200)
    k = db_fixture.kitap_getir_isbn(ornek_kitap_admin.isbn)
    assert k[3] == "Bilim Kurgu"

def test_13_kitaplari_listele_filtreler(db_fixture):
    db_fixture.kitap_ekle(Kitap("9780000000001", "A", "Y", "Roman", 100, "admin", "okundu"))
    db_fixture.kitap_ekle(Kitap("9780000000002", "B", "Y", "Bilim Kurgu", 100, "admin", "okunacak"))
    assert len(db_fixture.kitaplari_listele("admin", tur="Roman")) == 1

def test_14_kullanici_silme_cascade(db_fixture, ornek_kitap_admin):
    db_fixture.kitap_ekle(ornek_kitap_admin)
    db_fixture.kullanici_sil("admin")
    assert len(db_fixture.tum_kitaplari_getir()) == 0

def test_16_hatali_veritabani_baglantisi():
    db = VeritabaniYoneticisi()
    db.db_yolu = "/gecersiz/yol/test.db"
    with pytest.raises(Exception): db._tablolari_olustur()