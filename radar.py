# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ARCHIVO = "enviados.txt"

if not os.path.exists(ARCHIVO):
    open(ARCHIVO,"w").close()


# ======================
# TELEGRAM
# ======================

def telegram(msg):

    url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url,data={
        "chat_id":CHAT_ID,
        "text":msg
    })


# ======================
# BASE DATOS
# ======================

def enviados():

    with open(ARCHIVO,"r",encoding="utf8") as f:

        return f.read().splitlines()


def guardar(link):

    with open(ARCHIVO,"a",encoding="utf8") as f:

        f.write(link+"\n")


# ======================
# FILTROS CHILE MINERIA
# ======================

KEYWORDS=[
"supervisor",
"mantencion",
"mantenimiento",
"planner",
"planificador",
"contrato",
"contract"
]

EMPRESAS=[
"minera",
"bhp",
"codelco",
"anglo",
"sodexo",
"aramark",
"newrest",
"komatsu",
"finning"
]


def filtro(texto):

    t=texto.lower()

    return any(k in t for k in KEYWORDS) and any(e in t for e in EMPRESAS)



# ======================
# INDEED CHILE (FUNCIONA)
# ======================

def indeed():

    url="https://cl.indeed.com/jobs?q=minera&l=Chile"

    headers={"User-Agent":"Mozilla/5.0"}

    html=requests.get(url,headers=headers)

    soup=BeautifulSoup(html.text,"html.parser")

    trabajos=soup.select("h2 a")

    nuevos=0

    lista=enviados()

    for t in trabajos:

        titulo=t.text.strip()

        link="https://cl.indeed.com"+t["href"]

        texto=titulo+link

        if filtro(texto):

            if link not in lista:

                telegram(f"🚨 Indeed Chile\n{titulo}\n{link}")

                guardar(link)

                nuevos+=1

    return nuevos



# ======================
# CHILETRABAJOS
# ======================

def chiletrabajos():

    url="https://www.chiletrabajos.cl/buscar?q=minera"

    headers={"User-Agent":"Mozilla"}

    html=requests.get(url,headers=headers)

    soup=BeautifulSoup(html.text,"html.parser")

    trabajos=soup.select(".job-item a")

    nuevos=0

    lista=enviados()

    for t in trabajos:

        titulo=t.text.strip()

        link=t["href"]

        texto=titulo+link

        if filtro(texto):

            if link not in lista:

                telegram(f"🚨 Chiletrabajos\n{titulo}\n{link}")

                guardar(link)

                nuevos+=1

    return nuevos



# ======================
# MAIN
# ======================

def main():

    total=0

    total+=indeed()

    total+=chiletrabajos()

    if total==0:

        telegram("Radar Chile activo sin novedades")

    else:

        telegram(f"{total} ofertas nuevas en Chile")


if __name__=="__main__":

    main()
