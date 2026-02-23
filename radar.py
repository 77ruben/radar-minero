import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re, random
from datetime import datetime
import google.generativeai as genai

# =====================================================
#  1. CONFIGURACIÓN Y SECRETOS
# =====================================================
TOKEN     = os.environ.get("TOKEN")
CHAT_ID   = os.environ.get("CHAT_ID")
API_KEY   = os.environ.get("GEMINI_KEY")

# Configuración de IA
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    IA_ACTIVA = True
except:
    IA_ACTIVA = False

SEEN_FILE = "seen_jobs.json"

# Cabeceras para parecer un navegador real y evitar bloqueos
HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0"}
]

# =====================================================
#  2. FILTROS Y PALABRAS CLAVE
# =====================================================
KEYWORDS_BUSQUEDA = [
    "administrador contrato", "supervisor", "jefe turno", 
    "planner", "planificador", "ingeniero", "superintendente", 
    "facility manager", "jefe campamento", "project manager",
    "confiabilidad", "mantencion", "mantenimiento"
]

TURNOS_PRIORITARIOS = ["14x14", "7x7", "4x3", "10x10", "5x2"]

# =====================================================
#  3. FUNCIONES DE INTELIGENCIA ARTIFICIAL
# =====================================================
def analizar_con_ia(titulo, empresa, fuente):
    if not IA_ACTIVA:
        return True, "Modo Manual (Sin IA)", "N/A"
    
    # Prompt optimizado para ahorrar tokens y ser preciso
    prompt = (
        f"Analiza este empleo minero en Chile:\n"
        f"Cargo: {titulo}\nEmpresa: {empresa}\nFuente: {fuente}\n\n"
        f"Reglas:\n"
        f"1. BUSCO: Cargos Profesionales, Jefaturas, Supervisores, Ingenieros, Planners, Adm. Contratos.\n"
        f"2. DESCARTA: Operarios base, Choferes, Aseo, Guardias, Prácticas, Vendedores.\n"
        f"3. DETECTA: Turnos (14x14, 7x7, etc).\n\n"
        f"Responde SOLO JSON: {{\"valido\": true/false, \"motivo\": \"texto breve\", \"turno\": \"texto\"}}"
    )
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data.get("valido", False), data.get("motivo", "N/A"), data.get("turno", "No especificado")
    except:
        return True, "Error IA (Paso preventivo)", "N/A"

# =====================================================
#  4. FUNCIONES DEL SISTEMA
# =====================================================
def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def guardar_vistos(vistos):
    with open(SEEN_FILE, "w") as f: json.dump(list(vistos), f)

def enviar_telegram(msg, hid):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    botones = {"inline_keyboard": [[{"text": "✅ Visto", "callback_data": f"v:{hid}"}]]}
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "reply_markup": json.dumps(botones), "disable_web_page_preview": True}
    try: requests.post(url, json=data, timeout=10)
    except: pass

def hash_aviso(titulo, empresa):
    return hashlib.md5(f"{titulo}{empresa}".encode()).hexdigest()

def procesar_aviso(fuente, titulo, empresa, link, vistos):
    # Filtro básico de longitud y palabras prohibidas obvias antes de la IA
    if len(titulo) < 5: return 0
    if any(x in titulo.lower() for x in ["chofer", "auxiliar", "aseo", "guardia"]): return 0
    
    hid = hash_aviso(titulo, empresa)
    if hid in vistos: return 0

    valido, motivo, turno = analizar_con_ia(titulo, empresa, fuente)
    
    if valido:
        icon = "💎" if "14x14" in str(turno) or "7x7" in str(turno) else "🔔"
        msg = (
            f"{icon} <b>RADAR MINERO: NUEVO AVISO</b>\n\n"
            f"📋 <b>{titulo}</b>\n"
            f"🏢 {empresa}\n"
            f"⏰ Turno: {turno}\n"
            f"🤖 <i>{motivo}</i>\n\n"
            f"🔗 <a href='{link}'>VER VACANTE</a>\n"
            f"📍 {fuente}"
        )
        enviar_telegram(msg, hid)
        vistos.add(hid)
        print(f"   -> Enviado: {titulo}")
        return 1
    return 0

# =====================================================
#  5. MOTORES DE BÚSQUEDA (SCRAPERS)
# =====================================================

def get_soup(url):
    try:
        h = random.choice(HEADERS_LIST)
        r = requests.get(url, headers=h, timeout=20)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except: pass
    return None

