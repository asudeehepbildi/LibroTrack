import customtkinter as ctk
from tkinter import messagebox
import logging
import os
from PIL import Image
from controllers.kitap_controller import KitapController
from services.api_service import open_library_api_cek, url_to_image
from models.exceptions import LibroTrackError

# Siyah-Beyaz-Gri Minimalist Tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class LibroTrackGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.controller = KitapController()
        self.aktif_kullanici = "admin"
        self.geometry("1350x700")
        self.title("LibroTrack Yönetim Paneli")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color="#1a1a1a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="LIBROTRACK", font=("Arial", 20, "bold"), text_color="white").pack(pady=30)
        ctk.CTkButton(self.sidebar, text="Kitap Ekle", fg_color="#404040", height=40,
                      command=self.ekran_kitap_ekle).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Kütüphane", fg_color="#404040", height=40, command=self.ekran_listele).pack(
            pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="Kullanıcılar", fg_color="#404040", height=40,
                      command=self.ekran_kullanicilar).pack(pady=5, padx=10, fill="x")
        ctk.CTkButton(self.sidebar, text="İstatistikler", fg_color="#404040", height=40,
                      command=self.ekran_istatistik).pack(pady=5, padx=10, fill="x")

        self.main_frame = ctk.CTkFrame(self, fg_color="#d1d1d1", corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.ekran_listele()

    def clear_main(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def get_center_frame(self):
        self.clear_main()
        center = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        center.pack(expand=True)
        return center

    def handle_error(self, message):
        logging.error(f"Hata: {message}")
        messagebox.showerror("Hata", str(message))

    # --- KULLANICI YÖNETİMİ ---
    def kullanici_sil(self, kullanici_adi):
        if messagebox.askyesno("Onay", f"'{kullanici_adi}' adlı kullanıcıyı silmek istiyor musunuz?"):
            basarili, msj = self.controller.kullanici_sil(kullanici_adi)
            if basarili:
                messagebox.showinfo("Başarılı", msj)
                self.ekran_kullanicilar()
            else:
                self.handle_error(msj)

    def ekran_kullanicilar(self):
        c = self.get_center_frame()
        ctk.CTkLabel(c, text="Kullanıcı Yönetimi", font=("Arial", 16, "bold"), text_color="black").pack(pady=10)
        add_frame = ctk.CTkFrame(c, fg_color="transparent")
        add_frame.pack(pady=5)
        self.new_user_entry = ctk.CTkEntry(add_frame, placeholder_text="Yeni Kullanıcı Adı", width=250)
        self.new_user_entry.pack(side="left", padx=(0, 5))
        ctk.CTkButton(add_frame, text="Kullanıcı Ekle", fg_color="black", width=100,
                      command=self.kullanici_ekle_islem).pack(side="left")
        self.user_table_area = ctk.CTkScrollableFrame(c, width=400, height=300, fg_color="white")
        self.user_table_area.pack(pady=15)
        header = ctk.CTkFrame(self.user_table_area, fg_color="#333")
        header.pack(fill="x", pady=5)
        ctk.CTkLabel(header, text="Kullanıcı Adı", text_color="white", width=250, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="İşlemler", text_color="white", width=100, anchor="w").pack(side="left", padx=5)

        for user in self.controller.tum_kullanicilari_getir():
            row = ctk.CTkFrame(self.user_table_area, fg_color="#e0e0e0")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=user, text_color="black", font=("Arial", 14), width=250, anchor="w").pack(
                side="left", padx=5)
            btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=100)
            btn_frame.pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Sil", width=60, fg_color="red",
                          command=lambda u=user: self.kullanici_sil(u)).pack(side="left", padx=2)

    def kullanici_ekle_islem(self):
        u_name = self.new_user_entry.get().strip()
        basarili, msj = self.controller.kullanici_ekle(u_name)
        if basarili:
            messagebox.showinfo("Başarılı", msj)
            self.ekran_kullanicilar()
        else:
            self.handle_error(msj)

    # --- İSTATİSTİKLER ---
    def ekran_istatistik(self):
        c = self.get_center_frame()
        ctk.CTkLabel(c, text="Kütüphane İstatistikleri", font=("Arial", 16, "bold"), text_color="black").pack(pady=10)
        self.user_combo = ctk.CTkComboBox(c, values=self.controller.tum_kullanicilari_getir(), width=250)
        self.user_combo.set("Kullanıcı Seçiniz")
        self.user_combo.pack(pady=10)
        if self.user_combo._values:
            self.user_combo.set(
                self.aktif_kullanici if self.aktif_kullanici in self.user_combo._values else self.user_combo._values[0])

        ctk.CTkButton(c, text="Raporu Göster (Hızlı)", fg_color="black",
                      command=lambda: self.rapor_goster_islem(self.user_combo.get().strip(), force_update=False)).pack(
            pady=10)
        ctk.CTkButton(c, text="Grafikleri Yeniden Hesapla", fg_color="green",
                      command=lambda: self.rapor_goster_islem(self.user_combo.get().strip(), force_update=True)).pack(
            pady=5)

    def rapor_goster_islem(self, k_adi, force_update=False):
        if not k_adi or k_adi == "Kullanıcı Seçiniz":
            self.handle_error("Lütfen bir kullanıcı seçin.")
            return

        basarili, msj = self.controller.rapor_olustur(k_adi, force_update)
        if not basarili:
            self.handle_error(msj)
            return

        self.clear_main()
        report_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        report_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(report_frame, text=f"{k_adi} İstatistik Raporu", font=("Arial", 20, "bold"),
                     text_color="black").pack(pady=10)

        ozet = self.controller.istatistik_ozet_getir(k_adi)
        ozet_metin = f"Toplam Kitap: {ozet['toplam']} | Okunan Kitap: {ozet['okunan']} | Okunan Toplam Sayfa: {ozet['sayfa']}"
        ctk.CTkLabel(report_frame, text=ozet_metin, font=("Arial", 14), text_color="black").pack(pady=5)

        if os.path.exists(f"{k_adi}_tur_istatistik.png"):
            ctk.CTkLabel(report_frame, image=ctk.CTkImage(Image.open(f"{k_adi}_tur_istatistik.png"), size=(600, 450)),
                         text="").pack(pady=10)
        if os.path.exists(f"{k_adi}_aylik_trend.png"):
            ctk.CTkLabel(report_frame, image=ctk.CTkImage(Image.open(f"{k_adi}_aylik_trend.png"), size=(800, 400)),
                         text="").pack(pady=10)
        ctk.CTkButton(report_frame, text="Geri Dön", fg_color="gray", command=self.ekran_istatistik).pack(pady=20)

    # --- LİSTELEME EKRANI ---
    def ekran_listele(self):
        self.clear_main()
        f_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f_frame.pack(fill="x", padx=10, pady=5)
        self.f_user = ctk.CTkEntry(f_frame, placeholder_text="Kullanıcı", width=100)
        self.f_user.pack(side="left", padx=2)
        self.f_tur = ctk.CTkEntry(f_frame, placeholder_text="Tür", width=100)
        self.f_tur.pack(side="left", padx=2)
        self.f_baslik = ctk.CTkEntry(f_frame, placeholder_text="Başlık", width=100)
        self.f_baslik.pack(side="left", padx=2)
        self.f_yazar = ctk.CTkEntry(f_frame, placeholder_text="Yazar", width=100)
        self.f_yazar.pack(side="left", padx=2)
        self.f_durum = ctk.CTkEntry(f_frame, placeholder_text="Durum", width=100)
        self.f_durum.pack(side="left", padx=2)
        ctk.CTkButton(f_frame, text="Listele", fg_color="black", command=self.listele_ve_temizle_islem).pack(
            side="left", padx=5)
        self.table_area = ctk.CTkScrollableFrame(self.main_frame, fg_color="white")
        self.table_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.tabloyu_doldur()

    def listele_ve_temizle_islem(self):
        self.tabloyu_doldur()
        for entry in [self.f_user, self.f_tur, self.f_baslik, self.f_yazar, self.f_durum]:
            entry.delete(0, "end")
            entry.configure(placeholder_text=entry.cget("placeholder_text"))
        self.focus()

    def tabloyu_doldur(self):
        self.table_area.destroy()
        self.table_area = ctk.CTkScrollableFrame(self.main_frame, fg_color="white")
        self.table_area.pack(fill="both", expand=True, padx=10, pady=10)
        widths = [200, 150, 130, 100, 70, 110, 90]
        action_w = 250
        header = ctk.CTkFrame(self.table_area, fg_color="#333")
        header.pack(fill="x", pady=5)
        for h, w in zip(["Başlık", "Yazar", "ISBN", "Kullanıcı", "Sayfa", "Tür", "Durum"], widths):
            ctk.CTkLabel(header, text=h, text_color="white", width=w, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="İşlemler", text_color="white", width=action_w, anchor="w").pack(side="left", padx=5)

        try:
            kitaplar = self.controller.tum_kitaplari_getir()
            kullanici_f, tur_f, baslik_f = self.f_user.get().strip().lower(), self.f_tur.get().strip().lower(), self.f_baslik.get().strip().lower()
            yazar_f, durum_f = self.f_yazar.get().strip().lower(), self.f_durum.get().strip().lower()

            for k in kitaplar:
                if ((kullanici_f and kullanici_f not in k[5].lower()) or (tur_f and tur_f not in k[3].lower()) or
                        (baslik_f and baslik_f not in k[1].lower()) or (yazar_f and yazar_f not in k[2].lower()) or
                        (durum_f and durum_f not in k[6].lower())):
                    continue
                row = ctk.CTkFrame(self.table_area, fg_color="#e0e0e0")
                row.pack(fill="x", pady=2)
                for d, w in zip([k[1], k[2], k[0], k[5], k[4], k[3], k[6]], widths):
                    ctk.CTkLabel(row, text=str(d), text_color="black", width=w, anchor="w").pack(side="left", padx=5)
                btn_frame = ctk.CTkFrame(row, fg_color="transparent", width=action_w)
                btn_frame.pack(side="left", padx=5)
                ctk.CTkButton(btn_frame, text="Detay", width=50, fg_color="blue",
                              command=lambda isbn=k[0]: self.ekran_detay(isbn)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="Not", width=50, fg_color="green",
                              command=lambda isbn=k[0]: self.ekran_not_ekle(isbn)).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="Guncelle", width=60, fg_color="orange",
                              command=lambda isbn=k[0], user=k[5]: self.ekran_kitap_guncelle(isbn, user)).pack(
                    side="left", padx=2)
                ctk.CTkButton(btn_frame, text="Sil", width=50, fg_color="red",
                              command=lambda isbn=k[0], user=k[5]: self.kitap_sil(isbn, user)).pack(side="left", padx=2)
        except LibroTrackError as e:
            self.handle_error(e)

    def kitap_sil(self, isbn, kullanici_adi):
        if messagebox.askyesno("Onay", "Kitabı silmek istiyor musunuz?"):
            basarili, msj = self.controller.kitap_sil(isbn, kullanici_adi)
            if basarili:
                self.ekran_listele()
            else:
                self.handle_error(msj)

    # --- KİTAP EKLEME VE GÜNCELLEME EKRANLARI ---
    def ekran_kitap_ekle(self):
        c = self.get_center_frame()
        ctk.CTkLabel(c, text="* ISBN, Başlık, Yazar, Tür ve Sayfa alanları zorunludur.", font=("Arial", 12, "bold"),
                     text_color="#000033").pack(pady=(0, 15))
        isbn_frame = ctk.CTkFrame(c, fg_color="transparent", width=250)
        isbn_frame.pack(pady=5)
        self.i_isbn = ctk.CTkEntry(isbn_frame, placeholder_text="ISBN", width=160)
        self.i_isbn.grid(row=0, column=0, padx=(0, 5))
        ctk.CTkButton(isbn_frame, text="API ile Doldur", width=65, height=28, fg_color="green",
                      command=self.api_ile_doldur).grid(row=0, column=1)
        self.i = {f: ctk.CTkEntry(c, placeholder_text=f, width=250) for f in ["Başlık", "Yazar", "Sayfa"]}
        for e in self.i.values(): e.pack(pady=5)

        turler = ["Tür Seçiniz", "Roman", "Şiir", "Tarih", "Bilim Kurgu", "Eğitim", "Çocuk", "Diğer"]
        self.tur_combo = ctk.CTkComboBox(c, values=turler, width=250)
        self.tur_combo.pack(pady=5)
        self.tur_combo.set("Tür Seçiniz")

        kullanicilar = self.controller.tum_kullanicilari_getir()
        self.user_combo = ctk.CTkComboBox(c, values=kullanicilar, width=250)
        self.user_combo.pack(pady=5)
        self.user_combo.set(
            self.aktif_kullanici if self.aktif_kullanici in kullanicilar else (kullanicilar[0] if kullanicilar else ""))

        ctk.CTkButton(c, text="Kaydet", fg_color="black", command=self.kitap_kaydet).pack(pady=20)
        ctk.CTkButton(c, text="Geri", fg_color="gray", command=self.ekran_listele).pack(pady=5)

    def api_ile_doldur(self):
        isbn = self.i_isbn.get().strip()
        if not isbn:
            self.handle_error("ISBN alanı boş bırakılmamalıdır.")
            return
        data = open_library_api_cek(isbn)
        if data["baslik"]:
            self.i["Başlık"].delete(0, "end");
            self.i["Başlık"].insert(0, data["baslik"])
            self.i["Yazar"].delete(0, "end");
            self.i["Yazar"].insert(0, data["yazar"])
            self.i["Sayfa"].delete(0, "end");
            self.i["Sayfa"].insert(0, data["sayfa"])
            messagebox.showinfo("Başarılı", "Bilgiler API'den çekildi.")
        else:
            self.handle_error("Bu ISBN ile sistemde kitap bulunamadı.")

    def kitap_kaydet(self):
        isbn = self.i_isbn.get().strip()
        baslik = self.i["Başlık"].get().strip()
        yazar = self.i["Yazar"].get().strip()
        tur = self.tur_combo.get()
        sayfa_str = self.i["Sayfa"].get().strip()
        kullanici = self.user_combo.get().strip()

        basarili, msj = self.controller.kitap_ekle(isbn, baslik, yazar, tur, sayfa_str, kullanici)
        if basarili:
            messagebox.showinfo("Başarılı", msj)
            self.ekran_listele()
        else:
            self.handle_error(msj)

    def ekran_kitap_guncelle(self, isbn, kullanici_adi):
        c = self.get_center_frame()
        turler = ["Tür Seçiniz", "Roman", "Şiir", "Tarih", "Bilim Kurgu", "Eğitim", "Çocuk", "Diğer"]
        self.g = {
            "Tür": ctk.CTkComboBox(c, values=turler, width=250),
            "Sayfa": ctk.CTkEntry(c, placeholder_text="Yeni Sayfa", width=250),
            "Durum": ctk.CTkOptionMenu(c, values=["Seçiniz", "okunacak", "okunuyor", "okundu"], width=250),
        }
        self.g["Tür"].set("Tür Seçiniz")
        for e in self.g.values(): e.pack(pady=5)
        ctk.CTkButton(c, text="Güncelle", fg_color="black",
                      command=lambda: self.kitap_guncelle_islem(isbn, kullanici_adi)).pack(pady=10)
        ctk.CTkButton(c, text="Geri", fg_color="gray", command=self.ekran_listele).pack(pady=5)

    def kitap_guncelle_islem(self, isbn, kullanici_adi):
        tur = self.g["Tür"].get()
        durum = self.g["Durum"].get()
        sayfa_raw = self.g["Sayfa"].get().strip()

        basarili, msj = self.controller.kitap_guncelle(isbn, kullanici_adi, tur, durum, sayfa_raw)
        if basarili:
            messagebox.showinfo("Başarılı", msj)
            self.ekran_listele()
        else:
            self.handle_error(msj)

    def ekran_not_ekle(self, isbn):
        c = self.get_center_frame()
        self.n = {"Sayfa": ctk.CTkEntry(c, placeholder_text="Sayfa", width=250),
                  "İçerik": ctk.CTkEntry(c, placeholder_text="Not", width=250)}
        for e in self.n.values(): e.pack(pady=5)
        ctk.CTkLabel(c, text="Lütfen sayfa numarası ve notunuzu giriniz.", font=("Arial", 12, "bold"),
                     text_color="#000033").pack(pady=(0, 15))
        ctk.CTkButton(c, text="Ekle", fg_color="black", command=lambda: self.not_ekle_islem(isbn)).pack(pady=10)
        ctk.CTkButton(c, text="Geri", fg_color="gray", command=self.ekran_listele).pack(pady=5)

    def not_ekle_islem(self, isbn):
        sayfa_str = self.n["Sayfa"].get()
        icerik = self.n["İçerik"].get()

        basarili, msj = self.controller.not_ekle(isbn, sayfa_str, icerik)
        if basarili:
            messagebox.showinfo("Başarılı", msj)
            self.ekran_listele()
        else:
            self.handle_error(msj)

    # --- DETAY EKRANI ---
    def ekran_detay(self, isbn):
        self.clear_main()
        api = open_library_api_cek(isbn)
        try:
            kitap = self.controller.kitap_getir_isbn(isbn)
            container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            container.pack(fill="both", expand=True, padx=20, pady=20)
            container.grid_columnconfigure(1, weight=1)
            left_frame = ctk.CTkFrame(container, fg_color="transparent")
            left_frame.grid(row=0, column=0, sticky="n", padx=20)

            kapak_img = url_to_image(api["kapak_url"])
            if kapak_img:
                ctk.CTkLabel(left_frame, image=kapak_img, text="").pack(pady=10)
            else:
                ctk.CTkLabel(left_frame, text="Kitap görseli yok", text_color="red").pack(pady=10)

            right_frame = ctk.CTkFrame(container, fg_color="transparent")
            right_frame.grid(row=0, column=1, sticky="nsew", padx=20)
            for label, val in [("Başlık", kitap[1]), ("Yazar", kitap[2]), ("ISBN", kitap[0]), ("Tür", kitap[3]),
                               ("Sayfa", kitap[4]), ("Durum", kitap[6]), ("Bitiş", kitap[7] or "-")]:
                row = ctk.CTkFrame(right_frame, fg_color="transparent")
                row.pack(anchor="w", pady=2)
                ctk.CTkLabel(row, text=f"{label}:", font=("Arial", 14, "bold"), width=120, anchor="w",
                             text_color="black").pack(side="left")
                ctk.CTkLabel(row, text=str(val), font=("Arial", 14), text_color="black").pack(side="left")

            ctk.CTkLabel(right_frame, text="Açıklama:", font=("Arial", 14, "bold"), text_color="black").pack(anchor="w",
                                                                                                             pady=(10,
                                                                                                                   0))
            ctk.CTkLabel(right_frame, text=api["aciklama"], wraplength=400, text_color="black", justify="left").pack(
                anchor="w", pady=5)
            ctk.CTkLabel(right_frame, text="Notlar:", font=("Arial", 14, "bold"), text_color="black").pack(anchor="w",
                                                                                                           pady=(10, 0))
            notes_scroll = ctk.CTkScrollableFrame(right_frame, width=400, height=120, fg_color="#e0e0e0")
            notes_scroll.pack(anchor="w", pady=5, fill="x")

            notlar = self.controller.notlari_getir(isbn)
            if notlar:
                for sayfa, icerik in notlar:
                    ctk.CTkLabel(notes_scroll, text=f"Sayfa {sayfa}: {icerik}", text_color="black", wraplength=380,
                                 justify="left").pack(anchor="w", pady=2)
            else:
                ctk.CTkLabel(notes_scroll, text="Not yok.", text_color="black", justify="left").pack(anchor="w", pady=2)
            ctk.CTkButton(container, text="Geri", fg_color="gray", command=self.ekran_listele).grid(row=1, column=0,
                                                                                                    columnspan=2,
                                                                                                    pady=20)
        except LibroTrackError as e:
            self.handle_error(e)