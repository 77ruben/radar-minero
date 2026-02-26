import requests
from bs4 import BeautifulSoup
import os

print("RADAR MINERO V20 FILTRO PRO — NIVEL HEADHUNTER")

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
# MEMORIA
# ==========================

ARCHIVO_MEMORIA = "memoria.txt"


def cargar_memoria():

    try:

        with open(ARCHIVO_MEMORIA, "r") as f:

            return set(f.read().splitlines())

    except:

        return set()


def guardar_memoria(memoria):

    with open(ARCHIVO_MEMORIA, "w") as f:

        for link in memoria:

            f.write(link + "\n")


memoria = cargar_memoria()


# ==========================
# FILTRO PROFESIONAL
# ==========================

CARGOS_PRO = [

    "supervisor",
    "jefe",
    "administrador de contratos",
    "administrador contrato",
    "contract administrator",
    "contract manager",
    "planificador",
    "planner",
    "ingeniero mantenimiento",
    "ingeniero mantencion",
    "supervisor operaciones",
    "jefe mantenimiento",
    "jefe mantencion",
    "maintenance supervisor",

]

EXCLUIR = [

    "practica",
    "práctica",
    "alumno",
    "trainee",
    "aprendiz",
    "operador",
    "operaria",
]

def cumple_filtro(texto):

    texto = texto.lower()

    if any(x in texto for x in EXCLUIR):

        return False

    if any(x in texto for x in CARGOS_PRO):

        return True

    return False


# ==========================
# BUSCADOR GENERICO
# ==========================

def buscar(nombre, url, dominio):

    print("Buscando en", nombre)

    lista = []

    try:

        r = requests.get(url, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.find_all("a"):

            titulo = link.get_text(strip=True)

            href = link.get("href")

            if not titulo or not href:

                continue

            if href.startswith("/"):

                href = dominio + href

            texto = titulo + " " + nombre

            if cumple_filtro(texto):

                lista.append({

                    "titulo": titulo,

                    "empresa": nombre,

                    "link": href

                })

                print("VALIDO:", titulo)

    except:

        print("Error en", nombre)

    return lista


# ==========================
# EMPRESAS
# ==========================

empleos = []

empleos += buscar(

    "Codelco",

    "https://empleos.codelco.cl/",

    "https://empleos.codelco.cl"

)

empleos += buscar(

    "BHP",

    "https://jobs.bhp.com/search/",

    "https://jobs.bhp.com"

)

empleos += buscar(

    "Finning",

    "https://finning.csod.com/ux/ats/careersite/4/home?c=finning&lang=es-CL",

    "https://finning.csod.com"

)

empleos += buscar(

    "Komatsu",

    "https://komatsu.jobs/jobs",

    "https://komatsu.jobs"

)


# ==========================
# ELIMINAR DUPLICADOS INTERNOS
# ==========================

unicos = []

vistos = set()

for e in empleos:

    if e["link"] not in vistos:

        unicos.append(e)

        vistos.add(e["link"])

empleos = unicos


# ==========================
# FILTRAR NUEVOS
# ==========================

nuevos = []

for e in empleos:

    if e["link"] not in memoria:

        nuevos.append(e)

        memoria.add(e["link"])


# ==========================
# TELEGRAM
# ==========================

enviar("RADAR V20 FILTRO PRO INICIADO")


if nuevos:

    msg = "EMPLEOS NUEVOS\n\n"

    for e in nuevos:

        msg += f"{e['titulo']}\n{e['empresa']}\n{e['link']}\n\n"

    enviar(msg)

else:

    enviar("Sin empleos nuevos compatibles con tu perfil")


enviar("RADAR V20 FINALIZADO")


# ==========================
# GUARDAR MEMORIA
# ==========================

guardar_memoria(memoria)
