import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA_FILE = "memoria.json"

try:
    with open(MEMORIA_FILE,"r") as f:
        memoria = json.load(f)
except:
    memoria = []

URL = "https://www.trabajando.cl/trabajos/mineria"

def enviar(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id":CHAT_ID,"text":msg}
    )

enviar("RADAR MINERO TRABAJANDO.CL INICIADO")

html = requests.get(URL).text

soup = BeautifulSoup(html,"html.parser")

links = soup.find_all("a")

nuevos = 0

for link in links:

    titulo = link.get_text().strip()

    if len(titulo) > 20:

        if titulo not in memoria:

            memoria.append(titulo)

            nuevos += 1

            enviar(f"""

EMPLEO MINERO DETECTADO

{titulo}

Fuente: Trabajando.cl

""")

with open(MEMORIA_FILE,"w") as f:

    json.dump(memoria,f)

enviar(f"""

RADAR FINALIZADO

Nuevos: {nuevos}

Memoria: {len(memoria)}

""")
