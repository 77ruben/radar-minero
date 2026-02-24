import os
import sys

# Intentar importar la librería y capturar el error exacto
try:
    from google import genai
    from google.genai import types
    LIB_INSTALADA = True
except ImportError as e:
    LIB_INSTALADA = False
    ERROR_IMPORT = str(e)

import requests

TOKEN = os.environ.get("TOKEN", "").strip()
CHAT_ID = os.environ.get("CHAT_ID", "").strip()
GEMINI_KEY = os.environ.get("GEMINI_KEY", "").strip()

def enviar_error_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": f"❌ DEBUG IA:\n{msg}"})

def probar_ia():
    if not LIB_INSTALADA:
        enviar_error_telegram(f"Librería google-genai no encontrada. Error: {ERROR_IMPORT}")
        return

    if not GEMINI_KEY:
        enviar_error_telegram("La GEMINI_KEY está vacía en los Secretos de GitHub.")
        return

    try:
        # Intento de conexión simple
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hola"
        )
        enviar_error_telegram(f"✅ ¡CONEXIÓN EXITOSA! La IA respondió: {response.text}")
    except Exception as e:
        # Esto nos enviará el error real (si es la clave, el modelo, o la red)
        enviar_error_telegram(f"Error al conectar con Gemini: {str(e)}")

if __name__ == "__main__":
    probar_ia()
