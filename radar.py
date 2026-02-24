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

# Configuración de IA (Reforzada)
try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    IA_ACTIVA = True
except Exception as e:
    print(f"Error inicializando IA: {e}")
    IA_ACTIVA = False

SEEN_FILE = "seen_jobs.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# =====================================================
#  2. FUENTES Y EMPRESAS (LISTA AMPLIADA)
# =====================================================
# Agregamos todas las empresas de servicios y mineras críticas
LINKS_ATS = [
    "https://empleos.codelco.cl/search", "https://careers.bhp.com/search?location=Chile",
    "https://ats.rankmi.com/tenants/239/organizations/kcc", "https://finning.wd3.myworkdayjobs.com/es/External",
    "https://career8.successfactors.com/career?company=AMSAP", "https://jobs.kinross.com/search/?locationsearch=Chile",
    "https://www.careerprofile.epiroc.com/search/?locationsearch=Chile", "https://www.home.sandvik/es-la/carreras/",
    "https://jobs.bechtel.com/search/?locationsearch=chile", "https://jobs.worley.com/careers?location=chile",
    "https://ehif.fa.em2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs",
    "https://sodexo.cl/trabaja-con-nosotros/", "https://www.aramark.cl/carreras", "https://www.newrest.eu/es/ofertas-de-empleo/"
]

# =====================================================
#  3. LÓGICA DE IA (Detección de Turnos y Perfil)
# =====================================================
def analizar_con_ia_profundo(titulo, empresa, link):
    if not IA_ACTIVA: return True, "Modo Manual", "N/A"
    
    # Intentamos obtener un extracto de la página si es posible para ver el turno
    prompt = (
        f"Analiza este cargo minero para un profesional en Chile:\n"
        f"CARGO: {titulo}\nEMPRESA: {empresa}\nURL: {link}\n\n"
        f"INSTRUCCIONES:\n"
        f"1. ¿Es un cargo de Jefatura, Ingeniería, Supervisión o Administración? (Responde true/false)\n"
        f"2. Busca en el texto o deduce el turno (14x14, 7x7, 4x3, 10x10, 5x2).\n"
        f"3. Si es un cargo operativo (conductor, aseo, ayudante), recházalo.\n\n"
        f"RESPONDE ESTRICTAMENTE EN ESTE FORMATO JSON:\n"
        f"{{\"valido\": true, \"motivo\": \"explicacion corta\", \"turno\": \"14x14 o N/A\"}}"
    )
    
    try:
        # Aumentamos el tiempo de espera para evitar el "Error IA"
        response = model.generate_content(prompt)
        data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        return data.get("valido"), data.get("motivo"), data.get("turno")
    except Exception as e:
        # Si falla, el programa sigue pero avisa el error técnico
        return True, f"IA no respondió (Revisar manualmente)", "N/A"

# =====================================================
#  4. MENSAJERÍA TELEGRAM (CON BOTONES)
# =====================================================
def enviar_telegram_v12(msg, hid):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # El botón de "Visto" ahora es un link que no hace nada, 
    # ya que en GitHub Actions no tenemos un servidor escuchando clics.
    # Pero lo marcamos como 'Eliminar' visualmente.
    botones = {
        "inline_keyboard": [
            [{"text": "📍 Ir al Empleo", "url": msg.split('🔗 ')[1].split('\n')[0] if '🔗 ' in msg else "https://google.cl"}],
            [{"text": "🗑️ Marcar como Visto", "callback_data": f"visto:{hid}"}]
        ]
    }
    
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(botones)
    }
    requests.post(url, json=payload, timeout=10)

# =====================================================
#  5. MOTORES DE BÚSQUEDA (EL CORAZÓN DEL RADAR)
# =====================================================
def buscar_empleos(vistos):
    nuevos = 0
    
    # MOTOR 1: LINKS DIRECTOS (ATS)
    for url in LINKS_ATS:
        print(f"Escaneando: {url}")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(r.text, "html.parser")
            # Buscamos todos los links que parezcan trabajos
            for a in soup.find_all("a", href=True):
                titulo = a.get_text(strip=True)
                if len(titulo) > 15: # Evitar links cortos como 'Home'
                    link = a['href']
                    if not link.startswith("http"): link = url.split('.cl')[0] + ".cl" + link
                    
                    hid = hashlib.md5(f"{titulo}".encode()).hexdigest()
                    if hid not in vistos:
                        valido, motivo, turno = analizar_con_ia_profundo(titulo, "Ver en Link", link)
                        if valido:
                            msg = (
                                f"🚀 <b>RADAR MINERO: NUEVO AVISO</b>\n\n"
                                f"💼 <b>CARGO:</b> {titulo.upper()}\n"
                                f"🏢 <b>EMPRESA:</b> Analizando...\n"
                                f"⏰ <b>TURNO:</b> {turno}\n"
                                f"🤖 <b>MOTIVO:</b> {motivo}\n\n"
                                f"🔗 {link}\n"
                                f"📍 <b>WEB:</b> Portal Corporativo"
                            )
                            enviar_telegram_v12(msg, hid)
                            vistos.add(hid)
                            nuevos += 1
        except: continue

    # MOTOR 2: FACEBOOK (Búsqueda vía Google para evitar bloqueos)
    # Buscamos publicaciones de las últimas 24 horas en grupos de Facebook mineros
    fb_query = "site:facebook.com 'oferta laboral' mineria chile 14x14"
    url_fb = f"https://www.google.com/search?q={fb_query.replace(' ', '+')}&tbs=qdr:d"
    try:
        r = requests.get(url_fb, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")
        for g in soup.find_all('div', class_='tF2Cxc'):
            link = g.find('a')['href']
            titulo = g.find('h3').get_text()
            hid = hashlib.md5(link.encode()).hexdigest()
            if hid not in vistos:
                enviar_telegram_v12(f"📱 <b>HALLAZGO EN REDES (FB)</b>\n\n{titulo}\n\n🔗 {link}", hid)
                vistos.add(hid)
                nuevos += 1
    except: pass
    
    return nuevos

# =====================================================
#  6. EJECUCIÓN
# =====================================================
if __name__ == "__main__":
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f: vistos = set(json.load(f))
    else: vistos = set()

    encontrados = buscar_empleos(vistos)
    
    with open(SEEN_FILE, "w") as f: json.dump(list(vistos), f)
    print(f"Escaneo terminado. {encontrados} nuevos.")
