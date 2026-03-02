import requests
import os

print("RADAR TECK ACTIVO")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URL = "https://jobs.teck.com/services/recruiting/v1/jobs"

headers = {
    "Content-Type": "application/json"
}

payload = {
    "locale": "es_ES",
    "pageNumber": 1
}

response = requests.post(URL, json=payload, headers=headers)

message = ""
count = 0

if response.status_code == 200:
    data = response.json()

    jobs = data.get("jobSearchResult", [])
    total = data.get("totalJobs", 0)

    for item in jobs:
        job = item.get("response", {})
        title = job.get("unifiedStandardTitle")
        location = job.get("jobLocationShort", [""])[0].replace("<br/>", "")
        job_id = job.get("id")
        url_title = job.get("urlTitle")

        link = f"https://jobs.teck.com/job/{url_title}/{job_id}/es_ES"

        message += f"{title}\n{location}\n{link}\n\n"
        count += 1

if count == 0:
    message = "Radar Teck activo.\nNo se detectaron empleos."
else:
    message = f"🚨 TECK ({count}) 🚨\n\n" + message

telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(telegram_url, data={
    "chat_id": CHAT_ID,
    "text": message[:4000]
})

print("Proceso finalizado")
