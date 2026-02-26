import requests
from bs4 import BeautifulSoup
import os
import json

print("RADAR V26 BLACK BELT INICIADO")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

ARCHIVO = "historial.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

KEYWORDS = [
    "mantenimiento",
    "mantencion",
    "operaciones",
    "supervisor",
    "jefe",
    "administrador",
    "contrato",
    "planner",
    "planificador",
    "ingeniero",
    "turno",
    "7x7",
    "14x14",
    "4x3"
]

EXCLUIR = [
    "practica",
    "práctica",
    "trainee",
    "alumno"
]

EMPRESAS = {

    "Codelco": "https://empleos.codelco.cl",
    "Kinross": "https://jobs.kinross.com",
    "BHP": "https://jobs.bhp.com",
    "Anglo American": "https://jobs.angloamerican.com",
    "Antofagasta Minerals": "https://www.aminerals.cl",
    "Collahuasi": "https://www.collahuasi.cl",
    "Teck": "https://jobs.teck.com",
    "Sierra Gorda": "https://www.sgscm.cl",
    "Finning": "https://finning.csod.com",
    "Komatsu": "https://komatsu.jobs",
    "Enaex": "https://enaex.jobs",
    "Orica": "https://orica.jobs",
    "Metso": "https://metso.jobs"
}

# ------------------------------
# HISTORIAL
# ------------------------------

if os.path.exists(ARCHIVO):
    with open(ARCHIVO, "r") as f:
        historial = json.load(f)
else:
    historial = []

nuevos = []

# ------------------------------
# FILTRO
# ------------------------------

def cumple(texto):
    t = texto.lower()

    if any(x in t for x in EXCLUIR):
        return False

    return any(k in t for k in KEYWORDS)

# ------------------------------
# SCRAPER SIMPLE
# ------------------------------

def scrap_empresa(nombre, url):

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.find_all("a"):

            titulo = link.get_text(strip=True)
            href = link.get("href")

            if not href or not titulo:
                continue

            if "/job" not in href.lower():
                continue

            if not cumple(titulo):
                continue

            if href.startswith("/"):
                link_completo = url.rstrip("/") + href
            else:
                link_completo = href

            if link_completo in historial:
                continue

            nuevos.append(
                f"{titulo}\n{nombre}\n{link_completo}"
            )

            historial.append(link_completo)

    except:
        print(f"Error en {nombre}")

# ------------------------------
# EJECUCION
# ------------------------------

for empresa, url in EMPRESAS.items():
    scrap_empresa(empresa, url)

# ------------------------------
# GUARDAR HISTORIAL
# ------------------------------

with open(ARCHIVO, "w") as f:
    json.dump(historial, f)

# ------------------------------
# TELEGRAM
# ------------------------------

if nuevos:
    mensaje = "RADAR V26 BLACK BELT\n\n" + "\n\n".join(nuevos[:25])
else:
    mensaje = "RADAR V26 BLACK BELT\n\nSin empleos nuevos compatibles"

requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": mensaje
    }
)

print("RADAR V26 FINALIZADO")
