import requests
from bs4 import BeautifulSoup
import os

print("RADAR KINROSS GOLD — CHILE")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

URL = "https://jobs.kinross.com/search/?createNewAlert=false&q=&locationsearch=Chile+"

def obtener_empleos_kinross():
    empleos = []

    response = requests.get(URL, headers=HEADERS)

    if response.status_code != 200:
        print("Error al conectar con Kinross")
        return empleos

    soup = BeautifulSoup(response.text, "html.parser")

    # Los empleos vienen en filas tipo job-result
    jobs = soup.find_all("tr", class_="data-row")

    for job in jobs:

        titulo_tag = job.find("a")

        if titulo_tag:
            titulo = titulo_tag.text.strip()
            link = "https://jobs.kinross.com" + titulo_tag["href"]

            texto_completo = job.get_text(" ", strip=True)

            # Filtro real Chile
            if "Chile" not in texto_completo:
                continue

            registro = f"{titulo}\n{link}"

            if registro not in empleos:
                empleos.append(registro)

    return empleos


empleos = obtener_empleos_kinross()

if empleos:
    mensaje = "🚨 KINROSS GOLD (Chile) 🚨\n\n"
    mensaje += "\n\n".join(empleos)

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": mensaje}
    )

    print("Enviado a Telegram correctamente.")

else:
    print("Sin empleos detectados en Kinross Chile.")
