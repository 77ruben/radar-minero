import requests
from bs4 import BeautifulSoup
import os

print("INICIO RADAR MINERO")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

KEYWORDS = [
    "supervisor",
    "mantencion",
    "mantenimiento",
    "planner",
    "planificador",
    "ingeniero",
    "administrador",
    "contrato"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

encontrados = []

for pagina in range(0, 30, 10):

    url = f"https://cl.indeed.com/jobs?q=mineria&l=Chile&sort=date&start={pagina}"

    response = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(response.text, "html.parser")

    trabajos = soup.select(".job_seen_beacon")

    for trabajo in trabajos:

        titulo = trabajo.select_one("h2").text.strip()

        link = trabajo.select_one("a")["href"]

        link = "https://cl.indeed.com" + link

        if any(p in titulo.lower() for p in KEYWORDS):

            encontrados.append(titulo + "\n" + link)


if encontrados:

    mensaje = "🚨 RADAR MINERO 🚨\n\n"

    for e in encontrados[:10]:

        mensaje += e + "\n\n"

else:

    mensaje = "Radar activo sin novedades"


urlTelegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": mensaje
}

requests.post(urlTelegram, data=data)

print("FIN RADAR MINERO")
