import sqlite3
import logging
import pandas as pd
import yaml
import os
from typing import List, Tuple, Any
from models.models import Kitap
from models.exceptions import (
    KitapBulunamadiError,
    ISBNZatenMevcutError,
    VeritabaniHatasi,
    YapilandirmaHatasi,
)

# Yapılandırma (config) yükleme bloğu
try:
    with open("../config.yaml", "r", encoding="utf-8") as f:
        # safe_load: YAML içindeki tehlikeli Python komutlarının çalıştırılmasını engeller, güvenli okuma yapar.
        config = yaml.safe_load(f)
except FileNotFoundError:
    # Kullanıcının dosya sisteminde config eksikse programın çökmemesi için
    # bellekte varsayılan (fallback) ayarlar yüklenerek devam edilir.
    config = {
        "veritabanı": {"yol": "data/librotrack.db"},
        "loglama": {
            "seviye_konsol": "INFO",
            "seviye_dosya": "DEBUG",
            "dosya": "librotrack.log",
        },
    }
except yaml.YAMLError as e:
    raise YapilandirmaHatasi(f"config.yaml formatı bozuk! Detay: {e}")

# Merkezi Loglama Konfigürasyonu
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
log_formati = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

dosya_seviyesi = config.get("loglama", {}).get("seviye_dosya", "DEBUG")
dosya_handler = logging.FileHandler(
    config.get("loglama", {}).get("dosya", "librotrack.log"), encoding="utf-8"
)
dosya_handler.setLevel(
    getattr(logging, dosya_seviyesi)
)  # getattr: logging kütüphanesinin içinden ('INFO', 'DEBUG' gibi) metin olarak gelen seviyeyi değişkene dönüştürür. Uzun if-else bloklarını önler.
dosya_handler.setFormatter(log_formati)
logger.addHandler(dosya_handler)

konsol_seviyesi = config.get("loglama", {}).get("seviye_konsol", "INFO")
konsol_handler = logging.StreamHandler()
konsol_handler.setLevel(getattr(logging, konsol_seviyesi))
konsol_handler.setFormatter(log_formati)
logger.addHandler(konsol_handler)


