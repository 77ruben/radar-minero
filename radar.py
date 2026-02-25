"""
RADAR MINERO V17 - VERSIÓN ESTABLE
Optimizado para cuotas gratuitas y nueva librería google-genai
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib
from datetime import datetime
from google import genai
from google.genai import types

# ─────────────────────────────────────────
# CONFIGURACIÓN DE ENTORNO
# ─────────────────────────────────────────
TOKEN      = os.environ.get("TOKEN", "").strip()
CHAT_ID    = os.environ.get("CHAT_ID", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()

# Archivos de persistencia
SEEN_FILE  = "seen_jobs.json"
CARTA_FILE = "cartas_pendientes.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Perfil del usuario para la IA
PERFIL_RUBEN = """
Ruben Morales: Ing. Ejecución Industrial. 15+ años exp. Supervisor Mantención, Admin Contrato.
Experto en SAP PM, Licitaciones, Faenas mineras (Centinela, Teck). Busca: Jefe/Sup Mantención o Admin Contrato.
"""

# ─────────────────────────────────────────
# INICIALIZACIÓN DE IA
# ─────────────────────────────────────────
client = None
if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        print("✅ Cliente IA Inicializado")
    except Exception as e:
        print(f"❌ Error inicializando cliente: {e}")

# ─────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────
def cargar_json(archivo, default):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f: return json.load(f)
        except: return default
    return default

def guardar_json(archivo, data):
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def enviar_telegram(msg):
    if not TOKEN or not CHAT_ID: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
    except: pass

# ─────────────────────────────────────────
# LÓGICA DE ANÁLISIS
# ─────────────────────────────────────────
def analizar_aviso(titulo, empresa, link):
    if not client: return None
    
    print(f"🤖 Analizando con IA: {titulo}...")
    
    # Intentamos extraer un poco de texto del aviso
    desc = ""
    try:
        res = requests.get(link, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        desc = soup.get_text()[:2000] # Primeros 2000 caracteres
    except: desc = "No se pudo extraer descripción."

    prompt = (
        f"Analiza este aviso para {PERFIL_RUBEN}.\n"
        f"AVISO: {titulo} en {empresa}.\n"
        f"TEXTO: {desc}\n\n"
        f"Responde SOLO en este formato JSON:\n"
        f'{{"puntaje": 1-10, "porque": "...", "carta": "..."}}'
    )

    try:
        # USAMOS 1.5-FLASH PARA MEJOR CUOTA
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"⚠️ Error en consulta IA: {e}")
        time.sleep(10) # Pausa por si es error de cuota
        return None

# ─────────────────────────────────────────
# PROCESO PRINCIPAL
# ─────────────────────────────────────────
def ejecutar_radar():
    vistos = set(cargar_json(SEEN_FILE, []))
    cartas = cargar_json(CARTA_FILE, {})
    
    # Fuentes de búsqueda
    busquedas = ["supervisor mantencion mineria", "administrador contrato mineria Chile"]
    encontrados = 0

    for q in busquedas:
        url = f"https://www.computrabajo.cl/trabajos-de-{q.replace(' ', '-')}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            ofertas = soup.find_all("article", class_="box_offer")[:5] # Top 5 por búsqueda

            for art in ofertas:
                t_tag = art.find("a", class_="js-o-link")
                if not t_tag: continue
                
                titulo = t_tag.get_text(strip=True)
                link = "https://www.computrabajo.cl" + t_tag['href']
                hid = hashlib.md5(link.encode()).hexdigest()

                if hid in vistos: continue

                # Análisis
                resultado = analizar_aviso(titulo, "Empresa en Portal", link)
                
                if resultado and resultado.get("puntaje", 0) >= 6:
                    msg = (
                        f"💎 <b>OFERTA INTERESANTE ({resultado['puntaje']}/10)</b>\n\n"
                        f"📌 <b>{titulo}</b>\n"
                        f"📝 {resultado['porque']}\n\n"
                        f"🔗 <a href='{link}'>Ver Postulación</a>"
                    )
                    enviar_telegram(msg)
                    cartas[hid] = {"titulo": titulo, "carta": resultado.get("carta", "")}
                    encontrados += 1
                
                vistos.add(hid)
                time.sleep(5) # PAUSA ANTI-BLOQUEO Y CUOTA

        except Exception as e:
            print(f"Error en búsqueda {q}: {e}")

    guardar_json(SEEN_FILE, list(vistos))
    guardar_json(CARTA_FILE, cartas)
    print(f"✅ Proceso terminado. Nuevos: {encontrados}")

if __name__ == "__main__":
    ejecutar_radar()
