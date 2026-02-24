"""
RADAR MINERO V15 ULTIMATE - Ruben Morales
Combina V9 (fuentes verificadas) + V14 (Gemini IA) + mejoras propias
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re
from datetime import datetime
import google.generativeai as genai

# ─────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────
TOKEN      = os.environ["TOKEN"]
CHAT_ID    = os.environ["CHAT_ID"]
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")
SEEN_FILE  = "seen_jobs.json"
CARTA_FILE = "cartas_pendientes.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}

# ─────────────────────────────────────────
# PERFIL COMPLETO DE RUBEN (base para IA)
# ─────────────────────────────────────────
PERFIL_RUBEN = """
NOMBRE: Ruben Alonso Morales Melgarejo
TITULO: Ingeniero de Ejecucion Industrial - mencion Mantenimiento y Logistica
DIPLOMADO: Direccion de Proyectos, Universidad del Desarrollo (2024-2025)
EXPERIENCIA: 15+ años en mineria e industria

ULTIMOS CARGOS:
1. Supervisor de Mantencion y OOCC - Compass Group / Minera Centinela, Calama (2022-2025)
   Mantenciones mayores, infraestructura de campamento, coordinacion de equipos,
   optimizacion de recursos, continuidad operacional.

2. Administrador de Contrato - Aramark / Minera Teck QB2, Iquique (2019-2021)
   Gestion de subcontratos, planificacion y ejecucion de mantenciones,
   control de avances, cumplimiento contractual, supervision HSE.

OTROS: Supervisor Obras (COSAL), Jefe Local (FRONTEL), Inspector Calidad Piping (SALFA),
       Inspector Soldadura Buque Rompehielo (ASMAR)

COMPETENCIAS: SAP PM, AutoCAD, Visio, MS Project, Excel Avanzado
CERTIFICACIONES: Auditor TRI NORMA ISO 9001 / ISO 14001 / ISO 45001
LICENCIAS: Clase B (2007) + Clase D Grua Horquilla Alto Tonelaje

CARGOS QUE BUSCA (prioridad):
1. Administrador de Contratos
2. Supervisor de Mantenimiento / OOCC
3. Jefe de Mantenimiento
4. Planner / Planificador Mantenimiento
5. Facility Manager / Administrador Campamento
6. Coordinador Contratos / Proyectos

