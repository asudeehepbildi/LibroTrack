import argparse
import logging
import sys
import requests
from datetime import date
from models.models import Kitap
from models.database import VeritabaniYoneticisi
from models.exceptions import (
    VeritabaniHatasi,
    YapilandirmaHatasi,
    SistemErisimHatasi,
    LibroTrackError,
)

logger = logging.getLogger()


class LibroTrackParser(argparse.ArgumentParser):
    """Argparse'ın varsayılan (İngilizce/teknik) hata mesajları yerine,
    kullanıcıya anlaşılır Türkçe bir uyarı basan özel parser sınıfı.
    Örneğin zorunlu bir parametre eksik girildiğinde veya --durum gibi
    sınırlı seçenekli (choices) bir alana geçersiz değer verildiğinde devreye girer.
    """

    def error(self, message: str) -> None:
        # sys.stderr: Standart hata çıktı akışıdır. Konsolda hataların kırmızı/belirgin yazdırılması (ortama göre) ve loglanabilmesi için stdout yerine stderr kullanılır.
        sys.stderr.write(f"[GİRDİ HATASI] Komut eksik veya hatalı girildi: {message}\n")
        sys.stderr.write(
            "Lütfen doğru kullanım için '-h' parametresini ekleyerek tekrar deneyin.\n"
        )
        sys.exit(
            2
        )  # İşletim sistemine komutun başarısız olduğunu (hata kodu 2) bildirerek programı kapatır.


def open_library_api_cek(isbn: str) -> dict:
    """Open Library API'sine istek atıp kitap kapağı ve açıklamasını çeker.

    Args:
        isbn (str): API'den sorgulanacak kitabın ISBN numarası.

    Returns:
        dict: Çekilen açıklama (aciklama) ve kapak (kapak_url) verisini içeren sözlük.
    """
    api_verisi = {"aciklama": "API'de açıklama bulunamadı.", "kapak_url": "Kapak yok"}
    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        # timeout=5 parametresi, karşı sunucu çökmüşse veya internet kopuksa programın
        # askıda kalmasını (hang) engeller, işlemi zaman aşımına uğratıp yoluna devam eder.
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            key = f"ISBN:{isbn}"
            if key in data:
                api_verisi["aciklama"] = data[key].get("notes", api_verisi["aciklama"])
                api_verisi["kapak_url"] = (
                    data[key].get("cover", {}).get("large", api_verisi["kapak_url"])
                )
                logging.info(f"Dış API'den '{isbn}' için metadata çekildi.")
    except Exception as e:
        logging.debug(f"API bağlantı hatası, yerel verilerle devam ediliyor: {e}")
    return api_verisi


