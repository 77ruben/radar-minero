import requests
from bs4 import BeautifulSoup
import os

print("INICIO RADAR MINERO")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# PALABRAS CLAVE SEGÚN TU PERFIL
KEYWORDS = [
    "supervisor",
    "mantencion",
    "mantenimiento",
    "administrador",
    "contrato",
    "ingeniero",
    "planificador",
    "jefe"
]

# URL INDEED CHILE MINERIA
URL = "https://cl.indeed.com/jobs?q=mineria&l=Chile&sort=date"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")

jobs = soup.select(".job_seen_beacon")

encontrados = []

for job in jobs:

    titulo = job.select_one("h2").text.lower()

    link = job.select_one("a")["href"]

    link = "https://cl.indeed.com" + link

    if any(palabra in titulo for palabra in KEYWORDS):

        encontrados.append(
            titulo + "\n" + link
        )

# MENSAJE FINAL

if encontrados:

    mensaje = "🚨 EMPLEOS MINEROS ENCONTRADOS:\n\n"

    for e in encontrados[:5]:

        mensaje += e + "\n\n"

else:

    mensaje = "Radar Minero activo.\nNo hay empleos nuevos que coincidan con tu perfil."

# ENVIAR A TELEGRAM

urlTelegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": mensaje
}

requests.post(urlTelegram, data=data)

print("FIN RADAR")
