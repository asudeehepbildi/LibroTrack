# 📚 LibroTrack

> **Kitaplık Yönetim ve İstatistik Sistemi**
> Kütüphanedeki kitapları listeleyebileceğiniz, kitaplar hakkında ortak notlar paylaşabileceğiniz ve kütüphane verilerini dijital ortamda takip etmenizi sağlayan modern bir masaüstü uygulaması.
> 
> Bu proje, başlangıçta komut satırı (CLI) tabanlı bir kütüphane yönetim sistemi olarak geliştirilmiştir. Projenin kullanımını kolaylaştırmak ve daha etkileşimli bir kullanıcı deneyimi sunmak amacıyla, mevcut mantıksal katman üzerine **Tkinter** tabanlı grafiksel arayüz (GUI) entegre edilmiştir.
---
## Öne Çıkan Özellikler

Bu kütüphane yönetim sistemi, kullanıcıların etkileşimli bir arayüz üzerinden kitaplara erişmesini ve dijital notlar almasını sağlayan bir yapı sunar. Mevcut sürümdeki temel yetenekler şunlardır:

*   **Tkinter Tabanlı Arayüz:** Kullanıcı dostu, masaüstü üzerinde çalışan modern bir arayüz tasarımı.
*   **Merkezi Kitap Erişimi:** Sisteme giriş yapan tüm kullanıcılar, kütüphanede kayıtlı olan tüm kitapları görüntüleyebilir ve erişim sağlayabilir.
*   **İşbirlikçi Not Sistemi:** Kütüphanedeki tüm kitaplar için not bırakma özelliği aktif olup, eklenen notlar sistemdeki diğer tüm kullanıcılar tarafından görüntülenebilir.
*   **Kullanıcı Yetkilendirme (P-Level) Hazırlığı:** Proje mimarisi, "Kütüphane Yetkilisi" ve "Standart Kullanıcı" gibi farklı yetki seviyelerini destekleyecek şekilde tasarlanmıştır. Bu sayede yönetimsel işlemler (kitap ekleme/silme vb.) belirli kullanıcı seviyelerine kısıtlanabilir.
*   **Dinamik Veri İletişimi:** Arayüz, arka planda çalışan Python mantıksal katmanıyla sürekli veri alışverişinde bulunarak kitap verilerinin güncel kalmasını sağlar.

---

## 🛠️ Kullanılan Teknolojiler

* **Geliştirme Dili:** Python 
* **Kullanıcı Arayüzü (GUI):** CustomTkinter
* **Veritabanı Yönetimi:** SQLite
* **Veri Analizi ve Görselleştirme:** Pandas, Matplotlib
* **Dış Servis Entegrasyonu:** Open Library API

---

## 📂 Proje Dosya Yapısı

* `gui.py`: Uygulamanın ana giriş noktasıdır. Tkinter (CustomTkinter) tabanlı grafiksel arayüzü barındırır.
* `libro.py`: Projenin komut satırı (CLI) arayüzünü yöneten alternatif giriş dosyasıdır.
* `database.py`: SQLite veritabanı bağlantılarını ve CRUD (Ekle/Sil/Güncelle/Listele vb.) operasyonlarını yönetir.
* `models.py`: Kitap, Kullanıcı ve Kütüphane gibi temel veri sınıflarını (OOP nesnelerini) içerir.
* `exceptions.py`: Proje genelinde kullanılan özel hata sınıflarını (LibroTrackError vb.) barındırır.
* `raporlama.py`: Kullanıcı istatistiklerini hesaplayarak Pandas ve Matplotlib ile grafiklere dönüştürür.
* `test_kutuphane.py`: Pytest kullanılarak yazılmış birim testlerini (unit test) içerir.
* `config.yaml`: Loglama seviyeleri ve veritabanı dosya yolu gibi sistem yapılandırmalarını tutar.
* `requirements.txt`: Projenin çalışması için gerekli olan 3. parti kütüphanelerin (CustomTkinter, Pandas, Requests vb.) ve sürümlerinin listesini içerir.
---

## 💻 Kurulum Talimatları

Bu projeyi kaynak kodundan (terminal üzerinden) çalıştırmak için aşağıdaki adımları sırasıyla uygulayabilirsiniz. Sisteminizde Python 3'ün yüklü olduğundan ve kurulum sırasında "Add Python to PATH" seçeneğinin işaretlendiğinden emin olun.

### 1. Bağımlılıkların Yüklenmesi
Proje dosyalarının bulunduğu klasörü açın. Dosya yoluna tıklayıp `cmd` yazarak terminali bu dizinde başlatın ve aşağıdaki komutu çalıştırarak gerekli kütüphaneleri indirin:

```bash
pip install -r requirements.txt
```

### 2. Uygulamanın Başlatılması
Kütüphane kurulumları tamamlandıktan sonra ana arayüzü başlatmak için terminale şu komutu girin:

