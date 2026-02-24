"""
RADAR MINERO V16 - EDICIÓN CORREGIDA (NUEVA LIBRERÍA GOOGLE)
Autor: Ruben Morales
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib, re
from datetime import datetime
# IMPORTAMOS LA NUEVA LIBRERÍA OFICIAL
from google import genai
from google.genai import types

# ─────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────
TOKEN     = os.environ.get("TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")
# CORRECCION CRITICA: .strip() elimina espacios/saltos de linea que causan el error "Illegal header"
GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()

SEEN_FILE  = "seen_jobs.json"
CARTA_FILE = "cartas_pendientes.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}

# ─────────────────────────────────────────
# PERFIL RUBEN (Contexto para la IA)
# ─────────────────────────────────────────
PERFIL_RUBEN = """
PERFIL: Ruben Morales, Ingeniero Ejecucion Industrial (Mantenimiento/Logistica).
EXP: 15+ años. Supervisor Mantencion (Compass/Centinela), Admin Contrato (Aramark/Teck QB2).
COMPETENCIAS: SAP PM, Licitaciones, Control Costos, Auditor Trinorma.
BUSCA: Admin Contrato, supervisor, Jefe/Supervisor Mantencion, Planner, Facility Manager.
PREFERENCIA: Turnos 14x14, 10x10, 7x7, 4x3. Norte de Chile.
"""

# ─────────────────────────────────────────
# INICIALIZAR NUEVA IA (google-genai)
# ─────────────────────────────────────────
client = None
IA_ACTIVA = False

if GEMINI_KEY:
    try:
        # Inicialización con la nueva sintaxis V1
        client = genai.Client(api_key=GEMINI_KEY)
        IA_ACTIVA = True
        print("✅ Gemini IA (google-genai) activada correctamente")
    except Exception as e:
        print(f"⚠️ Error iniciando Gemini: {e}")

# ─────────────────────────────────────────
# FUNCIONES DE ANALISIS
# ─────────────────────────────────────────
def obtener_texto_aviso(link):
    try:
        r = requests.get(link, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        # Limpiar HTML
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except:
        return ""

def analizar_con_gemini(titulo, empresa, link, texto_extraido):
    if not IA_ACTIVA or not client:
        return 5, "IA inactiva", "No especifica", "No especifica", "", "No especifica"

    prompt = (
        f"Actúa como reclutador minero. Analiza este aviso para Ruben Morales.\n"
        f"PERFIL RUBEN: {PERFIL_RUBEN}\n"
        f"AVISO: {titulo} en {empresa}. TEXTO: {texto_extraido}\n\n"
        f"Responde SOLO JSON valido:\n"
        f'{{"puntaje": 1-10, "porque": "breve justificacion", "turno": "ej 7x7", '
        f'"sueldo": "monto o N/A", "beneficios": "resumen", "carta": "carta breve profesional"}}'
    )

    try:
        # NUEVA SINTAXIS DE LLAMADA (V1)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        # Parseo seguro
        data = json.loads(response.text)
        return (
            int(data.get("puntaje", 5)),
            data.get("porque", "Analisis IA"),
            data.get("turno", "No especifica"),
            data.get("sueldo", "No especifica"),
            data.get("carta", ""),
            data.get("beneficios", "No especifica")
        )
    except Exception as e:
        print(f"  ❌ Error generando contenido: {e}")
        return 5, "Error tecnico IA", "Ver link", "N/A", "", "N/A"

# ─────────────────────────────────────────
# SISTEMA DE ARCHIVOS Y TELEGRAM
# ─────────────────────────────────────────
def cargar_json(archivo):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r") as f: return json.load(f)
        except: return {} if "carta" in archivo else []
    return {} if "carta" in archivo else []

def guardar_json(archivo, data):
    with open(archivo, "w") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def enviar_telegram(msg, hid, tiene_carta):
    if not TOKEN or not CHAT_ID: return
    
    # Botones simplificados para evitar errores
    kb = {"inline_keyboard": [[{"text": "✅ Visto", "callback_data": f"v:{hid}"}]]}
    if tiene_carta:
        kb["inline_keyboard"].append([{"text": "📄 Ver Carta (JSON)", "callback_data": "carta"}])

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": msg,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": kb
            },
            timeout=10
        )
    except Exception as e:
        print(f"  Error Telegram: {e}")

# ─────────────────────────────────────────
# LOGICA PRINCIPAL
# ─────────────────────────────────────────
def procesar(fuente, titulo, empresa, link, vistos, cartas):
    # Filtro basico anti-basura
    if len(titulo) < 5 or any(x in titulo.lower() for x in ["chofer", "aseo", "guardia", "cocina"]):
        return 0
        
    hid = hashlib.md5(f"{titulo}{empresa}".encode()).hexdigest()
    
    # Si ya lo vimos (en lista o dict), saltar
    if isinstance(vistos, list): vistos = set(vistos) # Compatibilidad
    if hid in vistos: return 0

    print(f"🔍 Analizando: {titulo[:40]}...")
    
    # Analisis
    texto = obtener_texto_aviso(link)
    puntaje, porque, turno, sueldo, carta, benef = analizar_con_gemini(titulo, empresa, link, texto)

    # Solo enviamos si el puntaje es decente (>=5) o si la IA fallo (5)
    if puntaje < 4:
        print(f"   🗑️ Descartado por bajo puntaje ({puntaje})")
        vistos.add(hid)
        return 0

    # Guardar Carta
    if carta:
        cartas[hid] = {"titulo": titulo, "empresa": empresa, "carta": carta}

    # Formatear Mensaje
    icon = "💎" if puntaje >= 8 else "🔔"
    msg = (
        f"{icon} <b>RADAR MINERO: {puntaje}/10</b>\n\n"
        f"📋 <b>{titulo}</b>\n"
        f"🏭 {empresa}\n"
        f"⏰ Turno: {turno}\n"
        f"💰 Sueldo: {sueldo}\n"
        f"🤖 <i>{porque}</i>\n\n"
        f"🔗 <a href='{link}'>VER AVISO</a>\n"
        f"📍 Fuente: {fuente}"
    )

    enviar_telegram(msg, hid, bool(carta))
    vistos.add(hid)
    return 1

# ─────────────────────────────────────────
# MOTORES DE BUSQUEDA (SIMPLIFICADOS)
# ─────────────────────────────────────────
def barrido_general(vistos, cartas):
    nuevos = 0
    # Lista prioritaria de búsqueda
    busquedas = [
        "administrador contrato mineria", 
        "supervisor mantencion", 
        "jefe mantenimiento",
        "planner mineria",
        "facility manager campamento",
        "newrest", "sodexo", "aramark", "codelco", "bhp"
    ]
    
    for q in busquedas:
        # Usamos Computrabajo como proxy seguro (no bloquea como Google)
        url = f"https://www.computrabajo.cl/trabajos-de-{q.replace(' ', '-')}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            
            for art in soup.find_all("article", class_="box_offer"):
                try:
                    t_tag = art.find("a", class_="js-o-link")
                    if not t_tag: continue
                    
                    titulo = t_tag.get_text(strip=True)
                    link = t_tag['href']
                    if not link.startswith("http"): link = "https://www.computrabajo.cl" + link
                    
                    emp_tag = art.find("a", class_="fc_base")
                    empresa = emp_tag.get_text(strip=True) if emp_tag else "Confidencial"
                    
                    nuevos += procesar("Computrabajo", titulo, empresa, link, vistos, cartas)
                except: continue
            time.sleep(1) # Cortesia
        except Exception as e:
            print(f"Error buscando {q}: {e}")
            
    return nuevos

# ─────────────────────────────────────────
# EJECUCION
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 INICIANDO RADAR MINERO V16 FIX")
    
    # Cargar datos
    vistos_raw = cargar_json(SEEN_FILE)
    vistos = set(vistos_raw) if isinstance(vistos_raw, list) else set()
    cartas = cargar_json(CARTA_FILE)
    
    # Ejecutar
    n = barrido_general(vistos, cartas)
    
    # Guardar
    guardar_json(SEEN_FILE, list(vistos))
    guardar_json(CARTA_FILE, cartas)
    
    print(f"✅ FIN. Nuevos avisos: {n}")
