import requests
import os

print("INICIANDO RADAR ANTOFAGASTA MINERALS")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

url = "https://career8.successfactors.com/career/jobsearch/search"

params = {
    "company": "AMSAP",
    "locale": "es_ES",
    "pageSize": "50",
    "pageNumber": "1"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

response = requests.get(url, params=params, headers=headers)

print("Status code:", response.status_code)

if response.status_code != 200:
    raise Exception(f"Error HTTP {response.status_code}")

data = response.json()

jobs = data.get("jobSearchResult", {}).get("results", [])

message = ""
count = 0

for job in jobs:
    title = job.get("jobTitle")
    location = job.get("location")
    job_id = job.get("jobReqId")

    link = f"https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH&jobReqId={job_id}"

    message += f"{title}\n{location}\n{link}\n\n"
    count += 1

if count == 0:
    message = "Radar Antofagasta Minerals activo.\nNo se detectaron empleos."
else:
    message = f"🚨 EMPLEOS ANTOFAGASTA MINERALS ({count}) 🚨\n\n" + message

telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(telegram_url, data={
    "chat_id": CHAT_ID,
    "text": message[:4000]
})

print("Radar ejecutado correctamente")
