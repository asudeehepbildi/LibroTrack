from models.database import VeritabaniYoneticisi
from models.models import Kitap, Kutuphane
from services.raporlama import istatistikleri_olustur
from models.exceptions import VeritabaniHatasi, KitapBulunamadiError, ISBNZatenMevcutError, LibroTrackError, \
    RaporlamaHatasi
from datetime import date


class KitapController:
    def __init__(self):
        self.db = VeritabaniYoneticisi()
        self.kutuphane_servisi = Kutuphane(self.db)

    # --- Veri Getirme İşlemleri ---
    def tum_kitaplari_getir(self):
        return self.db.tum_kitaplari_getir()

    def kitap_getir_isbn(self, isbn):
        return self.db.kitap_getir_isbn(isbn)

    def tum_kullanicilari_getir(self):
        return self.db.tum_kullanicilari_getir()

    def istatistik_ozet_getir(self, k_adi):
        return self.db.istatistik_ozet_getir(k_adi)

    def notlari_getir(self, isbn):
        return self.db.notlari_getir(isbn)

    # --- Kullanıcı İşlemleri ---
    def kullanici_ekle(self, u_name):
        if not u_name:
            return False, "Kullanıcı adı boş bırakılamaz."
        if u_name.isdigit():
            return False, "Kullanıcı adı sadece rakamlardan oluşamaz, harf içermelidir."
        try:
            self.db.kullanici_ekle(u_name)
            return True, "Kullanıcı sisteme eklendi!"
        except VeritabaniHatasi as e:
            return False, str(e)

    def kullanici_sil(self, kullanici_adi):
        try:
            self.db.kullanici_sil(kullanici_adi)
            return True, "Kullanıcı ve ilişkili tüm verileri silindi."
        except VeritabaniHatasi as e:
            return False, str(e)

    # --- Kitap İşlemleri ---
    def kitap_ekle(self, isbn, baslik, yazar, tur, sayfa_str, kullanici):
        if not isbn or not baslik or not yazar or tur == "Tür Seçiniz" or not sayfa_str or kullanici == "Kullanıcı Seçiniz":
            return False, "Tüm alanlar zorunludur ve seçimler yapılmalıdır."
        if not isbn.isdigit():
            return False, "ISBN sadece rakamlardan oluşmalıdır."
        if len(isbn) not in [10, 13]:
            return False, "ISBN numarası 10 veya 13 haneli olmalıdır."
        if yazar.isdigit():
            return False, "Yazar ismi sadece rakamlardan oluşamaz, harf içermelidir."

        try:
            sayfa = int(sayfa_str)
            k = Kitap(isbn=isbn, baslik=baslik, yazar=yazar, tur=tur, sayfa_sayisi=sayfa, kullanici_adi=kullanici)
            self.kutuphane_servisi.yeni_kitap_islem(k)
            return True, "Eklendi!"
        except ValueError:
            return False, "Sayfa sayısı pozitif bir tamsayı olmalıdır."
        except (VeritabaniHatasi, ISBNZatenMevcutError) as e:
            return False, str(e)

    def kitap_guncelle(self, isbn, kullanici_adi, tur, durum, sayfa_raw):
        try:
            sayfa = None
            if sayfa_raw:
                if not sayfa_raw.isdigit():
                    return False, "Sayfa sayısı bir tamsayı olmalıdır."
                sayfa = int(sayfa_raw)
            guncel_tur = tur if tur != "Tür Seçiniz" else None

            if guncel_tur or sayfa:
                self.db.kitap_guncelle(isbn, kullanici_adi, guncel_tur, sayfa)
            if durum != "Seçiniz":
                bitis = date.today().strftime("%Y-%m-%d") if durum == "okundu" else None
                self.db.kitap_durum_guncelle(isbn, kullanici_adi, durum, bitis)
            return True, "Güncellendi!"
        except Exception as e:
            return False, str(e)

    def kitap_sil(self, isbn, kullanici_adi):
        try:
            self.db.kitap_sil(isbn, kullanici_adi)
            return True, "Kitap silindi!"
        except (VeritabaniHatasi, KitapBulunamadiError) as e:
            return False, str(e)

    # --- Not İşlemleri ---
    def not_ekle(self, isbn, sayfa_str, icerik):
        try:
            sayfa = int(sayfa_str)
            kitap = self.db.kitap_getir_isbn(isbn)
            if not kitap or sayfa < 1 or sayfa > kitap[4] or not icerik.strip():
                return False, "Geçersiz giriş!"
            self.db.not_ekle(isbn, sayfa, icerik)
            return True, "Not eklendi!"
        except ValueError:
            return False, "Sayfa numarası tamsayı olmalıdır."
        except (VeritabaniHatasi, LibroTrackError) as e:
            return False, str(e)

    # --- Rapor İşlemleri ---
    def rapor_olustur(self, k_adi, force_update):
        try:
            istatistikleri_olustur(k_adi, force_update=force_update)
            return True, ""
        except (VeritabaniHatasi, RaporlamaHatasi) as e:
            return False, str(e)