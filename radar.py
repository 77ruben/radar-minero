"""
RADAR MINERO - MODO DIAGNÓSTICO
Este script "chismoso" nos dirá exactamente dónde se corta la comunicación.
"""

import requests
from bs4 import BeautifulSoup
import os, time, json, hashlib
from google import genai
from google.genai import types

# ─────────────────────────────────────────
# 1. CARGA DE VARIABLES (CON DEBUG)
# ─────────────────────────────────────────
TOKEN      = os.environ.get("TOKEN", "").strip()
CHAT_ID    = os.environ.get("CHAT_ID", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()

print("--- DIAGNÓSTICO DE VARIABLES ---")
print(f"Token Telegram: {'Cargado ✅' if len(TOKEN) > 10 else 'FALTANTE ❌'}")
print(f"Chat ID: {'Cargado ✅' if len(CHAT_ID) > 5 else 'FALTANTE ❌'}")
print(f"Gemini Key: {'Cargado ✅' if len(GEMINI_KEY) > 10 else 'FALTANTE ❌'}")
print("--------------------------------")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# ─────────────────────────────────────────
# 2. PRUEBA DE CONEXIÓN TELEGRAM
# ─────────────────────────────────────────
def test_telegram_inicial():
    print("📨 Intentando enviar mensaje de prueba a Telegram...")
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": "🔔 <b>TEST DE CONEXIÓN</b>\nSi lees esto, el Bot funciona."}, timeout=10)
        if r.status_code == 200:
            print("✅ MENSAJE DE PRUEBA ENVIADO CON ÉXITO")
            return True
        else:
            print(f"❌ ERROR TELEGRAM ({r.status_code}): {r.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR DE CONEXIÓN TELEGRAM: {e}")
        return False

# ─────────────────────────────────────────
# 3. CLIENTE IA
# ─────────────────────────────────────────
client = None
if GEMINI_KEY:
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        print("✅ Cliente Gemini inicializado")
    except Exception as e:
        print(f"❌ Error al crear cliente Gemini: {e}")

# ─────────────────────────────────────────
# 4. FUNCIONES DE ANÁLISIS
# ─────────────────────────────────────────
def analizar_con_ia(titulo, empresa):
    if not client: 
        print("   ⚠️ Salto IA: Cliente no activo")
        return None
    
    print(f"   🤖 Preguntando a Gemini sobre: {titulo}...")
    prompt = (
        f"Analiza: Cargo '{titulo}' en '{empresa}' para Ingeniero Industrial experto en Mantención Minera.\n"
        f"Responde SOLO JSON: {{\"puntaje\": 1-10, \"motivo\": \"breve resumen\"}}"
    )
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)
        print(f"   ✅ Gemini respondió: Puntaje {data.get('puntaje')}")
        return data
    except Exception as e:
        print(f"   ❌ Error Gemini: {e}")
        return None

def enviar_telegram_oferta(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        )
    except: pass

# ─────────────────────────────────────────
# 5. EJECUCIÓN (SIN FILTROS DE MEMORIA)
# ─────────────────────────────────────────
def correr_diagnostico():
    # Paso 1: Testear Telegram
    if not test_telegram_inicial():
        print("⛔ DETENIENDO: Si Telegram falla, no tiene sentido seguir.")
        return

    # Paso 2: Testear Scraping
    print("\n🌍 Iniciando Búsqueda en Computrabajo...")
    url = "https://www.computrabajo.cl/trabajos-de-administrador-contrato-mineria"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"   Estado HTTP: {r.status_code}")
        
        soup = BeautifulSoup(r.text, "html.parser")
        ofertas = soup.find_all("article", class_="box_offer")
        
        print(f"   📦 Ofertas encontradas en HTML: {len(ofertas)}")
        
        if len(ofertas) == 0:
            print("   ⚠️ ALERTA: No se encontraron ofertas. Posible cambio de clases CSS en la web.")
        
        # Procesamos solo la primera oferta para probar
        for art in ofertas[:1]: 
            t_tag = art.find("a", class_="js-o-link")
            if t_tag:
                titulo = t_tag.get_text(strip=True)
                link = t_tag['href']
                print(f"\n   🔎 Analizando aviso: {titulo}")
                
                # Análisis IA
                resultado = analizar_con_ia(titulo, "Empresa Detectada")
                
                if resultado:
                    msg = (
                        f"🚀 <b>RADAR DIAGNÓSTICO</b>\n"
                        f"Cargo: {titulo}\n"
                        f"Puntaje IA: {resultado['puntaje']}/10\n"
                        f"Motivo: {resultado['motivo']}"
                    )
                    enviar_telegram_oferta(msg)
                    print("   📨 Reporte enviado a Telegram")
                
                # Pausa para no saturar cuota
                time.sleep(2)

    except Exception as e:
        print(f"❌ Error crítico en scraping: {e}")

if __name__ == "__main__":
    correr_diagnostico()
