import requests
from bs4 import BeautifulSoup
import os
import json
import re

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

print("RADAR MINERO V14 PRO CHILE INICIADO")

# ==========================
# FILTROS PROFESIONALES
# ==========================

CARGOS = [

"supervisor",
"administrador de contratos",
"contract administrator",
"jefe",
"planner",
"planificador",
"mantencion",
"mantenimiento",
"maintenance",
"confiabilidad",
"reliability",
"ingeniero mantenimiento"

]

TURNOS = [

"14x14",
"10x10",
"7x7",
"4x3",
"turno"

]

UBICACION_CHILE = [

"chile",
"antofagasta",
"calama",
"copiapo",
"iquique",
"faena",
"minera",
"collahuasi",
"escondida",
"spence",
"los bronces",
"codelco",
"chuquicamata"

]

PALABRAS_EXTRANJERO = [

"peru",
"australia",
"canada",
"usa",
"mexico",
"argentina",
"wy",
"tn",
"nsw",
"queensland"

]

# ==========================
# MEMORIA
# ==========================

ARCHIVO = "memoria.json"

try:
    with open(ARCHIVO,"r") as f:
        memoria = json.load(f)
except:
    memoria = []

# ==========================
# IA ANALISIS
# ==========================

def analisis_ia(texto):

    t = texto.lower()

    if any(p in t for p in PALABRAS_EXTRANJERO):
        return False, "Extranjero"

    if not any(p in t for p in UBICACION_CHILE):
        return False, "No indica Chile"

    if any(c in t for c in CARGOS):

        if any(turno in t for turno in TURNOS):
            return True, "Cargo + Turno OK"

        return True, "Cargo OK"

    return False, "No cumple perfil"


# ==========================
# TELEGRAM
# ==========================

def enviar(msg):

    requests.get(

        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        params={"chat_id":CHAT_ID,"text":msg}

    )

# ==========================
# BUSCAR TRABAJOS
# ==========================

def buscar_bhp():

    lista = []

    url = "https://careers.bhp.com/search/?q=&locationsearch=Chile"

    html = requests.get(url).text

    soup = BeautifulSoup(html,"html.parser")

    for a in soup.find_all("a"):

        titulo = a.text.strip()

        link = a.get("href","")

        if "/job/" in link:

            lista.append({

                "empresa":"BHP",
                "titulo":titulo,
                "link":"https://careers.bhp.com"+link

            })

    return lista


def buscar_liebherr():

    lista=[]

    url="https://www.liebherr.com/en/cln/careers/job-vacancies/job-vacancies.html"

    html=requests.get(url).text

    soup=BeautifulSoup(html,"html.parser")

    for a in soup.find_all("a"):

        titulo=a.text.strip()

        link=a.get("href","")

        if "job" in link.lower():

            lista.append({

                "empresa":"Liebherr",
                "titulo":titulo,
                "link":link

            })

    return lista


def buscar_komatsu():

    lista=[]

    url="https://komatsu.jobs/search/?location=Chile"

    html=requests.get(url).text

    soup=BeautifulSoup(html,"html.parser")

    for a in soup.find_all("a"):

        titulo=a.text.strip()

        link=a.get("href","")

        if "/job/" in link:

            lista.append({

                "empresa":"Komatsu",
                "titulo":titulo,
                "link":link

            })

    return lista


# ==========================
# EJECUCION
# ==========================

todos=[]

for funcion in [

buscar_bhp,
buscar_liebherr,
buscar_komatsu

]:

    try:

        todos.extend(funcion())

    except:

        print("Error fuente")

# ==========================

revisados=0
validos=0

for trabajo in todos:

    revisados+=1

    texto = trabajo["titulo"]

    ok, razon = analisis_ia(texto)

    if not ok:
        continue

    if trabajo["link"] in memoria:
        continue

    memoria.append(trabajo["link"])

    validos+=1

    enviar(

f"""

NUEVO EMPLEO MINERO CHILE

Empresa: {trabajo["empresa"]}

Cargo:
{trabajo["titulo"]}

Link:
{trabajo["link"]}

IA:
{razon}

"""

)

# ==========================

with open(ARCHIVO,"w") as f:
    json.dump(memoria,f)

# ==========================

enviar(

f"""

RADAR FINALIZADO

Revisados:{revisados}

Validos:{validos}

Memoria:{len(memoria)}

"""

)
