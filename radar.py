import requests
from bs4 import BeautifulSoup
import os
import time

print("INICIANDO RADAR MINERO V4")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ============================
# PERFIL PROFESIONAL RUBÉN
# ============================

PERFIL = [

    "mantencion",
    "mantenimiento",

    "planificacion",
    "planificador",
    "planner",
    "programador",

    "confiabilidad",

    "contrato",

    "logistica",

    "operaciones",

    "ingeniero",
    "supervisor",

    "industrial",

    "gestion",

]

# ============================
# MINERAS
# ============================

MINERIA = [

    "minera",
    "faena",

    "codelco",
    "bhp",
    "anglo american",
    "collahuasi",
    "escondida",

    "antofagasta minerals",

    "pelambres",
    "centinela",
    "zaldívar",

    "candelaria",

    "lundin",

    "teck",

    "spence",

    "kinross",

    "mantos copper",

    "sierra gorda"

]

# ============================
# SERVICIOS MINEROS
# ============================

SERVICIOS = [

    "komatsu",
    "finning",
    "epiroc",
    "sandvik",

    "bechtel",
    "fluor",
    "worley",
    "wood",
    "ausenco",

    "sigdo koppers",
    "skic",

    "salfa",

    "confipetrol",

    "metso",

    "abb",
    "siemens"

]

# ============================
# TURNOS
# ============================

TURNOS = [

    "14x14",
    "10x10",
    "7x7",
    "4x3"

]

# ============================
# EXCLUIR
# ============================

EXCLUIR = [

    "bodega",
    "operario",
    "chofer",
    "conductor",
    "vendedor",
    "guardia",
    "retail"

]

# ============================
# FUNCIÓN FILTRO
# ============================

def cumple(texto):

    texto = texto.lower()

    perfil = any(p in texto for p in PERFIL)

    mineria = any(m in texto for m in MINERIA)

    servicio = any(s in texto for s in SERVICIOS)

    turno = any(t in texto for t in TURNOS)

    excluir = any(e in texto for e in EXCLUIR)

    return perfil and (mineria or servicio) and turno and not excluir


# ============================
# TELEGRAM
# ============================

def enviar(mensaje):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {

        "chat_id": CHAT_ID,
        "text": mensaje

    }

    requests.post(url, data=data)


# ============================
# BUSCAR EN CHILETRABAJOS
# ============================

def chiletrabajos():

    url = "https://www.chiletrabajos.cl/trabajo/mineria"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    avisos = soup.find_all("a")

    encontrados = 0

    for aviso in avisos:

        texto = aviso.text.strip()

        link = aviso.get("href")

        if texto and link:

            if cumple(texto):

                mensaje = f"MINERO V4\n\n{texto}\n\nhttps://www.chiletrabajos.cl{link}"

                enviar(mensaje)

                encontrados += 1

                time.sleep(3)

    print("Chiletrabajos:", encontrados)


# ============================
# INDEED
# ============================

def indeed():

    url = "https://cl.indeed.com/jobs?q=mineria&l=Chile"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    avisos = soup.find_all("a")

    encontrados = 0

    for aviso in avisos:

        texto = aviso.text.strip()

        link = aviso.get("href")

        if texto and link:

            if cumple(texto):

                mensaje = f"INDEED V4\n\n{texto}\n\nhttps://cl.indeed.com{link}"

                enviar(mensaje)

                encontrados += 1

                time.sleep(3)

    print("Indeed:", encontrados)


# ============================
# LABORUM
# ============================

def laborum():

    url = "https://www.laborum.cl/empleos-mineria.html"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    avisos = soup.find_all("a")

    encontrados = 0

    for aviso in avisos:

        texto = aviso.text.strip()

        link = aviso.get("href")

        if texto and link:

            if cumple(texto):

                mensaje = f"LABORUM V4\n\n{texto}\n\n{link}"

                enviar(mensaje)

                encontrados += 1

                time.sleep(3)

    print("Laborum:", encontrados)


# ============================
# EJECUCIÓN
# ============================

enviar("RADAR MINERO V4 ACTIVO")

chiletrabajos()

indeed()

laborum()

print("FINALIZADO RADAR V4")
