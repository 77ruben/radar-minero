import requests
from bs4 import BeautifulSoup
import os
import json
import re

print("RADAR MINERO V16 — PRIORIDAD MAXIMA ACTIVADA")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA = "memoria.json"

# ==========================
# MEMORIA ANTI DUPLICADOS
# ==========================

def cargar_memoria():
    try:
        with open(MEMORIA,"r") as f:
            return json.load(f)
    except:
        return []

def guardar_memoria(mem):
    with open(MEMORIA,"w") as f:
        json.dump(mem,f)

memoria = cargar_memoria()

# ==========================
# PRIORIDAD MAXIMA TU PERFIL
# ==========================

PRIORIDAD_MAXIMA = [

"administrador de contratos",
"supervisor",
"supervisor mantencion",
"supervisor mantenimiento",
"supervisor operaciones",
"supervisor confiabilidad",
"ingeniero confiabilidad",
"ingeniero mantenimiento",
"ingeniero planificacion",
"planner mantenimiento"

]

# ==========================
# UBICACIONES CHILE
# ==========================

UBICACION_CHILE = [

"chile",
"antofagasta",
"calama",
"copiapo",
"iquique",
"faena",
"escondida",
"spence",
"collahuasi",
"los pelambres",
"centinela"

]

# ==========================
# TURNOS
# ==========================

TURNOS = [

"7x7",
"14x14",
"10x10",
"4x3"

]

# ==========================
# FUNCIONES IA BARONIN
# ==========================

def es_chile(texto):

    texto = texto.lower()

    return any(u in texto for u in UBICACION_CHILE)


def detectar_turno(texto):

    texto = texto.lower()

    for t in TURNOS:

        if t in texto:
            return t

    return "No indica"


def calcular_score(titulo):

    titulo = titulo.lower()

    score = 0

    for p in PRIORIDAD_MAXIMA:

        if p in titulo:
            score += 25

    return score


def prioridad(score):

    if score >= 75:
        return "🚨 PRIORIDAD MAXIMA — POSTULAR URGENTE"

    if score >= 50:
        return "🟡 PRIORIDAD ALTA"

    if score >= 25:
        return "🟢 PRIORIDAD MEDIA"

    return "DESCARTADO"


# ==========================
# TELEGRAM
# ==========================

def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url,data={

        "chat_id":CHAT_ID,
        "text":msg

    })


# ==========================
# SCRAPER BHP CHILE
# ==========================

def bhp():

    url = "https://careers.bhp.com/search/?createNewAlert=false&q=Chile&optionsFacetsDD_country=Chile"

    r = requests.get(url)

    soup = BeautifulSoup(r.text,"html.parser")

    trabajos = soup.find_all("a")

    encontrados = []

    for t in trabajos:

        titulo = t.text.strip()

        link = t.get("href","")

        if "/job/" in link:

            link = "https://careers.bhp.com"+link

            encontrados.append({

                "empresa":"BHP",
                "titulo":titulo,
                "link":link

            })

    return encontrados


# ==========================
# PROCESAR EMPLEOS
# ==========================

revisados=0
validos=0

empleos = bhp()

for e in empleos:

    revisados+=1

    titulo=e["titulo"]
    link=e["link"]
    empresa=e["empresa"]

    if link in memoria:
        continue

    if not es_chile(titulo):
        continue

    score=calcular_score(titulo)

    nivel=prioridad(score)

    if nivel=="DESCARTADO":
        continue

    turno=detectar_turno(titulo)

    mensaje=f"""

{nivel}

Empresa: {empresa}

Cargo:
{titulo}

Turno: {turno}

Score IA: {score}%

Link:
{link}

IA Baronin:
Alta compatibilidad con tu perfil profesional.

"""

    enviar(mensaje)

    memoria.append(link)

    validos+=1


guardar_memoria(memoria)


# ==========================
# FINAL
# ==========================

enviar(f"""

RADAR FINALIZADO

Revisados:{revisados}

Validos:{validos}

Memoria:{len(memoria)}

""")
