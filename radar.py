import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

print("RADAR MINERO V15 ULTRA INICIADO")

# ==========================
# CONFIG PERFIL RUBEN
# ==========================

CARGOS_PRIORIDAD = [

"supervisor",
"administrador de contratos",
"contract administrator",
"ingeniero confiabilidad",
"reliability",
"planificador",
"planner",
"jefe mantenimiento"

]

TURNOS = [

"14x14",
"10x10",
"7x7",
"4x3"

]

UBICACION = [

"chile",
"antofagasta",
"calama",
"copiapo",
"faena",
"minera"

]

# ==========================
# MEMORIA
# ==========================

try:
    with open("memoria.json","r") as f:
        memoria=json.load(f)
except:
    memoria=[]

# ==========================
# TELEGRAM
# ==========================

def enviar(msg):

    requests.get(

        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        params={"chat_id":CHAT_ID,"text":msg}

    )

# ==========================
# LEER DESCRIPCION
# ==========================

def leer_descripcion(link):

    try:

        html=requests.get(link,timeout=10).text

        return html.lower()

    except:

        return ""

# ==========================
# IA REAL
# ==========================

def filtro_ia(titulo,link):

    texto = titulo.lower()

    if not any(c in texto for c in CARGOS_PRIORIDAD):
        return False,"Cargo no coincide"

    descripcion = leer_descripcion(link)

    texto_total = texto + descripcion

    if not any(u in texto_total for u in UBICACION):
        return False,"No Chile"

    turno_detectado="No indica"

    for t in TURNOS:

        if t in texto_total:
            turno_detectado=t

    return True,f"OK Turno:{turno_detectado}"

# ==========================
# BHP
# ==========================

def bhp():

    lista=[]

    url="https://careers.bhp.com/search/?locationsearch=Chile"

    soup=BeautifulSoup(requests.get(url).text,"html.parser")

    for a in soup.find_all("a"):

        link=a.get("href","")

        if "/job/" in link:

            lista.append({

                "empresa":"BHP",
                "titulo":a.text.strip(),
                "link":"https://careers.bhp.com"+link

            })

    return lista


# ==========================
# KOMATSU
# ==========================

def komatsu():

    lista=[]

    url="https://komatsu.jobs/search/?location=Chile"

    soup=BeautifulSoup(requests.get(url).text,"html.parser")

    for a in soup.find_all("a"):

        link=a.get("href","")

        if "/job/" in link:

            lista.append({

                "empresa":"Komatsu",
                "titulo":a.text.strip(),
                "link":link

            })

    return lista


# ==========================
# EJECUCION
# ==========================

fuentes=[bhp,komatsu]

todos=[]

for f in fuentes:

    try:
        todos.extend(f())
    except:
        print("error fuente")

revisados=0
validos=0

for job in todos:

    revisados+=1

    ok,info=filtro_ia(job["titulo"],job["link"])

    if not ok:
        continue

    if job["link"] in memoria:
        continue

    memoria.append(job["link"])

    validos+=1

    enviar(f"""

NUEVO EMPLEO MINERO PREMIUM

Empresa: {job['empresa']}

Cargo:
{job['titulo']}

Link:
{job['link']}

IA:
{info}

""")

# ==========================

with open("memoria.json","w") as f:

    json.dump(memoria,f)

# ==========================

enviar(f"""

RADAR FINALIZADO

Revisados:{revisados}

Validos:{validos}

Memoria:{len(memoria)}

""")
