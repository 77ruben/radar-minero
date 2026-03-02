import requests
import os

print("INICIANDO RADAR BHP REAL")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

# Endpoint correcto actual Workday BHP
URL = "https://bhp.wd3.myworkdayjobs.com/wday/cxs/bhp/BHP_Careers/jobs"

payload = {
    "limit": 100,
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

    message = ""

    for job in jobs:
        title = job.get("title", "")
        location = job.get("locationsText", "")
        external_path = job.get("externalPath", "")

        if "Chile" in location:
            link = f"https://bhp.wd3.myworkdayjobs.com/BHP_Careers/job/{external_path}"
            message += f"{title}\n📍 {location}\n{link}\n\n"

    if message == "":
        message = "Radar BHP activo.\nSe consultó correctamente, pero no se detectaron empleos en Chile."

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
