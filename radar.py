import requests
from bs4 import BeautifulSoup
import os

print("RADAR COLLAHUASI ACTIVO")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URL = "https://www.collahuasi.cl/trabaja-con-nosotros/ofertas-laborales/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Buscamos elementos específicos de empleo: <h2>, <a>, o clase CSS
empleos = []

# Ejemplo: si el empleo está en un <h2> o en un <a> con texto relevante
for tag in soup.find_all(["h2", "a"]):
    texto = tag.get_text(strip=True)

    # Filtramos por "Aprendiz" (para el programa de aprendices)
    if "aprendiz" in texto.lower():
        link = tag.get("href", "")

        # Si es relativo, completemos la URL
        if link and not link.startswith("http"):
            link = "https://www.collahuasi.cl" + link

        empleos.append(f"{texto}\n{link}")

# Armar mensaje para Telegram
if not empleos:
    message = "Radar Collahuasi activo.\nNo se detectó el empleo de programa de aprendices."
else:
    message = "🚨 COLLAHUASI - Empleo Detectado 🚨\n\n" + "\n\n".join(empleos)

telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(telegram_url, data={
    "chat_id": CHAT_ID,
    "text": message[:4000]
})

print("Proceso finalizado")
