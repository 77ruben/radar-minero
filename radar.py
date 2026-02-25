import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA_FILE = "memoria.json"
SEEN_FILE = "seen_jobs.json"


def cargar_json(file, default):

    try:
        with open(file, encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def guardar_json(file, data):

    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


memoria = cargar_json(MEMORIA_FILE, {})

turnos = memoria.get("turnos_buenos", [])

rechazados = memoria.get("rechazados", [])

vistos = cargar_json(SEEN_FILE, [])


KEYWORDS = [

"supervisor",
"mantencion",
"mantenimiento",
"planificacion",
"confiabilidad",
"contratos",
"mina"

]


URLS = [

"https://www.trabajando.cl/trabajo-mineria",
"https://www.computrabajo.cl/trabajo-de-mineria",
"https://cl.indeed.com/jobs?q=mineria"

]


def cumple(texto):

    texto = texto.lower()

    if any(r in texto for r in rechazados):
        return False

    if any(k in texto for k in KEYWORDS):

        if any(t in texto for t in turnos):
            return True

    return False


def enviar(msg):

    requests.get(

        f"https://api.telegram.org/bot{TOKEN}/sendMessage",

        params={

            "chat_id": CHAT_ID,

            "text": msg

        }

    )


nuevos = 0

for url in URLS:

    try:

        soup = BeautifulSoup(

            requests.get(url).text,

            "html.parser"

        )

        for a in soup.find_all("a"):

            titulo = a.text.strip()

            link = a.get("href")

            if cumple(titulo):

                if titulo not in vistos:

                    enviar(

f"⛏️ {titulo}\n{link}"

                    )

                    vistos.append(titulo)

                    nuevos += 1

    except:
        pass


guardar_json(SEEN_FILE, vistos)


if nuevos == 0:

    enviar("Radar activo sin novedades")
