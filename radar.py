import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA = "memoria.json"

try:
    with open(MEMORIA,"r") as f:
        memoria = json.load(f)
except:
    memoria = []

URL = "https://www.laborum.cl/empleos-busqueda-mineria.html"

def enviar(msg):

    requests.post(

        f"https://api.telegram.org/bot{TOKEN}/sendMessage",

        data={"chat_id":CHAT_ID,"text":msg}

    )

enviar("RADAR MINERO LABORUM INICIADO")

html = requests.get(URL).text

soup = BeautifulSoup(html,"html.parser")

empleos = soup.find_all("a")

nuevos = 0

for e in empleos:

    titulo = e.get_text().strip()

    if "min" in titulo.lower():

        if titulo not in memoria and len(titulo) > 15:

            memoria.append(titulo)

            nuevos += 1

            enviar(f"""

EMPLEO MINERO DETECTADO

{titulo}

Fuente: Laborum

""")


with open(MEMORIA,"w") as f:

    json.dump(memoria,f)


enviar(f"""

RADAR FINALIZADO

Nuevos: {nuevos}

Memoria total: {len(memoria)}

""")
