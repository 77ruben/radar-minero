import requests
from bs4 import BeautifulSoup
import os
import json
import re

print("INICIO RADAR MINERO PRO")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA_FILE = "memoria.json"
SEEN_FILE = "seen_jobs.json"


# ------------------------
# FUNCIONES JSON
# ------------------------

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

vistos = cargar_json(SEEN_FILE, [])

rechazados = memoria.get("rechazados", [])

turnos_buenos = memoria.get(
    "turnos_buenos",
    ["7x7", "10x10", "14x14", "4x3"]
)


# ------------------------
# FILTRO PROFESIONAL MINERO
# ------------------------

KEYWORDS = [

"supervisor",
"supervisor operaciones",
"supervisor de operaciones",

"administrador de contrato",
"administrador de contratos",

"jefe",
"jefe mantenimiento",
"jefe mantencion",
"jefe operaciones",

"mantencion",
"mantenimiento",

"planificador",
"planificacion",

"confiabilidad",

"ingeniero mantenimiento",
"ingeniero mantencion",

"mina",
"mineria"

]


# ------------------------
# EMPRESAS OBJETIVO CHILE
# ------------------------

EMPRESAS = [

"kinross",
"candelaria",
"bhp",
"escondida",
"collahuasi",
"anglo american",
"antofagasta minerals",
"spence",
"teck",
"que brada blanca",
"cerro negro norte",
"cmp",
"cap mineria",
"lomas bayas",
"zaldívar"

]


# ------------------------
# PORTALES
# ------------------------

URLS = {

"Trabajando":

"https://www.trabajando.cl/trabajo-mineria",

"Indeed":

"https://cl.indeed.com/jobs?q=mineria",

"Computrabajo":

"https://www.computrabajo.cl/trabajo-de-mineria"

}


# ------------------------
# DETECTAR TURNO
# ------------------------

def detectar_turno(texto):

    texto = texto.lower()

    for turno in turnos_buenos:

        if turno in texto:
            return turno

    return "No especificado"


# ------------------------
# VALIDAR EMPLEO
# ------------------------

def cumple(titulo):

    t = titulo.lower()

    if any(r in t for r in rechazados):
        return False

    if any(k in t for k in KEYWORDS):
        return True

    return False


# ------------------------
# ENVIAR TELEGRAM
# ------------------------

def enviar_telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.get(

        url,

        params={

            "chat_id": CHAT_ID,

            "text": msg

        }

    )


# ------------------------
# SCRAPER
# ------------------------

nuevos = 0

for portal, url in URLS.items():

    print("Revisando:", portal)

    try:

        html = requests.get(url, timeout=20).text

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a"):

            titulo = a.get_text().strip()

            link = a.get("href")

            if not titulo:
                continue

            if not link:
                continue


            if cumple(titulo):

                if titulo not in vistos:


                    turno = detectar_turno(titulo)


                    mensaje = (

f"⛏️ {titulo}\n"
f"🏢 Portal: {portal}\n"
f"🕒 Turno: {turno}\n"
f"{link}"

                    )


                    enviar_telegram(mensaje)


                    vistos.append(titulo)

                    nuevos += 1


    except Exception as e:

        print("Error en", portal, e)


guardar_json(SEEN_FILE, vistos)


# ------------------------
# MENSAJE FINAL
# ------------------------

if nuevos == 0:

    enviar_telegram("Radar activo sin novedades")

else:

    enviar_telegram(
        f"Radar detectó {nuevos} empleos nuevos"
    )


print("FIN RADAR")
