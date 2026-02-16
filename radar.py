import requests
import os
from bs4 import BeautifulSoup

# usar EXACTAMENTE los mismos nombres que ya funcionan en GitHub Secrets
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def enviar_telegram(mensaje):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    r = requests.post(url, data=data)

    print("Respuesta Telegram:", r.text)


def buscar_indeed():

    url = "https://cl.indeed.com/jobs?q=mineria&l=Chile"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    trabajos = soup.select("h2.jobTitle")

    resultados = []

    for trabajo in trabajos[:5]:

        titulo = trabajo.get_text(strip=True)

        resultados.append(titulo)

    return resultados


# lógica principal
empleos = buscar_indeed()

if empleos:

    mensaje = "⛏ RADAR MINERO ACTIVO\n\n"

    for e in empleos:

        mensaje += "• " + e + "\n"

else:

    mensaje = "⛏ RADAR MINERO ACTIVO\nSin resultados nuevos"


# ESTA es la misma función que ya te funcionó
enviar_telegram(mensaje)
