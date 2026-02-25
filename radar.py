import requests
from bs4 import BeautifulSoup
import os
import json
import re

print("RADAR MINERO V17 ULTRA — COBERTURA TOTAL CHILE")

TOKEN=os.environ["TOKEN"]
CHAT_ID=os.environ["CHAT_ID"]

MEMORIA="memoria.json"

# =====================
# MEMORIA
# =====================

def cargar_memoria():
    try:
        with open(MEMORIA,"r") as f:
            return json.load(f)
    except:
        return []

def guardar_memoria(m):
    with open(MEMORIA,"w") as f:
        json.dump(m,f)

memoria=cargar_memoria()

# =====================
# CONFIG IA BARONIN
# =====================

KEYWORDS=[

"administrador de contratos",
"supervisor",
"supervisor mantencion",
"supervisor mantenimiento",
"ingeniero confiabilidad",
"ingeniero mantenimiento",
"planner",
"planificador"

]

UBICACION=[

"chile",
"antofagasta",
"calama",
"copiapo",
"iquique",
"faena"

]

TURNOS=["7x7","14x14","10x10","4x3"]

# =====================
# IA FUNCIONES
# =====================

def es_chile(texto):

    texto=texto.lower()

    return any(u in texto for u in UBICACION)


def detectar_turno(texto):

    texto=texto.lower()

    for t in TURNOS:

        if t in texto:

            return t

    return "No indica"


def score(titulo):

    titulo=titulo.lower()

    s=0

    for k in KEYWORDS:

        if k in titulo:

            s+=25

    return s


def prioridad(s):

    if s>=75:
        return "🚨 PRIORIDAD MAXIMA"

    if s>=50:
        return "🟡 PRIORIDAD ALTA"

    if s>=25:
        return "🟢 PRIORIDAD MEDIA"

    return "🔎 DETECTADO"


def enviar(msg):

    url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url,data={"chat_id":CHAT_ID,"text":msg})

# =====================
# SCRAPERS
# =====================

def bhp():

    lista=[]

    url="https://careers.bhp.com/search/?optionsFacetsDD_country=Chile"

    r=requests.get(url)

    soup=BeautifulSoup(r.text,"html.parser")

    for a in soup.find_all("a"):

        link=a.get("href","")

        if "/job/" in link:

            link="https://careers.bhp.com"+link

            titulo=a.text.strip()

            try:

                p=requests.get(link)

                texto=p.text.lower()

            except:

                texto=titulo

            lista.append(("BHP",titulo,link,texto))

    return lista


def laborum():

    lista=[]

    url="https://www.laborum.cl/empleos-mineria.html"

    r=requests.get(url)

    soup=BeautifulSoup(r.text,"html.parser")

    for a in soup.find_all("a"):

        link=a.get("href","")

        titulo=a.text.strip
