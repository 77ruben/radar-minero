import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HEADERS = {"User-Agent":"Mozilla/5.0"}

HISTORIAL_FILE="historial.json"

KEYWORDS=[
"supervisor",
"supervisor de operaciones",
"administrador",
"administrador de contratos",
"jefe",
"jefe de operaciones",
"subgerente",
"sub gerente",
"lider",
"líder",
"encargado",
"superintendent",
"manager",
"operations supervisor"
]

EXCLUIR=[
"practica",
"práctica",
"trainee",
"intern"
]

# -------------------------
# HISTORIAL
# -------------------------

if os.path.exists(HISTORIAL_FILE):
    with open(HISTORIAL_FILE,"r") as f:
        historial=json.load(f)
else:
    historial=[]

nuevos=[]
reporte=[]

# -------------------------
# TELEGRAM
# -------------------------

def telegram(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id":CHAT_ID,"text":msg[:4000]}
    )

# -------------------------
# FILTRO
# -------------------------

def cumple(titulo):

    t=titulo.lower()

    if any(x in t for x in EXCLUIR):
        return False

    return any(k in t for k in KEYWORDS)

# -------------------------
# EJECUTOR SEGURO
# -------------------------

def ejecutar(nombre,func):

    try:

        encontrados=func()

        if encontrados==0:
            reporte.append(f"✔ {nombre}: sin empleos nuevos")

        else:
            reporte.append(f"✔ {nombre}: {encontrados} empleos")

    except Exception as e:

        reporte.append(f"❌ {nombre}: ERROR scraping")

# -------------------------
# CODELCO
# -------------------------

def codelco():

    count=0

    url="https://empleos.codelco.cl/search/?q="

    r=requests.get(url,headers=HEADERS,timeout=20)

    soup=BeautifulSoup(r.text,"html.parser")

    for link in soup.find_all("a",href=True):

        if "/job/" not in link["href"]:
            continue

        titulo=link.text.strip()

        if not cumple(titulo):
            continue

        job_link="https://empleos.codelco.cl"+link["href"]

        if job_link in historial:
            continue

        nuevos.append(f"{titulo}\n{job_link}")

        historial.append(job_link)

        count+=1

    return count

# -------------------------
# KINROSS
# -------------------------

def kinross():

    count=0

    url="https://jobs.kinross.com/search/?locationsearch=Chile"

    r=requests.get(url,headers=HEADERS,timeout=20)

    soup=BeautifulSoup(r.text,"html.parser")

    jobs=soup.find_all("tr",class_="data-row")

    for job in jobs:

        tag=job.find("a")

        if not tag:
            continue

        titulo=tag.text.strip()

        if not cumple(titulo):
            continue

        link="https://jobs.kinross.com"+tag["href"]

        if link in historial:
            continue

        nuevos.append(f"{titulo}\n{link}")

        historial.append(link)

        count+=1

    return count

# -------------------------
# ANGLO AMERICAN
# -------------------------

def anglo():

    count=0

    url="https://www.angloamerican.com/site-services/search-and-apply-data-fetch"

    params={
    "aadata":"get-search-jobs",
    "languageCode":"en-GB",
    "country":"chile"
    }

    r=requests.get(url,params=params,headers=HEADERS,timeout=20)

    data=r.json()

    for item in data.get("jobs",[]):

        titulo=item.get("jobTitle","")

        if not cumple(titulo):
            continue

        link=item.get("applyUrl")

        if not link:
            continue

        if link in historial:
            continue

        nuevos.append(f"{titulo}\n{link}")

        historial.append(link)

        count+=1

    return count

# -------------------------
# EJECUCIÓN
# -------------------------

ejecutar("Codelco",codelco)
ejecutar("Kinross",kinross)
ejecutar("Anglo American",anglo)

# -------------------------
# GUARDAR HISTORIAL
# -------------------------

with open(HISTORIAL_FILE,"w") as f:
    json.dump(historial,f)

# -------------------------
# MENSAJES TELEGRAM
# -------------------------

if nuevos:

    telegram("🚨 EMPLEOS DETECTADOS 🚨\n\n"+"\n\n".join(nuevos[:20]))

telegram("📡 REPORTE RADAR\n\n"+"\n".join(reporte))
