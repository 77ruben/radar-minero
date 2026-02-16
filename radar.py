import requests
import os
from bs4 import BeautifulSoup

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    requests.post(url, data=data)


def buscar():

    url = "https://cl.indeed.com/jobs?q=mining&l=Chile"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    trabajos = soup.select("h2.jobTitle")

    lista = []

    for t in trabajos[:10]:

        lista.append(t.get_text())

    return lista


empleos = buscar()

if empleos:

    mensaje = "Radar Minero\n\n"

    for e in empleos:

        mensaje += "• " + e + "\n"

else:

    mensaje = "Radar Minero activo\nSin resultados"


enviar(mensaje)
