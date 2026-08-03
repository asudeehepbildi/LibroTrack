import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Kitap:
    """Kütüphanedeki tek bir kitabın verilerini tutan model sınıfı.

    Attributes:
        isbn (str): Kitabın benzersiz numarası.
        baslik (str): Kitabın adı.
        yazar (str): Kitabın yazarı.
        tur (str): Kitabın türü/kategorisi.
        sayfa_sayisi (int): Kitabın toplam sayfa sayısı.
        kullanici_adi (str): Kitabı ekleyen kullanıcı profili (varsayılan 'admin').
        durum (str): Okuma durumu (varsayılan 'okunacak').
        bitis_tarihi (Optional[str]): Kitabın bitirildiği tarih.
        aciklama (Optional[str]): API'den çekilen kitap açıklaması.
        kapak_url (Optional[str]): API'den çekilen kapak görseli linki.
    """

    isbn: str
    baslik: str
    yazar: str
    tur: str
    sayfa_sayisi: int
    kullanici_adi: str = "admin"
    durum: str = "okunacak"
    bitis_tarihi: Optional[str] = None
    aciklama: Optional[str] = "Bilgi yok"
    kapak_url: Optional[str] = "URL yok"

    # Doğrudan erişimi kapatmak için korumalı değişken (Property mantığı için)
    _sayfa_sayisi: int = field(init=False, repr=False)

    def __post_init__(self):
        """Nesne oluşturulduktan sonra ISBN doğrulaması yapar."""
        if not self.isbn_dogrula(self.isbn):
            raise ValueError(
                f"Geçersiz ISBN: {self.isbn}. ISBN 10 veya 13 haneli olmalıdır."
            )

    @staticmethod
    def isbn_dogrula(isbn: str) -> bool:
        """ISBN uzunluğunu kontrol eder."""
        return len(isbn) in [10, 13]

    @property
    def sayfa_sayisi(self) -> int:
        """int: Kitabın sayfa sayısını döndürür."""
        return self._sayfa_sayisi

    @sayfa_sayisi.setter
    def sayfa_sayisi(self, deger: int) -> None:
        """Sayfa sayısını atamadan önce doğrular.

        Args:
            deger (int): Atanmak istenen sayfa sayısı.

        Raises:
            ValueError: Sayfa sayısı 0 veya negatif ise fırlatılır.
        """
        # Hatalı verinin veritabanına ulaşmasını henüz nesne seviyesindeyken engelliyoruz.
        if deger <= 0:
            raise ValueError("Sayfa sayısı pozitif bir tam sayı olmak zorundadır!")
        self._sayfa_sayisi = deger


class Kullanici:
    """Sistemi kullanan profil bilgilerini yöneten sınıf."""

    def __init__(self, kullanici_adi: str, eposta: str) -> None:
        """Kullanici nesnesini başlatır.

        Args:
            kullanici_adi (str): Kullanıcının sisteme giriş adı.
            eposta (str): Kullanıcının e-posta adresi.
        """
        self.kullanici_adi: str = kullanici_adi
        self.eposta: str = eposta

    @staticmethod
    def eposta_gecerli_mi(eposta: str) -> bool:
        """E-posta formatının geçerliliğini doğrular.

        Args:
            eposta (str): Doğrulanacak e-posta metni.

        Returns:
            bool: Format geçerliyse True, değilse False döner.
        """
        # Sınıf örneğine (instance) ihtiyaç duymayan, dışarıdan da kullanılabilen
        # bağımsız bir araç (utility) fonksiyonu olduğu için staticmethod seçildi.
        regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(regex, eposta))


class Kutuphane:
    """Veritabanı ile arayüz arasındaki iş mantığı (Service) katmanı."""

    def __init__(self, veritabani_yoneticisi) -> None:
        """Kutuphane nesnesini başlatır.

        Args:
            veritabani_yoneticisi (VeritabaniYoneticisi): Veritabanı işlemleri için enjekte edilen nesne.
        """
        # Sıkı bağlılığı (tight coupling) önlemek ve birim testlerde bellekte çalışan
        # sahte (mock) veritabanı verebilmek için Dependency Injection (Bağımlılık Enjeksiyonu) uygulandı.
        self.db = veritabani_yoneticisi

    def yeni_kitap_islem(self, kitap_objesi: Kitap) -> None:
        """Yeni kitabı kütüphaneye ekler.

        Args:
            kitap_objesi (Kitap): Veritabanına kaydedilecek kitap modeli.
        """
        self.db.kitap_ekle(kitap_objesi)

    def kitap_temizle(self, isbn: str) -> None:
        """Belirtilen kitabı kütüphaneden siler.

        Args:
            isbn (str): Silinecek kitabın ISBN numarası.
        """
        self.db.kitap_sil(isbn)
