"""
╔══════════════════════════════════════════════════════╗
║    RADAR MINERO V8 PLUS 2 - Rubén Morales            ║
║                                                      ║
║  NOVEDADES:                                          ║
║  ► URLs corregidas en mineras y servicios            ║
║  ► Botones ✅ Visto / ❌ Eliminar en Telegram        ║
║  ► Sistema de puntuación ⭐                          ║
║  ► Alertas urgentes 🚨                               ║
║  ► Turnos destacados ⏰                              ║
║  ► 62 fuentes cubiertas                              ║
╚══════════════════════════════════════════════════════╝
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re
from datetime import datetime

print("=" * 55)
print("      RADAR MINERO V8 PLUS 2")
print(f"      {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 55)

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

# ─────────────────────────────────────────────────────
# PUNTUACIÓN
# ─────────────────────────────────────────────────────
PERFIL_ALTO = [
    "administrador de contrato", "administrador contrato",
    "administradora de contrato", "contract manager",
    "contract administrator",
    "jefe de mantenimiento", "jefe mantención", "jefe mantencion",
    "planner", "planificador", "planificadora",
    "supervisor de mantenimiento", "supervisor mantención",
    "administrador de campamento", "camp manager",
    "facility manager", "facilities manager",
]
PERFIL_MEDIO = [
    "ingeniero de mantenimiento", "ingeniero mantención",
    "ingeniero industrial", "ingeniería industrial",
    "confiabilidad", "reliability",
    "coordinador de contratos", "coordinador de proyectos",
    "project manager", "project engineer",
    "jefe de operaciones", "jefe de proyecto", "jefe de planta",
    "supervisor de operaciones", "supervisor de terreno",
    "logistica", "logística", "supply chain",
    "planificacion", "planificación",
    "infraestructura", "oocc", "obras civiles",
]
PERFIL_BAJO = [
    "ingeniero", "ingeniería", "ingenieria", "engineering",
    "mantencion", "mantención", "mantenimiento", "maintenance",
    "supervisor", "supervisora", "administrador", "administradora",
    "operaciones", "industrial", "campamento", "facility", "facilities",
    "auditor", "calidad", "hse",
]
TURNOS_KW = [
    "14x14", "14 x 14", "10x10", "10 x 10",
    "7x7", "7 x 7", "4x3", "4 x 3", "5x2",
    "turno rotativo", "régimen de turno", "turno minero", "faena",
]
EXCLUIR = [
    "guardia", "vigilante", "chofer", "conductor",
    "vendedor", "vendedora", "cajero", "cajera",
    "digitador", "secretaria", "recepcionista",
    "cocinero", "cocinera", "garzón", "garzon",
    "manipuladora de alimentos",
    "médico", "medico", "enfermero", "enfermera",
    "contador", "contadora", "psicólogo", "psicóloga",
    "practicante", "pasantía", "pasantia", "internship",
    "operario de producción", "junior sin experiencia",
    "aseador", "aseo",
]
UBICACIONES_KW = [
    "antofagasta", "calama", "iquique", "atacama", "copiapó", "copiapo",
    "chuquicamata", "tocopilla", "mejillones", "sierra gorda", "taltal",
    "diego de almagro", "norte grande", "norte chico", "norte de chile",
    "región de antofagasta", "región de tarapacá", "ii región",
    "región de atacama", "iii región", "i región", "región de coquimbo",
    "faena minera", "proyecto minero", "pampa",
    "quebrada blanca", "centinela", "escondida", "collahuasi", "pelambres",
]
EMPRESAS_PRIORITARIAS = [
    "codelco", "bhp", "escondida", "spence", "collahuasi",
    "anglo american", "antofagasta minerals", "pelambres",
    "centinela", "zaldivar", "teck", "quebrada blanca", "qb2",
    "sqm", "kinross", "lundin", "candelaria", "gold fields",
    "sierra gorda", "cap minería", "compass", "sodexo", "aramark",
    "fluor", "worley", "techint", "wood group",
    "sigdo koppers", "salfacorp", "mas errazuriz",
    "komatsu", "finning", "sandvik", "epiroc",
]

# ─────────────────────────────────────────────────────
# DEDUPLICACIÓN
# ─────────────────────────────────────────────────────
def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def guardar_vistos(vistos):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(vistos), f, indent=2)

def hash_aviso(titulo, link):
    return hashlib.md5(f"{titulo.lower().strip()}{link.strip()}".encode()).hexdigest()

# ─────────────────────────────────────────────────────
# FILTROS
# ─────────────────────────────────────────────────────
def calcular_match(titulo):
    t = titulo.lower()
    if any(p in t for p in PERFIL_ALTO):  return "⭐⭐⭐ MATCH PERFECTO"
    if any(p in t for p in PERFIL_MEDIO): return "⭐⭐ Buen match"
    if any(p in t for p in PERFIL_BAJO):  return "⭐ Match parcial"
    return ""

def cumple_perfil(texto):
    t = texto.lower()
    if any(x in t for x in EXCLUIR): return False
    return any(p in t for p in PERFIL_ALTO + PERFIL_MEDIO + PERFIL_BAJO)

def es_prioritaria(texto):
    return any(e in texto.lower() for e in EMPRESAS_PRIORITARIAS)

def detectar_turno(texto):
    t = texto.lower()
    for kw in TURNOS_KW:
        if kw.lower() in t: return kw.upper()
    return None

def detectar_ubicacion(texto):
    t = texto.lower()
    for u in UBICACIONES_KW:
        if u in t: return u.title()
    return None

# ─────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────
def enviar(msg, reply_markup=None):
    data = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data=data, timeout=10
        ).raise_for_status()
    except Exception as e:
        print(f"  ⚠️  Telegram: {e}")
    time.sleep(1.2)

def botones(hid):
    return {
        "inline_keyboard": [[
            {"text": "✅ Visto",    "callback_data": f"visto:{hid}"},
            {"text": "❌ Eliminar", "callback_data": f"eliminar:{hid}"},
        ]]
    }

def formato_aviso(fuente, titulo, empresa, ubicacion, turno, link, match_str, urgente):
    if urgente:
        header = "🚨 <b>ALERTA URGENTE — EMPRESA PRIORITARIA</b>"
    elif "⭐⭐⭐" in match_str:
        header = "🔥 <b>NUEVO EMPLEO — MATCH PERFECTO</b>"
    elif "⭐⭐" in match_str:
        header = "🔔 <b>NUEVO EMPLEO — BUEN MATCH</b>"
    else:
        header = "🔔 <b>NUEVO EMPLEO</b>"
    lineas = [header, f"📋 <b>{titulo[:130]}</b>", f"🏢 {fuente}"]
    if match_str:   lineas.append(match_str)
    if empresa:     lineas.append(f"🏭 {empresa[:90]}")
    if ubicacion:   lineas.append(f"📍 {ubicacion}")
    lineas.append(f"⏰ <b>TURNO: {turno}</b> ✔️" if turno else "⏰ Turno: no especificado")
    if link:        lineas.append(f"🔗 {link[:300]}")
    return "\n".join(lineas)

# ─────────────────────────────────────────────────────
# FUNCIÓN CENTRAL
# ─────────────────────────────────────────────────────
def procesar_aviso(fuente, titulo, empresa, ubicacion_extra, link, vistos):
    if not cumple_perfil(titulo) or len(titulo) < 8:
        return 0
    hid = hash_aviso(titulo, link or "")
    if hid in vistos:
        return 0
    turno     = detectar_turno(titulo)
    ubicacion = detectar_ubicacion(titulo) or ubicacion_extra
    match_str = calcular_match(titulo)
    urgente   = es_prioritaria(f"{titulo} {empresa or ''} {fuente}")
    msg = formato_aviso(fuente, titulo, empresa, ubicacion,
                        turno, link, match_str, urgente)
    enviar(msg, reply_markup=botones(hid))
    vistos.add(hid)
    return 1

# ─────────────────────────────────────────────────────
# SCRAPERS GENÉRICOS
# ─────────────────────────────────────────────────────
def scrape_simple(nombre, url, base_url, empresa_nombre, ubicacion_default, vistos):
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
            encontrados += procesar_aviso(
                nombre, titulo, empresa_nombre, ubicacion_default, link, vistos)
    except Exception as e:
        print(f"  ⚠️  {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

def scrape_portal(nombre, urls, base_url, vistos):
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            cards = (
                soup.find_all(["article","li"],
                    class_=re.compile(r"job|aviso|card|oferta|listing|empleo|position", re.I))
                or soup.find_all("div",
                    class_=re.compile(r"job|aviso|card|oferta|listing|empleo|position", re.I))
                or soup.find_all("a", href=True)
            )
            for card in cards:
                t_tag   = card.find(["h2","h3","h4","a"]) or card
                titulo  = t_tag.text.strip()
                l_tag   = (card.find("a", href=True) if card.name != "a" else card)
                link    = l_tag["href"] if l_tag else url
                if link and not link.startswith("http"):
                    link = base_url.rstrip("/") + "/" + link.lstrip("/")
                e_tag   = card.find(class_=re.compile(r"empresa|company|organiz", re.I))
                empresa = e_tag.text.strip() if e_tag else None
                txt     = card.get_text() if hasattr(card, "get_text") else titulo
                encontrados += procesar_aviso(
                    nombre, titulo, empresa, detectar_ubicacion(txt), link or url, vistos)
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

# ══════════════════════════════════════════════════════
#  BLOQUE 1 — PORTALES ESPECIALIZADOS MINERÍA
#  URLs apuntan directamente a secciones de empleo
# ══════════════════════════════════════════════════════
def scrape_trabajoenmineria(v): return scrape_portal("TrabajoenMineria.cl",
    ["https://www.trabajoenmineria.cl/ofertas",
     "https://www.trabajoenmineria.cl/ofertas?area=mantenimiento",
     "https://www.trabajoenmineria.cl/ofertas?area=ingenieria"],
    "https://www.trabajoenmineria.cl", v)

def scrape_mineria_cl(v): return scrape_portal("Mineria.cl Empleos",
    ["https://www.mineria.cl/empleos/"], "https://www.mineria.cl", v)

def scrape_expertominero(v): return scrape_portal("ExpertoMinero.cl",
    ["https://www.expertominero.cl/empleos/"], "https://www.expertominero.cl", v)

def scrape_minerosonline(v): return scrape_portal("MinerosOnline",
    ["https://www.minerosonline.com/empleos/"], "https://www.minerosonline.com", v)

def scrape_reclutamineria(v): return scrape_portal("ReclutaMineria.cl",
    ["https://www.reclutamineria.cl/empleos/"], "https://www.reclutamineria.cl", v)

def scrape_mining_people(v): return scrape_simple("Mining People Intl.",
    "https://www.miningpeople.com.au/jobs?location=Chile",
    "https://www.miningpeople.com.au", "Mining People Intl.", "Norte Chile", v)

def scrape_bolsa_mineria(v): return scrape_portal("EmpleosMineria.cl",
    ["https://www.empleosmineria.cl/",
     "https://www.empleosmineria.cl/?cat=mantenimiento"],
    "https://www.empleosmineria.cl", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 2 — PORTALES GENERALES
# ══════════════════════════════════════════════════════
def scrape_trabajando(v): return scrape_portal("Trabajando.cl",
    ["https://www.trabajando.cl/trabajos-mineria",
     "https://www.trabajando.cl/trabajos-mantenimiento-industrial",
     "https://www.trabajando.cl/trabajos-ingeniero-industrial"],
    "https://www.trabajando.cl", v)

def scrape_laborum(v): return scrape_portal("Laborum.cl",
    ["https://www.laborum.cl/empleos/mineria",
     "https://www.laborum.cl/empleos/mantenimiento-industrial",
     "https://www.laborum.cl/empleos/administracion-contratos"],
    "https://www.laborum.cl", v)

def scrape_computrabajo(v): return scrape_portal("Computrabajo.cl",
    ["https://www.computrabajo.cl/trabajos-de-mineria",
     "https://www.computrabajo.cl/trabajos-de-mantenimiento-industrial",
     "https://www.computrabajo.cl/trabajos-de-administracion-de-contratos"],
    "https://www.computrabajo.cl", v)

def scrape_indeed(vistos):
    print("\n🔍 Indeed Chile...")
    n = 0
    for q in ["administrador+contrato+mineria","supervisor+mantencion+mineria+chile",
              "ingeniero+mantenimiento+mineria+chile","planner+mineria+chile",
              "administrador+campamento+mineria"]:
        url = f"https://cl.indeed.com/jobs?q={q}&l=Chile&sort=date"
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div", class_=re.compile(r"job_seen|SerpJobCard|tapItem", re.I)):
                t = card.find(["h2","h3","a"])
                titulo = t.text.strip() if t else ""
                l = card.find("a", href=True)
                link = (("https://cl.indeed.com"+l["href"])
                        if l and not l["href"].startswith("http") else (l["href"] if l else url))
                e = card.find(class_=re.compile(r"company", re.I))
                n += procesar_aviso("Indeed", titulo, e.text.strip() if e else None,
                    detectar_ubicacion(card.get_text()), link, vistos)
            time.sleep(2)
        except Exception as e: print(f"  ⚠️  Indeed: {e}")
    print(f"  ✅ {n} nuevos"); return n

def scrape_linkedin(vistos):
    print("\n🔍 LinkedIn Jobs...")
    n = 0
    for q, loc in [("administrador%20contrato%20mineria","Chile"),
                   ("supervisor%20mantencion%20mineria","Antofagasta%2C%20Chile"),
                   ("ingeniero%20mantenimiento%20mineria","Calama%2C%20Chile"),
                   ("planner%20mineria%20chile","Chile"),
                   ("facility%20manager%20campamento%20mineria","Chile")]:
        url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}&f_TPR=r86400&sortBy=DD"
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div", class_=re.compile(r"base-card|job-search-card", re.I)):
                t = card.find(["h3","h4","a"])
                titulo = t.text.strip() if t else ""
                l = card.find("a", href=True)
                link = l["href"].split("?")[0] if l else url
                e = card.find(class_=re.compile(r"base-search-card__subtitle|company", re.I))
                u = card.find(class_=re.compile(r"base-search-card__metadata|location", re.I))
                n += procesar_aviso("LinkedIn", titulo, e.text.strip() if e else None,
                    u.text.strip() if u else None, link, vistos)
            time.sleep(3)
        except Exception as e: print(f"  ⚠️  LinkedIn: {e}")
    print(f"  ✅ {n} nuevos"); return n

def scrape_bne(v): return scrape_portal("BNE Chile",
    ["https://www.bne.cl/empleos?q=administrador+contrato+mineria",
     "https://www.bne.cl/empleos?q=supervisor+mantencion+mineria"],
    "https://www.bne.cl", v)

def scrape_portalempleo(v): return scrape_portal("PortalEmpleo.cl",
    ["https://www.portalempleo.cl/trabajo/mineria/",
     "https://www.portalempleo.cl/trabajo/mantenimiento-industrial/"],
    "https://www.portalempleo.cl", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 3 — MINERAS DIRECTAS
#  URLs corregidas apuntando a portales de empleo reales
# ══════════════════════════════════════════════════════
def scrape_codelco(v): return scrape_portal("Codelco",
    ["https://www.trabajando.cl/empresa/codelco",
     "https://www.laborum.cl/empleos?empresa=codelco",
     "https://cl.indeed.com/jobs?q=codelco&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_bhp(v): return scrape_portal("BHP / Escondida",
    ["https://www.trabajando.cl/empresa/bhp",
     "https://cl.indeed.com/jobs?q=bhp+escondida&l=Chile&sort=date",
     "https://www.computrabajo.cl/trabajos-de-bhp"],
    "https://www.trabajando.cl", v)

def scrape_collahuasi(v): return scrape_portal("Collahuasi",
    ["https://www.trabajando.cl/empresa/collahuasi",
     "https://cl.indeed.com/jobs?q=collahuasi&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_angloamerican(v): return scrape_portal("Anglo American",
    ["https://www.trabajando.cl/empresa/anglo-american",
     "https://cl.indeed.com/jobs?q=anglo+american+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_aminerals(v): return scrape_portal("Antofagasta Minerals",
    ["https://cl.indeed.com/jobs?q=pelambres+centinela+minera&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/minera-los-pelambres",
     "https://www.trabajando.cl/empresa/minera-centinela"],
    "https://www.trabajando.cl", v)

def scrape_teck(v): return scrape_portal("Teck / QB2",
    ["https://cl.indeed.com/jobs?q=teck+quebrada+blanca&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/teck"],
    "https://www.trabajando.cl", v)

def scrape_kinross(v): return scrape_portal("Kinross Chile",
    ["https://cl.indeed.com/jobs?q=kinross+chile&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/kinross"],
    "https://www.trabajando.cl", v)

def scrape_lundin(v): return scrape_portal("Lundin Mining / Candelaria",
    ["https://cl.indeed.com/jobs?q=lundin+candelaria&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/minera-candelaria"],
    "https://www.trabajando.cl", v)

def scrape_sqm(v): return scrape_portal("SQM Chile",
    ["https://www.trabajando.cl/empresa/sqm",
     "https://cl.indeed.com/jobs?q=sqm+litio&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_cap(v): return scrape_portal("CAP Minería",
    ["https://www.trabajando.cl/empresa/cap-mineria",
     "https://cl.indeed.com/jobs?q=cap+mineria&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_enami(v): return scrape_portal("ENAMI",
    ["https://cl.indeed.com/jobs?q=enami&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/enami"],
    "https://www.trabajando.cl", v)

def scrape_sierragorda(v): return scrape_portal("Sierra Gorda SCM",
    ["https://cl.indeed.com/jobs?q=sierra+gorda+minera&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/sierra-gorda-scm"],
    "https://www.trabajando.cl", v)

def scrape_agnico(v): return scrape_portal("Agnico Eagle Chile",
    ["https://cl.indeed.com/jobs?q=agnico+eagle+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_goldfields(v): return scrape_portal("Gold Fields / Salares Norte",
    ["https://cl.indeed.com/jobs?q=gold+fields+salares+norte&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_lithium(v): return scrape_portal("Lithium Americas",
    ["https://cl.indeed.com/jobs?q=lithium+americas+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 4 — CAMPAMENTOS / ALIMENTACIÓN
#  URLs corregidas con portales de empleo verificados
# ══════════════════════════════════════════════════════
def scrape_compass(v): return scrape_portal("Compass Group Chile",
    ["https://www.trabajando.cl/empresa/compass-group",
     "https://cl.indeed.com/jobs?q=compass+group+chile&l=Chile&sort=date",
     "https://www.computrabajo.cl/trabajos-de-compass-group"],
    "https://www.trabajando.cl", v)

def scrape_sodexo(v): return scrape_portal("Sodexo Chile",
    ["https://www.trabajando.cl/empresa/sodexo",
     "https://cl.indeed.com/jobs?q=sodexo+chile&l=Chile&sort=date",
     "https://www.computrabajo.cl/trabajos-de-sodexo"],
    "https://www.trabajando.cl", v)

def scrape_aramark(v): return scrape_portal("Aramark Chile",
    ["https://www.trabajando.cl/empresa/aramark",
     "https://cl.indeed.com/jobs?q=aramark+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_eurest(v): return scrape_portal("Eurest Chile",
    ["https://www.trabajando.cl/empresa/eurest",
     "https://cl.indeed.com/jobs?q=eurest+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_applus(v): return scrape_portal("Applus Chile",
    ["https://cl.indeed.com/jobs?q=applus+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_igt(v): return scrape_portal("IGT Chile",
    ["https://cl.indeed.com/jobs?q=igt+chile+campamento&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_cgg(v): return scrape_portal("CGG Solutions",
    ["https://cl.indeed.com/jobs?q=cgg+solutions+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 5 — INGENIERÍA / EPC / CONSTRUCCIÓN
# ══════════════════════════════════════════════════════
def scrape_fluor(v): return scrape_portal("Fluor Chile",
    ["https://www.trabajando.cl/empresa/fluor",
     "https://cl.indeed.com/jobs?q=fluor+chile+ingenieria&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_worley(v): return scrape_portal("Worley Chile",
    ["https://cl.indeed.com/jobs?q=worley+chile&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/worley"],
    "https://www.trabajando.cl", v)

def scrape_wood(v): return scrape_portal("Wood Group Chile",
    ["https://cl.indeed.com/jobs?q=wood+group+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_techint(v): return scrape_portal("Techint Chile",
    ["https://www.trabajando.cl/empresa/techint",
     "https://cl.indeed.com/jobs?q=techint+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_maserr(v): return scrape_portal("MAS Errázuriz",
    ["https://www.trabajando.cl/empresa/mas-errazuriz",
     "https://cl.indeed.com/jobs?q=mas+errazuriz+mineria&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_sk(v): return scrape_portal("Sigdo Koppers",
    ["https://www.trabajando.cl/empresa/sigdo-koppers",
     "https://cl.indeed.com/jobs?q=sigdo+koppers&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_salfa(v): return scrape_portal("Salfa / Salfacorp",
    ["https://www.trabajando.cl/empresa/salfacorp",
     "https://cl.indeed.com/jobs?q=salfacorp+salfa&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_belfi(v): return scrape_portal("Belfi Ingeniería",
    ["https://cl.indeed.com/jobs?q=belfi+ingenieria+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_icafal(v): return scrape_portal("Icafal Ingeniería",
    ["https://cl.indeed.com/jobs?q=icafal+ingenieria&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_vesco(v): return scrape_portal("Vesco Consultores",
    ["https://www.trabajando.cl/empresa/vesco",
     "https://cl.indeed.com/jobs?q=vesco+mineria&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 6 — EQUIPOS OEM / PROVEEDORES
# ══════════════════════════════════════════════════════
def scrape_komatsu(v): return scrape_portal("Komatsu Chile",
    ["https://www.trabajando.cl/empresa/komatsu",
     "https://cl.indeed.com/jobs?q=komatsu+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_finning(v): return scrape_portal("Finning / Caterpillar Chile",
    ["https://www.trabajando.cl/empresa/finning",
     "https://cl.indeed.com/jobs?q=finning+caterpillar+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_sandvik(v): return scrape_portal("Sandvik Chile",
    ["https://www.trabajando.cl/empresa/sandvik",
     "https://cl.indeed.com/jobs?q=sandvik+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_epiroc(v): return scrape_portal("Epiroc Chile",
    ["https://cl.indeed.com/jobs?q=epiroc+chile&l=Chile&sort=date",
     "https://www.trabajando.cl/empresa/epiroc"],
    "https://www.trabajando.cl", v)

def scrape_metso(v): return scrape_portal("Metso Outotec Chile",
    ["https://cl.indeed.com/jobs?q=metso+outotec+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_weir(v): return scrape_portal("Weir Minerals Chile",
    ["https://cl.indeed.com/jobs?q=weir+minerals+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_flsmidth(v): return scrape_portal("FLSmidth Chile",
    ["https://cl.indeed.com/jobs?q=flsmidth+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

def scrape_tk(v): return scrape_portal("Thyssenkrupp Chile",
    ["https://cl.indeed.com/jobs?q=thyssenkrupp+chile&l=Chile&sort=date"],
    "https://cl.indeed.com", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 7 — INSPECCIÓN / RRHH / OTROS
# ══════════════════════════════════════════════════════
def scrape_bv(v): return scrape_portal("Bureau Veritas Chile",
    ["https://www.trabajando.cl/empresa/bureau-veritas",
     "https://cl.indeed.com/jobs?q=bureau+veritas+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_sgs(v): return scrape_portal("SGS Chile",
    ["https://www.trabajando.cl/empresa/sgs",
     "https://cl.indeed.com/jobs?q=sgs+chile+mineria&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_confip(v): return scrape_portal("Confipetrol",
    ["https://www.trabajando.cl/empresa/confipetrol",
     "https://cl.indeed.com/jobs?q=confipetrol+chile&l=Chile&sort=date"],
    "https://www.trabajando.cl", v)

def scrape_adecco(v): return scrape_portal("Adecco Chile",
    ["https://www.adecco.cl/empleos/?sector=mineria",
     "https://www.adecco.cl/empleos/?sector=ingenieria-industrial"],
    "https://www.adecco.cl", v)

def scrape_hays(v): return scrape_portal("Hays Chile",
    ["https://www.hays.cl/empleo/buscar-empleo?q=mining&location=Chile"],
    "https://www.hays.cl", v)

def scrape_manpower(v): return scrape_portal("ManpowerGroup Chile",
    ["https://www.manpower.cl/empleos?q=mineria+mantenimiento",
     "https://www.manpower.cl/empleos?q=administrador+contrato"],
    "https://www.manpower.cl", v)

def scrape_randstad(v): return scrape_portal("Randstad Chile",
    ["https://www.randstad.cl/jobs/?q=mineria",
     "https://www.randstad.cl/jobs/?q=mantenimiento+industrial"],
    "https://www.randstad.cl", v)

# ══════════════════════════════════════════════════════
#  EJECUCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════
FUENTES = [
    # Portales especializados minería
    scrape_trabajoenmineria, scrape_mineria_cl, scrape_expertominero,
    scrape_minerosonline, scrape_reclutamineria, scrape_mining_people, scrape_bolsa_mineria,
    # Portales generales
    scrape_trabajando, scrape_laborum, scrape_computrabajo,
    scrape_indeed, scrape_linkedin, scrape_bne, scrape_portalempleo,
    # Mineras directas
    scrape_codelco, scrape_bhp, scrape_collahuasi, scrape_angloamerican,
    scrape_aminerals, scrape_teck, scrape_kinross, scrape_lundin,
    scrape_sqm, scrape_cap, scrape_enami, scrape_sierragorda,
    scrape_agnico, scrape_goldfields, scrape_lithium,
    # Campamentos / Alimentación
    scrape_compass, scrape_sodexo, scrape_aramark, scrape_eurest,
    scrape_applus, scrape_igt, scrape_cgg,
    # Ingeniería / EPC
    scrape_fluor, scrape_worley, scrape_wood, scrape_techint,
    scrape_maserr, scrape_sk, scrape_salfa, scrape_belfi, scrape_icafal, scrape_vesco,
    # Equipos OEM
    scrape_komatsu, scrape_finning, scrape_sandvik, scrape_epiroc,
    scrape_metso, scrape_weir, scrape_flsmidth, scrape_tk,
    # Inspección / RRHH
    scrape_bv, scrape_sgs, scrape_confip, scrape_adecco,
    scrape_hays, scrape_manpower, scrape_randstad,
]

N      = len(FUENTES)
vistos = cargar_vistos()

print(f"\n📂 Historial: {len(vistos)} avisos procesados")

enviar(
    f"🤖 <b>RADAR MINERO V8 PLUS 2</b>\n"
    f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    f"🔍 Escaneando <b>{N} fuentes</b>\n"
    f"📊 Historial: {len(vistos)} avisos procesados"
)

total = 0
for i, fn in enumerate(FUENTES, 1):
    print(f"\n[{i}/{N}]", end="")
    total += fn(vistos)

guardar_vistos(vistos)

print(f"\n{'═'*55}")
print(f"  NUEVOS: {total}  |  FUENTES: {N}")
print(f"{'═'*55}")

enviar(
    f"{'✅' if total > 0 else '😴'} <b>Búsqueda completada</b>\n"
    f"📊 <b>{total}</b> aviso(s) nuevo(s)\n"
    f"🔍 {N} fuentes escaneadas\n"
    f"🕐 {'Próxima en 6 horas' if total == 0 else 'Revisa los avisos arriba ☝️'}"
)
