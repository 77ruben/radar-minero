"""
DEBUG RADAR V16 - DIAGNÓSTICO TOTAL
"""
import os, json, requests, hashlib
from google import genai
from google.genai import types

# ─────────────────────────────────────────
# CARGA DE CREDENCIALES
# ─────────────────────────────────────────
TOKEN     = os.environ.get("TOKEN", "").strip()
CHAT_ID   = os.environ.get("CHAT_ID", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()

print(f"DEBUG: Token cargado: {'SI' if TOKEN else 'NO'}")
print(f"DEBUG: Chat ID cargado: {'SI' if CHAT_ID else 'NO'}")
print(f"DEBUG: Gemini Key cargada: {'SI' if GEMINI_KEY else 'NO'}")

# ─────────────────────────────────────────
# PRUEBA 1: GOOGLE GENAI (IA)
# ─────────────────────────────────────────
def test_ia():
    print("--- 🧠 INICIANDO PRUEBA DE IA ---")
    if not GEMINI_KEY:
        print("❌ ERROR: No hay llave de Gemini en secretos.")
        return None
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Saluda a Ruben Morales en una frase breve sobre mineria.",
            config=types.GenerateContentConfig(temperature=0.7)
        )
        print(f"✅ IA RESPONDE: {response.text.strip()}")
        return client
    except Exception as e:
        print(f"❌ ERROR IA: {e}")
        return None

# ─────────────────────────────────────────
# PRUEBA 2: TELEGRAM
# ─────────────────────────────────────────
def test_telegram(mensaje):
    print("--- 📨 INICIANDO PRUEBA DE TELEGRAM ---")
    if not TOKEN or not CHAT_ID:
        print("❌ ERROR: Faltan credenciales de Telegram.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("✅ MENSAJE ENVIADO A TELEGRAM")
        else:
            print(f"❌ ERROR TELEGRAM: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ ERROR CONEXIÓN TELEGRAM: {e}")

# ─────────────────────────────────────────
# PRUEBA 3: INTEGRACIÓN TOTAL (Simular un aviso real)
# ─────────────────────────────────────────
def test_aviso_completo(client):
    print("--- ⚡ INICIANDO INTEGRACIÓN COMPLETA ---")
    titulo = "SUPERVISOR DE MANTENCIÓN - CENTINELA (PRUEBA)"
    empresa = "Antofagasta Minerals"
    texto_aviso = "Se busca Supervisor con 10 años de experiencia en SAP PM para turno 7x7 en faena norte."

    prompt = (
        f"Analiza este aviso para Ruben Morales (Ingeniero Industrial). "
        f"Aviso: {titulo} en {empresa}. Texto: {texto_aviso}. "
        f"Responde SOLO JSON: {{\"puntaje\": 10, \"porque\": \"Test de sistema\", \"carta\": \"Hola, soy Ruben...\"}}"
    )

    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(resp.text)
        msg = (
            f"🚀 <b>TEST DE INTEGRACIÓN EXITOSO</b>\n\n"
            f"📋 {titulo}\n"
            f"🏭 {empresa}\n"
            f"⭐ Puntaje IA: {data['puntaje']}/10\n"
            f"🤖 <i>{data['porque']}</i>\n\n"
            f"📄 Carta generada correctamente."
        )
        test_telegram(msg)
    except Exception as e:
        print(f"❌ FALLO INTEGRACIÓN: {e}")

# EJECUCIÓN DEL DIAGNÓSTICO
if __name__ == "__main__":
    client = test_ia()
    if client:
        test_aviso_completo(client)
    else:
        test_telegram("⚠️ Error en el Radar: La IA no pudo conectarse. Revisa los logs.")
