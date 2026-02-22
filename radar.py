"""
╔══════════════════════════════════════════════════════════╗
║         RADAR MINERO V9 PRO - Rubén Morales              ║
║                                                          ║
║  NOVEDADES V9:                                           ║
║  ► Sistema de puntuación ⭐ por palabras clave           ║
║  ► Alerta urgente 🚨 para empresas prioritarias          ║
║  ► Destacado especial ⏰ para avisos con turno           ║
║  ► Registro automático en Google Sheets                  ║
║  ► Botones ✅/❌ en cada aviso de Telegram               ║
║  ► 62 fuentes cubiertas                                  ║
╚══════════════════════════════════════════════════════════╝
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

print("=" * 57)
print("      RADAR MINERO V9 PRO")
print(f"      {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 57)

# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────
TOKEN              = os.environ["TOKEN"]
CHAT_ID            = os.environ["CHAT_ID"]
SEEN_FILE          = "seen_jobs.json"
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")
SHEET_NAME         = "Radar Minero - Postulaciones"

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
# SISTEMA DE PUNTUACIÓN ⭐
# ─────────────────────────────────────────────────────────
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
    "supervisor", "supervisora",
    "administrador", "administradora",
    "operaciones", "industrial",
    "campamento", "facility", "facilities",
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
    return hashlib.md5(f"{titulo.lower().strip()}{link.strip()}".encode()).hexdigest()

# ─────────────────────────────────────────────────────────
# FILTROS Y PUNTUACIÓN
# ─────────────────────────────────────────────────────────
def calcular_match(titulo):
    t = titulo.lower()
    if any(p in t for p in PERFIL_ALTO):
        return 3, "⭐⭐⭐ MATCH PERFECTO"
    if any(p in t for p in PERFIL_MEDIO):
        return 2, "⭐⭐ Buen match"
    if any(p in t for p in PERFIL_BAJO):
        return 1, "⭐ Match parcial"
    return 0, ""

def cumple_perfil(texto):
    t = texto.lower()
    if any(x in t for x in EXCLUIR):
        return False
    return (any(p in t for p in PERFIL_ALTO)
            or any(p in t for p in PERFIL_MEDIO)
            or any(p in t for p in PERFIL_BAJO))

def es_empresa_prioritaria(texto):
    return any(e in texto.lower() for e in EMPRESAS_PRIORITARIAS)

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
# GOOGLE SHEETS
# ─────────────────────────────────────────────────────────
def conectar_sheets():
    if not GOOGLE_CREDENTIALS:
        print("  ⚠️  Sin credenciales Google Sheets")
        return None
    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet  = client.open(SHEET_NAME).sheet1
        # Encabezados si la hoja está vacía
        if not sheet.row_values(1):
            sheet.insert_row([
                "Fecha Encontrado", "Fuente", "Cargo", "Empresa",
                "Ubicación", "Turno", "Match", "Link",
                "Estado", "Fecha Postulación", "Notas"
            ], 1)
        return sheet
    except Exception as e:
        print(f"  ⚠️  Google Sheets: {e}")
        return None

def registrar_en_sheets(sheet, fuente, titulo, empresa,
                         ubicacion, turno, match_str, link):
    if not sheet:
        return
    try:
        sheet.append_row([
            datetime.now().strftime("%d/%m/%Y %H:%M"),
            fuente, titulo[:150], empresa or "",
            ubicacion or "", turno or "", match_str,
            link or "", "Pendiente", "", "",
        ])
    except Exception as e:
        print(f"  ⚠️  Error Sheets: {e}")

# ─────────────────────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────────────────────
def enviar(msg, reply_markup=None):
    url_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id":   CHAT_ID,
        "text":      msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(url_api, data=data, timeout=10).raise_for_status()
    except Exception as e:
        print(f"  ⚠️  Telegram: {e}")
    time.sleep(1.2)

def botones_postulacion(hid):
    return {
        "inline_keyboard": [[
            {"text": "✅ Postulé",         "callback_data": f"postule:{hid}"},
            {"text": "🔖 Guardar",         "callback_data": f"guardar:{hid}"},
            {"text": "❌ No me interesa",  "callback_data": f"descarta:{hid}"},
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
    if turno:
        lineas.append(f"⏰ <b>TURNO: {turno}</b> ✔️")
    else:
        lineas.append(f"⏰ Turno: no especificado")
    if link:        lineas.append(f"🔗 {link[:300]}")
    return "\n".join(lineas)

# ─────────────────────────────────────────────────────────
# FUNCIÓN CENTRAL
# ─────────────────────────────────────────────────────────
def procesar_aviso(fuente, titulo, empresa, ubicacion_extra, link, vistos, sheet):
    if not cumple_perfil(titulo) or len(titulo) < 8:
        return 0
    hid = hash_aviso(titulo, link or "")
    if hid in vistos:
        return 0
    turno     = detectar_turno(titulo)
    ubicacion = detectar_ubicacion(titulo) or ubicacion_extra
    _, match_str = calcular_match(titulo)
    urgente   = es_empresa_prioritaria(f"{titulo} {empresa or ''} {fuente}")
    msg = formato_aviso(fuente, titulo, empresa, ubicacion,
                        turno, link, match_str, urgente)
    enviar(msg, reply_markup=botones_postulacion(hid))
    registrar_en_sheets(sheet, fuente, titulo, empresa,
                        ubicacion, turno, match_str, link)
    vistos.add(hid)
    return 1

# ─────────────────────────────────────────────────────────
# SCRAPERS GENÉRICOS
# ─────────────────────────────────────────────────────────
def scrape_simple(nombre, url, base_url, empresa_nombre, ubicacion_default, vistos, sheet):
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
                nombre, titulo, empresa_nombre, ubicacion_default, link, vistos, sheet)
    except Exception as e:
        print(f"  ⚠️  {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

def scrape_portal(nombre, urls, base_url, vistos, sheet):
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
                    nombre, titulo, empresa, detectar_ubicacion(txt),
                    link or url, vistos, sheet)
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

# ══════════════════════════════════════════════════════════
#  PORTALES ESPECIALIZADOS MINERÍA
# ══════════════════════════════════════════════════════════
def scrape_trabajoenmineria(v,s): return scrape_portal("TrabajoenMineria.cl",
    ["https://www.trabajoenmineria.cl/ofertas",
     "https://www.trabajoenmineria.cl/ofertas?area=mantenimiento",
     "https://www.trabajoenmineria.cl/ofertas?area=ingenieria"],
    "https://www.trabajoenmineria.cl", v, s)

def scrape_mineria_cl(v,s): return scrape_portal("Mineria.cl Empleos",
    ["https://www.mineria.cl/empleos/"], "https://www.mineria.cl", v, s)

def scrape_expertominero(v,s): return scrape_portal("ExpertoMinero.cl",
    ["https://www.expertominero.cl/empleos/"], "https://www.expertominero.cl", v, s)

def scrape_minerosonline(v,s): return scrape_portal("MinerosOnline",
    ["https://www.minerosonline.com/empleos/"], "https://www.minerosonline.com", v, s)

def scrape_reclutamineria(v,s): return scrape_portal("ReclutaMineria.cl",
    ["https://www.reclutamineria.cl/empleos/"], "https://www.reclutamineria.cl", v, s)

def scrape_mining_people(v,s): return scrape_simple("Mining People Intl.",
    "https://www.miningpeople.com.au/jobs?location=Chile",
    "https://www.miningpeople.com.au", "Mining People Intl.", "Norte Chile", v, s)

def scrape_bolsa_mineria(v,s): return scrape_portal("EmpleosMineria.cl",
    ["https://www.empleosmineria.cl/",
     "https://www.empleosmineria.cl/?cat=mantenimiento"],
    "https://www.empleosmineria.cl", v, s)

# ══════════════════════════════════════════════════════════
#  PORTALES GENERALES
# ══════════════════════════════════════════════════════════
def scrape_trabajando(v,s): return scrape_portal("Trabajando.cl",
    ["https://www.trabajando.cl/trabajos-mineria",
     "https://www.trabajando.cl/trabajos-mantenimiento-industrial",
     "https://www.trabajando.cl/trabajos-ingeniero-industrial"],
    "https://www.trabajando.cl", v, s)

def scrape_laborum(v,s): return scrape_portal("Laborum.cl",
    ["https://www.laborum.cl/empleos/mineria",
     "https://www.laborum.cl/empleos/mantenimiento-industrial",
     "https://www.laborum.cl/empleos/administracion-contratos"],
    "https://www.laborum.cl", v, s)

def scrape_computrabajo(v,s): return scrape_portal("Computrabajo.cl",
    ["https://www.computrabajo.cl/trabajos-de-mineria",
     "https://www.computrabajo.cl/trabajos-de-mantenimiento-industrial",
     "https://www.computrabajo.cl/trabajos-de-administracion-de-contratos"],
    "https://www.computrabajo.cl", v, s)

def scrape_indeed(vistos, sheet):
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
                link = (("https://cl.indeed.com"+l["href"]) if l and not l["href"].startswith("http") else (l["href"] if l else url))
                e = card.find(class_=re.compile(r"company", re.I))
                n += procesar_aviso("Indeed", titulo, e.text.strip() if e else None,
                    detectar_ubicacion(card.get_text()), link, vistos, sheet)
            time.sleep(2)
        except Exception as e: print(f"  ⚠️  Indeed: {e}")
    print(f"  ✅ {n} nuevos"); return n

def scrape_linkedin(vistos, sheet):
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
                    u.text.strip() if u else None, link, vistos, sheet)
            time.sleep(3)
        except Exception as e: print(f"  ⚠️  LinkedIn: {e}")
    print(f"  ✅ {n} nuevos"); return n

def scrape_bne(v,s): return scrape_portal("BNE Chile",
    ["https://www.bne.cl/empleos?q=administrador+contrato+mineria",
     "https://www.bne.cl/empleos?q=supervisor+mantencion+mineria"],
    "https://www.bne.cl", v, s)

def scrape_portalempleo(v,s): return scrape_portal("PortalEmpleo.cl",
    ["https://www.portalempleo.cl/trabajo/mineria/",
     "https://www.portalempleo.cl/trabajo/mantenimiento-industrial/"],
    "https://www.portalempleo.cl", v, s)

# ══════════════════════════════════════════════════════════
#  MINERAS DIRECTAS
# ══════════════════════════════════════════════════════════
def scrape_codelco(v,s):      return scrape_simple("Codelco","https://www.codelco.com/trabaja-con-nosotros/prontus_codelco/2012-01-16/120018.html","https://www.codelco.com","Codelco","Norte Chile / Varias faenas",v,s)
def scrape_bhp(v,s):          return scrape_simple("BHP Chile","https://careers.bhp.com/search-jobs/Chile","https://careers.bhp.com","BHP","Antofagasta / Escondida / Spence",v,s)
def scrape_collahuasi(v,s):   return scrape_simple("Collahuasi","https://www.collahuasi.cl/trabaja-con-nosotros/","https://www.collahuasi.cl","Collahuasi","Iquique / Tarapacá",v,s)
def scrape_angloamerican(v,s):return scrape_simple("Anglo American","https://www.angloamerican.com/careers/job-search?country=Chile","https://www.angloamerican.com","Anglo American","Los Bronces / El Soldado",v,s)
def scrape_aminerals(v,s):    return scrape_simple("Antofagasta Minerals","https://www.aminerals.cl/personas/trabaja-con-nosotros/","https://www.aminerals.cl","Ant. Minerals (Pelambres/Centinela)","Antofagasta / Pelambres",v,s)
def scrape_teck(v,s):         return scrape_simple("Teck / QB2","https://jobs.teck.com/search/?q=chile","https://jobs.teck.com","Teck / QB2","Iquique / Tarapacá",v,s)
def scrape_kinross(v,s):      return scrape_simple("Kinross Chile","https://careers.kinross.com/search/?q=chile","https://careers.kinross.com","Kinross","Atacama / Maricunga",v,s)
def scrape_lundin(v,s):       return scrape_simple("Lundin Mining","https://www.lundinmining.com/about/careers/","https://www.lundinmining.com","Lundin Mining","Atacama / Candelaria",v,s)
def scrape_sqm(v,s):          return scrape_simple("SQM Chile","https://www.sqm.com/es/nuestra-gente/trabaja-con-nosotros/","https://www.sqm.com","SQM","Antofagasta / Litio",v,s)
def scrape_cap(v,s):          return scrape_simple("CAP Minería","https://www.capmineria.cl/personas/trabaja-con-nosotros/","https://www.capmineria.cl","CAP Minería","Atacama / CDA",v,s)
def scrape_enami(v,s):        return scrape_simple("ENAMI","https://www.enami.cl/trabaja-con-nosotros","https://www.enami.cl","ENAMI","Norte / Centro Chile",v,s)
def scrape_sierragorda(v,s):  return scrape_simple("Sierra Gorda SCM","https://sierragorda.cl/trabaja-con-nosotros/","https://sierragorda.cl","Sierra Gorda SCM","Antofagasta",v,s)
def scrape_agnico(v,s):       return scrape_simple("Agnico Eagle","https://www.agnicoeagle.com/English/careers/job-opportunities/default.aspx","https://www.agnicoeagle.com","Agnico Eagle","Norte Chile",v,s)
def scrape_goldfields(v,s):   return scrape_simple("Gold Fields Chile","https://careers.goldfields.com/search/?q=chile","https://careers.goldfields.com","Gold Fields","Atacama / Salares Norte",v,s)
def scrape_lithium(v,s):      return scrape_simple("Lithium Americas","https://lithiumamericas.com/careers/","https://lithiumamericas.com","Lithium Americas","Antofagasta / Rincón",v,s)

# ══════════════════════════════════════════════════════════
#  CAMPAMENTOS / ALIMENTACIÓN
# ══════════════════════════════════════════════════════════
def scrape_compass(v,s):  return scrape_simple("Compass Group","https://www.compass-chile.cl/trabaja-con-nosotros/","https://www.compass-chile.cl","Compass Group","Norte Chile",v,s)
def scrape_sodexo(v,s):   return scrape_simple("Sodexo Chile","https://jobs.sodexo.com/search/?q=chile","https://jobs.sodexo.com","Sodexo","Norte Chile",v,s)
def scrape_aramark(v,s):  return scrape_simple("Aramark Chile","https://careers.aramark.com/search/?q=chile","https://careers.aramark.com","Aramark","Norte Chile",v,s)
def scrape_eurest(v,s):   return scrape_simple("Eurest Chile","https://www.eurest.cl/oportunidades-laborales/","https://www.eurest.cl","Eurest","Norte Chile",v,s)
def scrape_applus(v,s):   return scrape_simple("Applus Chile","https://www.applus.com/es/careers/job-search?country=Chile","https://www.applus.com","Applus","Norte Chile",v,s)
def scrape_igt(v,s):      return scrape_simple("IGT Chile","https://www.igtchile.cl/trabaja-con-nosotros/","https://www.igtchile.cl","IGT Chile","Norte Chile",v,s)
def scrape_cgg(v,s):      return scrape_simple("CGG Solutions","https://www.cggsolutions.cl/trabaja-con-nosotros/","https://www.cggsolutions.cl","CGG Solutions","Norte Chile",v,s)

# ══════════════════════════════════════════════════════════
#  INGENIERÍA / EPC / CONSTRUCCIÓN
# ══════════════════════════════════════════════════════════
def scrape_fluor(v,s):    return scrape_simple("Fluor Chile","https://careers.fluor.com/job-search-results/?category=Engineering&location=Chile","https://careers.fluor.com","Fluor","Norte Chile / Proyectos",v,s)
def scrape_worley(v,s):   return scrape_simple("Worley Chile","https://careers.worley.com/jobs?location=Chile","https://careers.worley.com","Worley","Antofagasta / Santiago",v,s)
def scrape_wood(v,s):     return scrape_simple("Wood Group","https://careers.woodplc.com/jobs?location=Chile","https://careers.woodplc.com","Wood Group","Norte Chile",v,s)
def scrape_techint(v,s):  return scrape_simple("Techint Chile","https://jobs.techint.com/jobs?country=CL","https://jobs.techint.com","Techint","Norte Chile",v,s)
def scrape_maserr(v,s):   return scrape_simple("MAS Errázuriz","https://www.maserrazuriz.cl/trabaja-con-nosotros/","https://www.maserrazuriz.cl","MAS Errázuriz","Norte Chile",v,s)
def scrape_sk(v,s):       return scrape_simple("Sigdo Koppers","https://www.sigdokoppers.cl/personas/trabaja-con-nosotros/","https://www.sigdokoppers.cl","Sigdo Koppers","Norte Chile",v,s)
def scrape_salfa(v,s):    return scrape_simple("Salfa / Salfacorp","https://www.salfacorp.com/trabaja-con-nosotros/","https://www.salfacorp.com","Salfa / Salfacorp","Norte Chile",v,s)
def scrape_belfi(v,s):    return scrape_simple("Belfi Ingeniería","https://www.belfi.cl/trabaja-con-nosotros/","https://www.belfi.cl","Belfi","Chile",v,s)
def scrape_icafal(v,s):   return scrape_simple("Icafal Ingeniería","https://www.icafal.cl/trabaja-con-nosotros/","https://www.icafal.cl","Icafal","Chile",v,s)
def scrape_vesco(v,s):    return scrape_simple("Vesco Consultores","https://www.vesco.cl/empleo/","https://www.vesco.cl","Vesco","Chile",v,s)

# ══════════════════════════════════════════════════════════
#  EQUIPOS OEM / PROVEEDORES
# ══════════════════════════════════════════════════════════
def scrape_komatsu(v,s):  return scrape_simple("Komatsu Chile","https://komatsu.jobs/search/?q=chile","https://komatsu.jobs","Komatsu","Norte Chile",v,s)
def scrape_finning(v,s):  return scrape_simple("Finning Chile","https://jobs.finning.com/search/?q=chile","https://jobs.finning.com","Finning / Caterpillar","Antofagasta / Calama",v,s)
def scrape_sandvik(v,s):  return scrape_simple("Sandvik Chile","https://www.sandvik.com/en/careers/job-openings/?country=Chile","https://www.sandvik.com","Sandvik","Norte Chile",v,s)
def scrape_epiroc(v,s):   return scrape_simple("Epiroc Chile","https://careers.epiroc.com/jobs?location=Chile","https://careers.epiroc.com","Epiroc","Norte Chile",v,s)
def scrape_metso(v,s):    return scrape_simple("Metso Outotec","https://www.metso.com/careers/open-positions/?country=Chile","https://www.metso.com","Metso Outotec","Norte Chile",v,s)
def scrape_weir(v,s):     return scrape_simple("Weir Minerals","https://careers.weir/search/?q=chile","https://careers.weir","Weir Minerals","Norte Chile",v,s)
def scrape_flsmidth(v,s): return scrape_simple("FLSmidth Chile","https://www.flsmidth.com/en-gb/company/careers/vacancies?country=Chile","https://www.flsmidth.com","FLSmidth","Norte Chile",v,s)
def scrape_tk(v,s):       return scrape_simple("Thyssenkrupp","https://www.thyssenkrupp.com/en/careers/job-search?q=chile","https://www.thyssenkrupp.com","Thyssenkrupp","Norte Chile",v,s)

# ══════════════════════════════════════════════════════════
#  INSPECCIÓN / RRHH / OTROS
# ══════════════════════════════════════════════════════════
def scrape_bv(v,s):       return scrape_simple("Bureau Veritas","https://candidatos.bureauveritas.cl/jobsearch","https://candidatos.bureauveritas.cl","Bureau Veritas","Chile",v,s)
def scrape_sgs(v,s):      return scrape_simple("SGS Chile","https://www.sgs.com/en/careers/job-search?country=Chile","https://www.sgs.com","SGS","Norte Chile",v,s)
def scrape_confip(v,s):   return scrape_simple("Confipetrol","https://confipetrol.cl/trabaja-con-nosotros/","https://confipetrol.cl","Confipetrol","Norte Chile",v,s)
def scrape_adecco(v,s):   return scrape_portal("Adecco Chile",["https://www.adecco.cl/empleos/?sector=mineria","https://www.adecco.cl/empleos/?sector=ingenieria-industrial"],"https://www.adecco.cl",v,s)
def scrape_hays(v,s):     return scrape_simple("Hays Chile","https://www.hays.cl/empleo/buscar-empleo?q=mining&location=Chile","https://www.hays.cl","Hays Recruitment","Norte Chile",v,s)
def scrape_manpower(v,s): return scrape_portal("ManpowerGroup",["https://www.manpower.cl/empleos?q=mineria+mantenimiento","https://www.manpower.cl/empleos?q=administrador+contrato"],"https://www.manpower.cl",v,s)
def scrape_randstad(v,s): return scrape_portal("Randstad Chile",["https://www.randstad.cl/jobs/?q=mineria","https://www.randstad.cl/jobs/?q=mantenimiento+industrial"],"https://www.randstad.cl",v,s)

# ══════════════════════════════════════════════════════════
#  EJECUCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════
FUENTES = [
    scrape_trabajoenmineria, scrape_mineria_cl, scrape_expertominero,
    scrape_minerosonline, scrape_reclutamineria, scrape_mining_people, scrape_bolsa_mineria,
    scrape_trabajando, scrape_laborum, scrape_computrabajo,
    scrape_indeed, scrape_linkedin, scrape_bne, scrape_portalempleo,
    scrape_codelco, scrape_bhp, scrape_collahuasi, scrape_angloamerican,
    scrape_aminerals, scrape_teck, scrape_kinross, scrape_lundin,
    scrape_sqm, scrape_cap, scrape_enami, scrape_sierragorda,
    scrape_agnico, scrape_goldfields, scrape_lithium,
    scrape_compass, scrape_sodexo, scrape_aramark, scrape_eurest,
    scrape_applus, scrape_igt, scrape_cgg,
    scrape_fluor, scrape_worley, scrape_wood, scrape_techint,
    scrape_maserr, scrape_sk, scrape_salfa, scrape_belfi, scrape_icafal, scrape_vesco,
    scrape_komatsu, scrape_finning, scrape_sandvik, scrape_epiroc,
    scrape_metso, scrape_weir, scrape_flsmidth, scrape_tk,
    scrape_bv, scrape_sgs, scrape_confip, scrape_adecco,
    scrape_hays, scrape_manpower, scrape_randstad,
]

N      = len(FUENTES)
vistos = cargar_vistos()
sheet  = conectar_sheets()

print(f"\n📂 Historial: {len(vistos)} avisos procesados")
print(f"📊 Google Sheets: {'conectado ✅' if sheet else 'no disponible ⚠️'}")

enviar(
    f"🤖 <b>RADAR MINERO V9 PRO</b>\n"
    f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    f"🔍 Escaneando <b>{N} fuentes</b>\n"
    f"📊 Historial: {len(vistos)} avisos procesados\n"
    f"{'📋 Google Sheets activo ✅' if sheet else '⚠️ Sheets sin conectar'}"
)

total = 0
for i, fn in enumerate(FUENTES, 1):
    print(f"\n[{i}/{N}]", end="")
    total += fn(vistos, sheet)

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
