import requests
from bs4 import BeautifulSoup
import os

print("RADAR LUNDIN MINING — CHILE")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://jobs.lundinmining.com"
SEARCH_URL = BASE_URL + "/tile-search-results/?q=&locationsearch=Chile&startrow={}"

def obtener_empleos_lundin():
    empleos = []
    startrow = 0
    step = 25

    while True:
        url = SEARCH_URL.format(startrow)
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        jobs = soup.find_all("li", class_="job-tile")

        if not jobs:
            break

        for job in jobs:
            titulo_tag = job.find("a", class_="jobTitle-link")
            if titulo_tag:
                titulo = titulo_tag.text.strip()
                link = BASE_URL + titulo_tag["href"]
                empleos.append(f"{titulo}\n{link}")

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
