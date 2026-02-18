# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os
import time

# =====================
# TELEGRAM DESDE SECRETS
# =====================

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Error Telegram:", e)

# =====================
# FILTROS PROFESIONALES
# =====================

CARGOS = [
    "supervisor", "mantencion", "mantenimiento",
    "planner", "planificador", "contrato",
    "contract", "administrador", "operaciones",
    "maintenance", "services", "service"
]

EMPRESAS = [
    "minera", "mining", "bhp", "codelco", "angloamerican",
    "escondida", "kinross", "antofagasta minerals",
    "collahuasi", "finning", "komatsu", "sodexo",
    "aramark", "newrest", "gategroup", "adecco", "manpower"
]

ARCHIVO = "ofertas_chile.txt"

if not os.path.exists(ARCHIVO):
    open(ARCHIVO, "w").close()

def cargar_enviados():
    with open(ARCHIVO, "r", encoding="utf-8") as f:
        return f.read().splitlines()

def guardar(link):
    with open(ARCHIVO, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def cumple(text):
    txt = text.lower()
    return any(k in txt for k in CARGOS) and any(e in txt for e in EMPRESAS)

# =====================
# Indeed Chile
# =====================

def buscar_indeed_chile():
    url = "https://cl.indeed.com/jobs?q=mineria&l=Chile"
    headers = {"User-Agent":"Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    trabajos = soup.select("a.tapItem")
    enviados = cargar_enviados()
    nuevos = 0

    for t in trabajos:
        titulo = t.get_text().strip()
        link = "https://cl.indeed.com" + t.get("href")
        text = f"{titulo} {link}"
        if cumple(text) and link not in enviados:
            mensaje = f"🚨 OFERTA CHILE (Indeed)\n{titulo}\n{link}"
            telegram(mensaje)
            guardar(link)
            nuevos += 1
    return nuevos

# =====================
# Portales Oficiales - MINERÍA CHILE
# =====================

def buscar_portal_bhp():
    url = "https://careers.bhp.com/search-jobs?location=Chile"
    headers = {"User-Agent":"Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    trabajos = soup.select("a.job-title-link")
    enviados = cargar_enviados()
    nuevos = 0

    for t in trabajos:
        titulo = t.text.strip()
        link = "https://careers.bhp.com" + t.get("href")
        text = f"{titulo} {link}"
        if cumple(text) and link not in enviados:
            msg = f"🚨 OFERTA BHP CHILE\n{titulo}\n{link}"
            telegram(msg)
            guardar(link)
            nuevos += 1
    return nuevos

def buscar_portal_codelco():
    url = "https://trabajaencodelco.cl/trabajos/page/1/"
    headers = {"User-Agent":"Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    trabajos = soup.select("div.job-listing a")
    enviados = cargar_enviados()
    nuevos = 0

    for t in trabajos:
        titulo = t.text.strip()
        link = t.get("href")
        text = f"{titulo} {link}"
        if "codelco" in link and cumple(text) and link not in enviados:
            msg = f"🚨 OFERTA CODELCO\n{titulo}\n{link}"
            telegram(msg)
            guardar(link)
            nuevos += 1
    return nuevos

def buscar_portal_anglo():
    url = "https://www.angloamerican.com/careers/search-and-apply"
    headers = {"User-Agent":"Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    trabajos = soup.select("a.SearchResultCard") or soup.select("a.job-item")
    enviados = cargar_enviados()
    nuevos = 0

    for t in trabajos:
        titulo = t.get_text().strip()
        link = t.get("href")
        if not link.startswith("http"):
            link = "https://www.angloamerican.com" + link
        text = f"{titulo} {link}"
        if cumple(text) and link not in enviados:
            msg = f"🚨 OFERTA ANGLO AMERICAN\n{titulo}\n{link}"
            telegram(msg)
            guardar(link)
            nuevos += 1
    return nuevos

# =====================
# Empresas de Servicios
# =====================

def buscar_portal_sodexo():
    url = "https://careers.sodexo.com/search-jobs"
    headers = {"User-Agent":"Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    trabajos = soup.select("a.job-title")
    enviados = cargar_enviados()
    nuevos = 0

    for t in trabajos:
        titulo = t.text.strip()
        link = t.get("href")
        if not link.startswith("http"):
            link = "https://careers.sodexo.com" + link
        text = f"{titulo} {link}"
        if cumple(text) and link not in enviados:
            msg = f"🚨 OFERTA SODEXO Chile/LatAm\n{titulo}\n{link}"
            telegram(msg)
            guardar(link)
            nuevos += 1
    return nuevos

def buscar_portal_aramark():
    url = "https://aramark.wd3.myworkdayjobs.com/External"
    headers = {"User-Agent":"Mozilla/5.0"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    trabajos = soup.select("a.job-title")
    enviados = cargar_enviados()
    nuevos = 0

    for t in trabajos:
        titulo = t.text.strip()
        link = t.get("href")
        if not link.startswith("http"):
            link = "https://aramark.wd3.myworkdayjobs.com" + link
        text = f"{titulo} {link}"
        if cumple(text) and link not in enviados:
            msg = f"🚨 OFERTA ARAMARK Chile/LatAm\n{titulo}\n{link}"
            telegram(msg)
            guardar(link)
            nuevos += 1
    return nuevos

# =====================
# EJECUCIÓN PRINCIPAL
# =====================

def main():
    total = 0

    total += buscar_indeed_chile()
    total += buscar_portal_bhp()
    total += buscar_portal_codelco()
    total += buscar_portal_anglo()
    total += buscar_portal_sodexo()
    total += buscar_portal_aramark()

    if total == 0:
        telegram("Radar activo CHILE sin novedades.")
    else:
        telegram(f"{total} ofertas nuevas detectadas.")

if __name__ == "__main__":
    main()
