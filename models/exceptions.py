# Not: Sınıf içi boş (pass) olsa da, Exception sınıfından miras aldığı için
# __init__ metoduna gönderilen mesajı otomatik olarak 'args' içine kaydeder
# ve hata oluştuğunda bu mesajı print(e) ile geri döndürür.
class LibroTrackError(Exception):
    """Projedeki tüm özel hataların türetildiği ana taban sınıf."""

    pass


class KitapBulunamadiError(LibroTrackError):
    """İstenen ISBN kütüphanede bulunamadığında fırlatılır."""

    pass


class ISBNZatenMevcutError(LibroTrackError):
    """Zaten var olan bir ISBN ile kitap eklenmeye çalışıldığında fırlatılır."""

    pass


class VeritabaniHatasi(LibroTrackError):
    """Genel SQLite ve veritabanı bağlantı/sorgu hatalarını sarmalamak için kullanılır."""

    pass


class GirdiDogrulamaError(LibroTrackError):
    """Kullanıcının CLI üzerinden geçersiz parametreler girmesi durumunda fırlatılır."""

    pass


class RaporlamaHatasi(LibroTrackError):
    """Grafik çizimi veya rapor üretimi sırasında hata oluşursa fırlatılır."""

    pass


class YapilandirmaHatasi(LibroTrackError):
    """config.yaml dosyası bozuk olduğunda fırlatılır."""

    pass


class SistemErisimHatasi(LibroTrackError):
    """Veritabanı klasörüne yazma izni olmadığında fırlatılır."""

    pass