```bash
python Gui.py
```
---
## ⌨️Komut Satırı (CLI) Kullanım Kılavuzu
Projenin tüm fonksiyonlarını terminal üzerinden yönetmek isterseniz aşağıdaki komut setini kullanabilirsiniz.

Önemli: --kullanici parametresini kullanarak tüm işlemleri belirli bir kullanıcı profili adına gerçekleştirebilirsiniz. Eğer bu parametre girilmezse, işlemler varsayılan olarak admin profili ile yürütülür.

```bash
python libro.py --kullanici [kullanici_adi] [komut] [argümanlar]
```

## Komut Listesi

| Komut | Açıklama | Gerekli Parametreler |
| :--- | :--- | :--- |
| `kitap-ekle` | Kütüphaneye yeni kitap ekler. | `--isbn`, `--baslik`, `--yazar`, `--tur`, `--sayfa-sayisi` |
| `kitap-sil` | Kitabı ve tüm notlarını siler. | `--isbn` |
| `kitap-guncelle` | Kitap bilgilerini günceller. | `--isbn` |
| `kitap-listele` | Kitapları filtreleyerek listeler. | *Opsiyonel:* `--tur`, `--durum` |
| `durum-guncelle` | Okuma durumunu değiştirir. | `--isbn`, `--durum` |
| `kitap-ara` | Anahtar kelime ile arama yapar. | `--anahtar-kelime` |
| `not-ekle` | Kitaba not ekler. | `--isbn`, `--sayfa`, `--icerik` |
| `not-listele` | Kitaba ait notları gösterir. | `--isbn` |
| `istatistik-al` | Sayısal özet sunar ve grafik üretir. | Yok |
| `csv-aktar` | Okunan kitapları CSV dosyasına aktarır. | Yok |

---

## Örnek Kullanımlar

**Kitap Ekleme:**
```bash
python libro.py kitap-ekle --isbn 123456789 --baslik "Suç ve Ceza" --yazar "Dostoyevski" --tur "Klasik" --sayfa-sayisi 687
```

**Belirli Bir Kullanıcı Adına Kitap Ekleme:**
```bash
python libro.py --kullanici "Asude" kitap-ekle --isbn 987654321 --baslik "1984" --yazar "George Orwell" --tur "Bilim Kurgu" --sayfa-sayisi 328
```

**Okuma Durumunu Güncelleme:**
```bash
python libro.py durum-guncelle --isbn 123456789 --durum okundu
```
---
## ⚙️ Uygulamayı Test Etmek için Hazır Veri Girişi
Sistemi hızlıca test etmek ve veritabanını 10 adet gerçek kitap verisiyle doldurmak için aşağıdaki hazır PowerShell kodunu kullanabilirsiniz.

**Adım Adım Çalıştırma:**
1. Proje klasörünü açın.
2. Klasörün boş bir yerinde `Shift + Sağ Tık` yapıp **"PowerShell penceresini buradan açın"** seçeneğine tıklayın.
3. Sanal ortamı aktif edin: `.\temiz_ortam\Scripts\activate`
4. Aşağıdaki kodu kopyalayıp terminale yapıştırın ve **Enter**'a basın:

```bash
$kitaplar = @(
    @{isbn="9789750719387"; baslik="Dönüşüm"; yazar="Franz Kafka"; tur="Roman"; sayfa=100},
    @{isbn="9789750802966"; baslik="Kürk Mantolu Madonna"; yazar="Sabahattin Ali"; tur="Roman"; sayfa=177},
    @{isbn="9789750718380"; baslik="Suç ve Ceza"; yazar="Fyodor Dostoyevski"; tur="Klasik"; sayfa=687},
    @{isbn="9789754700145"; baslik="İnce Memed"; yazar="Yaşar Kemal"; tur="Roman"; sayfa=424},
    @{isbn="9789750739941"; baslik="Küçük Prens"; yazar="Antoine de Saint-Exupéry"; tur="Çocuk"; sayfa=112},
    @{isbn="9789750719394"; baslik="Şato"; yazar="Franz Kafka"; tur="Roman"; sayfa=352},
    @{isbn="9789752731234"; baslik="Simyacı"; yazar="Paulo Coelho"; tur="Roman"; sayfa=208},
    @{isbn="9789750720512"; baslik="1984"; yazar="George Orwell"; tur="Bilim Kurgu"; sayfa=352},
    @{isbn="9789750801754"; baslik="Puslu Kıtalar Atlası"; yazar="İhsan Oktay Anar"; tur="Roman"; sayfa=256},
    @{isbn="9789750719370"; baslik="Dava"; yazar="Franz Kafka"; tur="Roman"; sayfa=288}
)
foreach ($k in $kitaplar) { python libro.py kitap-ekle --isbn$k.isbn --baslik $k.baslik --yazar$k.yazar --tur $k.tur --sayfa-sayisi$k.sayfa }