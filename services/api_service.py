import requests
import logging
import io
from PIL import Image
import customtkinter as ctk

def open_library_api_cek(isbn: str) -> dict:
    api_verisi = {
        "aciklama": "API'de açıklama bulunamadı.",
        "kapak_url": "Kapak yok",
        "baslik": "",
        "yazar": "",
        "sayfa": "",
    }
    try:
        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            key = f"ISBN:{isbn}"
            if key in data:
                book = data[key]
                api_verisi["aciklama"] = book.get("notes", api_verisi["aciklama"])
                api_verisi["kapak_url"] = book.get("cover", {}).get("large", api_verisi["kapak_url"])
                api_verisi["baslik"] = book.get("title", "")
                authors = book.get("authors", [])
                api_verisi["yazar"] = ", ".join([a.get("name", "") for a in authors])
                api_verisi["sayfa"] = str(book.get("number_of_pages", ""))
    except requests.RequestException as e:
        logging.debug(f"API bağlantı hatası: {e}")
    return api_verisi

def url_to_image(url):
    try:
        response = requests.get(url, timeout=5)
        img_data = io.BytesIO(response.content)
        pil_image = Image.open(img_data)
        return ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 300))
    except (requests.RequestException, IOError):
        return None