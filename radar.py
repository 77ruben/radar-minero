import requests
from bs4 import BeautifulSoup
import os
import json
import time

print("RADAR MINERO V18 PRO — NIVEL RECLUTADOR")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA="memoria.json"

# =====================
# TELEGRAM
# =====================

def telegram(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id":CHAT_ID,"text":msg}
    )


# =====================
# MEMORIA
# =====================

def cargar():

    try:
        with open(MEMORIA,"r") as f:
            return json.load(f)
    except:
        return []

def guardar(m):

    with open(MEMORIA,"w") as f:
        json.dump(m,f)

memoria=cargar()

# =====================
# IA FILTRO TU PERFIL
# =====================

KEYWORDS=[

"administrador de contratos",
"supervisor",
"confiabilidad",
"mantenimiento",
"mantencion",
"planner",
"planificador"

]

TURNOS=["7x7","14x14","10x10","4x3"]

UBICACION=[

"chile",
"antofagasta",
"calama",
"copiapo",
"iquique",
"faena"

]


def score(texto):

    s=0

    texto=texto.lower()

    for k in KEYWORDS:

        if k in texto:

            s+=20

    return s


def prioridad(s):

    if s>=60:
        return "🚨 PRIORIDAD MAXIMA"

    if s>=40:
        return "🟡 PRIORIDAD ALTA"

    if s>=20:
        return "🟢 PRIORIDAD MEDIA"

    return "🔎 DETECTADO"


def turno(texto):

    texto=texto.lower()

    for t in TURNOS:

        if t in texto:

            return t

    return "No indica"


def es_chile(texto):

    texto=texto.lower()

    return any(u in texto for u in UBICACION)


# =====================
# SCRAPER BHP REAL
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

            try:

                p=requests.get(link)

                texto=p.text

            except:

                texto=a.text

            lista.append(("BHP",a.text.strip(),link,texto))

            time.sleep(1)

    return lista


# =====================
# SCRAPER FINNING
# =====================

def finning():

    lista=[]
