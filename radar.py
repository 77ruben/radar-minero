import requests
from bs4 import BeautifulSoup
import os
import json

print("INICIO RADAR MINERO V6.1")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA_FILE = "memoria.json"
SEEN_FILE = "seen_jobs.json"


# ----------------
# JSON
# ----------------

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

turnos = memoria.get(
    "turnos_buenos",
    ["7x7", "10x10", "14x14", "4x3"]
)

rechazados = memoria.get("rechazados", [])


# ----------------
# FILTROS
# ----------------

KEYWORDS = [

"supervisor",

"operaciones",

"administrador",

"contrato",

"jefe",

"mantencion",

"mantenimiento",

"mineria",

"mina"

]


# ----------------
# PORTALES QUE FUNCIONAN REALMENTE
# ----------------

URLS = [

"https://www.chiletrabajos.cl/buscar?q=mineria",

"https://www.chiletrabajos.cl/buscar?q=supervisor+mineria",

"https://www.chiletrabajos.cl/buscar?q=administrador+contrato+mineria"

]


# ----------------
# TURNO
# ----------------

def detectar_turno(texto):

    texto = texto.lower()

    for t in turnos:

        if t in texto:

            return t

    return "No especificado"


# ----------------
# VALIDAR
# ----------------

def cumple(titulo):

    t = titulo.lower()

    if any(r in t for r in rechazados):

        return False

    if any(k in t for k in KEYWORDS):

        return True

    return False


# ----------------
# TELEGRAM
# ----------------

def enviar(msg):

    requests.get(

        f"https://api.telegram.org/bot{TOKEN}/sendMessage",

        params={

            "chat_id": CHAT_ID,

            "text": msg

        }

    )


# ----------------
# SCRAPER REAL
# ----------------

nuevos = 0

for url in URLS:

    print("Revisando", url)

    try:

        html = requests.get(url, timeout=20).text

        soup = BeautifulSoup(html, "html.parser")

        trabajos = soup.select("a")

        for job in trabajos:

            titulo = job.get_text().strip()

            link = job.get("href")

            if not titulo:

                continue

            if not link:

                continue


            if cumple(titulo):

                if titulo not in vistos:


                    turno = detectar_turno(titulo)


                    mensaje = (

f"⛏️ {titulo}\n"
f"🕒 Turno: {turno}\n"
f"https://www.chiletrabajos.cl{link}"

                    )


                    enviar(mensaje)

                    vistos.append(titulo)

                    nuevos += 1


    except Exception as e:

        print("ERROR:", e)


guardar_json(SEEN_FILE, vistos)


# ----------------
# FINAL
# ----------------

if nuevos == 0:

    enviar("Radar activo sin novedades")

else:

    enviar(f"Radar detectó {nuevos} empleos nuevos")


print("FIN")
