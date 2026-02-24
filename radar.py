import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib
from datetime import datetime
import google.generativeai as genai

# =====================================================
#  1. CONFIGURACIÓN (Secrets)
# =====================================================
TOKEN     = os.environ.get("TOKEN")
CHAT_ID   = os.environ.get("CHAT_ID")
API_KEY   = os.environ.get("GEMINI_KEY")

try:
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    IA_ACTIVA = True
except:
    IA_ACTIVA = False

SEEN_FILE = "seen_jobs.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

# =====================================================
#  2. LISTA DE EMPRESAS Y CARGOS (Fuentes Reales)
# =====================================================
EMPRESAS_OBJETIVO = [
    "Codelco", "BHP", "Antofagasta Minerals", "Finning", "Komatsu", 
    "Newrest", "Sodexo", "Aramark", "Metso", "Kinross", "Teck", "Albemarle",
    "Sigdo Koppers", "Salfacorp", "Techint", "Bechtel", "Worley"
]

# =====================================================
#  3. EL MOTOR DE INTELIGENCIA (Gemini)
# =====================================================
def analizar_con_ia(titulo, empresa, descripcion):
    if not IA_ACTIVA: return True, "Revisión Manual", "N/A"
    
    prompt = (
        f"Analiza este aviso: '{titulo}' en '{empresa}'.\n"
        f"Texto extraido: {descripcion[:500]}\n\n"
        f"Responde SOLO JSON:\n"
        f"{{\"profesional\": true/false, \"turno\": \"ej: 7x7\", \"porque\": \"breve\"}}"
    )
    
    try:
        response = model.generate_content(prompt)
        res = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        return res.get("profesional"), res.get("porque"), res.get("turno")
    except:
        return True, "Error IA (Pasa a revisión)", "Ver link"

# =====================================================
#  4. MENSAJERÍA (Telegram con Botones Reales)
# =====================================================
def enviar_telegram(titulo, empresa, turno, motivo, link, hid):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    mensaje = (
        f"⚒️ <b>NUEVA OPORTUNIDAD MINERA</b>\n\n"
        f"📋 <b>CARGO:</b> {titulo.upper()}\n"
        f"🏢 <b>EMPRESA:</b> {empresa}\n"
        f"⏰ <b>TURNO:</b> {turno}\n"
        f"🤖 <b>IA:</b> {motivo}\n\n"
        f"🔗 <a href='{link}'>POSTULAR AQUÍ</a>"
    )
    
    # Botón de "Visto" que redirige a una confirmación (para que no de error)
    botones = {"inline_keyboard": [[{"text": "✅ Marcar como Visto", "url": "https://t.me/TuBotName?start=visto"}]]}
    
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML", "reply_markup": json.dumps(botones)}
    requests.post(url, json=payload, timeout=10)

# =====================================================
#  5. SCRAPERS (Fuentes que NO bloquean)
# =====================================================
def buscar_en_portales(vistos):
    encontrados = 0
    # Usamos Computrabajo e Indeed como "espejos" de las webs oficiales
    for empresa in EMPRESAS_OBJETIVO:
        print(f"Buscando {empresa}...")
        # Lógica Computrabajo (Es la más estable en Chile)
        slug = empresa.lower().replace(" ", "-")
        url = f"https://www.computrabajo.cl/trabajos-de-{slug}"
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            
            for oferta in soup.find_all("article", class_="box_offer"):
                titulo_tag = oferta.find("a", class_="js-o-link")
                if not titulo_tag: continue
                
                titulo = titulo_tag.get_text(strip=True)
                link = "https://www.computrabajo.cl" + titulo_tag['href']
                descripcion = oferta.find("p").get_text(strip=True) if oferta.find("p") else ""
                
                hid = hashlib.md5(f"{titulo}{empresa}".encode()).hexdigest()
                if hid in vistos: continue
                
                # LA IA ANALIZA EL TEXTO REAL DE LA DESCRIPCIÓN
                es_valido, motivo, turno = analizar_con_ia(titulo, empresa, descripcion)
                
                if es_valido:
                    enviar_telegram(titulo, empresa, turno, motivo, link, hid)
                    vistos.add(hid)
                    encontrados += 1
            
            time.sleep(2) # Respeto al servidor
        except: continue
        
    return encontrados

# =====================================================
#  6. MAIN
# =====================================================
if __name__ == "__main__":
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f: vistos = set(json.load(f))
    else: vistos = set()

    print(f"🚀 Iniciando Radar V14 Pro...")
    nuevos = buscar_en_portales(vistos)
    
    with open(SEEN_FILE, "w") as f: json.dump(list(vistos), f)
    print(f"✅ Finalizado. Nuevos: {nuevos}")
