import requests
import os
import json

print("INICIANDO RADAR BHP WORKDAY")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

# Endpoint interno Workday BHP
URL = "https://bhp.wd3.myworkdayjobs.com/wday/cxs/bhp/BHP/jobs"

payload = {
    "appliedFacets": {
        "Location_Country": ["bc33aa3152ec42d4995f4791a106ed09"]  # Chile
    },
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

    if not jobs:
        message = "Radar BHP activo.\nNo se encontraron empleos en Chile."
    else:
        message = "🚨 EMPLEOS BHP CHILE DETECTADOS 🚨\n\n"

        for job in jobs:
            title = job.get("title")
            location = job.get("locationsText")
            job_id = job.get("externalPath")

            link = f"https://bhp.wd3.myworkdayjobs.com/BHP/job/{job_id}"

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
