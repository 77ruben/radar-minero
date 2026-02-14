import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

KEYWORDS = [

"supervisor",
"mantencion",
"contrato",
"planificador",
"mantenimiento",
"operaciones"

]

URLS = [

"https://cl.indeed.com/jobs?q=mineria&l=Chile",
"https://cl.indeed.com/jobs?q=supervisor+mineria&l=Chile",
"https://cl.indeed.com/jobs?q=maintenance+mining&l=Chile"

]

ARCHIVO = "vistos.json"

try:
    with open(ARCHIVO,"r") as f:
        vistos = json.load(f)
except:
    vistos = []

nuevos = []

for URL in URLS:

    page = requests.get(URL)

    soup = BeautifulSoup(page.content,"html.parser")

    jobs = soup.select(".tapItem")

    for job in jobs:

        titulo = job.select_one("h2").text.lower()

        link = "https://cl.indeed.com" + job.select_one("a")["href"]

        if link in vistos:
            continue

        if any(k in titulo for k in KEYWORDS):

            nuevos.append((titulo,link))

            vistos.append(link)

with open(ARCHIVO,"w") as f:

    json.dump(vistos,f)

if nuevos:

    mensaje = "🚨 RADAR MINERO PRO\n\n"

    for t,l in nuevos:

        mensaje += t.upper()+"\n"+l+"\n\n"

    requests.post(

    f"https://api.telegram.org/bot{TOKEN}/sendMessage",

    data={"chat_id":CHAT_ID,"text":mensaje}

    )

print("OK")
