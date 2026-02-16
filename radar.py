import requests
import os

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

print("TOKEN:", TOKEN)
print("CHAT_ID:", CHAT_ID)

if TOKEN and CHAT_ID:

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": "✅ Radar Minero conectado correctamente"
    }

    r = requests.post(url, data=data)

    print("Respuesta:", r.text)

else:

    print("ERROR: Secrets no encontrados")
