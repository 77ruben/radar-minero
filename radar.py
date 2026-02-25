import requests
from bs4 import BeautifulSoup
import os
import sys
import traceback

print("RADAR MINERO V19 HEADHUNTER — NIVEL PROFESIONAL")

# ==========================
# TELEGRAM
# ==========================

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def enviar(msg):

    try:

        requests.post(

            f"https://api.telegram.org/bot{TOKEN}/sendMessage",

            data={"chat_id": CHAT_ID, "text": msg}

        )

    except:

        print("Error enviando Telegram")


# ==========================
# FILTRO INTELIGENTE
# ==========================

PALABRAS_CLAVE = [

    "supervisor",
    "jefe",
    "lider",
    "líder",

    "administrador",
    "contrato",
    "contratos",

    "operaciones",

    "mantencion",
    "mantenimiento",

    "planificador",

    "ingeniero",

]

TURNOS = [

    "7x7",
    "10x10",
    "14x14",
    "4x3",

]

EXCLUIR = [

    "alumno",
    "practica",
    "práctica",
    "trainee",
    "aprendiz",

]


def cumple_filtro(texto):

    texto = texto.lower()

    if any(x in texto for x in EXCLUIR):

        return False

    if any(x in texto for x in PALABRAS_CLAVE):

        return True

    if any(x in texto for x in TURNOS):

        return True

    return False


# ==========================
# BUSQUEDA GENERICA
# ==========================

def buscar_generico(nombre, url):

    print("Buscando en", nombre)

    lista = []

    try:

        r = requests.get(url, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.find_all("a")

        for link in links:

            titulo = link.get_text(strip=True)

            href = link.get("href")

            if not titulo or not href:

                continue

            # convertir link relativo en absoluto
            if href.startswith("/"):

                href = url.rstrip("/") + href

            texto = titulo + " " + nombre

            if cumple_filtro(texto):

                lista.append({

                    "titulo": titulo,

                    "empresa": nombre,

                    "link": href

                })

                print("VALIDO:", titulo)

    except:

        print(nombre, "omitido")

    return lista

# ==========================
# EMPRESAS
# ==========================

def bhp():

    return buscar_generico(

        "BHP",

        "https://jobs.bhp.com/search/"

    )


def finning():

    return buscar_generico(

        "Finning",

        "https://finning.csod.com/ux/ats/careersite/4/home?c=finning&lang=es-CL"

    )


def komatsu():

    return buscar_generico(

        "Komatsu",

        "https://komatsu.jobs/jobs"

    )


def collahuasi():

    return buscar_generico(

        "Collahuasi",

        "https://www.collahuasi.cl/personas/trabaja-con-nosotros/"

    )


def codelco():

    return buscar_generico(

        "Codelco",

        "https://empleos.codelco.cl/"

    )


def amsa():

    return buscar_generico(

        "Antofagasta Minerals",

        "https://www.aminerals.cl/empleo/"

    )


def anglo():

    return buscar_generico(

        "Anglo American",

        "https://jobs.angloamerican.com/"

    )


# ==========================
# INICIO
# ==========================

enviar("RADAR V19 HEADHUNTER INICIADO")

empleos = []

try:

    empleos += bhp()
    empleos += finning()
    empleos += komatsu()
    empleos += collahuasi()
    empleos += codelco()
    empleos += amsa()
    empleos += anglo()

except:

    print("Error general")

print("TOTAL:", len(empleos))


# ==========================
# RESULTADOS
# ==========================

if empleos:

    mensaje = "EMPLEOS ENCONTRADOS\n\n"

    for e in empleos[:10]:

        mensaje += f"{e['titulo']}\n{e['empresa']}\n{e['link']}\n\n"

    enviar(mensaje)

else:

    enviar("Sin empleos validos en esta ejecución")


enviar("RADAR V19 FINALIZADO")
