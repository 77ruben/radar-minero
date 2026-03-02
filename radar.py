import requests
from bs4 import BeautifulSoup
import os

print("RADAR COLLAHUASI ACTIVO")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URL = "https://www.collahuasi.cl/trabaja-con-nosotros/ofertas-laborales/"
BASE = "https://www.collahuasi.cl"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

empleos = []

# Buscar enlaces que contengan "programa-aprendices"
for link in soup.find_all("a", href=True):
    href = link["href"]

    if "programa-aprendices" in href:
        titulo = link.get_text(strip=True)

        # Si el link es relativo, completarlo
        if not href.startswith("http"):
            href = BASE + href

        empleos.append(f"{titulo}\n{href}")

if not empleos:
    message = "Radar Collahuasi activo.\nNo se detectaron programas de aprendices."
else:
    message = "🚨 COLLAHUASI 🚨\n\n" + "\n\n".join(empleos)

telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(telegram_url, data={
    "chat_id": CHAT_ID,
    "text": message[:4000]
})

print("Proceso finalizado")
