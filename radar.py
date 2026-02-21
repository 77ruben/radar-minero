"""
╔══════════════════════════════════════════════════════╗
║       RADAR MINERO V8 ULTRA MAX - Rubén Morales      ║
║                                                      ║
║  FUENTES CUBIERTAS (62 total):                       ║
║  ► 7  Portales especializados minería                ║
║  ► 8  Portales generales de empleo                   ║
║  ► 15 Mineras directas                               ║
║  ► 7  Empresas campamento / alimentación             ║
║  ► 10 Ingeniería / EPC / construcción                ║
║  ► 8  Equipos OEM / proveedores                      ║
║  ► 7  Inspección / calidad / RRHH / otros            ║
╚══════════════════════════════════════════════════════╝
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re
from datetime import datetime

print("=" * 57)
print("      RADAR MINERO V8 ULTRA MAX")
print(f"      {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 57)

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
TOKEN     = os.environ["TOKEN"]
CHAT_ID   = os.environ["CHAT_ID"]
SEEN_FILE = "seen_jobs.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─────────────────────────────────────────────────────────
# PALABRAS CLAVE DEL PERFIL
# ─────────────────────────────────────────────────────────
PERFIL = [
    # Ingeniería
    "ingeniero", "ingeniería", "ingenieria", "engineering",
    # Mantenimiento
    "mantencion", "mantención", "mantenimiento", "maintenance",
    "jefe de mantenimiento", "jefe mantención", "jefe mantencion",
    "especialista en mantenimiento",
    # Contratos
    "administrador de contrato", "administrador contrato",
    "administradora de contrato", "contract manager",
    "contract administrator", "contracts",
    "coordinador de contratos", "coordinadora de contratos",
    # Planificación
    "planificacion", "planificación", "planner", "planificador",
    "planificadora",
    # Confiabilidad
    "confiabilidad", "reliability", "rcm", "ram", "fmea",
    "mantenimiento predictivo", "mantenimiento preventivo",
    # Logística
    "logistica", "logística", "supply chain", "abastecimiento",
    "supervisor de bodega",
    # Supervisión / Jefatura
    "supervisor", "supervisora", "jefe de operaciones",
    "jefe de proyecto", "jefe de planta", "jefe de turno",
    "jefe de área",
    # Proyectos / Gestión
    "project manager", "dirección de proyectos",
    "coordinador de proyectos", "gestión de proyectos",
    "gerente de proyectos", "project engineer",
    # Infraestructura / Campamentos
    "facility", "facilities", "infraestructura",
    "campamento", "camp manager", "camp boss",
    "administrador campamento", "administrador de campamento",
    # Operaciones
    "operaciones", "operations manager",
    # Industrial / OOCC
    "industrial", "oocc", "obras civiles", "obras menores",
    # ISO / Calidad / Seguridad
    "auditor", "iso 9001", "iso 14001", "iso 45001",
    "calidad", "hse",
]

TURNOS_KW = [
    "14x14", "14 x 14",
    "10x10", "10 x 10",
    "7x7",   "7 x 7",
    "4x3",   "4 x 3",
    "5x2",   "5 x 2",
    "turno rotativo", "régimen de turno",
    "turno minero", "faena",
]

EXCLUIR = [
    "guardia de seguridad", "guardia", "vigilante",
    "chofer", "conductor",
    "vendedor", "vendedora", "ejecutivo de ventas",
    "cajero", "cajera",
    "digitador", "digitadora",
    "secretaria", "recepcionista",
    "cocinero", "cocinera", "garzón", "garzon",
    "manipuladora de alimentos",
    "médico", "medico", "enfermero", "enfermera",
    "contador", "contadora", "psicólogo", "psicóloga",
    "practicante", "pasantía", "pasantia", "internship",
    "operario de producción", "operaria de producción",
    "junior sin experiencia", "aseador", "aseo",
]

UBICACIONES_KW = [
    "antofagasta", "calama", "iquique", "atacama", "copiapó", "copiapo",
    "chuquicamata", "tocopilla", "mejillones", "sierra gorda", "taltal",
    "diego de almagro", "baquedano", "norte grande", "norte chico",
    "norte de chile", "región de antofagasta", "región de tarapacá",
    "ii región", "región de atacama", "iii región", "i región",
    "región de coquimbo", "faena minera", "minera", "proyecto minero",
    "pampa", "quebrada blanca", "centinela", "escondida", "collahuasi",
    "pelambres", "chuqui",
]

# ─────────────────────────────────────────────────────────
# DEDUPLICACIÓN
# ─────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────
# FILTROS
# ─────────────────────────────────────────────────────────
def cumple_perfil(texto):
    t = texto.lower()
    if any(x in t for x in EXCLUIR):
        return False
    return any(p in t for p in PERFIL)

def detectar_turno(texto):
    t = texto.lower()
    for kw in TURNOS_KW:
        if kw.lower() in t:
            return kw.upper()
    return None

def detectar_ubicacion(texto):
    t = texto.lower()
    for u in UBICACIONES_KW:
        if u in t:
            return u.title()
    return None

# ─────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────
def enviar(msg):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id":  CHAT_ID,
        "text":     msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        requests.post(url_api, data=data, timeout=10).raise_for_status()
    except Exception as e:
        print(f"  ⚠️  Telegram: {e}")
    time.sleep(1.2)

def formato_aviso(fuente, titulo, empresa, ubicacion, turno, link):
    lineas = [
        "🔔 <b>NUEVO EMPLEO</b>",
        f"📋 <b>{titulo[:130]}</b>",
        f"🏢 {fuente}",
    ]
    if empresa:   lineas.append(f"🏭 {empresa[:90]}")
    if ubicacion: lineas.append(f"📍 {ubicacion}")
    if turno:     lineas.append(f"⏰ {turno}")
    if link:      lineas.append(f"🔗 {link[:300]}")
    return "\n".join(lineas)

# ─────────────────────────────────────────────────────────
# SCRAPERS GENÉRICOS
# ─────────────────────────────────────────────────────────
def scrape_simple(nombre, url, base_url, empresa_nombre, ubicacion_default, vistos):
    """Escanea todos los <a> de una URL corporativa."""
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            titulo = a.text.strip()
            link   = a["href"]
            if not link.startswith("http"):
                link = base_url.rstrip("/") + "/" + link.lstrip("/")
            if not cumple_perfil(titulo) or len(titulo) < 8:
                continue
            hid = hash_aviso(titulo, link)
            if hid in vistos:
                continue
            turno    = detectar_turno(titulo)
            ubicacion = detectar_ubicacion(titulo) or ubicacion_default
            msg = formato_aviso(nombre, titulo, empresa_nombre, ubicacion, turno, link)
            enviar(msg)
            vistos.add(hid)
            encontrados += 1
    except Exception as e:
        print(f"  ⚠️  {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados


def scrape_portal(nombre, urls, base_url, vistos):
    """Escanea portales con tarjetas/cards de avisos."""
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = (
                soup.find_all(["article", "li"],
                    class_=re.compile(r"job|aviso|card|oferta|listing|empleo|position", re.I))
                or soup.find_all("div",
                    class_=re.compile(r"job|aviso|card|oferta|listing|empleo|position", re.I))
                or soup.find_all("a", href=True)
            )
            for card in cards:
                t_tag  = card.find(["h2","h3","h4","a"]) or card
                titulo = t_tag.text.strip()
                l_tag  = (card.find("a", href=True) if card.name != "a" else card)
                link   = l_tag["href"] if l_tag else url
                if link and not link.startswith("http"):
                    link = base_url.rstrip("/") + "/" + link.lstrip("/")
                e_tag    = card.find(class_=re.compile(r"empresa|company|organiz", re.I))
                empresa  = e_tag.text.strip() if e_tag else None
                u_tag    = card.find(class_=re.compile(r"ubicacion|location|ciudad", re.I))
                txt      = card.get_text() if hasattr(card, "get_text") else titulo
                ubicacion = u_tag.text.strip() if u_tag else detectar_ubicacion(txt)
                if not cumple_perfil(titulo) or len(titulo) < 8:
                    continue
                hid = hash_aviso(titulo, link or url)
                if hid in vistos:
                    continue
                turno = detectar_turno(txt)
                msg = formato_aviso(nombre, titulo, empresa, ubicacion, turno, link or url)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  {nombre} — {url}: {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

# ══════════════════════════════════════════════════════════
#  BLOQUE 1 — PORTALES ESPECIALIZADOS MINERÍA (7)
# ══════════════════════════════════════════════════════════

def scrape_trabajoenmineria(vistos):
    return scrape_portal("TrabajoenMineria.cl",
        ["https://www.trabajoenmineria.cl/ofertas",
         "https://www.trabajoenmineria.cl/ofertas?area=mantenimiento",
         "https://www.trabajoenmineria.cl/ofertas?area=ingenieria"],
        "https://www.trabajoenmineria.cl", vistos)

def scrape_mineria_cl(vistos):
    return scrape_portal("Mineria.cl Empleos",
        ["https://www.mineria.cl/empleos/"],
        "https://www.mineria.cl", vistos)

def scrape_expertominero(vistos):
    return scrape_portal("ExpertoMinero.cl",
        ["https://www.expertominero.cl/empleos/"],
        "https://www.expertominero.cl", vistos)

def scrape_minerosonline(vistos):
    return scrape_portal("MinerosOnline",
        ["https://www.minerosonline.com/empleos/"],
        "https://www.minerosonline.com", vistos)

def scrape_reclutamineria(vistos):
    return scrape_portal("ReclutaMineria.cl",
        ["https://www.reclutamineria.cl/empleos/"],
        "https://www.reclutamineria.cl", vistos)

def scrape_mining_people(vistos):
    return scrape_simple("Mining People International",
        "https://www.miningpeople.com.au/jobs?location=Chile",
        "https://www.miningpeople.com.au",
        "Mining People Intl.", "Norte Chile / Minería", vistos)

def scrape_bolsa_mineria(vistos):
    return scrape_portal("EmpleosMineria.cl",
        ["https://www.empleosmineria.cl/",
         "https://www.empleosmineria.cl/?cat=mantenimiento"],
        "https://www.empleosmineria.cl", vistos)

# ══════════════════════════════════════════════════════════
#  BLOQUE 2 — PORTALES GENERALES (8)
# ══════════════════════════════════════════════════════════

def scrape_trabajando(vistos):
    return scrape_portal("Trabajando.cl",
        ["https://www.trabajando.cl/trabajos-mineria",
         "https://www.trabajando.cl/trabajos-mantenimiento-industrial",
         "https://www.trabajando.cl/trabajos-ingeniero-industrial"],
        "https://www.trabajando.cl", vistos)

def scrape_laborum(vistos):
    return scrape_portal("Laborum.cl",
        ["https://www.laborum.cl/empleos/mineria",
         "https://www.laborum.cl/empleos/mantenimiento-industrial",
         "https://www.laborum.cl/empleos/administracion-contratos"],
        "https://www.laborum.cl", vistos)

def scrape_computrabajo(vistos):
    return scrape_portal("Computrabajo.cl",
        ["https://www.computrabajo.cl/trabajos-de-mineria",
         "https://www.computrabajo.cl/trabajos-de-mantenimiento-industrial",
         "https://www.computrabajo.cl/trabajos-de-administracion-de-contratos"],
        "https://www.computrabajo.cl", vistos)

def scrape_indeed(vistos):
    print("\n🔍 Indeed Chile...")
    encontrados = 0
    queries = [
        "administrador+contrato+mineria",
        "supervisor+mantencion+mineria+chile",
        "ingeniero+mantenimiento+mineria+chile",
        "planner+mineria+chile",
        "administrador+campamento+mineria",
    ]
    for q in queries:
        url = f"https://cl.indeed.com/jobs?q={q}&l=Chile&sort=date"
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div",
                    class_=re.compile(r"job_seen|SerpJobCard|tapItem", re.I)):
                t = card.find(["h2","h3","a"])
                titulo = t.text.strip() if t else ""
                l = card.find("a", href=True)
                link = (("https://cl.indeed.com" + l["href"])
                        if l and not l["href"].startswith("http") else
                        (l["href"] if l else url))
                e = card.find(class_=re.compile(r"company", re.I))
                empresa = e.text.strip() if e else None
                if not cumple_perfil(titulo) or len(titulo) < 8:
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                txt = card.get_text()
                msg = formato_aviso("Indeed", titulo, empresa,
                                    detectar_ubicacion(txt), detectar_turno(txt), link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  Indeed ({q}): {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

def scrape_linkedin(vistos):
    print("\n🔍 LinkedIn Jobs...")
    encontrados = 0
    queries = [
        ("administrador%20contrato%20mineria",        "Chile"),
        ("supervisor%20mantencion%20mineria",          "Antofagasta%2C%20Chile"),
        ("ingeniero%20mantenimiento%20mineria",        "Calama%2C%20Chile"),
        ("planner%20mineria%20chile",                  "Chile"),
        ("facility%20manager%20campamento%20mineria",  "Chile"),
    ]
    for q, loc in queries:
        url = (f"https://www.linkedin.com/jobs/search/"
               f"?keywords={q}&location={loc}&f_TPR=r86400&sortBy=DD")
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div",
                    class_=re.compile(r"base-card|job-search-card", re.I)):
                t = card.find(["h3","h4","a"])
                titulo = t.text.strip() if t else ""
                l = card.find("a", href=True)
                link = l["href"].split("?")[0] if l else url
                e = card.find(class_=re.compile(r"base-search-card__subtitle|company", re.I))
                empresa = e.text.strip() if e else None
                u = card.find(class_=re.compile(r"base-search-card__metadata|location", re.I))
                ubicacion = u.text.strip() if u else None
                if not cumple_perfil(titulo) or len(titulo) < 8:
                    continue
                hid = hash_aviso(titulo, link)
                if hid in vistos:
                    continue
                txt   = card.get_text()
                turno = detectar_turno(txt)
                msg   = formato_aviso("LinkedIn", titulo, empresa, ubicacion, turno, link)
                enviar(msg)
                vistos.add(hid)
                encontrados += 1
            time.sleep(3)
        except Exception as e:
            print(f"  ⚠️  LinkedIn ({q}): {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

def scrape_bne(vistos):
    return scrape_portal("BNE Chile (Gobierno)",
        ["https://www.bne.cl/empleos?q=administrador+contrato+mineria",
         "https://www.bne.cl/empleos?q=supervisor+mantencion+mineria",
         "https://www.bne.cl/empleos?q=planner+mineria"],
        "https://www.bne.cl", vistos)

def scrape_portalempleo(vistos):
    return scrape_portal("PortalEmpleo.cl",
        ["https://www.portalempleo.cl/trabajo/mineria/",
         "https://www.portalempleo.cl/trabajo/mantenimiento-industrial/"],
        "https://www.portalempleo.cl", vistos)

# ══════════════════════════════════════════════════════════
#  BLOQUE 3 — MINERAS DIRECTAS (15)
# ══════════════════════════════════════════════════════════

def scrape_codelco(vistos):
    return scrape_simple("Codelco",
        "https://www.codelco.com/trabaja-con-nosotros/prontus_codelco/2012-01-16/120018.html",
        "https://www.codelco.com", "Codelco", "Norte Chile / Varias faenas", vistos)

def scrape_bhp(vistos):
    return scrape_simple("BHP Chile",
        "https://careers.bhp.com/search-jobs/Chile",
        "https://careers.bhp.com", "BHP", "Antofagasta / Escondida / Spence", vistos)

def scrape_collahuasi(vistos):
    return scrape_simple("Collahuasi",
        "https://www.collahuasi.cl/trabaja-con-nosotros/",
        "https://www.collahuasi.cl", "Collahuasi", "Iquique / Tarapacá", vistos)

def scrape_angloamerican(vistos):
    return scrape_simple("Anglo American Chile",
        "https://www.angloamerican.com/careers/job-search?country=Chile",
        "https://www.angloamerican.com", "Anglo American",
        "Los Bronces / El Soldado", vistos)

def scrape_antofagasta_minerals(vistos):
    return scrape_simple("Antofagasta Minerals",
        "https://www.aminerals.cl/personas/trabaja-con-nosotros/",
        "https://www.aminerals.cl",
        "Ant. Minerals (Pelambres/Centinela/Zaldivar)",
        "Antofagasta / Pelambres", vistos)

def scrape_teck(vistos):
    return scrape_simple("Teck Chile (QB2)",
        "https://jobs.teck.com/search/?q=chile",
        "https://jobs.teck.com", "Teck / QB2", "Iquique / Tarapacá", vistos)

def scrape_kinross(vistos):
    return scrape_simple("Kinross Chile (Maricunga)",
        "https://careers.kinross.com/search/?q=chile",
        "https://careers.kinross.com", "Kinross", "Atacama / Maricunga", vistos)

def scrape_lundin(vistos):
    return scrape_simple("Lundin Mining (Candelaria/Caserones)",
        "https://www.lundinmining.com/about/careers/",
        "https://www.lundinmining.com", "Lundin Mining",
        "Atacama / Candelaria", vistos)

def scrape_sqm(vistos):
    return scrape_simple("SQM Chile",
        "https://www.sqm.com/es/nuestra-gente/trabaja-con-nosotros/",
        "https://www.sqm.com", "SQM", "Antofagasta / Litio / Atacama", vistos)

def scrape_cap(vistos):
    return scrape_simple("CAP Minería (CDA)",
        "https://www.capmineria.cl/personas/trabaja-con-nosotros/",
        "https://www.capmineria.cl", "CAP Minería", "Atacama / CDA", vistos)

def scrape_enami(vistos):
    return scrape_simple("ENAMI",
        "https://www.enami.cl/trabaja-con-nosotros",
        "https://www.enami.cl", "ENAMI", "Norte / Centro Chile", vistos)

def scrape_sierragorda(vistos):
    return scrape_simple("Sierra Gorda SCM",
        "https://sierragorda.cl/trabaja-con-nosotros/",
        "https://sierragorda.cl", "Sierra Gorda SCM", "Antofagasta", vistos)

def scrape_agnicoeagle(vistos):
    return scrape_simple("Agnico Eagle Chile",
        "https://www.agnicoeagle.com/English/careers/job-opportunities/default.aspx",
        "https://www.agnicoeagle.com", "Agnico Eagle", "Norte Chile", vistos)

def scrape_goldfields(vistos):
    return scrape_simple("Gold Fields Chile (Salares Norte)",
        "https://careers.goldfields.com/search/?q=chile",
        "https://careers.goldfields.com", "Gold Fields",
        "Atacama / Salares Norte", vistos)

def scrape_lithium_americas(vistos):
    return scrape_simple("Lithium Americas (Rincón)",
        "https://lithiumamericas.com/careers/",
        "https://lithiumamericas.com", "Lithium Americas",
        "Antofagasta / Rincón", vistos)

# ══════════════════════════════════════════════════════════
#  BLOQUE 4 — CAMPAMENTOS / ALIMENTACIÓN / FACILITIES (7)
# ══════════════════════════════════════════════════════════

def scrape_compass(vistos):
    return scrape_simple("Compass Group Chile",
        "https://www.compass-chile.cl/trabaja-con-nosotros/",
        "https://www.compass-chile.cl", "Compass Group", "Norte Chile (faenas)", vistos)

def scrape_sodexo(vistos):
    return scrape_simple("Sodexo Chile",
        "https://jobs.sodexo.com/search/?q=chile&locationsearch=chile",
        "https://jobs.sodexo.com", "Sodexo", "Norte Chile (faenas)", vistos)

def scrape_aramark(vistos):
    return scrape_simple("Aramark Chile",
        "https://careers.aramark.com/search/?q=chile",
        "https://careers.aramark.com", "Aramark", "Norte Chile (campamentos)", vistos)

def scrape_eurest(vistos):
    return scrape_simple("Eurest Chile",
        "https://www.eurest.cl/oportunidades-laborales/",
        "https://www.eurest.cl", "Eurest", "Norte Chile", vistos)

def scrape_applus(vistos):
    return scrape_simple("Applus Chile",
        "https://www.applus.com/es/careers/job-search?country=Chile",
        "https://www.applus.com", "Applus", "Norte Chile", vistos)

def scrape_igt(vistos):
    return scrape_simple("IGT Chile (campamentos)",
        "https://www.igtchile.cl/trabaja-con-nosotros/",
        "https://www.igtchile.cl", "IGT Chile", "Norte Chile / Faenas", vistos)

def scrape_cgg(vistos):
    return scrape_simple("CGG Solutions",
        "https://www.cggsolutions.cl/trabaja-con-nosotros/",
        "https://www.cggsolutions.cl", "CGG Solutions", "Norte Chile", vistos)

# ══════════════════════════════════════════════════════════
#  BLOQUE 5 — INGENIERÍA / EPC / CONSTRUCCIÓN (10)
# ══════════════════════════════════════════════════════════

def scrape_fluor(vistos):
    return scrape_simple("Fluor Chile",
        "https://careers.fluor.com/job-search-results/?category=Engineering&location=Chile",
        "https://careers.fluor.com", "Fluor",
        "Norte Chile / Proyectos Mineros", vistos)

def scrape_worley(vistos):
    return scrape_simple("Worley Chile",
        "https://careers.worley.com/jobs?location=Chile",
        "https://careers.worley.com", "Worley", "Antofagasta / Santiago", vistos)

def scrape_wood(vistos):
    return scrape_simple("Wood Group Chile",
        "https://careers.woodplc.com/jobs?location=Chile",
        "https://careers.woodplc.com", "Wood Group", "Norte Chile", vistos)

def scrape_techint(vistos):
    return scrape_simple("Techint Chile",
        "https://jobs.techint.com/jobs?country=CL",
        "https://jobs.techint.com", "Techint", "Norte Chile / Proyectos", vistos)

def scrape_mas_errazuriz(vistos):
    return scrape_simple("MAS Errázuriz",
        "https://www.maserrazuriz.cl/trabaja-con-nosotros/",
        "https://www.maserrazuriz.cl", "MAS Errázuriz", "Norte Chile / Minería", vistos)

def scrape_sigdo_koppers(vistos):
    return scrape_simple("Sigdo Koppers (SK)",
        "https://www.sigdokoppers.cl/personas/trabaja-con-nosotros/",
        "https://www.sigdokoppers.cl", "Sigdo Koppers", "Norte Chile", vistos)

def scrape_salfa(vistos):
    return scrape_simple("Salfa / Salfacorp",
        "https://www.salfacorp.com/trabaja-con-nosotros/",
        "https://www.salfacorp.com", "Salfa / Salfacorp",
        "Norte Chile / Faenas", vistos)

def scrape_belfi(vistos):
    return scrape_simple("Belfi Ingeniería",
        "https://www.belfi.cl/trabaja-con-nosotros/",
        "https://www.belfi.cl", "Belfi", "Chile / Minería", vistos)

def scrape_icafal(vistos):
    return scrape_simple("Icafal Ingeniería",
        "https://www.icafal.cl/trabaja-con-nosotros/",
        "https://www.icafal.cl", "Icafal Ingeniería", "Chile", vistos)

def scrape_vesco(vistos):
    return scrape_simple("Vesco Consultores",
        "https://www.vesco.cl/empleo/",
        "https://www.vesco.cl", "Vesco Consultores", "Chile / Minería", vistos)

# ══════════════════════════════════════════════════════════
#  BLOQUE 6 — EQUIPOS OEM / PROVEEDORES INDUSTRIALES (8)
# ══════════════════════════════════════════════════════════

def scrape_komatsu(vistos):
    return scrape_simple("Komatsu Chile",
        "https://komatsu.jobs/search/?q=chile",
        "https://komatsu.jobs", "Komatsu", "Norte Chile / Faenas", vistos)

def scrape_finning(vistos):
    return scrape_simple("Finning Chile (Caterpillar)",
        "https://jobs.finning.com/search/?q=chile&locationsearch=chile",
        "https://jobs.finning.com", "Finning / Caterpillar",
        "Antofagasta / Calama", vistos)

def scrape_sandvik(vistos):
    return scrape_simple("Sandvik Chile",
        "https://www.sandvik.com/en/careers/job-openings/?country=Chile",
        "https://www.sandvik.com", "Sandvik", "Norte Chile / Minería", vistos)

def scrape_epiroc(vistos):
    return scrape_simple("Epiroc Chile",
        "https://careers.epiroc.com/jobs?location=Chile",
        "https://careers.epiroc.com", "Epiroc", "Norte Chile / Minería", vistos)

def scrape_metso(vistos):
    return scrape_simple("Metso Outotec Chile",
        "https://www.metso.com/careers/open-positions/?country=Chile",
        "https://www.metso.com", "Metso Outotec", "Norte Chile", vistos)

def scrape_weir(vistos):
    return scrape_simple("Weir Minerals Chile",
        "https://careers.weir/search/?q=chile",
        "https://careers.weir", "Weir Minerals", "Norte Chile", vistos)

def scrape_flsmidth(vistos):
    return scrape_simple("FLSmidth Chile",
        "https://www.flsmidth.com/en-gb/company/careers/vacancies?country=Chile",
        "https://www.flsmidth.com", "FLSmidth", "Norte Chile", vistos)

def scrape_thyssenkrupp(vistos):
    return scrape_simple("Thyssenkrupp Industrial Solutions",
        "https://www.thyssenkrupp.com/en/careers/job-search?q=chile",
        "https://www.thyssenkrupp.com", "Thyssenkrupp", "Norte Chile / Minería", vistos)

# ══════════════════════════════════════════════════════════
#  BLOQUE 7 — INSPECCIÓN / RRHH / CALIDAD / OTROS (7)
# ══════════════════════════════════════════════════════════

def scrape_bureau_veritas(vistos):
    return scrape_simple("Bureau Veritas Chile",
        "https://candidatos.bureauveritas.cl/jobsearch",
        "https://candidatos.bureauveritas.cl", "Bureau Veritas",
        "Chile / Minería", vistos)

def scrape_sgs(vistos):
    return scrape_simple("SGS Chile",
        "https://www.sgs.com/en/careers/job-search?country=Chile",
        "https://www.sgs.com", "SGS", "Norte Chile / Minería", vistos)

def scrape_confipetrol(vistos):
    return scrape_simple("Confipetrol",
        "https://confipetrol.cl/trabaja-con-nosotros/",
        "https://confipetrol.cl", "Confipetrol", "Norte Chile / Minería", vistos)

def scrape_adecco(vistos):
    return scrape_portal("Adecco Chile",
        ["https://www.adecco.cl/empleos/?sector=mineria",
         "https://www.adecco.cl/empleos/?sector=ingenieria-industrial"],
        "https://www.adecco.cl", vistos)

def scrape_hays(vistos):
    return scrape_simple("Hays Chile (mining)",
        "https://www.hays.cl/empleo/buscar-empleo?q=mining&location=Chile",
        "https://www.hays.cl", "Hays Recruitment", "Norte Chile", vistos)

def scrape_manpower(vistos):
    return scrape_portal("ManpowerGroup Chile",
        ["https://www.manpower.cl/empleos?q=mineria+mantenimiento",
         "https://www.manpower.cl/empleos?q=administrador+contrato"],
        "https://www.manpower.cl", vistos)

def scrape_randstad(vistos):
    return scrape_portal("Randstad Chile",
        ["https://www.randstad.cl/jobs/?q=mineria",
         "https://www.randstad.cl/jobs/?q=mantenimiento+industrial"],
        "https://www.randstad.cl", vistos)

# ══════════════════════════════════════════════════════════
#  EJECUCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════

FUENTES = [
    # ── Portales especializados minería ──────────────────
    scrape_trabajoenmineria, scrape_mineria_cl,
    scrape_expertominero, scrape_minerosonline,
    scrape_reclutamineria, scrape_mining_people,
    scrape_bolsa_mineria,

    # ── Portales generales ───────────────────────────────
    scrape_trabajando, scrape_laborum, scrape_computrabajo,
    scrape_indeed, scrape_linkedin, scrape_bne, scrape_portalempleo,

    # ── Mineras directas ─────────────────────────────────
    scrape_codelco, scrape_bhp, scrape_collahuasi,
    scrape_angloamerican, scrape_antofagasta_minerals,
    scrape_teck, scrape_kinross, scrape_lundin,
    scrape_sqm, scrape_cap, scrape_enami, scrape_sierragorda,
    scrape_agnicoeagle, scrape_goldfields, scrape_lithium_americas,

    # ── Campamentos / Alimentación / Facilities ──────────
    scrape_compass, scrape_sodexo, scrape_aramark,
    scrape_eurest, scrape_applus, scrape_igt, scrape_cgg,

    # ── Ingeniería / EPC / Construcción ─────────────────
    scrape_fluor, scrape_worley, scrape_wood, scrape_techint,
    scrape_mas_errazuriz, scrape_sigdo_koppers, scrape_salfa,
    scrape_belfi, scrape_icafal, scrape_vesco,

    # ── Equipos OEM / Proveedores ────────────────────────
    scrape_komatsu, scrape_finning, scrape_sandvik,
    scrape_epiroc, scrape_metso, scrape_weir,
    scrape_flsmidth, scrape_thyssenkrupp,

    # ── Inspección / RRHH / Otros ────────────────────────
    scrape_bureau_veritas, scrape_sgs, scrape_confipetrol,
    scrape_adecco, scrape_hays, scrape_manpower, scrape_randstad,
]

N = len(FUENTES)

vistos = cargar_vistos()
print(f"\n📂 Historial: {len(vistos)} avisos ya procesados")

enviar(
    f"🤖 <b>RADAR MINERO V8 ULTRA MAX</b>\n"
    f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    f"🔍 Escaneando <b>{N} fuentes</b>\n"
    f"📊 Historial: {len(vistos)} avisos ya procesados"
)

total = 0
for i, fn in enumerate(FUENTES, 1):
    print(f"\n[{i}/{N}]", end="")
    total += fn(vistos)

guardar_vistos(vistos)

print(f"\n{'═'*57}")
print(f"  NUEVOS: {total}  |  FUENTES: {N}")
print(f"{'═'*57}")

enviar(
    f"{'✅' if total > 0 else '😴'} <b>Búsqueda completada</b>\n"
    f"📊 <b>{total}</b> aviso(s) nuevo(s)\n"
    f"🔍 {N} fuentes escaneadas\n"
    f"🕐 {'Próxima en 6 horas' if total == 0 else 'Revisa los avisos arriba ☝️'}"
)
