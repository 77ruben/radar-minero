import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re
from datetime import datetime
import google.generativeai as genai

# =====================================================
#  1. CONFIGURACIÓN DE SEGURIDAD (GitHub Secrets)
# =====================================================
TOKEN     = os.environ.get("TOKEN")
CHAT_ID   = os.environ.get("CHAT_ID")
API_KEY   = os.environ.get("GEMINI_KEY")

# Configuración IA
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    IA_ACTIVA = True
except:
    IA_ACTIVA = False

# =====================================================
#  2. PARÁMETROS DE BÚSQUEDA
# =====================================================
SEEN_FILE = "seen_jobs.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

# Palabras clave para la búsqueda inicial (antes de pasar por la IA)
KEYWORDS_BUSQUEDA = [
    "administrador contrato", "supervisor mantenimiento", "ingeniero mineria",
    "planner mantenimiento", "jefe turno", "facility manager", "jefe campamento",
    "planificador", "ingeniero confiabilidad", "jefe proyecto minero"
]

# =====================================================
#  3. LÓGICA DE FILTRADO CON IA
# =====================================================
def analizar_con_ia(titulo, empresa, fuente):
    if not IA_ACTIVA:
        return True, "Modo manual (IA apagada)", "No detectado"
    
    prompt = (
        f"Eres un experto en reclutamiento para la gran minería en Chile.\n"
        f"Analiza este aviso: '{titulo}' en la empresa '{empresa}' (Fuente: {fuente}).\n\n"
        f"Criterios:\n"
        f"1. Acepta solo cargos profesionales o de mando: Ingenieros, Jefes, Supervisores, Planners, Administradores.\n"
        f"2. Rechaza cargos operativos básicos: Choferes, Cocineros, Guardias, Operarios, Prácticas.\n"
        f"3. Detecta turnos como 14x14, 7x7, 4x3, 10x10.\n\n"
        f"Responde estrictamente en JSON:\n"
        f"{{\"valido\": true/false, \"motivo\": \"breve explicacion\", \"turno\": \"turno detectado o N/A\"}}"
    )
    
    try:
        response = model.generate_content(prompt)
        # Limpiar respuesta por si la IA agrega markdown
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw_text)
        return data.get("valido"), data.get("motivo"), data.get("turno")
    except:
        return True, "Error IA - Pasa a revisión manual", "N/A"

# =====================================================
#  4. FUNCIONES DE SISTEMA
# =====================================================
def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f: return set(json.load(f))
    return set()

def guardar_vistos(vistos):
    with open(SEEN_FILE, "w") as f: json.dump(list(vistos), f)

def enviar_telegram(msg, hid):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    botones = {"inline_keyboard": [[{"text": "✅ Marcar Visto", "callback_data": f"v:{hid}"}]]}
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "reply_markup": json.dumps(botones), "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
        time.sleep(1.5) # Evitar spam-bloqueo de Telegram
    except: pass

def hash_aviso(titulo, empresa):
    return hashlib.md5(f"{titulo.lower()}{empresa.lower()}".encode()).hexdigest()

# =====================================================
#  5. MOTORES DE SCRAPING (FUENTES ADAPTATIVAS)
# =====================================================

def procesar_y_enviar(fuente, titulo, empresa, link, vistos):
    if len(titulo) < 7: return 0
    hid = hash_aviso(titulo, empresa)
    if hid in vistos: return 0

    valido, motivo, turno = analizar_con_ia(titulo, empresa, fuente)
    
    if valido:
        msg = (
            f"🚀 <b>RADAR IA: OPORTUNIDAD ENCONTRADA</b>\n\n"
            f"📋 <b>Cargo:</b> {titulo.upper()}\n"
            f"🏢 <b>Empresa:</b> {empresa}\n"
            f"⏰ <b>Turno Detectado:</b> {turno}\n"
            f"🤖 <b>Análisis IA:</b> <i>{motivo}</i>\n\n"
            f"🔗 <a href='{link}'>VER AVISO Y POSTULAR</a>\n"
            f"📍 Fuente: {fuente}"
        )
        enviar_telegram(msg, hid)
        vistos.add(hid)
        return 1
    return 0

# --- SCRAPER DE PORTALES (INDEED / COMPUTRABAJO) ---
def scrape_portales(vistos):
    total = 0
    # Agrupamos búsquedas por palabras clave
    for kw in KEYWORDS_BUSQUEDA:
        print(f"🔍 Buscando en Portales: {kw}...")
        # Indeed Chile
        url_in = f"https://cl.indeed.com/jobs?q={kw.replace(' ', '+')}&l=Chile&sort=date"
        try:
            r = requests.get(url_in, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for job in soup.find_all("div", class_="job_seen_beacon")[:8]:
                titulo = job.find("h2").get_text(strip=True)
                empresa = job.find("span", attrs={"data-testid": "company-name"}).get_text(strip=True)
                link = "https://cl.indeed.com" + job.find("a")['href']
                total += procesar_y_enviar("Indeed", titulo, empresa, link, vistos)
        except: pass
    return total

# --- SCRAPER DE EMPRESAS ESPECÍFICAS (VIA COMPUTRABAJO/DIRECTO) ---
def scrape_empresas_especificas(vistos):
    total = 0
    # Lista de slugs para Computrabajo (más estable para scraping)
    # Incluye Mineras, Newrest, Servicios e Ingeniería
    slugs = [
        ("Newrest", "newrest-chile"), ("Sodexo", "sodexo"), ("Aramark", "aramark"),
        ("Codelco", "codelco"), ("BHP", "bhp"), ("Antofagasta Minerals", "antofagasta-minerals"),
        ("Finning", "finning"), ("Komatsu", "komatsu"), ("Metso", "metso-outotec"),
        ("Sigdo Koppers", "sigdo-koppers"), ("Salfacorp", "salfacorp"), ("Belfi", "belfi"),
        ("Techint", "techint"), ("Mas Errazuriz", "mas-errazuriz"), ("SGS", "sgs"),
        ("Bureau Veritas", "bureau-veritas"), ("Applus", "applus-chile"),
        ("Sandvik", "sandvik"), ("Epiroc", "epiroc"), ("Acciona", "acciona")
    ]
    
    for nombre, slug in slugs:
        print(f"🏢 Revisando Empresa: {nombre}...")
        url = f"https://www.computrabajo.cl/trabajos-de-{slug}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            for art in soup.find_all("article", class_="box_offer"):
                t_tag = art.find("h2") or art.find("a", class_="js-o-link")
                titulo = t_tag.get_text(strip=True)
                link = t_tag.find("a")["href"] if t_tag.find("a") else url
                if not link.startswith("http"): link = "https://www.computrabajo.cl" + link
                total += procesar_y_enviar(nombre, titulo, nombre, link, vistos)
        except: pass
    return total

# =====================================================
#  6. EJECUCIÓN PRINCIPAL
# =====================================================
if __name__ == "__main__":
    inicio = datetime.now()
    print(f"🚀 RADAR V10 INICIADO: {inicio.strftime('%H:%M:%S')}")
    
    vistos = cargar_vistos()
    
    encontrados = 0
    encontrados += scrape_portales(vistos)
    encontrados += scrape_empresas_especificas(vistos)
    
    guardar_vistos(vistos)
    
    fin = datetime.now()
    duracion = fin - inicio
    print(f"✅ ESCANEO COMPLETADO. Nuevos: {encontrados} | Duración: {duracion}")

    # Mensaje de resumen opcional a Telegram
    if encontrados == 0:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": "😴 Escaneo finalizado. No hay cargos nuevos que cumplan el perfil profesional hoy."})
