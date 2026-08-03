import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import yaml
import logging
import os
from exceptions import VeritabaniHatasi, RaporlamaHatasi

# YAML dosyasını okuma ve veritabanı yolunu belirleme
try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # config.yaml dosyasındaki 'veritabanı' anahtarına göre yolu alıyoruz
    DB_YOLU = config.get("veritabanı", {}).get("yol", "data/librotrack.db")
except Exception:
    DB_YOLU = "data/librotrack.db"


def istatistikleri_olustur(kullanici_adi: str, force_update: bool = False) -> None:
    """Kullanıcı kütüphanesindeki verilerden pasta ve çubuk (bar) grafikleri oluşturur.

    Args:
        kullanici_adi (str): Grafikleri çizilecek olan kullanıcı profilinin adı.
        force_update (bool): Grafikler diskte olsa bile yeniden çizilmeyi zorlamak için flag.
    """
    # EKLENEN OPTİMİZASYON: Dosyalar zaten varsa ve zorunlu güncelleme istenmediyse fonksiyondan çık
    if (
        not force_update
        and os.path.exists(f"{kullanici_adi}_tur_istatistik.png")
        and os.path.exists(f"{kullanici_adi}_aylik_trend.png")
    ):
        return
    try:
        with sqlite3.connect(DB_YOLU) as conn:
            # 1. Pasta Grafiği
            df_tur = pd.read_sql_query(
                "SELECT tur, COUNT(*) as adet FROM kitaplar WHERE kullanici_adi = ? GROUP BY tur",
                conn,
                params=(kullanici_adi,),
            )
            if not df_tur.empty:
                try:
                    plt.figure(figsize=(8, 6))
                    plt.pie(
                        df_tur["adet"],
                        labels=df_tur["tur"],
                        autopct="%1.1f%%",
                        startangle=140,
                    )
                    plt.title(f"{kullanici_adi} - Kitap Türü Dağılımı")
                    plt.savefig(f"{kullanici_adi}_tur_istatistik.png", dpi=300)
                    plt.close()  # RAM kullanımını optimize etmek için çizim bittikten sonra figürü kapatır.
                except Exception as e:
                    raise RaporlamaHatasi(f"Pasta grafiği çizilemedi: {e}")

            # 2. Bar Grafiği
            df_ay = pd.read_sql_query(
                "SELECT bitis_tarihi FROM kitaplar WHERE durum = 'okundu' AND kullanici_adi = ? AND bitis_tarihi IS NOT NULL",
                conn,
                params=(kullanici_adi,),
            )
            if not df_ay.empty:
                try:
                    df_ay["bitis_tarihi"] = pd.to_datetime(
                        df_ay["bitis_tarihi"]
                    )  # tarih bilgisi veritabanından string olarak gelir, bize tarih olarak lazım olduğu için dönüştürülür.

                    # .dt.to_period("M"): Gün bazlı tarihleri Ay-Yıl periyoduna yuvarlar ki aylık gruplama yapılabilsin.
                    df_ay["ay"] = df_ay["bitis_tarihi"].dt.to_period("M")
                    aylik_okuma = df_ay.groupby("ay").size()

                    plt.figure(figsize=(10, 5))
                    aylik_okuma.plot(kind="bar", color="skyblue", edgecolor="black")
                    plt.title(f"{kullanici_adi} - Aylık Okuma Trendi")
                    plt.xlabel("Ay / Yıl")
                    plt.ylabel("Okunan Kitap Sayısı")
                    plt.xticks(rotation=45)
                    plt.tight_layout()  # Alt ve yan eksen yazılarının grafiğin dışına taşıp kesilmesini önler.
                    plt.savefig(f"{kullanici_adi}_aylik_trend.png", dpi=300)
                    plt.close()
                except Exception as e:
                    raise RaporlamaHatasi(f"Bar grafiği çizilemedi: {e}")
    except sqlite3.Error as e:
        raise VeritabaniHatasi(f"Grafik SQL hatası: {e}")
