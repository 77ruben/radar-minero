import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

ARCHIVO_MEMORIA = "memoria.json"

# CARGAR MEMORIA

try:
    with open(ARCHIVO_MEMORIA,"r") as f:
        memoria = json.load(f)
except:
    memoria = []

# FILTROS

CARGOS = [
"supervisor",
"mantencion",
"mantenimiento",
"planificador",
"confiabilidad",
"contrato"
]

MINERAS = [
"minera",
"mining",
"faena",
"codelco",
"bhp",
"collahuasi",
"kinross",
"antofagasta minerals",
"teck"
]

EXCLUIR = [
"sueldo",
"salario",
"blog"
]

URLS = [

"https://www.chiletrabajos.cl/trabajo/minera",
"https://cl.indeed.com/jobs?q=minera",
"https://www.laborum.cl"

]

def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url,data={
    "chat_id":CHAT_ID,
    "text":msg
})

def analizar(texto):

    texto = texto.lower()

    if any(e in texto for e in EXCLUIR):
        return False,"Basura"

    if not any(c in texto for c in CARGOS):
        return False,"No es cargo objetivo"

    if not any(m in texto for m in MINERAS):
        return False,"No es minería"

    return True,"Empleo Minero Real"


enviar("RADAR V7 PRO IA INICIADO")

total = 0
nuevos = 0
repetidos = 0

for url in URLS:

    html = requests.get(url).text

    soup = BeautifulSoup(html,"html.parser")

    links = soup.find_all("a")

    for link in links:

        texto = link.get_text().strip()

        if texto == "":
            continue

        total += 1

        valido,razon = analizar(texto)

        if valido:

            if texto in memoria:

                repetidos += 1

            else:

                nuevos += 1

                memoria.append(texto)

                enviar(f"""

NUEVO EMPLEO MINERO DETECTADO

Cargo:
{texto}

Fuente:
{url}

Analisis IA:
{razon}

""")


# GUARDAR MEMORIA

with open(ARCHIVO_MEMORIA,"w") as f:

    json.dump(memoria,f)


enviar(f"""

RADAR V7 PRO FINALIZADO

Revisados: {total}

Nuevos: {nuevos}

Repetidos: {repetidos}

Memoria IA: {len(memoria)} empleos almacenados

""")