# --- MOTOR A: Scraper Directo de Sitios Corporativos ---
def scrape_sitios_directos(vistos):
    print("\n🌍 Escaneando Sitios Corporativos...")
    count = 0
    
    # Lista maestra de tus links + lógica de paginación simple
    targets = [
        ("Codelco", "https://empleos.codelco.cl/search/?q=&q2=&alertId=&locationsearch=&title=&location=Chile&date="),
        ("BHP", "https://careers.bhp.com/search/?q=&locationsearch=Chile"),
        ("Kinross", "https://jobs.kinross.com/search/?q=&locationsearch=Chile"),
        ("Epiroc", "https://www.careerprofile.epiroc.com/search/?q=&locationsearch=Chile"),
        ("Bechtel", "https://jobs.bechtel.com/search/?q=&locationsearch=Chile"),
        ("Teck", "https://jobs.teck.com/search/?q=&locationsearch=Chile"),
        ("Antofagasta Minerals", "https://career8.successfactors.com/career?company=AMSAP&locationsearch=Chile"),
        ("Komatsu", "https://komatsu.trabajando.cl/trabajo-empleo")
    ]

    for nombre, url_base in targets:
        print(f"   Analizando {nombre}...")
        soup = get_soup(url_base)
        if not soup:
            # Si falla el directo (por bloqueo), activamos Plan B en Indeed
            print(f"   ⚠️ {nombre} bloqueado/JS -> Activando Plan B (Indeed)")
            count += scrape_indeed_fallback(nombre, vistos)
            continue
            
        # Intentamos extraer links de tablas estándar
        found_in_site = 0
        links = soup.find_all("a", href=True)
        for a in links:
            url_job = a['href']
            txt = a.get_text(strip=True)
            
            # Limpieza y validación de links
            if len(txt) > 10 and not "javascript" in url_job:
                if not url_job.startswith("http"):
                    # Reconstruir url relativa
                    base_domain = "/".join(url_base.split("/")[:3])
                    url_job = base_domain + url_job if url_job.startswith("/") else base_domain + "/" + url_job
                
                # Verificar si parece un trabajo
                if any(kw in txt.lower() for kw in ["ingeniero", "jefe", "supervisor", "admin", "planner", "técnico"]):
                    found_in_site += procesar_aviso(f"Web {nombre}", txt, nombre, url_job, vistos)
        
        if found_in_site == 0:
            # Si no encontró nada (posiblemente por carga dinámica JS), usar fallback
            count += scrape_indeed_fallback(nombre, vistos)
        else:
            count += found_in_site
            
    return count

# --- MOTOR B: Fallback (Plan B) en Indeed/Computrabajo ---
def scrape_indeed_fallback(empresa_nombre, vistos):
    # Busca la empresa específica en portales públicos si el sitio oficial falla
    c = 0
    # Indeed Query
    q_url = f"https://cl.indeed.com/jobs?q={empresa_nombre}&l=Chile&sort=date"
    soup = get_soup(q_url)
    if soup:
        for card in soup.find_all("div", class_="job_seen_beacon"):
            try:
                t = card.find("h2").get_text(strip=True)
                l = "https://cl.indeed.com" + card.find("a")['href']
                c += procesar_aviso("Indeed-Respaldo", t, empresa_nombre, l, vistos)
            except: pass
            
    # Computrabajo Query (Muy efectivo para empresas de servicios)
    slug = empresa_nombre.lower().replace(" ", "-")
    ct_url = f"https://www.computrabajo.cl/trabajos-de-{slug}"
    soup_ct = get_soup(ct_url)
    if soup_ct:
        for art in soup_ct.find_all("article", class_="box_offer"):
            try:
                t = art.find("h2").get_text(strip=True)
                l = art.find("a")['href']
                if not l.startswith("http"): l = "https://www.computrabajo.cl" + l
                c += procesar_aviso("Computrabajo-Respaldo", t, empresa_nombre, l, vistos)
            except: pass
    return c

# --- MOTOR C: Búsqueda General (El radar original) ---
def scrape_general(vistos):
    print("\n🔍 Escaneando Portales Generales...")
    count = 0
    # Búsquedas combinadas en Indeed
    queries = [
        "administrador contrato mineria", 
        "jefe turno mineria", 
        "planner mantenimiento 7x7",
        "newrest", "sodexo", "aramark", # Servicios
        "finning", "metso", "sandvik"   # OEM
    ]
    
    for q in queries:
        url = f"https://cl.indeed.com/jobs?q={q.replace(' ','+')}&l=Chile&sort=date"
        soup = get_soup(url)
        if soup:
            for card in soup.find_all("td", class_="resultContent"):
                try:
                    title = card.find("h2").get_text(strip=True)
                    company = card.find("span", attrs={"data-testid":"company-name"}).get_text(strip=True)
                    link = "https://cl.indeed.com" + card.find("a")['href']
                    count += procesar_aviso("Indeed General", title, company, link, vistos)
                except: pass
        time.sleep(2)
    return count

# =====================================================
#  6. EJECUCIÓN PRINCIPAL
# =====================================================
if __name__ == "__main__":
    print(f"🚀 RADAR MINERO V11 - INICIO: {datetime.now().strftime('%H:%M')}")
    vistos = cargar_vistos()
    
    nuevos = 0
    nuevos += scrape_sitios_directos(vistos) # Intenta tus links primero
    nuevos += scrape_general(vistos)         # Barre el resto del mercado
    
    guardar_vistos(vistos)
    print(f"✅ FIN DEL PROCESO. Nuevos avisos enviados: {nuevos}")
