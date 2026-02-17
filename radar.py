# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import time
import os

# =========================
# CONFIGURACION TELEGRAM
# =========================

TOKEN = "8230281232:AAFNFWGscdgbs97HsgeWQpnA-kCw6KwV0JQ"
CHAT_ID = "7232135381"

# =========================
# PALABRAS CLAVE CARGOS
# =========================

KEYWORDS = [
    "supervisor",
    "mantencion",
    "mantenimiento",
    "contrato",
    "contratos",
    "operaciones",
    "planificador"
]

# =========================
# EMPRESAS MINERAS
# =========================

EMPRESAS = [
    "bhp",
    "codelco",
    "kinross",
    "antofagasta minerals",
    "aminerals",
    "collahuasi",
    "sierra gorda",
    "komatsu",
    "finning",
    "liebherr",
    "metso",
    "sandvik",
    "epiroc",
    "anglo american",
    "teck",
    "cap mineria"
]

# =========================
# ARCHIVO BASE DATOS
# =========================

ARCHIVO = "ofertas_enviadas.txt"

# crear archivo si no existe
if not os.path.exists(ARCHIVO):
    open(ARCHIVO, "w").close()

# =========================
# FUNCION TELEGRAM
# =========================

def enviar_telegram(mensaje):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": mensaje
    }

    try:
        requests.post(url, data=data)
    except:
        print("Error enviando mensaje")

# =========================
# FUNCION FILTRO
# =========================

def cumple(texto):

    texto = texto.lower()

    if not any(k in texto for k in KEYWORDS):
        return False

    if not any(e in texto for e in EMPRESAS):
        return False

    return True

# =========================
# LEER OFERTAS YA ENVIADAS
# =========================

def cargar_enviados():

    with open(ARCHIVO, "r", encoding="utf-8") as f:
        return f.read().splitlines()

# =========================
# GUARDAR OFERTA
# =========================

def guardar(oferta):

    with open(ARCHIVO, "a", encoding="utf-8") as f:
        f.write(oferta + "\n")

# =========================
# BUSCAR EN INDEED
# =========================

def buscar_indeed():

    url = "https://cl.indeed.com/jobs?q=mineria&l=Chile"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    trabajos = soup.select("a.tapItem")

    enviados = cargar_enviados()

    encontrados = 0

    for trabajo in trabajos:

        titulo = trabajo.get_text().strip()

        link = "https://cl.indeed.com" + trabajo.get("href")

        texto = titulo + link

        if cumple(texto):

            if link not in enviados:

                mensaje = f"""
🚨 NUEVA OFERTA MINERA

{titulo}

{link}
"""

                enviar_telegram(mensaje)

                guardar(link)

                encontrados += 1

                print("Enviado:", titulo)

    return encontrados

# =========================
# PROGRAMA PRINCIPAL
# =========================

def main():

    print("Radar iniciado...")

    encontrados = buscar_indeed()

    if encontrados == 0:

        enviar_telegram("Radar activo sin novedades")

        print("Sin novedades")

    else:

        print("Ofertas nuevas:", encontrados)

# =========================

if __name__ == "__main__":

    main()
