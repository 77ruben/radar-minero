"""
╔══════════════════════════════════════════════════════╗
║    RADAR MINERO V9 - Rubén Morales                   ║
║                                                      ║
║  FUENTES VERIFICADAS:                                ║
║  ► 15 portales con scraper nativo                    ║
║  ► 47 empresas via Indeed + Computrabajo             ║
║  ► 5 fuentes SPA/React → reemplazadas por queries    ║
║  ► Botones ✅ Visto (cambia visual) / 🗑 Eliminar    ║
╚══════════════════════════════════════════════════════╝
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re
from datetime import datetime

print("=" * 55)
print("      RADAR MINERO V9")
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
# PERFIL Y FILTROS
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
    "infraestructura", "obras civiles",
]
PERFIL_BAJO = [
    "ingeniero", "ingeniería", "ingenieria", "engineering",
    "mantencion", "mantención", "mantenimiento", "maintenance",
    "supervisor", "supervisora", "administrador", "administradora",
    "operaciones", "industrial", "campamento",
    "facility", "facilities", "auditor", "calidad", "hse",
]
PERFIL_TODOS = PERFIL_ALTO + PERFIL_MEDIO + PERFIL_BAJO

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
    "aseador", "aseo", "lavandero", "camarero",
]
UBICACIONES_KW = [
    "antofagasta", "calama", "iquique", "atacama", "copiapó", "copiapo",
    "chuquicamata", "tocopilla", "mejillones", "sierra gorda", "taltal",
    "diego de almagro", "norte grande", "norte chico", "norte de chile",
    "región de antofagasta", "región de tarapacá",
    "región de atacama", "región de coquimbo",
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
# FILTROS Y PUNTUACIÓN
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
    return any(p in t for p in PERFIL_TODOS)

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
        "chat_id":   CHAT_ID,
        "text":      msg,
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
            {"text": "🗑 Eliminar", "callback_data": f"eliminar:{hid}"},
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
    if match_str:  lineas.append(match_str)
    if empresa:    lineas.append(f"🏭 {empresa[:90]}")
    if ubicacion:  lineas.append(f"📍 {ubicacion}")
    lineas.append(f"⏰ <b>TURNO: {turno}</b> ✔️" if turno else "⏰ Turno: no especificado")
    if link:       lineas.append(f"🔗 {link[:300]}")
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
# SCRAPER A: portales con estructura HTML nativa
# ─────────────────────────────────────────────────────
def scrape_portal(nombre, urls, base_url, vistos):
    print(f"\n🔍 {nombre}...")
    encontrados = 0
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            # Intentar tarjetas estructuradas primero
            cards = (
                soup.find_all(["article","li"],
                    class_=re.compile(r"job|aviso|card|oferta|listing|empleo|position|result", re.I))
                or soup.find_all("div",
                    class_=re.compile(r"job|aviso|card|oferta|listing|empleo|position|result", re.I))
            )
            if cards:
                for card in cards:
                    t_tag   = card.find(["h2","h3","h4","a"]) or card
                    titulo  = t_tag.get_text(strip=True)
                    l_tag   = card.find("a", href=True) if card.name != "a" else card
                    link    = l_tag["href"] if l_tag else url
                    if link and not link.startswith("http"):
                        link = base_url.rstrip("/") + "/" + link.lstrip("/")
                    e_tag   = card.find(class_=re.compile(r"empresa|company|organiz", re.I))
                    empresa = e_tag.get_text(strip=True) if e_tag else None
                    txt     = card.get_text()
                    encontrados += procesar_aviso(
                        nombre, titulo, empresa, detectar_ubicacion(txt), link or url, vistos)
            else:
                # Fallback: todos los links con texto de cargo
                for a in soup.find_all("a", href=True):
                    titulo = a.get_text(strip=True)
                    link   = a["href"]
                    if not link.startswith("http"):
                        link = base_url.rstrip("/") + "/" + link.lstrip("/")
                    encontrados += procesar_aviso(nombre, titulo, None, None, link, vistos)
            time.sleep(2)
        except Exception as e:
            print(f"  ⚠️  {nombre}: {e}")
    print(f"  ✅ {encontrados} nuevos")
    return encontrados

# ─────────────────────────────────────────────────────
# SCRAPER B: Indeed por empresa o cargo
# ─────────────────────────────────────────────────────
def scrape_indeed(query, nombre_display, ubicacion="Chile", vistos=None):
    url = (f"https://cl.indeed.com/jobs"
           f"?q={query.replace(' ','+')}"
           f"&l={ubicacion.replace(' ','+')}"
           f"&sort=date&fromage=30")
    n = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("div", attrs={"data-jk": True}):
            t = card.find(["h2","h3"], class_=re.compile(r"title|jobTitle", re.I))
            titulo = t.get_text(strip=True) if t else ""
            e = card.find(class_=re.compile(r"company|companyName", re.I))
            empresa = e.get_text(strip=True) if e else nombre_display
            jk  = card.get("data-jk","")
            link = f"https://cl.indeed.com/viewjob?jk={jk}" if jk else url
            u = card.find(class_=re.compile(r"location|companyLocation", re.I))
            ubicacion_card = u.get_text(strip=True) if u else None
            n += procesar_aviso(nombre_display, titulo, empresa, ubicacion_card, link, vistos)
        time.sleep(2)
    except Exception as e:
        print(f"  ⚠️  Indeed ({nombre_display}): {e}")
    return n

# ─────────────────────────────────────────────────────
# SCRAPER C: Computrabajo por empresa
# ─────────────────────────────────────────────────────
def scrape_computrabajo_empresa(nombre_display, slug, vistos):
    url = f"https://www.computrabajo.cl/trabajos-de-{slug}"
    n = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("article", class_=re.compile(r"box_offer|offer", re.I)):
            t = card.find(["h2","h3","a"])
            titulo = t.get_text(strip=True) if t else ""
            l = card.find("a", href=True)
            link = l["href"] if l else url
            if link and not link.startswith("http"):
                link = "https://www.computrabajo.cl" + link
            e = card.find(class_=re.compile(r"company|empresa", re.I))
            empresa = e.get_text(strip=True) if e else nombre_display
            txt = card.get_text()
            n += procesar_aviso(nombre_display, titulo, empresa,
                                detectar_ubicacion(txt), link, vistos)
        time.sleep(2)
    except Exception as e:
        print(f"  ⚠️  Computrabajo ({nombre_display}): {e}")
    return n

# ─────────────────────────────────────────────────────
# Función combinada B+C para empresas corporativas
# ─────────────────────────────────────────────────────
def scrape_empresa(nombre, query_indeed, slug_ct, ubicacion="Chile", vistos=None):
    print(f"\n🔍 {nombre}...")
    n  = scrape_indeed(query_indeed, nombre, ubicacion, vistos)
    n += scrape_computrabajo_empresa(nombre, slug_ct, vistos)
    print(f"  ✅ {n} nuevos")
    return n

# ══════════════════════════════════════════════════════
#  BLOQUE 1 — PORTALES ESPECIALIZADOS MINERÍA (tipo A)
# ══════════════════════════════════════════════════════
def scrape_trabajoenmineria(v): return scrape_portal("TrabajoenMineria.cl",
    ["https://www.trabajoenmineria.cl/ofertas",
     "https://www.trabajoenmineria.cl/ofertas?area=mantenimiento",
     "https://www.trabajoenmineria.cl/ofertas?area=ingenieria"],
    "https://www.trabajoenmineria.cl", v)

def scrape_mineria_cl(v): return scrape_portal("Mineria.cl",
    ["https://www.mineria.cl/empleos/"], "https://www.mineria.cl", v)

def scrape_expertominero(v): return scrape_portal("ExpertoMinero.cl",
    ["https://www.expertominero.cl/empleos/"], "https://www.expertominero.cl", v)

def scrape_minerosonline(v): return scrape_portal("MinerosOnline",
    ["https://www.minerosonline.com/empleos/"], "https://www.minerosonline.com", v)

def scrape_reclutamineria(v): return scrape_portal("ReclutaMineria.cl",
    ["https://www.reclutamineria.cl/empleos/"], "https://www.reclutamineria.cl", v)

def scrape_mining_people(v): return scrape_portal("Mining People Intl.",
    ["https://www.miningpeople.com.au/jobs?location=Chile"],
    "https://www.miningpeople.com.au", v)

# empleosmineria.cl → SPA sin estructura → reemplazada por Indeed queries
def scrape_queries_mineria(v):
    print("\n🔍 Búsquedas directas por cargo (Indeed)...")
    n  = scrape_indeed("administrador contrato mineria", "Indeed - Contratos", "Chile", v)
    n += scrape_indeed("supervisor mantencion mineria", "Indeed - Mantenimiento", "Antofagasta Chile", v)
    n += scrape_indeed("jefe mantenimiento mineria", "Indeed - Jefe Mantención", "Chile", v)
    n += scrape_indeed("planner planificador mineria", "Indeed - Planner", "Chile", v)
    n += scrape_indeed("facility manager campamento faena", "Indeed - Facility", "Chile", v)
    n += scrape_indeed("ingeniero confiabilidad mineria", "Indeed - Confiabilidad", "Chile", v)
    n += scrape_indeed("administrador campamento mineria", "Indeed - Campamento", "Chile", v)
    n += scrape_indeed("coordinador contratos mineria", "Indeed - Coordinador", "Chile", v)
    print(f"  ✅ {n} nuevos total queries")
    return n

# ══════════════════════════════════════════════════════
#  BLOQUE 2 — PORTALES GENERALES (tipo A)
# ══════════════════════════════════════════════════════
def scrape_trabajando(v): return scrape_portal("Trabajando.cl",
    ["https://www.trabajando.cl/trabajos-mineria",
     "https://www.trabajando.cl/trabajos-mantenimiento-industrial",
     "https://www.trabajando.cl/trabajos-ingeniero-industrial",
     "https://www.trabajando.cl/trabajos-administrador-de-contrato"],
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

def scrape_linkedin(vistos):
    print("\n🔍 LinkedIn Jobs...")
    n = 0
    queries = [
        ("administrador%20contrato%20mineria",       "Antofagasta%2C%20Chile"),
        ("supervisor%20mantencion%20mineria",         "Antofagasta%2C%20Chile"),
        ("jefe%20mantenimiento%20mineria",            "Calama%2C%20Chile"),
        ("planner%20mineria",                         "Chile"),
        ("facility%20manager%20campamento%20mineria", "Chile"),
        ("ingeniero%20confiabilidad%20mineria",       "Chile"),
    ]
    for q, loc in queries:
        url = (f"https://www.linkedin.com/jobs/search/"
               f"?keywords={q}&location={loc}&f_TPR=r2592000&sortBy=DD")
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div",
                    class_=re.compile(r"base-card|job-search-card", re.I)):
                t = card.find(["h3","h4"])
                titulo = t.get_text(strip=True) if t else ""
                l = card.find("a", href=True)
                link = l["href"].split("?")[0] if l else url
                e = card.find(class_=re.compile(r"base-search-card__subtitle", re.I))
                empresa = e.get_text(strip=True) if e else None
                u = card.find(class_=re.compile(r"base-search-card__metadata", re.I))
                ub = u.get_text(strip=True) if u else None
                n += procesar_aviso("LinkedIn", titulo, empresa, ub, link, vistos)
            time.sleep(3)
        except Exception as e:
            print(f"  ⚠️  LinkedIn: {e}")
    print(f"  ✅ {n} nuevos"); return n

def scrape_bne(v): return scrape_portal("BNE Chile",
    ["https://www.bne.cl/empleos?q=administrador+contrato+mineria",
     "https://www.bne.cl/empleos?q=supervisor+mantencion+mineria",
     "https://www.bne.cl/empleos?q=jefe+mantenimiento+mineria"],
    "https://www.bne.cl", v)

def scrape_portalempleo(v): return scrape_portal("PortalEmpleo.cl",
    ["https://www.portalempleo.cl/trabajo/mineria/",
     "https://www.portalempleo.cl/trabajo/mantenimiento-industrial/"],
    "https://www.portalempleo.cl", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 3 — MINERAS DIRECTAS (tipo B+C)
#  Todos los ATS corporativos bloquean scraping directo
#  → Indeed por nombre empresa + Computrabajo
# ══════════════════════════════════════════════════════
def scrape_codelco(v):      return scrape_empresa("Codelco",
    "codelco supervisor ingeniero administrador", "codelco", "Chile", v)

def scrape_bhp(v):          return scrape_empresa("BHP / Escondida / Spence",
    "bhp escondida spence supervisor ingeniero", "bhp", "Antofagasta Chile", v)

def scrape_collahuasi(v):   return scrape_empresa("Collahuasi",
    "collahuasi supervisor ingeniero planificador", "collahuasi", "Iquique Chile", v)

def scrape_angloamerican(v):return scrape_empresa("Anglo American",
    "anglo american chile supervisor ingeniero", "anglo-american", "Chile", v)

def scrape_pelambres(v):
    print("\n🔍 Pelambres / Centinela / Zaldivar...")
    n  = scrape_indeed("pelambres supervisor ingeniero administrador", "Pelambres", "Antofagasta Chile", v)
    n += scrape_indeed("centinela minera supervisor ingeniero", "Centinela", "Antofagasta Chile", v)
    n += scrape_indeed("zaldivar minera supervisor", "Zaldivar", "Antofagasta Chile", v)
    n += scrape_computrabajo_empresa("Minera Los Pelambres", "minera-los-pelambres", v)
    n += scrape_computrabajo_empresa("Minera Centinela", "minera-centinela", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_teck(v):         return scrape_empresa("Teck / QB2",
    "teck quebrada blanca supervisor ingeniero planificador", "teck", "Chile", v)

def scrape_kinross(v):      return scrape_empresa("Kinross Chile",
    "kinross maricunga chile supervisor ingeniero", "kinross", "Atacama Chile", v)

def scrape_lundin(v):
    print("\n🔍 Lundin Mining / Candelaria...")
    n  = scrape_indeed("candelaria lundin supervisor ingeniero mantencion", "Lundin/Candelaria", "Atacama Chile", v)
    n += scrape_computrabajo_empresa("Minera Candelaria", "minera-candelaria", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_sqm(v):          return scrape_empresa("SQM",
    "sqm litio supervisor ingeniero administrador", "sqm", "Antofagasta Chile", v)

def scrape_cap(v):          return scrape_empresa("CAP Minería",
    "cap mineria cda supervisor ingeniero", "cap-mineria", "Atacama Chile", v)

def scrape_enami(v):        return scrape_empresa("ENAMI",
    "enami supervisor ingeniero mantenimiento", "enami", "Chile", v)

def scrape_sierragorda(v):  return scrape_empresa("Sierra Gorda SCM",
    "sierra gorda scm supervisor ingeniero", "sierra-gorda-scm", "Antofagasta Chile", v)

def scrape_agnico(v):       return scrape_empresa("Agnico Eagle",
    "agnico eagle chile supervisor ingeniero", "agnico-eagle", "Chile", v)

def scrape_goldfields(v):   return scrape_empresa("Gold Fields / Salares Norte",
    "gold fields salares norte supervisor ingeniero", "gold-fields", "Atacama Chile", v)

def scrape_lithium(v):      return scrape_empresa("Lithium Americas / Rincón",
    "lithium americas rincon supervisor ingeniero", "lithium-americas", "Antofagasta Chile", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 4 — CAMPAMENTOS / ALIMENTACIÓN (tipo B+C)
#  Sitios corporativos no tienen empleos en Chile
# ══════════════════════════════════════════════════════
def scrape_compass(v):
    print("\n🔍 Compass Group Chile...")
    n  = scrape_indeed("compass group supervisor administrador campamento mineria", "Compass Group", "Chile", v)
    n += scrape_computrabajo_empresa("Compass Group", "compass-group", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_sodexo(v):
    print("\n🔍 Sodexo Chile...")
    n  = scrape_indeed("sodexo supervisor administrador campamento mineria", "Sodexo", "Chile", v)
    n += scrape_computrabajo_empresa("Sodexo", "sodexo", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_aramark(v):
    print("\n🔍 Aramark Chile...")
    n  = scrape_indeed("aramark supervisor administrador campamento chile", "Aramark", "Chile", v)
    n += scrape_computrabajo_empresa("Aramark", "aramark", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_eurest(v):       return scrape_empresa("Eurest Chile",
    "eurest supervisor administrador campamento chile", "eurest", "Chile", v)

def scrape_applus(v):       return scrape_empresa("Applus Chile",
    "applus supervisor ingeniero mineria chile", "applus", "Chile", v)

def scrape_igt(v):          return scrape_empresa("IGT Chile",
    "igt chile campamento supervisor administrador", "igt-chile", "Chile", v)

def scrape_cgg(v):          return scrape_empresa("CGG Solutions Chile",
    "cgg solutions supervisor administrador chile", "cgg-solutions", "Chile", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 5 — INGENIERÍA / EPC (tipo B+C)
#  Todos usan ATS Workday/SAP/Taleo → bloquean
# ══════════════════════════════════════════════════════
def scrape_fluor(v):        return scrape_empresa("Fluor Chile",
    "fluor chile ingeniero supervisor proyecto mineria", "fluor", "Chile", v)

def scrape_worley(v):       return scrape_empresa("Worley Chile",
    "worley chile ingeniero supervisor mineria", "worley", "Chile", v)

def scrape_wood(v):         return scrape_empresa("Wood Group Chile",
    "wood group chile ingeniero supervisor", "wood-group", "Chile", v)

def scrape_techint(v):      return scrape_empresa("Techint Chile",
    "techint chile supervisor ingeniero mantencion", "techint", "Chile", v)

def scrape_maserr(v):       return scrape_empresa("MAS Errázuriz",
    "mas errazuriz supervisor ingeniero mantencion mineria", "mas-errazuriz", "Chile", v)

def scrape_sk(v):
    print("\n🔍 Sigdo Koppers...")
    n  = scrape_indeed("sigdo koppers sk supervisor ingeniero mineria", "Sigdo Koppers", "Chile", v)
    n += scrape_computrabajo_empresa("Sigdo Koppers", "sigdo-koppers", v)
    # SK también publica bajo nombre de filiales
    n += scrape_indeed("enaex magotteaux skc supervisor ingeniero", "SK Filiales", "Chile", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_salfa(v):        return scrape_empresa("Salfa / Salfacorp",
    "salfacorp salfa supervisor ingeniero mantencion mineria", "salfacorp", "Chile", v)

def scrape_belfi(v):
    print("\n🔍 Belfi Ingeniería...")
    n  = scrape_indeed("belfi supervisor ingeniero mantencion proyecto", "Belfi", "Chile", v)
    n += scrape_computrabajo_empresa("Belfi", "belfi", v)
    n += scrape_portal("Belfi - Portal propio",
         ["https://www.belfi.cl/trabaja-con-nosotros/"], "https://www.belfi.cl", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_icafal(v):       return scrape_empresa("Icafal Ingeniería",
    "icafal supervisor ingeniero mantencion proyecto", "icafal", "Chile", v)

def scrape_vesco(v):
    print("\n🔍 Vesco Consultores...")
    n  = scrape_portal("Vesco - Portal propio",
         ["https://www.vesco.cl/empleo/"], "https://www.vesco.cl", v)
    n += scrape_indeed("vesco supervisor ingeniero mineria", "Vesco", "Chile", v)
    print(f"  ✅ {n} nuevos"); return n

# ══════════════════════════════════════════════════════
#  BLOQUE 6 — EQUIPOS OEM / PROVEEDORES (tipo B+C)
#  Todos usan ATS internacionales → bloquean
# ══════════════════════════════════════════════════════
def scrape_komatsu(v):      return scrape_empresa("Komatsu Chile",
    "komatsu chile supervisor ingeniero mantencion", "komatsu", "Chile", v)

def scrape_finning(v):      return scrape_empresa("Finning / Caterpillar",
    "finning caterpillar chile supervisor ingeniero", "finning", "Chile", v)

def scrape_sandvik(v):      return scrape_empresa("Sandvik Chile",
    "sandvik chile supervisor ingeniero mantencion", "sandvik", "Chile", v)

def scrape_epiroc(v):       return scrape_empresa("Epiroc Chile",
    "epiroc chile supervisor ingeniero mantencion", "epiroc", "Chile", v)

def scrape_metso(v):        return scrape_empresa("Metso Outotec Chile",
    "metso outotec chile supervisor ingeniero", "metso-outotec", "Chile", v)

def scrape_weir(v):         return scrape_empresa("Weir Minerals Chile",
    "weir minerals chile supervisor ingeniero", "weir-minerals", "Chile", v)

def scrape_flsmidth(v):     return scrape_empresa("FLSmidth Chile",
    "flsmidth chile supervisor ingeniero", "flsmidth", "Chile", v)

def scrape_tk(v):           return scrape_empresa("Thyssenkrupp Chile",
    "thyssenkrupp chile supervisor ingeniero", "thyssenkrupp", "Chile", v)

# ══════════════════════════════════════════════════════
#  BLOQUE 7 — INSPECCIÓN / RRHH
# ══════════════════════════════════════════════════════
def scrape_bv(v):           return scrape_empresa("Bureau Veritas Chile",
    "bureau veritas chile supervisor ingeniero auditoria", "bureau-veritas", "Chile", v)

def scrape_sgs(v):
    # sgs.com bloquea todo → solo portales chilenos
    print("\n🔍 SGS Chile...")
    n  = scrape_indeed("sgs chile supervisor ingeniero mineria auditoria", "SGS", "Chile", v)
    n += scrape_computrabajo_empresa("SGS", "sgs", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_confip(v):       return scrape_empresa("Confipetrol",
    "confipetrol supervisor ingeniero mantencion", "confipetrol", "Chile", v)

def scrape_adecco(v): return scrape_portal("Adecco Chile",
    ["https://www.adecco.cl/empleos/?sector=mineria",
     "https://www.adecco.cl/empleos/?sector=ingenieria-industrial",
     "https://www.adecco.cl/empleos/?sector=mantenimiento"],
    "https://www.adecco.cl", v)

def scrape_hays(v):
    # hays.cl es SPA React → no scrapeable
    print("\n🔍 Hays Chile...")
    n  = scrape_indeed("hays chile supervisor ingeniero mineria", "Hays", "Chile", v)
    n += scrape_computrabajo_empresa("Hays", "hays", v)
    print(f"  ✅ {n} nuevos"); return n

def scrape_manpower(v): return scrape_portal("ManpowerGroup Chile",
    ["https://www.manpower.cl/empleos?q=mineria+mantenimiento",
     "https://www.manpower.cl/empleos?q=administrador+contrato+mineria",
     "https://www.manpower.cl/empleos?q=supervisor+ingeniero+mineria"],
    "https://www.manpower.cl", v)

def scrape_randstad(v):
    # randstad.cl es SPA React → no scrapeable
    print("\n🔍 Randstad Chile...")
    n  = scrape_indeed("randstad chile supervisor ingeniero mineria", "Randstad", "Chile", v)
    n += scrape_computrabajo_empresa("Randstad", "randstad", v)
    print(f"  ✅ {n} nuevos"); return n

# ══════════════════════════════════════════════════════
#  EJECUCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════
FUENTES = [
    # Portales especializados
    scrape_trabajoenmineria, scrape_mineria_cl, scrape_expertominero,
    scrape_minerosonline, scrape_reclutamineria, scrape_mining_people,
    scrape_queries_mineria,
    # Portales generales
    scrape_trabajando, scrape_laborum, scrape_computrabajo,
    scrape_linkedin, scrape_bne, scrape_portalempleo,
    # Mineras directas
    scrape_codelco, scrape_bhp, scrape_collahuasi, scrape_angloamerican,
    scrape_pelambres, scrape_teck, scrape_kinross, scrape_lundin,
    scrape_sqm, scrape_cap, scrape_enami, scrape_sierragorda,
    scrape_agnico, scrape_goldfields, scrape_lithium,
    # Campamentos / Alimentación
    scrape_compass, scrape_sodexo, scrape_aramark, scrape_eurest,
    scrape_applus, scrape_igt, scrape_cgg,
    # Ingeniería / EPC
    scrape_fluor, scrape_worley, scrape_wood, scrape_techint,
    scrape_maserr, scrape_sk, scrape_salfa, scrape_belfi,
    scrape_icafal, scrape_vesco,
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
    f"🤖 <b>RADAR MINERO V9</b>\n"
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
