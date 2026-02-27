import requests
from bs4 import BeautifulSoup
import os
import json

print("RADAR V26.3 BLACK BELT INICIADO")

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

# --------------------------
# HISTORIAL
# --------------------------

if os.path.exists(ARCHIVO):
    with open(ARCHIVO, "r") as f:
        historial = json.load(f)
else:
    historial = []

nuevos = []

# --------------------------
# FILTRO
# --------------------------

def cumple(texto):
    t = texto.lower()

    if any(x in t for x in EXCLUIR):
        return False

    return any(k in t for k in KEYWORDS)

# --------------------------
# CODELCO SEARCH REAL
# --------------------------

try:
    url = "https://empleos.codelco.cl/search/?q="
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for link in soup.find_all("a", href=True):

        titulo = link.get_text(strip=True)
        href = link["href"]

        if "/job/" not in href:
            continue

        if not cumple(titulo):
            continue

        link_completo = "https://empleos.codelco.cl" + href

        if link_completo in historial:
            continue

        nuevos.append(f"{titulo}\nCodelco\n{link_completo}")
        historial.append(link_completo)

except Exception as e:
    print("Error Codelco:", e)

# --------------------------
# KINROSS PROFESIONALES REAL
# --------------------------

try:
    url = "https://jobs.kinross.com/go/Puestos-para-profesionales"
    r = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for link in soup.find_all("a", href=True):

        titulo = link.get_text(strip=True)
        href = link["href"]

        if "/job/" not in href:
            continue

        if not cumple(titulo):
            continue

        if href.startswith("/"):
            link_completo = "https://jobs.kinross.com" + href
        else:
            link_completo = href

        if link_completo in historial:
            continue

        nuevos.append(f"{titulo}\nKinross\n{link_completo}")
        historial.append(link_completo)

except Exception as e:
    print("Error Kinross:", e)

# --------------------------
# GUARDAR HISTORIAL
# --------------------------

with open(ARCHIVO, "w") as f:
    json.dump(historial, f)

# --------------------------
# TELEGRAM
# --------------------------

if nuevos:
    mensaje = "RADAR V26.3 BLACK BELT\n\n" + "\n\n".join(nuevos[:25])
else:
    mensaje = "RADAR V26.3 BLACK BELT\n\nSin empleos nuevos compatibles"

requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={
        "chat_id": CHAT_ID,
        "text": mensaje
    }
)

print("RADAR V26.3 FINALIZADO")