ZONA: Norte Chile (Antofagasta, Calama, Iquique, Atacama)
TURNO PREFERIDO: 14x14, 10x10, 7x7, 4x3
"""

# ─────────────────────────────────────────
# INICIALIZAR GEMINI
# ─────────────────────────────────────────
IA_ACTIVA = False
model = None
if GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        IA_ACTIVA = True
        print("Gemini IA activa")
    except Exception as e:
        print(f"Gemini no disponible: {e}")

# ─────────────────────────────────────────
# FILTROS RAPIDOS (sin IA)
# ─────────────────────────────────────────
PERFIL_ALTO = [
    "administrador de contrato","administrador contrato","administradora de contrato",
    "contract manager","contract administrator",
    "jefe de mantenimiento","jefe mantención","jefe mantencion",
    "planner","planificador","planificadora",
    "supervisor de mantenimiento","supervisor mantención","supervisor mantencion",
    "administrador de campamento","camp manager","facility manager","facilities manager",
    "superintendente mantenimiento","superintendente mantención",
]
PERFIL_MEDIO = [
    "ingeniero de mantenimiento","ingeniero mantención","ingeniero mantencion",
    "ingeniero industrial","ingeniería industrial",
    "confiabilidad","reliability engineer",
    "coordinador de contratos","coordinador contratos","coordinador de proyectos",
    "project manager","project engineer",
    "jefe de operaciones","jefe de proyecto","jefe de planta",
    "supervisor de operaciones","supervisor de terreno",
    "logistica","logística","supply chain","planificacion","planificación",
    "infraestructura","obras civiles","oocc",
]
PERFIL_BAJO = [
    "ingeniero","ingeniería","ingenieria","engineering",
    "mantencion","mantención","mantenimiento","maintenance",
    "supervisor","supervisora","administrador","administradora",
    "operaciones","industrial","campamento","facility","facilities",
    "auditor","calidad","hse","seguridad",
]
PERFIL_TODOS = PERFIL_ALTO + PERFIL_MEDIO + PERFIL_BAJO

EXCLUIR = [
    "guardia","vigilante","chofer","conductor de","vendedor","vendedora",
    "cajero","cajera","digitador","secretaria","recepcionista",
    "cocinero","cocinera","garzón","garzon","manipuladora de alimentos",
    "médico","medico","enfermero","enfermera","contador","contadora",
    "psicólogo","psicóloga","practicante","pasantía","pasantia","internship",
    "aseador","aseo","lavandero","camarero","operario de producción","operador de",
]
TURNOS_KW = ["14x14","14 x 14","10x10","7x7","7 x 7","4x3","5x2",
             "turno rotativo","régimen de turno","turno minero","faena"]
UBIC_KW = [
    "antofagasta","calama","iquique","atacama","copiapó","copiapo",
    "chuquicamata","tocopilla","mejillones","sierra gorda","taltal",
    "diego de almagro","norte grande","norte chico","norte de chile",
    "region de antofagasta","region de tarapaca","region de atacama",
    "faena minera","proyecto minero","pampa",
    "quebrada blanca","centinela","escondida","collahuasi","pelambres",
]
EMPRESAS_PRIO = [
    "codelco","bhp","escondida","spence","collahuasi","anglo american",
    "antofagasta minerals","pelambres","centinela","zaldivar","teck",
    "quebrada blanca","qb2","sqm","kinross","lundin","candelaria",
    "gold fields","sierra gorda","compass","sodexo","aramark",
    "fluor","worley","techint","wood group","sigdo koppers",
    "salfacorp","mas errazuriz","komatsu","finning","sandvik","epiroc",
]

def nivel_match(titulo):
    t = titulo.lower()
    if any(p in t for p in PERFIL_ALTO):  return 3
    if any(p in t for p in PERFIL_MEDIO): return 2
    if any(p in t for p in PERFIL_BAJO):  return 1
    return 0

def cumple_basico(titulo):
    t = titulo.lower()
    if any(x in t for x in EXCLUIR): return False
    return any(p in t for p in PERFIL_TODOS)

def detectar_turno(texto):
    t = texto.lower()
    for kw in TURNOS_KW:
        if kw in t: return kw.upper()
    return None

def detectar_ubicacion(texto):
    t = texto.lower()
    for u in UBIC_KW:
        if u in t: return u.title()
    return None

def es_prioritaria(texto):
    return any(e in texto.lower() for e in EMPRESAS_PRIO)

# ─────────────────────────────────────────
# GEMINI: analisis profundo
# ─────────────────────────────────────────
def obtener_texto_aviso(link):
    try:
        r = requests.get(link, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","nav","footer","header"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)
        texto = re.sub(r"\s+", " ", texto)
        return texto[:4000]
    except:
        return ""

def analizar_con_gemini(titulo, empresa, link, texto_aviso):
    if not IA_ACTIVA or not model:
        return 5, "IA no disponible", "No especifica", "No especifica", "", "No especifica"

    prompt = (
        "Eres un headhunter experto en mineria chilena. Analiza esta oferta y comparala con el candidato.\n\n"
        "=== PERFIL DEL CANDIDATO ===\n"
        + PERFIL_RUBEN +
        "\n=== OFERTA LABORAL ===\n"
        f"CARGO: {titulo}\n"
        f"EMPRESA: {empresa}\n"
        f"TEXTO: {texto_aviso if texto_aviso else '(no disponible)'}\n\n"
        "=== INSTRUCCIONES ===\n"
        "1. Puntaje 1-10 de compatibilidad de Ruben con esta oferta.\n"
        "   9-10: Encaja perfectamente | 7-8: Muy buen match | 5-6: Match moderado\n"
        "   3-4: Match parcial | 1-2: No es para su perfil\n"
        "2. Extrae: turno (ej 14x14), sueldo (si aparece), beneficios clave.\n"
        "3. Escribe carta de presentacion de MAX 150 palabras personalizada para este cargo.\n"
        "   Menciona experiencia especifica relevante. Tono: profesional, directo, seguro.\n\n"
        "Responde SOLO JSON sin markdown:\n"
        '{"puntaje": 7, "porque": "explicacion breve 2-3 lineas", '
        '"turno": "14x14 o No especifica", "sueldo": "$X o No especifica", '
        '"beneficios": "lista breve o No especifica", "carta": "Estimados..."}'
    )
    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.3},
            request_options={"timeout": 30}
        )
        txt = re.sub(r"```json|```", "", response.text).strip()
        data = json.loads(txt)
        return (
            int(data.get("puntaje", 5)),
            data.get("porque", ""),
            data.get("turno", "No especifica"),
            data.get("sueldo", "No especifica"),
            data.get("carta", ""),
            data.get("beneficios", "No especifica"),
        )
    except Exception as e:
        print(f"  Gemini error: {e}")
        return 5, "Error IA - revisar manualmente", "Ver link", "Ver link", "", "Ver link"

# ─────────────────────────────────────────
# PERSISTENCIA
# ─────────────────────────────────────────
def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f: return set(json.load(f))
    return set()

def guardar_vistos(v):
    with open(SEEN_FILE, "w") as f: json.dump(list(v), f, indent=2)

def cargar_cartas():
    if os.path.exists(CARTA_FILE):
        with open(CARTA_FILE) as f: return json.load(f)
    return {}

def guardar_cartas(c):
    with open(CARTA_FILE, "w") as f: json.dump(c, f, indent=2, ensure_ascii=False)

def hash_aviso(titulo, link):
    return hashlib.md5(f"{titulo.lower().strip()}{link.strip()}".encode()).hexdigest()

# ─────────────────────────────────────────
# TELEGRAM
# ─────────────────────────────────────────
def enviar_telegram(msg, reply_markup=None):
    data = {
        "chat_id": CHAT_ID, "text": msg,
        "parse_mode": "HTML", "disable_web_page_preview": True,
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data=data, timeout=12)
    except Exception as e:
        print(f"  Telegram error: {e}")
    time.sleep(1.2)

def botones_aviso(hid, tiene_carta=False):
    fila1 = [
        {"text": "Visto",    "callback_data": f"visto:{hid}"},
        {"text": "Eliminar", "callback_data": f"eliminar:{hid}"},
    ]
    kb = [fila1]
    if tiene_carta:
        kb.append([{"text": "Ver Carta de Presentacion", "callback_data": f"carta:{hid}"}])
    return {"inline_keyboard": kb}

def formato_mensaje(fuente, titulo, empresa, ubicacion, turno, sueldo,
                    beneficios, link, nivel_n, puntaje, porque, urgente):
    if urgente and puntaje >= 7:
        header = "URGENTE - EMPRESA PRIORITARIA - MATCH ALTO"
    elif urgente:
        header = "ALERTA URGENTE - EMPRESA PRIORITARIA"
    elif nivel_n == 3 and puntaje >= 7:
        header = "MATCH PERFECTO - ALTA COMPATIBILIDAD"
    elif nivel_n == 3:
        header = "MATCH PERFECTO"
    elif nivel_n == 2:
        header = "BUEN MATCH"
    else:
        header = "NUEVO EMPLEO"

    barra = ("X" * puntaje + "-" * (10 - puntaje)) if puntaje > 0 else ""
    lineas = [
        f"<b>{header}</b>",
        f"<b>{titulo[:130]}</b>",
        f"Fuente: {fuente}",
    ]
    if empresa and empresa != fuente:
        lineas.append(f"Empresa: {empresa[:80]}")
    if puntaje > 0:
        lineas.append(f"Compatibilidad: {puntaje}/10 [{barra}]")
    if porque:
        lineas.append(f"IA: {porque[:200]}")
    if ubicacion:
        lineas.append(f"Ubicacion: {ubicacion}")
    if turno and turno != "No especifica":
        lineas.append(f"TURNO: {turno}")
    else:
        lineas.append("Turno: no especificado")
    if sueldo and sueldo != "No especifica":
        lineas.append(f"Sueldo: {sueldo}")
    if beneficios and beneficios != "No especifica":
        lineas.append(f"Beneficios: {beneficios[:100]}")
    if link:
        lineas.append(f"Link: {link[:300]}")
    return "\n".join(lineas)

# ─────────────────────────────────────────
# FUNCION CENTRAL
# ─────────────────────────────────────────
def procesar_aviso(fuente, titulo, empresa, ubicacion_extra, link, vistos, cartas):
    if not cumple_basico(titulo) or len(titulo) < 8: return 0
    hid = hash_aviso(titulo, link or "")
    if hid in vistos: return 0

    nivel_n  = nivel_match(titulo)
    ubicacion = detectar_ubicacion(titulo) or ubicacion_extra
    turno_kw  = detectar_turno(titulo)
    urgente   = es_prioritaria(f"{titulo} {empresa or ''} {fuente}")

    puntaje, porque, turno, sueldo, carta, beneficios = (
        0, "", turno_kw or "No especifica", "No especifica", "", "No especifica"
    )

    if nivel_n >= 2 and IA_ACTIVA:
        print(f"    IA analizando: {titulo[:55]}...")
        texto_aviso = obtener_texto_aviso(link) if link else ""
        puntaje, porque, turno_ia, sueldo, carta, beneficios = analizar_con_gemini(
            titulo, empresa or fuente, link, texto_aviso
        )
        if turno_ia and turno_ia != "No especifica":
            turno = turno_ia
        if puntaje < 4:
            print(f"    Descartado (puntaje {puntaje}/10)")
            vistos.add(hid)
            return 0
        time.sleep(2)
    elif nivel_n == 1:
        puntaje = 4
    else:
        puntaje = 5

    tiene_carta = bool(carta and len(carta) > 20)
    if tiene_carta:
        cartas[hid] = {
            "titulo": titulo,
            "empresa": empresa or fuente,
            "carta": carta,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
        }

    msg = formato_mensaje(fuente, titulo, empresa, ubicacion, turno, sueldo,
                          beneficios, link, nivel_n, puntaje, porque, urgente)
    enviar_telegram(msg, reply_markup=botones_aviso(hid, tiene_carta))
    vistos.add(hid)
    return 1

# ─────────────────────────────────────────
# SCRAPERS TIPO A: portales HTML
# ─────────────────────────────────────────
def scrape_portal(nombre, urls, base_url, vistos, cartas):
    print(f"\n{nombre}...")
    n = 0
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
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
                    n += procesar_aviso(nombre, titulo, empresa,
                                        detectar_ubicacion(txt), link or url, vistos, cartas)
            else:
                for a in soup.find_all("a", href=True):
                    titulo = a.get_text(strip=True)
                    link   = a["href"]
                    if not link.startswith("http"):
                        link = base_url.rstrip("/") + "/" + link.lstrip("/")
                    n += procesar_aviso(nombre, titulo, None, None, link, vistos, cartas)
            time.sleep(2)
        except Exception as e:
            print(f"  Error {nombre}: {e}")
    print(f"  {n} nuevos")
    return n

# ─────────────────────────────────────────
# SCRAPER TIPO B: Indeed por query
# ─────────────────────────────────────────
def scrape_indeed(query, nombre, ubicacion="Chile", vistos=None, cartas=None):
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
            empresa = e.get_text(strip=True) if e else nombre
            jk   = card.get("data-jk","")
            link = f"https://cl.indeed.com/viewjob?jk={jk}" if jk else url
            u = card.find(class_=re.compile(r"location|companyLocation", re.I))
            ub = u.get_text(strip=True) if u else None
            n += procesar_aviso(nombre, titulo, empresa, ub, link, vistos, cartas)
        time.sleep(2)
    except Exception as e:
        print(f"  Error Indeed ({nombre}): {e}")
    return n

# ─────────────────────────────────────────
# SCRAPER TIPO C: Computrabajo por empresa
# ─────────────────────────────────────────
def scrape_ct(nombre, slug, vistos, cartas):
    url = f"https://www.computrabajo.cl/trabajos-de-{slug}"
    n = 0
    try:
        r = requests.get(url, headers=HEADERS, timeout=18)
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.find_all("article", class_=re.compile(r"box_offer|offer", re.I)):
            t = (card.find("a", class_=re.compile(r"js-o-link|title", re.I))
                 or card.find(["h2","h3"]))
            titulo = t.get_text(strip=True) if t else ""
            l = card.find("a", href=True)
            link = l["href"] if l else url
            if link and not link.startswith("http"):
                link = "https://www.computrabajo.cl" + link
            e = card.find(class_=re.compile(r"company|empresa", re.I))
            empresa = e.get_text(strip=True) if e else nombre
            desc = card.find("p")
            ub = detectar_ubicacion(desc.get_text() if desc else card.get_text())
            n += procesar_aviso(nombre, titulo, empresa, ub, link, vistos, cartas)
        time.sleep(2)
    except Exception as e:
        print(f"  Error CT ({nombre}): {e}")
    return n

def scrape_empresa(nombre, query_indeed, slug_ct, ubicacion="Chile", vistos=None, cartas=None):
    print(f"\n{nombre}...")
    n  = scrape_indeed(query_indeed, nombre, ubicacion, vistos, cartas)
    n += scrape_ct(nombre, slug_ct, vistos, cartas)
    print(f"  {n} nuevos")
    return n

# ─────────────────────────────────────────
# BLOQUE 1: Portales especializados mineria
# ─────────────────────────────────────────
def s_trabajoenmineria(v,c): return scrape_portal("TrabajoenMineria.cl",
    ["https://www.trabajoenmineria.cl/ofertas",
     "https://www.trabajoenmineria.cl/ofertas?area=mantenimiento",
     "https://www.trabajoenmineria.cl/ofertas?area=ingenieria"],
    "https://www.trabajoenmineria.cl", v, c)

def s_mineria_cl(v,c): return scrape_portal("Mineria.cl",
    ["https://www.mineria.cl/empleos/"], "https://www.mineria.cl", v, c)

def s_expertominero(v,c): return scrape_portal("ExpertoMinero.cl",
    ["https://www.expertominero.cl/empleos/"], "https://www.expertominero.cl", v, c)

def s_minerosonline(v,c): return scrape_portal("MinerosOnline",
    ["https://www.minerosonline.com/empleos/"], "https://www.minerosonline.com", v, c)

def s_reclutamineria(v,c): return scrape_portal("ReclutaMineria.cl",
    ["https://www.reclutamineria.cl/empleos/"], "https://www.reclutamineria.cl", v, c)

def s_mining_people(v,c): return scrape_portal("Mining People Intl.",
    ["https://www.miningpeople.com.au/jobs?location=Chile"],
    "https://www.miningpeople.com.au", v, c)

def s_queries_cargo(v,c):
    print("\nIndeed - busquedas por cargo...")
    queries = [
        ("administrador contrato mineria", "Chile"),
        ("supervisor mantencion mineria", "Antofagasta Chile"),
        ("jefe mantenimiento mineria", "Chile"),
        ("planner planificador mineria", "Chile"),
        ("facility manager campamento faena", "Chile"),
        ("ingeniero confiabilidad mineria", "Chile"),
        ("administrador campamento mineria", "Chile"),
        ("coordinador contratos mineria", "Chile"),
        ("superintendente mantenimiento mineria", "Chile"),
    ]
    n = sum(scrape_indeed(q, f"Indeed-cargo", loc, v, c) for q, loc in queries)
    print(f"  {n} nuevos total")
    return n

# ─────────────────────────────────────────
# BLOQUE 2: Portales generales
# ─────────────────────────────────────────
def s_trabajando(v,c): return scrape_portal("Trabajando.cl",
    ["https://www.trabajando.cl/trabajos-mineria",
     "https://www.trabajando.cl/trabajos-mantenimiento-industrial",
     "https://www.trabajando.cl/trabajos-administrador-de-contrato",
     "https://www.trabajando.cl/trabajos-ingeniero-industrial"],
    "https://www.trabajando.cl", v, c)

def s_laborum(v,c): return scrape_portal("Laborum.cl",
    ["https://www.laborum.cl/empleos/mineria",
     "https://www.laborum.cl/empleos/mantenimiento-industrial",
     "https://www.laborum.cl/empleos/administracion-contratos"],
    "https://www.laborum.cl", v, c)

def s_computrabajo(v,c): return scrape_portal("Computrabajo.cl",
    ["https://www.computrabajo.cl/trabajos-de-mineria",
     "https://www.computrabajo.cl/trabajos-de-mantenimiento-industrial",
     "https://www.computrabajo.cl/trabajos-de-administracion-de-contratos"],
    "https://www.computrabajo.cl", v, c)

def s_linkedin(v,c):
    print("\nLinkedIn Jobs...")
    n = 0
    queries = [
        ("administrador%20contrato%20mineria","Antofagasta%2C%20Chile"),
        ("supervisor%20mantencion%20mineria","Antofagasta%2C%20Chile"),
        ("jefe%20mantenimiento%20mineria","Calama%2C%20Chile"),
        ("planner%20mineria","Chile"),
        ("facility%20manager%20campamento%20mineria","Chile"),
        ("superintendente%20mantenimiento%20mineria","Chile"),
    ]
    for q, loc in queries:
        url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}&f_TPR=r2592000&sortBy=DD"
        try:
            r = requests.get(url, headers=HEADERS, timeout=18)
            soup = BeautifulSoup(r.text, "html.parser")
            for card in soup.find_all("div", class_=re.compile(r"base-card|job-search-card", re.I)):
                t = card.find(["h3","h4"])
                titulo = t.get_text(strip=True) if t else ""
                l = card.find("a", href=True)
                link = l["href"].split("?")[0] if l else url
                e = card.find(class_=re.compile(r"base-search-card__subtitle", re.I))
                empresa = e.get_text(strip=True) if e else None
                u = card.find(class_=re.compile(r"base-search-card__metadata", re.I))
                ub = u.get_text(strip=True) if u else None
                n += procesar_aviso("LinkedIn", titulo, empresa, ub, link, v, c)
            time.sleep(3)
        except Exception as e:
            print(f"  LinkedIn error: {e}")
    print(f"  {n} nuevos"); return n

def s_bne(v,c): return scrape_portal("BNE Chile",
    ["https://www.bne.cl/empleos?q=administrador+contrato+mineria",
     "https://www.bne.cl/empleos?q=supervisor+mantencion+mineria",
     "https://www.bne.cl/empleos?q=jefe+mantenimiento+mineria"],
    "https://www.bne.cl", v, c)

def s_portalempleo(v,c): return scrape_portal("PortalEmpleo.cl",
    ["https://www.portalempleo.cl/trabajo/mineria/",
     "https://www.portalempleo.cl/trabajo/mantenimiento-industrial/"],
    "https://www.portalempleo.cl", v, c)

def s_adecco(v,c): return scrape_portal("Adecco Chile",
    ["https://www.adecco.cl/empleos/?sector=mineria",
     "https://www.adecco.cl/empleos/?sector=mantenimiento"],
    "https://www.adecco.cl", v, c)

def s_manpower(v,c): return scrape_portal("ManpowerGroup Chile",
    ["https://www.manpower.cl/empleos?q=mineria+mantenimiento",
     "https://www.manpower.cl/empleos?q=administrador+contrato+mineria"],
    "https://www.manpower.cl", v, c)

# ─────────────────────────────────────────
# BLOQUE 3: Mineras directas
# ─────────────────────────────────────────
def s_codelco(v,c): return scrape_empresa("Codelco",
    "codelco supervisor ingeniero administrador contrato","codelco","Chile",v,c)

def s_bhp(v,c): return scrape_empresa("BHP / Escondida",
    "bhp escondida spence supervisor ingeniero","bhp","Antofagasta Chile",v,c)

def s_collahuasi(v,c): return scrape_empresa("Collahuasi",
    "collahuasi supervisor ingeniero planificador contrato","collahuasi","Iquique Chile",v,c)

def s_aminerals(v,c):
    print("\nAntofagasta Minerals...")
    n  = scrape_indeed("pelambres centinela zaldivar supervisor ingeniero","Pelambres/Centinela","Antofagasta Chile",v,c)
    n += scrape_ct("Minera Los Pelambres","minera-los-pelambres",v,c)
    n += scrape_ct("Minera Centinela","minera-centinela",v,c)
    print(f"  {n} nuevos"); return n

def s_teck(v,c): return scrape_empresa("Teck / QB2",
    "teck quebrada blanca supervisor ingeniero planificador","teck","Chile",v,c)

def s_angloamerican(v,c): return scrape_empresa("Anglo American",
    "anglo american chile supervisor ingeniero contrato","anglo-american","Chile",v,c)

def s_kinross(v,c): return scrape_empresa("Kinross",
    "kinross maricunga supervisor ingeniero","kinross","Atacama Chile",v,c)

def s_sqm(v,c): return scrape_empresa("SQM",
    "sqm litio supervisor ingeniero administrador","sqm","Antofagasta Chile",v,c)

def s_lundin(v,c):
    print("\nLundin / Candelaria...")
    n  = scrape_indeed("candelaria lundin supervisor ingeniero mantencion","Lundin/Candelaria","Atacama Chile",v,c)
    n += scrape_ct("Minera Candelaria","minera-candelaria",v,c)
    print(f"  {n} nuevos"); return n

def s_cap(v,c): return scrape_empresa("CAP Mineria",
    "cap mineria supervisor ingeniero mantencion","cap-mineria","Atacama Chile",v,c)

def s_agnico(v,c): return scrape_empresa("Agnico Eagle",
    "agnico eagle chile supervisor ingeniero","agnico-eagle","Chile",v,c)

def s_goldfields(v,c): return scrape_empresa("Gold Fields / Salares Norte",
    "gold fields salares norte supervisor ingeniero","gold-fields","Atacama Chile",v,c)

def s_sierragorda(v,c): return scrape_empresa("Sierra Gorda SCM",
    "sierra gorda scm supervisor ingeniero","sierra-gorda-scm","Antofagasta Chile",v,c)

def s_lithium(v,c): return scrape_empresa("Lithium Americas",
    "lithium americas rincon supervisor ingeniero","lithium-americas","Antofagasta Chile",v,c)

# ─────────────────────────────────────────
# BLOQUE 4: Campamentos / Servicios
# ─────────────────────────────────────────
def s_compass(v,c):
    print("\nCompass Group...")
    n  = scrape_indeed("compass group supervisor administrador campamento","Compass Group","Chile",v,c)
    n += scrape_ct("Compass Group","compass-group",v,c)
    print(f"  {n} nuevos"); return n

def s_sodexo(v,c):
    print("\nSodexo Chile...")
    n  = scrape_indeed("sodexo supervisor administrador campamento mineria","Sodexo","Chile",v,c)
    n += scrape_ct("Sodexo","sodexo",v,c)
    print(f"  {n} nuevos"); return n

def s_aramark(v,c):
    print("\nAramark Chile...")
    n  = scrape_indeed("aramark supervisor administrador campamento chile","Aramark","Chile",v,c)
    n += scrape_ct("Aramark","aramark",v,c)
    print(f"  {n} nuevos"); return n

def s_eurest(v,c): return scrape_empresa("Eurest Chile",
    "eurest supervisor administrador campamento","eurest","Chile",v,c)

# ─────────────────────────────────────────
# BLOQUE 5: Ingenieria / EPC
# ─────────────────────────────────────────
def s_fluor(v,c):   return scrape_empresa("Fluor Chile","fluor chile ingeniero supervisor mineria","fluor","Chile",v,c)
def s_worley(v,c):  return scrape_empresa("Worley Chile","worley chile ingeniero supervisor mineria","worley","Chile",v,c)
def s_wood(v,c):    return scrape_empresa("Wood Group Chile","wood group chile ingeniero supervisor","wood-group","Chile",v,c)
def s_techint(v,c): return scrape_empresa("Techint Chile","techint chile supervisor ingeniero mantencion","techint","Chile",v,c)
def s_maserr(v,c):  return scrape_empresa("MAS Errazuriz","mas errazuriz supervisor ingeniero mantencion","mas-errazuriz","Chile",v,c)

def s_sk(v,c):
    print("\nSigdo Koppers...")
    n  = scrape_indeed("sigdo koppers sk supervisor ingeniero mineria","Sigdo Koppers","Chile",v,c)
    n += scrape_ct("Sigdo Koppers","sigdo-koppers",v,c)
    n += scrape_indeed("enaex magotteaux skc supervisor ingeniero","SK Filiales","Chile",v,c)
    print(f"  {n} nuevos"); return n

def s_salfa(v,c):  return scrape_empresa("Salfacorp","salfacorp salfa supervisor ingeniero mantencion","salfacorp","Chile",v,c)
def s_vesco(v,c):
    print("\nVesco Consultores...")
    n  = scrape_portal("Vesco",["https://www.vesco.cl/empleo/"],"https://www.vesco.cl",v,c)
    n += scrape_indeed("vesco supervisor ingeniero mineria","Vesco","Chile",v,c)
    print(f"  {n} nuevos"); return n

# ─────────────────────────────────────────
# BLOQUE 6: OEM / Equipos
# ─────────────────────────────────────────
def s_komatsu(v,c):  return scrape_empresa("Komatsu Chile","komatsu chile supervisor ingeniero mantencion","komatsu","Chile",v,c)
def s_finning(v,c):  return scrape_empresa("Finning / Caterpillar","finning caterpillar chile supervisor ingeniero","finning","Chile",v,c)
def s_sandvik(v,c):  return scrape_empresa("Sandvik Chile","sandvik chile supervisor ingeniero mantencion","sandvik","Chile",v,c)
def s_epiroc(v,c):   return scrape_empresa("Epiroc Chile","epiroc chile supervisor ingeniero mantencion","epiroc","Chile",v,c)
def s_metso(v,c):    return scrape_empresa("Metso Outotec","metso outotec chile supervisor ingeniero","metso-outotec","Chile",v,c)
def s_weir(v,c):     return scrape_empresa("Weir Minerals","weir minerals chile supervisor ingeniero","weir-minerals","Chile",v,c)
def s_flsmidth(v,c): return scrape_empresa("FLSmidth Chile","flsmidth chile supervisor ingeniero","flsmidth","Chile",v,c)

# ─────────────────────────────────────────
# BLOQUE 7: RRHH / Inspeccion
# ─────────────────────────────────────────
def s_bv(v,c):     return scrape_empresa("Bureau Veritas Chile","bureau veritas chile supervisor ingeniero","bureau-veritas","Chile",v,c)
def s_sgs(v,c):
    print("\nSGS Chile...")
    n  = scrape_indeed("sgs chile supervisor ingeniero mineria","SGS","Chile",v,c)
    n += scrape_ct("SGS","sgs",v,c)
    print(f"  {n} nuevos"); return n
def s_confip(v,c): return scrape_empresa("Confipetrol","confipetrol supervisor ingeniero mantencion","confipetrol","Chile",v,c)
def s_hays(v,c):
    print("\nHays Chile...")
    n  = scrape_indeed("hays chile supervisor ingeniero mineria","Hays","Chile",v,c)
    n += scrape_ct("Hays","hays",v,c)
    print(f"  {n} nuevos"); return n
def s_randstad(v,c):
    print("\nRandstad Chile...")
    n  = scrape_indeed("randstad chile supervisor ingeniero mineria","Randstad","Chile",v,c)
    n += scrape_ct("Randstad","randstad",v,c)
    print(f"  {n} nuevos"); return n

# ─────────────────────────────────────────
# LISTA MAESTRA DE FUENTES
# ─────────────────────────────────────────
FUENTES = [
    s_trabajoenmineria, s_mineria_cl, s_expertominero,
    s_minerosonline, s_reclutamineria, s_mining_people, s_queries_cargo,
    s_trabajando, s_laborum, s_computrabajo,
    s_linkedin, s_bne, s_portalempleo, s_adecco, s_manpower,
    s_codelco, s_bhp, s_collahuasi, s_aminerals,
    s_teck, s_angloamerican, s_kinross, s_sqm,
    s_lundin, s_cap, s_agnico, s_goldfields, s_sierragorda, s_lithium,
    s_compass, s_sodexo, s_aramark, s_eurest,
    s_fluor, s_worley, s_wood, s_techint,
    s_maserr, s_sk, s_salfa, s_vesco,
    s_komatsu, s_finning, s_sandvik, s_epiroc,
    s_metso, s_weir, s_flsmidth,
    s_bv, s_sgs, s_confip, s_hays, s_randstad,
]

# ─────────────────────────────────────────
# EJECUCION PRINCIPAL
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("      RADAR MINERO V15 ULTIMATE")
    print(f"      {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"      IA: {'Gemini activo' if IA_ACTIVA else 'Modo keywords'}")
    print("=" * 55)

    vistos = cargar_vistos()
    cartas = cargar_cartas()
    N      = len(FUENTES)

    print(f"\nHistorial: {len(vistos)} avisos | Cartas: {len(cartas)}")

    enviar_telegram(
        f"<b>RADAR MINERO V15 ULTIMATE</b>\n"
        f"Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"Fuentes: <b>{N}</b>\n"
        f"IA: {'Gemini activo' if IA_ACTIVA else 'Modo keywords'}\n"
        f"Historial: {len(vistos)} avisos procesados"
    )

    total = 0
    for i, fn in enumerate(FUENTES, 1):
        print(f"\n[{i}/{N}]", end="")
        total += fn(vistos, cartas)

    guardar_vistos(vistos)
    guardar_cartas(cartas)

    print(f"\n{'='*55}")
    print(f"  NUEVOS: {total} | FUENTES: {N} | CARTAS: {len(cartas)}")
    print(f"{'='*55}")

    enviar_telegram(
        f"{'Busqueda completada' if total > 0 else 'Sin novedades'}\n"
        f"Nuevos: <b>{total}</b> aviso(s)\n"
        f"Cartas generadas: {len(cartas)}\n"
        f"Fuentes: {N}\n"
        f"{'Revisa los avisos de arriba' if total > 0 else 'Proxima busqueda en 6 horas'}\n"
        f"Usa /carta en el bot para ver cartas de presentacion"
    )
