import requests
import os

print("INICIANDO RADAR BHP GLOBAL")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

URL = "https://bhp.wd3.myworkdayjobs.com/wday/cxs/bhp/BHP/jobs"

payload = {
    "limit": 50,
    "offset": 0,
    "searchText": ""
}

headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(URL, headers=headers, json=payload)
    data = response.json()

    jobs = data.get("jobPostings", [])

    chile_jobs = []

    for job in jobs:
        location = job.get("locationsText", "")
        if "Chile" in location:
            chile_jobs.append(job)

    if not chile_jobs:
        message = "Radar BHP activo.\nNo se encontraron empleos en Chile en esta ejecución."
    else:
        message = "🚨 EMPLEOS BHP CHILE DETECTADOS 🚨\n\n"

        for job in chile_jobs:
            title = job.get("title")
            location = job.get("locationsText")
            external_path = job.get("externalPath")

            link = f"https://bhp.wd3.myworkdayjobs.com/BHP/job/{external_path}"

            message += f"{title}\n📍 {location}\n{link}\n\n"

    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    payload_telegram = {
        "chat_id": CHAT_ID,
        "text": message
    }

    r = requests.post(telegram_url, data=payload_telegram)

    if r.status_code != 200:
        raise Exception("Error enviando mensaje a Telegram")

    print("Radar ejecutado correctamente")

except Exception as e:
    print("ERROR:", e)
    raise
