import requests
from bs4 import BeautifulSoup
import os
import time

print("INICIANDO RADAR MINERO V4.1")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ============================
# PERFIL PROFESIONAL
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
    "administrtador de contrato"
    "ingeniero",
    "supervisor",
    "ADMINISTRADOR"
    "industrial",

    "gestion",

    "activo",
    "asset"

]

# ============================
# TODAS LAS MINERAS CHILE
# ============================

MINERAS = [

    "codelco",
    "escondida",
    "spence",
    "cerro negro",

    "collahuasi",

    "anglo american",

    "los pelambres",
    "centinela",
    "antucoya",
    "zaldívar",

    "candelaria",
    "caserones",
    "ojos del salado",

    "teck",
    "quebrada blanca",

    "kinross",

    "sierra gorda",

    "mantos copper",

    "lomas bayas",

    "cap mineria",

    "el abra",

    "radomiro tomic",

    "chuquicamata",

    "el teniente",

    "andina",

    "gabriela mistral",

    "minera esperanza",

    "minera florida",

    "punta del cobre"

]

# ============================
# SERVICIOS MINEROS COMPLETO
# ============================

SERVICIOS = [

    "komatsu",
    "finning",
    "epiroc",
    "sandvik",
    "liebherr",

    "metso",
    "outotec",

    "confipetrol",

    "sigdo koppers",
    "skic",

    "salfa",
    "salfa montaje",

    "bechtel",
    "fluor",
    "worley",
    "wood",
    "ausenco",
    "hatch",

    "abb",
    "siemens",

    "emerson",

    "weir",

    "famsa",

    "vecchiola",

    "besalco",

    "strabag",

    "ferrovial",
    "cam"
    "flesan",

    "ryq",
    "abengoa"
    "melon",
    "nexxo"
    "enaex",

    "orica",

    "sodexo",
    "ava montajes"
    "aramark"

]

# ============================
# TURNOS
# ============================

TURNOS = [

    "14x14",
    "10x10",
    "7x7",
    "4x3",

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
    "retail",
    "junior"

]

# ============================
# FILTRO POR PUNTAJE
# ============================

def cumple(texto):

    texto = texto.lower()

    puntos = 0

    if any(p in texto for p in PERFIL):
        puntos += 1

    if any(m in texto for m in MINERAS):
        puntos += 1

    if any(s in texto for s in SERVICIOS):
        puntos += 1

    if any(t in texto for t in TURNOS):
        puntos += 1

    if any(e in texto for e in EXCLUIR):
        return False

    return puntos >= 2


# ============================
# TELEGRAM
# ============================

def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {

        "chat_id": CHAT_ID,
        "text": msg

    }

    requests.post(url, data=data)


# ============================
# CHILETRABAJOS
# ============================

def chiletrabajos():

    url = "https://www.chiletrabajos.cl/trabajo/ingeniero"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    avisos = soup.find_all("a")

    encontrados = 0

    for aviso in avisos:

        texto = aviso.text.strip()

        link = aviso.get("href")

        if texto and link:

            if cumple(texto):

                mensaje = f"CHILETRABAJOS\n\n{texto}\n\nhttps://www.chiletrabajos.cl{link}"

                enviar(mensaje)

                encontrados += 1

                time.sleep(2)

    print("Chiletrabajos:", encontrados)

    return encontrados


# ============================
# INDEED
# ============================

def indeed():

    url = "https://cl.indeed.com/jobs?q=ingeniero+mineria&l=Chile"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    avisos = soup.find_all("a")

    encontrados = 0

    for aviso in avisos:

        texto = aviso.text.strip()

        link = aviso.get("href")

        if texto and link:

            if cumple(texto):

                mensaje = f"INDEED\n\n{texto}\n\nhttps://cl.indeed.com{link}"

                enviar(mensaje)

                encontrados += 1

                time.sleep(2)

    print("Indeed:", encontrados)

    return encontrados


# ============================
# LABORUM
# ============================

def laborum():

    url = "https://www.laborum.cl/empleos.html"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    avisos = soup.find_all("a")

    encontrados = 0

    for aviso in avisos:

        texto = aviso.text.strip()

        link = aviso.get("href")

        if texto and link:

            if cumple(texto):

                mensaje = f"LABORUM\n\n{texto}\n\n{link}"

                enviar(mensaje)

                encontrados += 1

                time.sleep(2)

    print("Laborum:", encontrados)

    return encontrados


# ============================
# EJECUCIÓN
# ============================

enviar("RADAR MINERO V4.1 ACTIVO")

total = 0

total += chiletrabajos()

total += indeed()

total += laborum()

if total == 0:

    enviar("Sin avisos filtrados en esta ejecución")

else:

    enviar(f"Total encontrados: {total}")

print("FINALIZADO")
