import requests
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("INICIO RADAR")

if not TOKEN:
    print("ERROR: TOKEN vacío")

if not CHAT_ID:
    print("ERROR: CHAT_ID vacío")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

mensaje = "Radar Minero operativo correctamente"

r = requests.get(url, params={
    "chat_id": CHAT_ID,
    "text": mensaje
})

print("URL:", url)
print("STATUS:", r.status_code)
print("RESPUESTA:", r.text)

print("FIN RADAR")
