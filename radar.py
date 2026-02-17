# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os

# =====================
# TELEGRAM DESDE SECRETS
# =====================

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# =====================
# FILTROS PROFESIONALES
# =====================

CARGOS = [
    "supervisor",
    "maintenance",
    "mantencion",
    "mantenimiento",
    "planner",
    "planificador",
    "contract",
    "contrato",
    "administrador",
    "operaciones"
]

EMPRESAS = [
    "minera",
    "mining",
    "bhp",
    "codelco",
    "kinross",
    "finning",
    "komatsu",
    "liebherr",
    "epiroc",
    "metso",
    "sandvik",
    "collahuasi",
    "antofagasta minerals"
]

ARCHIVO = "enviados.txt"

# =====================
# TELEGRAM
# =====================

def telegram(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }

    requests.post(url, data=data)

# =====================
# BASE DATOS
# =====================

def cargar():

    if not os.path.exists(ARCHIVO):

        return []

    with open(ARCHIVO,"r",encoding="utf8") as f:

        return f.read().splitlines()


def guardar(link):

    with open(ARCHIVO,"a",encoding="utf8") as f:

        f.write(link+"\n")

# =====================
# FILTRO INTELIGENTE
# =====================

def filtro(texto):

    texto = texto.lower()

    ok_cargo = any(x in texto for x in CARGOS)

    ok_empresa = any(x in texto for x in EMPRESAS)

    return ok_cargo and ok_empresa


# =====================
# INDEED
# =====================

def indeed():

    url = "https://cl.indeed.com/jobs?q=mineria&l=Chile"

    headers = {"User-Agent":"Mozilla"}

    html = requests.get(url,headers=headers)

    soup = BeautifulSoup(html.text,"html.parser")

    trabajos = soup.select("a.tapItem")

    enviados = cargar()

    nuevos = 0

    for t in trabajos:

        titulo = t.get_text()

        link = "https://cl.indeed.com"+t["href"]

        texto = titulo+link

        if filtro(texto):

            if link not in enviados:

                msg = f"""

🚨 OFERTA MINERA

{titulo}

{link}

"""

                telegram(msg)

                guardar(link)

                nuevos +=1

    return nuevos


# =====================
# LINKEDIN SIMPLE
# =====================

def linkedin():

    url = "https://www.linkedin.com/jobs/search/?keywords=mining%20chile"

    headers = {"User-Agent":"Mozilla"}

    html = requests.get(url,headers=headers)

    soup = BeautifulSoup(html.text,"html.parser")

    trabajos = soup.select("a")

    enviados = cargar()

    nuevos = 0

    for t in trabajos:

        titulo = t.get_text()

        link = t.get("href")

        if link and "job" in link:

            texto = titulo+link

            if filtro(texto):

                if link not in enviados:

                    msg=f"""

🚨 LINKEDIN MINERO

{titulo}

{link}

"""

                    telegram(msg)

                    guardar(link)

                    nuevos+=1

    return nuevos


# =====================
# MAIN
# =====================

def main():

    print("RADAR MINERO NIVEL DIOS")

    total = 0

    total += indeed()

    total += linkedin()

    if total==0:

        telegram("Radar activo sin novedades")

        print("Sin novedades")

    else:

        telegram(f"{total} nuevas ofertas detectadas")

        print(total,"ofertas nuevas")


if __name__=="__main__":

    main()
