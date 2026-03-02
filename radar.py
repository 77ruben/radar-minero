import requests
from bs4 import BeautifulSoup
import os

print("INICIANDO RADAR BHP HTML")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

URL = "https://careers.bhp.com/search?location=chile"

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = soup.find_all("a", href=True)

    message = ""
    count = 0

    for job in jobs:
        href = job["href"]

        if "/job/" in href:
            title = job.text.strip()
            link = "https://careers.bhp.com" + href

            if title:
                message += f"{title}\n{link}\n\n"
                count += 1

    if count == 0:
        message = "Radar BHP activo.\nNo se detectaron empleos en Chile (HTML visible)."
    else:
        message = f"🚨 EMPLEOS BHP CHILE DETECTADOS ({count}) 🚨\n\n" + message

    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message[:4000]  # límite Telegram
    }

    r = requests.post(telegram_url, data=payload)

    if r.status_code != 200:
        raise Exception("Error enviando mensaje a Telegram")

    print("Radar ejecutado correctamente")

except Exception as e:
    print("ERROR:", e)
    raise