class VeritabaniYoneticisi:
    """SQLite veritabanı şemasını ve CRUD (Oluşturma, Okuma, Güncelleme, Silme) işlemlerini yöneten sınıf."""

    def __init__(self) -> None:
        """Veritabanı yolunu ayarlar, klasör yoksa oluşturur ve tabloları başlatır."""
        self.db_yolu: str = config.get("veritabanı", {}).get(
            "yol", "data/librotrack.db"
        )
        self.connection = None

        # YENİ EKLENEN PROFESYONEL OPTİMİZASYON:
        # Veritabanı klasörü yoksa (örneğin .exe ilk kez çalışıyorsa) otomatik oluştur.
        klasor = os.path.dirname(self.db_yolu)
        if klasor and not os.path.exists(klasor):
            os.makedirs(klasor, exist_ok=True)

        self._tablolari_olustur()

    def _tablolari_olustur(self) -> None:
        """Gerekli SQLite tablolarını ve ilişkilerini oluşturur.

        Raises:
            VeritabaniHatasi: SQL çalıştırma hatası oluşursa fırlatılır.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                # Foreign key (yabancı anahtar) ilişkilerini aktif ediyoruz. SQLite varsayılan olarak bunu kapalı tutar.
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()

                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS kullanicilar (
                    kullanici_adi TEXT PRIMARY KEY)"""
                )

                # ON DELETE CASCADE: Kullanıcı silindiğinde veya kitap silindiğinde
                # ilişkili alt verilerin (notların) veritabanında çöp olarak kalmaması için veritabanı motoru tarafından otomatik silinmesini sağlar.
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS kitaplar (
                    isbn TEXT NOT NULL, baslik TEXT NOT NULL, yazar TEXT NOT NULL,
                    tur TEXT NOT NULL, sayfa_sayisi INTEGER NOT NULL, kullanici_adi TEXT NOT NULL,
                    durum TEXT NOT NULL, bitis_tarihi TEXT, aciklama TEXT, kapak_url TEXT,
                    PRIMARY KEY (isbn, kullanici_adi),
                    FOREIGN KEY (kullanici_adi) REFERENCES kullanicilar(kullanici_adi) ON DELETE CASCADE)"""
                )

                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS notlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, isbn TEXT NOT NULL,
                    sayfa_no INTEGER, not_icerik TEXT NOT NULL)"""
                )
                conn.commit()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Tablolar oluşturulamadı: {e}")

    def _kullaniciyi_garantiye_al(self, kullanici_adi: str) -> None:
        """Kullanıcı veritabanında yoksa oluşturur, varsa yoksayar.

        Args:
            kullanici_adi (str): Kontrol edilecek kullanıcı adı.
        """
        with sqlite3.connect(self.db_yolu) as conn:
            # INSERT OR IGNORE: Kullanıcı zaten varsa IntegrityError fırlatılmasını engeller, sessizce geçer.
            conn.execute(
                "INSERT OR IGNORE INTO kullanicilar (kullanici_adi) VALUES (?)",
                (kullanici_adi,),
            )
            conn.commit()

    def kitap_ekle(self, kitap: Kitap) -> None:
        """Modelden gelen Kitap nesnesini veritabanına ekler."""
        self._kullaniciyi_garantiye_al(kitap.kullanici_adi)
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                # Sütun isimlerini açıkça belirterek (SQL Injection'dan korunmak için paramerized query) sorguyu daha güvenli hale getiriyoruz
                conn.execute(
                    """INSERT INTO kitaplar 
                    (isbn, baslik, yazar, tur, sayfa_sayisi, kullanici_adi, durum, bitis_tarihi, aciklama, kapak_url) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        kitap.isbn,
                        kitap.baslik,
                        kitap.yazar,
                        kitap.tur,
                        kitap.sayfa_sayisi,
                        kitap.kullanici_adi,
                        kitap.durum,
                        kitap.bitis_tarihi,
                        kitap.aciklama,
                        kitap.kapak_url,
                    ),
                )
                conn.commit()
        except sqlite3.IntegrityError:
            raise ISBNZatenMevcutError(f"Bu ISBN ({kitap.isbn}) zaten mevcut!")
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Kitap ekleme başarısız: {e}")

    def kitap_guncelle(
        self, isbn: str, kullanici_adi: str, tur: str = None, sayfa: int = None
    ) -> None:
        """Kitabın tür veya sayfa sayısı bilgilerini günceller.

        Args:
            isbn (str): Güncellenecek kitabın ISBN numarası.
            kullanici_adi (str): İşlemi yapan kullanıcı adı.
            tur (str, optional): Yeni tür bilgisi. Defaults to None.
            sayfa (int, optional): Yeni sayfa sayısı. Defaults to None.

        Raises:
            VeritabaniHatasi: SQL güncelleme hatası oluşursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                if tur:
                    cursor.execute(
                        "UPDATE kitaplar SET tur = ? WHERE isbn = ? AND kullanici_adi = ?",
                        (tur, isbn, kullanici_adi),
                    )
                if sayfa:
                    cursor.execute(
                        "UPDATE kitaplar SET sayfa_sayisi = ? WHERE isbn = ? AND kullanici_adi = ?",
                        (sayfa, isbn, kullanici_adi),
                    )
                conn.commit()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Güncelleme hatası: {e}")

    def kitaplari_listele(
        self, kullanici_adi: str, tur: str = None, durum: str = None
    ) -> List[Tuple[Any, ...]]:
        """Kullanıcının kitaplarını opsiyonel filtrelere göre listeler.

        Args:
            kullanici_adi (str): Kitapları getirilecek kullanıcı.
            tur (str, optional): Türe göre filtreleme. Defaults to None.
            durum (str, optional): Duruma göre filtreleme. Defaults to None.

        Returns:
            List[Tuple[Any, ...]]: Eşleşen kitap satırlarının listesi.

        Raises:
            VeritabaniHatasi: Okuma sırasında SQL hatası oluşursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                sorgu = "SELECT * FROM kitaplar WHERE kullanici_adi = ?"
                parametreler = [kullanici_adi]

                # Dinamik sorgu (Dynamic Query) inşaası: Yalnızca girilen filtre
                # parametreleri sorguya eklenerek esneklik ve performans artırılmıştır.
                if tur:
                    sorgu += " AND tur = ?"
                    parametreler.append(tur)
                if durum:
                    sorgu += " AND durum = ?"
                    parametreler.append(durum)

                cursor = conn.cursor()
                cursor.execute(
                    sorgu, tuple(parametreler)
                )  # cursor.execute metodu, güvenlik ve tutarlılık gereği sorgu
                # parametrelerini değiştirilemez (immutable) bir yapı olan tuple içerisinde beklediği için
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise VeritabaniHatasi("Listeleme başarısız.")

    def kitap_ara(self, kullanici_adi: str, anahtar_kelime: str) -> list:
        """Başlık veya yazarda esnek kelime araması yapar.

        Args:
            kullanici_adi (str): Aramayı gerçekleştiren kullanıcı.
            anahtar_kelime (str): Aranacak metin parçası.

        Returns:
            list: Eşleşen kitap kayıtları.

        Raises:
            VeritabaniHatasi: Arama sorgusu başarısız olursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                # LIKE %kelime%: Aranan metnin tam eşleşmesine gerek kalmadan
                # başlık veya yazarın herhangi bir yerinde geçmesi durumunda getirilmesi için kullanılır.
                sorgu = "SELECT * FROM kitaplar WHERE kullanici_adi = ? AND (baslik LIKE ? OR yazar LIKE ?)"
                param = f"%{anahtar_kelime}%"
                cursor.execute(sorgu, (kullanici_adi, param, param))
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Arama SQL hatası: {e}")

    def kitap_durum_guncelle(
        self, isbn: str, kullanici_adi: str, yeni_durum: str, bitis_tarihi: str = None
    ) -> None:
        """Bir kitabın okuma durumunu günceller.

        Args:
            isbn (str): Güncellenecek kitabın ISBN'i.
            kullanici_adi (str): İşlemi yapan kullanıcı.
            yeni_durum (str): Okunacak, okunuyor veya okundu durumu.
            bitis_tarihi (str, optional): Okundu ise bitiş tarihi. Defaults to None.

        Raises:
            VeritabaniHatasi: SQL hatası durumunda.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                conn.execute(
                    "UPDATE kitaplar SET durum = ?, bitis_tarihi = ? WHERE isbn = ? AND kullanici_adi = ?",
                    (yeni_durum, bitis_tarihi, isbn, kullanici_adi),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Durum güncelleme başarısız: {e}")

    def kitap_sil(self, isbn: str, kullanici_adi: str) -> None:
        """Kitabı ve kitaba ait tüm notları kalıcı olarak siler.

        Args:
            isbn (str): Silinecek kitabın ISBN numarası.
            kullanici_adi (str): İşlemi talep eden kullanıcı.

        Raises:
            KitapBulunamadiError: Kitap kullanıcının kütüphanesinde yoksa.
            VeritabaniHatasi: SQL silme işleminde hata olursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT baslik FROM kitaplar WHERE isbn = ? AND kullanici_adi = ?",
                    (isbn, kullanici_adi),
                )
                if not cursor.fetchone():
                    raise KitapBulunamadiError(
                        "Silinecek kitap kütüphanenizde bulunamadı."
                    )
                conn.execute(
                    "DELETE FROM kitaplar WHERE isbn = ? AND kullanici_adi = ?",
                    (isbn, kullanici_adi),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Silme işlemi başarısız: {e}")

    def not_ekle(self, isbn: str, sayfa: int, icerik: str) -> None:
        """Kitaba yeni bir serbest not ekler.

        Args:
            isbn (str): Not eklenecek kitabın ISBN numarası.
            sayfa (int): Notun ait olduğu sayfa numarası.
            icerik (str): Notun metni.

        Raises:
            VeritabaniHatasi: SQL hatası oluşursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute(
                    "INSERT INTO notlar (isbn, sayfa_no, not_icerik) VALUES (?, ?, ?)",
                    (isbn, sayfa, icerik),
                )
                conn.commit()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Not ekleme başarısız: {e}")

    def notlari_getir(self, isbn: str) -> List[Tuple[Any, ...]]:
        """Bir kitaba ait tüm notları liste halinde getirir.

        Args:
            isbn (str): Notları getirilecek kitabın ISBN numarası.

        Returns:
            List[Tuple[Any, ...]]: Sayfa numarası ve not içeriğinden oluşan liste.

        Raises:
            VeritabaniHatasi: SQL okuma hatası oluşursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT sayfa_no, not_icerik FROM notlar WHERE isbn = ? ORDER BY sayfa_no",
                    (isbn,),
                )  # virgül: gönderilen parametre sayısı
                # tek olduğu ve cursor.execute fonksiyonuna
                # tuple gönderilmesi gerektiği için , konularak
                # tuple haline getirilir
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Notlar listelenemedi: {e}")

    def tum_kullanicilari_getir(self) -> List[str]:
        """Sistemdeki tüm kullanıcı adlarını listeler."""
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                return [
                    row[0]
                    for row in cursor.execute(
                        "SELECT kullanici_adi FROM kullanicilar"
                    ).fetchall()
                ]
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Kullanıcılar listelenemedi: {e}")

    def kullanici_ekle(self, kullanici_adi: str) -> None:
        """Arayüzden gelen yeni kullanıcıyı sisteme kaydeder (Public metot)."""
        # Var olan gizli (private) metodu güvenli bir şekilde dışarıya açıyoruz
        self._kullaniciyi_garantiye_al(kullanici_adi)

    def kullanici_sil(self, kullanici_adi: str) -> None:
        """Kullanıcıyı ve ona ait tüm kitapları ile notları siler."""
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                # PRAGMA foreign_keys = ON sayesinde bu kullanıcı silindiğinde,
                # kitaplar ve notlar tablolarındaki "ON DELETE CASCADE" kuralı tetiklenir
                # ve kullanıcıya ait tüm veriler otomatik temizlenir.
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute(
                    "DELETE FROM kullanicilar WHERE kullanici_adi = ?", (kullanici_adi,)
                )
                conn.commit()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Kullanıcı silinemedi: {e}")

    def tum_kitaplari_getir(self) -> List[Tuple[Any, ...]]:
        """Kütüphanedeki tüm kitapları (kullanıcı filtresi olmadan) getirir."""
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM kitaplar")
                return cursor.fetchall()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Kitaplar getirilemedi: {e}")

    def kitap_getir_isbn(self, isbn: str) -> Tuple[Any, ...]:
        """Spesifik bir kitabı ISBN numarasına göre getirir."""
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM kitaplar WHERE isbn = ?", (isbn,))
                return cursor.fetchone()
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Kitap detayları getirilemedi: {e}")

    def istatistik_ozet_getir(self, kullanici_adi: str) -> dict:
        """Sayısal kütüphane verilerinin (toplam/okunan kitap, sayfa) özetini çıkarır.

        Args:
            kullanici_adi (str): İstatistikleri çıkarılacak kullanıcı.

        Returns:
            dict: Toplam, okunan ve okunan sayfa sayılarını içeren sözlük.

        Raises:
            VeritabaniHatasi: Toplama veya sayma sorgusunda hata oluşursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM kitaplar WHERE kullanici_adi = ?",
                    (kullanici_adi,),
                )
                toplam = cursor.fetchone()[
                    0
                ]  # fetchone sonucu tuple olarak (örn: (15,) şeklinde) döndürdüğü için bize sadece sayı olan ilk eleman lazım, bu yüzden 0. indisi alırız.

                cursor.execute(
                    "SELECT COUNT(*), SUM(sayfa_sayisi) FROM kitaplar WHERE kullanici_adi = ? AND durum = 'okundu'",
                    (kullanici_adi,),
                )
                okundu_verisi = cursor.fetchone()
                okunan = okundu_verisi[0] if okundu_verisi[0] else 0
                okunan_sayfa = okundu_verisi[1] if okundu_verisi[1] else 0
                return {"toplam": toplam, "okunan": okunan, "sayfa": okunan_sayfa}
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"Özet istatistik hatası: {e}")

    def okunanlari_csv_yap(self, kullanici_adi: str) -> None:
        """Durumu okundu olan kitapları Pandas kullanarak CSV'ye dönüştürür.

        Args:
            kullanici_adi (str): İşlemi talep eden kullanıcı profili.

        Raises:
            VeritabaniHatasi: CSV dosyasına yazma veya SQL okuma hatası oluşursa.
        """
        try:
            with sqlite3.connect(self.db_yolu) as conn:
                # read_sql_query: SQLite'dan çekilen veriyi doğrudan bir Pandas DataFrame tablosuna çevirir.
                df = pd.read_sql_query(
                    f"SELECT * FROM kitaplar WHERE durum = 'okundu' AND kullanici_adi = '{kullanici_adi}'",
                    conn,
                )
                if not df.empty:
                    df.to_csv(
                        f"{kullanici_adi}_okunanlar.csv", index=False, encoding="utf-8"
                    )
        except sqlite3.Error as e:
            raise VeritabaniHatasi(f"CSV dışa aktarım hatası: {e}")

    def close(self):
        # 'hasattr' ile önce bu özelliğin var olup olmadığını kontrol ediyoruz
        # Varsa ve doluysa kapatıyoruz
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()