import requests
from bs4 import BeautifulSoup
import os

print("INICIANDO RADAR BHP CHILE")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

# URL oficial BHP Chile (Workday)
URL = "https://careers.bhp.com/careers/SearchJobs/?3_62_3=406&3_62_3_format=932"

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = soup.find_all("a", class_="jobTitle-link")

    if not jobs:
        message = "Radar BHP activo.\nNo se encontraron empleos publicados en esta ejecución."
    else:
        message = "🚨 EMPLEOS BHP CHILE DETECTADOS 🚨\n\n"

        for job in jobs:
            title = job.text.strip()
            link = "https://careers.bhp.com" + job.get("href")
            message += f"{title}\n{link}\n\n"

    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    r = requests.post(telegram_url, data=payload)

    if r.status_code != 200:
        raise Exception("Error enviando mensaje a Telegram")

    print("Radar ejecutado correctamente")

except Exception as e:
    print("ERROR:", e)
    raise
