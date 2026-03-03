import requests
from bs4 import BeautifulSoup
import os

print("RADAR LUNDIN MINING — CHILE FILTRADO REAL")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://jobs.lundinmining.com"
SEARCH_URL = BASE_URL + "/tile-search-results/?q=&startrow={}"

def obtener_empleos_lundin():
    empleos = []
    startrow = 0
    step = 25
    max_paginas = 3

    for _ in range(max_paginas):

        url = SEARCH_URL.format(startrow)
        response = requests.get(url, headers=HEADERS)

        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        jobs = soup.find_all("li", class_="job-tile")

        if not jobs:
            break

        nuevos = 0

        for job in jobs:
            titulo_tag = job.find("a", class_="jobTitle-link")
            location_tag = job.find("span", class_="jobLocation")

            if titulo_tag and location_tag:

                ubicacion = location_tag.text.strip()

                # FILTRO REAL CHILE
                if ", CL" not in ubicacion:
                    continue

                titulo = titulo_tag.text.strip()
                link = BASE_URL + titulo_tag["href"]

                registro = f"{titulo}\n{ubicacion}\n{link}"

                if registro not in empleos:
                    empleos.append(registro)
                    nuevos += 1

        if nuevos == 0:
            break

        startrow += step

    return empleos


empleos = obtener_empleos_lundin()

if empleos:
    mensaje = "🚨 LUNDIN MINING (Chile) 🚨\n\n"
    mensaje += "\n\n".join(empleos)

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": mensaje}
    )

    print("Enviado a Telegram correctamente.")

else:
    print("Sin empleos detectados en Lundin Chile.")
