import requests
from bs4 import BeautifulSoup
import os

print("INICIO RADAR MINERO PRO")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# FILTRO PROFESIONAL MINERO COMPLETO

KEYWORDS = [

    "supervisor",
    "mantencion",
    "mantenimiento",
    "planner",
    "planificador",
    "ingeniero",
    "confiabilidad",
    "reliability",
    "administrador",
    "contract",
    "contrato",
    "maintenance",
    "jefe",
    "programador",
    "scheduler"
]

URL = "https://cl.indeed.com/jobs?q=mineria&l=Chile&sort=date"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

soup = BeautifulSoup(response.text, "html.parser")

jobs = soup.select(".job_seen_beacon")

encontrados = []

for job in jobs:

    titulo = job.select_one("h2").text.strip()

    titulo_lower = titulo.lower()

    link = job.select_one("a")["href"]

    link = "https://cl.indeed.com" + link

    if any(p in titulo_lower for p in KEYWORDS):

        encontrados.append(
            titulo + "\n" + link
        )

# MENSAJE

if encontrados:

    mensaje = "🚨 EMPLEOS MINEROS DETECTADOS 🚨\n\n"

    for e in encontrados[:10]:

        mensaje += e + "\n\n"

else:

    mensaje = "Radar Minero activo.\nSin empleos nuevos compatibles."

# TELEGRAM

urlTelegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": mensaje
}

requests.post(urlTelegram, data=data)

print("FIN RADAR MINERO PRO")
