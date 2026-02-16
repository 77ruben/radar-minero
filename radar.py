import requests

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

print("INICIO RADAR")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": "🔥 MENSAJE DESDE GITHUB - PRUEBA REAL"
}

r = requests.post(url, data=data)

print("STATUS:", r.status_code)
print("RESPUESTA:", r.text)

print("FIN RADAR")
