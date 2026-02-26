import requests
from bs4 import BeautifulSoup
import os
import json

print("RADAR V25 TITAN HEADHUNTER INICIADO")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

ARCHIVO = "historial.json"

# PALABRAS CLAVE HEADHUNTER

KEYWORDS = [

    "mantenimiento",
    "mantencion",
    "operaciones",
    "operacion",
    "supervisor",
    "jefe",
    "administrador",
    "contrato",
    "planner",
    "planificador",
    "ingeniero"

]

# CARGAR HISTORIAL

if os.path.exists(ARCHIVO):

    with open(ARCHIVO,"r") as f:
        historial = json.load(f)

else:

    historial = []


nuevos = []


# FUNCION FILTRO

def cumple(texto):

    texto = texto.lower()

    return any(k in texto for k in KEYWORDS)



# ========================
# CODELCO REAL
# ========================

try:

    url = "https://empleos.codelco.cl"

    soup = BeautifulSoup(requests.get(url).text,"html.parser")

    for link in soup.find_all("a"):

        titulo = link.text.strip()

        href = link.get("href")

        if not href:
            continue

        if "/job/" not in href:
            continue

        if not cumple(titulo):
            continue

        link_completo = url + href

        if link_completo in historial:
            continue

        nuevos.append(
            titulo + "\nCodelco\n" + link_completo
        )

        historial.append(link_completo)

except:

    pass



# ========================
# KINROSS REAL
# ========================

try:

    url = "https://jobs.kinross.com"

    soup = BeautifulSoup(requests.get(url).text,"html.parser")

    for link in soup.find_all("a"):

        titulo = link.text.strip()

        href = link.get("href")

        if not href:
            continue

        if "/job/" not in href:
            continue

        if not cumple(titulo):
            continue

        link_completo = url + href

        if link_completo in historial:
            continue

        nuevos.append(
            titulo + "\nKinross\n" + link_completo
        )

        historial.append(link_completo)

except:

    pass



# GUARDAR HISTORIAL

with open(ARCHIVO,"w") as f:

    json.dump(historial,f)



# ENVIAR TELEGRAM

if nuevos:

    mensaje = "\n\n".join(nuevos)

else:

    mensaje = "Sin empleos nuevos reales"


requests.post(

    f"https://api.telegram.org/bot{TOKEN}/sendMessage",

    data={

        "chat_id": CHAT_ID,

        "text": "RADAR V25 TITAN HEADHUNTER\n\n" + mensaje

    }

)


print("RADAR V25 FINALIZADO")
