"""
RADAR MINERO V6 PRO - Rubén Morales
Búsqueda activa de empleos en minería chilena
Deduplicación por archivo JSON en el repositorio
Notificación via Telegram
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import json
import hashlib
import re
from datetime import datetime

print("=" * 50)
print("  RADAR MINERO V6 PRO")
print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 50)

# ─────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────
TOKEN   = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SEEN_FILE = "seen_jobs.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────────
# PERFIL DE BÚSQUEDA
# ─────────────────────────────────────────────────
PERFIL = [
    "ingeniero", "ingeniería", "ingenieria",
    "mantencion", "mantención", "mantenimiento",
    "administrador de contrato", "administrador contrato",
    "planificacion", "planificación", "planner", "planificador",
    "confiabilidad", "reliability",
    "logistica", "logística",
    "supervisor", "jefe de mantenimiento", "jefe mantención",
    "contract manager", "contracts",
    "facility", "facilities",
    "infraestructura", "operaciones",
]

TURNOS = [
    "14x14", "14 x 14",
    "10x10", "10 x 10",
    "7x7", "7 x 7",
    "4x3", "4 x 3",
    "turno", "faena", "campamento",
]

EXCLUIR = [
    "bodega", "guardia", "chofer", "vendedor", "vendedora",
    "cajero", "cajera", "digitador", "secretaria", "recepcionista",
    "operario", "junior sin experiencia",
]

UBICACIONES_KEYWORDS = [
    "antofagasta", "calama", "iquique", "atacama", "copiapó", "copiapo",
    "chuquicamata", "tocopilla", "mejillones", "sierra gorda",
    "norte", "ii región", "i región", "iii región", "región de antofagasta",
]

# ─────────────────────────────────────────────────
# DEDUPLICACIÓN
# ─────────────────────────────────────────────────
def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def guardar_vistos(vistos):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(vistos), f, indent=2)

def hash_aviso(titulo, link):
    raw = f"{titulo.lower().strip()}{link.strip()}"
    return hashlib.md5(raw.encode()).hexdigest()

# ─────────────────────────────────────────────────
# FILTROS
# ─────────────────────────────────────────────────
def cumple_perfil(texto):
    texto = texto.lower()
    if any(x in texto for x in EXCLUIR):
        return False
    return any(p in texto for p in PERFIL)

def detectar_turno(texto):
    texto = texto.lower()
    for t in TURNOS:
        if t.lower() in texto:
            return t.upper()
    return None

def detectar_ubicacion(texto):
    texto = texto.lower()
    for u in UBICACIONES_KEYWORDS:
        if u in texto:
            return u.title()
    return None

# ─────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────
def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"  ⚠️  Error Telegram: {e}")
    time.sleep(1.5)

def formato_aviso(fuente, titulo, empresa, ubicacion, turno, link):
    lineas = [
        f"🔔 <b>NUEVO EMPLEO - {fuente}</b>",
        f"📋 <b>{titulo}</b>",
    ]
    if empresa:
        lineas.append(f"🏭 {empresa}")
    if ubicacion:
        lineas.append(f"📍 {ubicacion}")
    if turno:
        lineas.append(f"⏰ Turno: {turno}")
    if link:
        lineas.append(f"🔗 {link}")
    return "\n".join(lineas)

# ─────────────────────────────────────────────────
# FUENTES
# ─────────────────────────────────────────────────

def scrape_trabajando(vistos):
    """Trabajando.cl - minería"""
    nombre = "Trabajando.cl"
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    urls = [
        "https://www.trabajando.cl/trabajos-mineria",
        "https://www.trabajando.cl/trabajos-mantenimiento-industrial",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for tag in soup.find_all("a", href=True):
                titulo = tag.text.strip()
                link = tag["href"]
                if not titulo or len(titulo) < 10:
                    continue
                if not link.startswith("http"):
                    link = "https://www.trabajando.cl" + link
                if not cumple_perfil(titulo):
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                turno = detectar_turno(titulo)
                ubicacion = detectar_ubicacion(titulo)
                msg = formato_aviso(nombre, titulo, None, ubicacion, turno, link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
        except Exception as e:
            print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_laborum(vistos):
    """Laborum.cl - búsqueda minería"""
    nombre = "Laborum.cl"
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    urls = [
        "https://www.laborum.cl/empleos/mineria",
        "https://www.laborum.cl/empleos/mantenimiento-industrial",
        "https://www.laborum.cl/empleos/administracion-contratos",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            # Laborum usa tarjetas con clase específica
            for card in soup.find_all(["article", "div"], class_=re.compile(r"job|aviso|card|oferta", re.I)):
                titulo_tag = card.find(["h2", "h3", "a"])
                if not titulo_tag:
                    continue
                titulo = titulo_tag.text.strip()
                link_tag = card.find("a", href=True)
                link = link_tag["href"] if link_tag else url
                if not link.startswith("http"):
                    link = "https://www.laborum.cl" + link
                empresa_tag = card.find(class_=re.compile(r"empresa|company", re.I))
                empresa = empresa_tag.text.strip() if empresa_tag else None
                ubicacion_tag = card.find(class_=re.compile(r"ubicacion|location|ciudad", re.I))
                ubicacion = ubicacion_tag.text.strip() if ubicacion_tag else detectar_ubicacion(titulo)
                if not cumple_perfil(titulo):
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                turno = detectar_turno(card.text)
                msg = formato_aviso(nombre, titulo, empresa, ubicacion, turno, link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
        except Exception as e:
            print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_computrabajo(vistos):
    """Computrabajo.cl"""
    nombre = "Computrabajo"
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    urls = [
        "https://www.computrabajo.cl/trabajos-de-mineria",
        "https://www.computrabajo.cl/trabajos-de-mantenimiento-industrial",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for article in soup.find_all("article"):
                titulo_tag = article.find(["h2", "h3", "a"])
                if not titulo_tag:
                    continue
                titulo = titulo_tag.text.strip()
                link_tag = article.find("a", href=True)
                link = link_tag["href"] if link_tag else url
                if not link.startswith("http"):
                    link = "https://www.computrabajo.cl" + link
                empresa_tag = article.find(class_=re.compile(r"empresa|company", re.I))
                empresa = empresa_tag.text.strip() if empresa_tag else None
                if not cumple_perfil(titulo):
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                ubicacion = detectar_ubicacion(article.text)
                turno = detectar_turno(article.text)
                msg = formato_aviso(nombre, titulo, empresa, ubicacion, turno, link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
        except Exception as e:
            print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_indeed(vistos):
    """Indeed Chile"""
    nombre = "Indeed"
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    queries = [
        "administrador+contrato+mineria",
        "supervisor+mantencion+mineria",
        "ingeniero+mantenimiento+mineria+chile",
    ]
    for q in queries:
        url = f"https://cl.indeed.com/jobs?q={q}&l=Chile"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div", class_=re.compile(r"job_seen_beacon|jobsearch-SerpJobCard|job-card", re.I)):
                titulo_tag = card.find(["h2", "h3", "a"])
                if not titulo_tag:
                    continue
                titulo = titulo_tag.text.strip()
                link_tag = card.find("a", href=True)
                link = "https://cl.indeed.com" + link_tag["href"] if link_tag and not link_tag["href"].startswith("http") else (link_tag["href"] if link_tag else url)
                empresa_tag = card.find(class_=re.compile(r"company|empresa", re.I))
                empresa = empresa_tag.text.strip() if empresa_tag else None
                if not cumple_perfil(titulo):
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                ubicacion = detectar_ubicacion(card.text)
                turno = detectar_turno(card.text)
                msg = formato_aviso(nombre, titulo, empresa, ubicacion, turno, link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  Error {nombre} ({q}): {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_linkedin(vistos):
    """LinkedIn Jobs"""
    nombre = "LinkedIn"
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    queries = [
        ("administrador%20contrato%20mineria%20chile", "Chile"),
        ("supervisor%20mantencion%20mineria", "Antofagasta%2C%20Chile"),
        ("ingeniero%20mantenimiento%20mineria", "Calama%2C%20Chile"),
    ]
    for q, loc in queries:
        url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}&f_TPR=r86400"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div", class_=re.compile(r"base-card|job-search-card", re.I)):
                titulo_tag = card.find(["h3", "h4", "a"])
                if not titulo_tag:
                    continue
                titulo = titulo_tag.text.strip()
                link_tag = card.find("a", href=True)
                link = link_tag["href"].split("?")[0] if link_tag else url
                empresa_tag = card.find(class_=re.compile(r"company|empresa|base-search-card__subtitle", re.I))
                empresa = empresa_tag.text.strip() if empresa_tag else None
                ubicacion_tag = card.find(class_=re.compile(r"location|base-search-card__metadata", re.I))
                ubicacion = ubicacion_tag.text.strip() if ubicacion_tag else None
                if not cumple_perfil(titulo):
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                turno = detectar_turno(card.text)
                msg = formato_aviso(nombre, titulo, empresa, ubicacion, turno, link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
            time.sleep(3)
        except Exception as e:
            print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_codelco(vistos):
    """Portal directo Codelco"""
    nombre = "Codelco"
    print(f"\n🔍 {nombre}...")
    url = "https://www.codelco.com/trabaja-con-nosotros/prontus_codelco/2012-01-16/120018.html"
    encontrados = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            titulo = a.text.strip()
            link = a["href"]
            if not link.startswith("http"):
                link = "https://www.codelco.com" + link
            if not cumple_perfil(titulo) or len(titulo) < 8:
                continue
            hid = hash_aviso(titulo, link)
            if hid in vistos:
                continue
            msg = formato_aviso(nombre, titulo, "Codelco", None, None, link)
            enviar(msg)
            vistos.add(hid)
            encontrados += 1
    except Exception as e:
        print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_bhp(vistos):
    """BHP Careers"""
    nombre = "BHP"
    print(f"\n🔍 {nombre}...")
    url = "https://careers.bhp.com/search-jobs/Chile"
    encontrados = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all(["li", "div"], class_=re.compile(r"job|position|listing", re.I)):
            titulo_tag = card.find(["h3", "h4", "a", "span"])
            if not titulo_tag:
                continue
            titulo = titulo_tag.text.strip()
            link_tag = card.find("a", href=True)
            link = link_tag["href"] if link_tag else url
            if not link.startswith("http"):
                link = "https://careers.bhp.com" + link
            if not cumple_perfil(titulo) or len(titulo) < 8:
                continue
            hid = hash_aviso(titulo, link)
            if hid in vistos:
                continue
            turno = detectar_turno(card.text)
            msg = formato_aviso(nombre, titulo, "BHP", "Antofagasta/Atacama", turno, link)
            enviar(msg)
            vistos.add(hid)
            encontrados += 1
    except Exception as e:
        print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_collahuasi(vistos):
    """Collahuasi"""
    nombre = "Collahuasi"
    print(f"\n🔍 {nombre}...")
    url = "https://www.collahuasi.cl/trabaja-con-nosotros/"
    encontrados = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            titulo = a.text.strip()
            link = a["href"]
            if not link.startswith("http"):
                link = "https://www.collahuasi.cl" + link
            if not cumple_perfil(titulo) or len(titulo) < 8:
                continue
            hid = hash_aviso(titulo, link)
            if hid in vistos:
                continue
            msg = formato_aviso(nombre, titulo, "Collahuasi", "Iquique / Tarapacá", None, link)
            enviar(msg)
            vistos.add(hid)
            encontrados += 1
    except Exception as e:
        print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_angloamerican(vistos):
    """Anglo American Chile"""
    nombre = "Anglo American"
    print(f"\n🔍 {nombre}...")
    url = "https://www.angloamerican.com/careers/job-search?country=Chile"
    encontrados = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all(["li", "div", "article"], class_=re.compile(r"job|vacancy|position", re.I)):
            titulo_tag = card.find(["h2", "h3", "h4", "a"])
            if not titulo_tag:
                continue
            titulo = titulo_tag.text.strip()
            link_tag = card.find("a", href=True)
            link = link_tag["href"] if link_tag else url
            if not link.startswith("http"):
                link = "https://www.angloamerican.com" + link
            if not cumple_perfil(titulo) or len(titulo) < 8:
                continue
            hid = hash_aviso(titulo, link)
            if hid in vistos:
                continue
            msg = formato_aviso(nombre, titulo, "Anglo American", "Los Bronces / El Soldado", None, link)
            enviar(msg)
            vistos.add(hid)
            encontrados += 1
    except Exception as e:
        print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_antofagasta_minerals(vistos):
    """Antofagasta Minerals (Pelambres, Centinela, Zaldívar)"""
    nombre = "Antofagasta Minerals"
    print(f"\n🔍 {nombre}...")
    url = "https://www.aminerals.cl/personas/trabaja-con-nosotros/"
    encontrados = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            titulo = a.text.strip()
            link = a["href"]
            if not link.startswith("http"):
                link = "https://www.aminerals.cl" + link
            if not cumple_perfil(titulo) or len(titulo) < 8:
                continue
            hid = hash_aviso(titulo, link)
            if hid in vistos:
                continue
            msg = formato_aviso(nombre, titulo, "Antofagasta Minerals", None, None, link)
            enviar(msg)
            vistos.add(hid)
            encontrados += 1
    except Exception as e:
        print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_trabajoenmineria(vistos):
    """trabajoenmineria.cl - portal especializado"""
    nombre = "TrabajoenMineria.cl"
    print(f"\n🔍 {nombre}...")
    url = "https://www.trabajoenmineria.cl/ofertas"
    encontrados = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all(["article", "div", "li"], class_=re.compile(r"job|oferta|aviso|card", re.I)):
            titulo_tag = card.find(["h2", "h3", "h4", "a"])
            if not titulo_tag:
                continue
            titulo = titulo_tag.text.strip()
            link_tag = card.find("a", href=True)
            link = link_tag["href"] if link_tag else url
            if not link.startswith("http"):
                link = "https://www.trabajoenmineria.cl" + link
            empresa_tag = card.find(class_=re.compile(r"empresa|company", re.I))
            empresa = empresa_tag.text.strip() if empresa_tag else None
            ubicacion = detectar_ubicacion(card.text)
            turno = detectar_turno(card.text)
            if not cumple_perfil(titulo):
                continue
            hid = hash_aviso(titulo, link)
            if hid in vistos:
                continue
            msg = formato_aviso(nombre, titulo, empresa, ubicacion, turno, link)
            enviar(msg)
            vistos.add(hid)
            encontrados += 1
    except Exception as e:
        print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


def scrape_bne(vistos):
    """Bolsa Nacional de Empleo (Gobierno)"""
    nombre = "BNE Chile"
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    urls = [
        "https://www.bne.cl/empleos?q=administrador+contrato+mineria",
        "https://www.bne.cl/empleos?q=supervisor+mantencion+mineria",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all(["article", "div"], class_=re.compile(r"job|empleo|card|oferta", re.I)):
                titulo_tag = card.find(["h2", "h3", "a"])
                if not titulo_tag:
                    continue
                titulo = titulo_tag.text.strip()
                link_tag = card.find("a", href=True)
                link = link_tag["href"] if link_tag else url
                if not link.startswith("http"):
                    link = "https://www.bne.cl" + link
                if not cumple_perfil(titulo) or len(titulo) < 8:
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                ubicacion = detectar_ubicacion(card.text)
                turno = detectar_turno(card.text)
                msg = formato_aviso(nombre, titulo, None, ubicacion, turno, link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
        except Exception as e:
            print(f"  ⚠️  Error {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos avisos")
    return encontrados


# ─────────────────────────────────────────────────
# EJECUCIÓN PRINCIPAL
# ─────────────────────────────────────────────────
vistos = cargar_vistos()
print(f"\n📂 Avisos ya vistos: {len(vistos)}")

enviar(
    f"🤖 <b>RADAR MINERO V6 PRO</b>\n"
    f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    f"🔍 Iniciando búsqueda en {10} fuentes..."
)

total = 0
total += scrape_trabajoenmineria(vistos)
total += scrape_trabajando(vistos)
total += scrape_laborum(vistos)
total += scrape_computrabajo(vistos)
total += scrape_indeed(vistos)
total += scrape_linkedin(vistos)
total += scrape_codelco(vistos)
total += scrape_bhp(vistos)
total += scrape_collahuasi(vistos)
total += scrape_angloamerican(vistos)
total += scrape_antofagasta_minerals(vistos)
total += scrape_bne(vistos)

guardar_vistos(vistos)

print(f"\n{'='*50}")
print(f"  TOTAL NUEVOS AVISOS: {total}")
print(f"{'='*50}")

if total == 0:
    enviar("😴 Sin avisos nuevos en esta ejecución.")
else:
    enviar(f"✅ <b>Búsqueda completada</b>\n📊 {total} aviso(s) nuevo(s) encontrado(s).")
