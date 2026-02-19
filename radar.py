import requests
from bs4 import BeautifulSoup
import os
import time

print("INICIANDO RADAR MINERO V5 PRO")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =====================================================
# PERFIL RUBÉN
# =====================================================

PERFIL = [

    "ingeniero",
    "mantencion",
    "mantenimiento",
    "administrador",
    "planificacion",
    "planner",
    "planificador",
    "administrador de contrato",
    "confiabilidad",

    "contrato",

    "logistica",

    "supervisor",
    "supervisor de operaciones",
    "industrial",
    "supervisor de terreno",
    "operaciones"

]

# =====================================================
# MINERIA / SERVICIOS
# =====================================================

EMPRESAS = [

    "codelco",
    "bhp",
    "escondida",
    "spence",

    "collahuasi",

    "anglo american",

    "antofagasta minerals",
    "pelambres",
    "centinela",

    "candelaria",
    "QB"
    "teck",
    "quebrada blanca",
    "kinross",

    "sierra gorda",

    "komatsu",

    "finning",

    "sandvik",

    "epiroc",

    "metso",

    "confipetrol"

]

# =====================================================
# EXCLUIR
# =====================================================

EXCLUIR = [

    "bodega",
    "operario",
    "guardia",
    "chofer",
    "vendedor"

]

# =====================================================
# FILTRO
# =====================================================

def cumple(texto):

    texto = texto.lower()

    puntos = 0

    if any(p in texto for p in PERFIL):
        puntos += 1

    if any(e in texto for e in EMPRESAS):
        puntos += 1

    if any(x in texto for x in EXCLUIR):
        return False

    return puntos >= 1


# =====================================================
# TELEGRAM
# =====================================================

def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {

        "chat_id": CHAT_ID,
        "text": msg

    }

    requests.post(url, data=data)


# =====================================================
# TRABAJANDO.COM
# =====================================================

def trabajando():

    print("Buscando Trabajando")

    url = "https://www.trabajando.cl/trabajos-mineria"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    avisos = soup.find_all("a")

    encontrados = 0

    for aviso in avisos:

        texto = aviso.text.strip()

        link = aviso.get("href")

        if texto and link:

            if cumple(texto):

                enviar(f"TRABAJANDO\n\n{texto}\n\n{link}")

                encontrados += 1

                time.sleep(2)

    return encontrados


# =====================================================
# BHP DIRECTO
# =====================================================

def bhp():

    print("Buscando BHP")

    url = "https://careers.bhp.com"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    texto = soup.text.lower()

    encontrados = 0

    if cumple(texto):

        enviar("BHP tiene avisos activos\nhttps://careers.bhp.com")

        encontrados += 1

    return encontrados


# =====================================================
# CODELCO DIRECTO
# =====================================================

def codelco():

    print("Buscando Codelco")

    url = "https://www.codelco.com/trabaja-con-nosotros"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    texto = soup.text.lower()

    encontrados = 0

    if cumple(texto):

        enviar("CODELCO tiene avisos activos\nhttps://www.codelco.com")

        encontrados += 1

    return encontrados


# =====================================================
# KOMATSU
# =====================================================

def komatsu():

    print("Buscando Komatsu")

    url = "https://komatsu.jobs"

    r = requests.get(url)

    soup = BeautifulSoup(r.text, "html.parser")

    texto = soup.text.lower()

    encontrados = 0

    if cumple(texto):

        enviar("KOMATSU tiene avisos\nhttps://komatsu.jobs")

        encontrados += 1

    return encontrados


# =====================================================
# EJECUCION
# =====================================================

enviar("RADAR MINERO V5 PRO ACTIVO")

total = 0

total += trabajando()

total += bhp()

total += codelco()

total += komatsu()

if total == 0:

    enviar("Sin avisos en esta ejecución")

else:

    enviar(f"TOTAL: {total}")

print("FINALIZADO")