def main() -> None:
    """LibroTrack komut satırı arayüzünün (CLI) ana giriş fonksiyonu.

    Argparse ile terminalden gelen argümanları ayrıştırır ve veritabanı
    sınıfına ilgili talimatları gönderir. Alt komutlar (subparsers) sayesinde
    'kitap-ekle', 'kitap-sil' gibi spesifik eylemler modüler olarak yönetilir.
    """
    try:
        db = VeritabaniYoneticisi()
    except (YapilandirmaHatasi, SistemErisimHatasi, VeritabaniHatasi) as e:
        logging.critical(f"Sistem Başlatma Hatası: {e}")
        sys.exit(1)

    parser = LibroTrackParser(description="LibroTrack (Çoklu Kullanıcı & API Destekli)")
    parser.add_argument(
        "--kullanici", default="admin", help="İşlemi yapacak kullanıcı profili."
    )

    # Subparsers: Terminalde boşluk bırakılarak girilen alt komutları (örn: python libro.py kitap-ekle) yakalamak için kullanılır.
    subparsers = parser.add_subparsers(dest="komut")

    ekle = subparsers.add_parser("kitap-ekle", help="Sisteme yeni bir kitap ekler.")
    ekle.add_argument("--isbn", required=True)
    ekle.add_argument("--baslik", required=True)
    ekle.add_argument("--yazar", required=True)
    ekle.add_argument("--tur", required=True)
    ekle.add_argument("--sayfa-sayisi", type=int, required=True)

    sil = subparsers.add_parser("kitap-sil", help="Kitabı ve tüm notlarını siler.")
    sil.add_argument("--isbn", required=True)

    gun_veri = subparsers.add_parser(
        "kitap-guncelle", help="Kitabın tür veya sayfa sayısını günceller."
    )
    gun_veri.add_argument("--isbn", required=True)
    gun_veri.add_argument("--tur", help="Yeni tür bilgisi")
    gun_veri.add_argument("--sayfa-sayisi", type=int, help="Yeni sayfa sayısı")

    listele = subparsers.add_parser("kitap-listele", help="Kitapları listeler.")
    listele.add_argument("--tur", help="Türe göre filtrele")
    listele.add_argument(
        "--durum",
        choices=["okunacak", "okunuyor", "okundu"],
        help="Duruma göre filtrele",
    )

    gun_durum = subparsers.add_parser(
        "durum-guncelle", help="Okuma durumunu değiştirir."
    )
    gun_durum.add_argument("--isbn", required=True)
    gun_durum.add_argument(
        "--durum", choices=["okunacak", "okunuyor", "okundu"], required=True
    )

    ara = subparsers.add_parser("kitap-ara", help="Anahtar kelime ile arama yapar.")
    ara.add_argument("--anahtar-kelime", required=True)

    not_e = subparsers.add_parser("not-ekle", help="Kitaba not ekler.")
    not_e.add_argument("--isbn", required=True)
    not_e.add_argument("--sayfa", type=int, required=True)
    not_e.add_argument("--icerik", required=True)

    not_l = subparsers.add_parser(
        "not-listele", help="Bir kitaba ait tüm notları gösterir."
    )
    not_l.add_argument("--isbn", required=True)

    subparsers.add_parser("istatistik-al", help="Sayısal özet basar ve grafik üretir.")
    subparsers.add_parser("csv-aktar", help="Okunmuş kitapları CSV yapar.")

    args = parser.parse_args()
    aktif_profil = args.kullanici

    if args.komut == "kitap-ekle":
        try:
            # 1. API'den verileri çek
            api_verisi = open_library_api_cek(args.isbn)
            yeni_kitap = Kitap(
                isbn=args.isbn,
                baslik=args.baslik,
                yazar=args.yazar,
                tur=args.tur,
                sayfa_sayisi=args.sayfa_sayisi,
                kullanici_adi=aktif_profil,
                aciklama=api_verisi["aciklama"],
                kapak_url=api_verisi["kapak_url"],
            )
            db.kitap_ekle(yeni_kitap)
            logging.info(f"Kitap Eklendi: {args.baslik}")
            sys.exit(
                0
            )  # 0, işletim sistemine "İşlem hatasız ve başarıyla bitti" sinyali gönderir.
        except ValueError as e:
            logging.error(f"Ekleme başarısız (Veri Hatası): {e}")
            sys.exit(1)
        except LibroTrackError as e:
            logging.error(f"Ekleme başarısız: {e}")
            sys.exit(1)
    elif args.komut == "kitap-sil":
        try:
            db.kitap_sil(args.isbn, aktif_profil)
            logging.info(f"Kitap Silindi: {args.isbn}")
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"Silme başarısız: {e}")
            sys.exit(1)
    elif args.komut == "kitap-guncelle":
        try:
            if not args.tur and not args.sayfa_sayisi:
                logging.warning(
                    "Güncellenecek herhangi bir alan (--tur veya --sayfa-sayisi) girilmedi."
                )
                sys.exit(1)
            db.kitap_guncelle(args.isbn, aktif_profil, args.tur, args.sayfa_sayisi)
            logging.info(f"Kitap bilgileri güncellendi: {args.isbn}")
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"Güncelleme başarısız: {e}")
            sys.exit(1)
    elif args.komut == "kitap-listele":
        try:
            kitaplar = db.kitaplari_listele(aktif_profil, args.tur, args.durum)
            for k in kitaplar:
                print(
                    f"ISBN: {k[0]:<12} | Başlık: {k[1]:<25} | Tür: {k[3]:<12} | Durum: {k[6]}"
                )
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"Listeleme başarısız: {e}")
            sys.exit(1)
    elif args.komut == "durum-guncelle":
        try:
            bitis_tarihi = (
                date.today().strftime("%Y-%m-%d") if args.durum == "okundu" else None
            )
            db.kitap_durum_guncelle(args.isbn, aktif_profil, args.durum, bitis_tarihi)
            logging.info(f"Okuma durumu güncellendi: {args.durum}")
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"Durum güncellenemedi: {e}")
            sys.exit(1)
    elif args.komut == "kitap-ara":
        try:
            sonuclar = db.kitap_ara(aktif_profil, args.anahtar_kelime)
            for k in sonuclar:
                print(f"Bulunan Kitap -> ISBN: {k[0]} | Başlık: {k[1]} | Yazar: {k[2]}")
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"Arama başarısız: {e}")
            sys.exit(1)
    elif args.komut == "not-ekle":
        try:
            db.not_ekle(args.isbn, args.sayfa, args.icerik)
            logging.info("Not eklendi.")
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"Not eklenemedi: {e}")
            sys.exit(1)
    elif args.komut == "not-listele":
        try:
            notlar = db.notlari_getir(args.isbn)
            if not notlar:
                print("Bu kitaba ait hiç not bulunamadı.")
            else:
                for sayfa, icerik in notlar:
                    print(f"Sayfa {sayfa}: {icerik}")
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"Notlar alınamadı: {e}")
            sys.exit(1)
    elif args.komut == "istatistik-al":
        try:
            ozet = db.istatistik_ozet_getir(aktif_profil)
            print("=== KÜTÜPHANE ÖZETİ ===")
            print(f"Toplam Kitap Sayısı: {ozet['toplam']}")
            print(f"Okunan Kitap Sayısı: {ozet['okunan']}")
            print(f"Tamamlanan Toplam Sayfa: {ozet['sayfa']}")
            from services.raporlama import istatistikleri_olustur

            istatistikleri_olustur(aktif_profil)
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"İstatistik alınamadı: {e}")
            sys.exit(1)
    elif args.komut == "csv-aktar":
        try:
            db.okunanlari_csv_yap(aktif_profil)
            sys.exit(0)
        except LibroTrackError as e:
            logging.error(f"CSV aktarımında hata: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
