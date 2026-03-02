import requests
from bs4 import BeautifulSoup
import os

print("RADAR FREEPORT ACTIVO")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URL = "https://jobs.fcx.com/South-America/go/Oportunidades-Laborales-en-Chile/8009100/"
BASE = "https://jobs.fcx.com"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

jobs = []

for job in soup.find_all("a", class_="jobTitle-link"):
    title = job.get_text(strip=True)
    link = BASE + job["href"]
    location = job["href"].split("/")[3]  # ciudad viene en la URL
    jobs.append(f"{title}\n{location}\n{link}\n")

if len(jobs) == 0:
    message = "Radar Freeport activo.\nNo se detectaron empleos."
else:
    message = f"🚨 FREEPORT ({len(jobs)}) 🚨\n\n" + "\n".join(jobs)

telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

requests.post(telegram_url, data={
    "chat_id": CHAT_ID,
    "text": message[:4000]
})

print("Proceso finalizado")
