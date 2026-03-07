import requests
from bs4 import BeautifulSoup
import os
import json

print("RADAR MINERO SUPERVISION")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

HISTORIAL_FILE = "historial.json"

# ----------------------------
# FILTRO DE CARGOS
# ----------------------------

KEYWORDS = [
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

EXCLUIR = [
"practica",
"práctica",
"trainee",
"intern",
"alumno"
]

# ----------------------------
# HISTORIAL
# ----------------------------

if os.path.exists(HISTORIAL_FILE):
    with open(HISTORIAL_FILE,"r") as f:
        historial = json.load(f)
else:
    historial = []

nuevos = []
reporte = []

# ----------------------------
# TELEGRAM
# ----------------------------

def telegram(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": msg[:4000]
        }
    )

# ----------------------------
# FILTRO
# ----------------------------

def cumple(titulo):

    t = titulo.lower()

    if any(x in t for x in EXCLUIR):
        return False

    return any(k in t for k in KEYWORDS)

# ----------------------------
# EJECUTOR SEGURO
# ----------------------------

def ejecutar(nombre,func):

    try:

        encontrados = func()

        if encontrados == 0:
            reporte.append(f"✔ {nombre}: sin empleos nuevos")

        else:
            reporte.append(f"✔ {nombre}: {encontrados} empleos")

    except Exception as e:

        reporte.append(f"❌ {nombre}: ERROR scraping")

# ----------------------------
# CODELCO
# ----------------------------

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

        nuevos.append(f"{titulo}\nCodelco\n{job_link}")

        historial.append(job_link)

        count+=1

    return count

# ----------------------------
# BHP
# ----------------------------

def bhp():

    count=0

    url="https://careers.bhp.com/search?location=chile"

    r=requests.get(url,headers=HEADERS,timeout=20)

    soup=BeautifulSoup(r.text,"html.parser")

    for link in soup.find_all("a",href=True):

        if "/job/" not in link["href"]:
            continue

        titulo=link.text.strip()

        if not cumple(titulo):
            continue

        job_link="https://careers.bhp.com"+link["href"]

        if job_link in historial:
            continue

        nuevos.append(f"{titulo}\nBHP\n{job_link}")

        historial.append(job_link)

        count+=1

    return count

# ----------------------------
# TECK (API)
# ----------------------------

def teck():

    count=0

    url="https://jobs.teck.com/services/recruiting/v1/jobs"

    payload={"locale":"es_ES","pageNumber":0}

    r=requests.post(url,json=payload,timeout=20)

    data=r.json()

    for item in data.get("jobSearchResult",[]):

        job=item.get("response",{})

        titulo=job.get("unifiedStandardTitle")

        if not titulo:
            continue

        if not cumple(titulo):
            continue

        job_id=job.get("id")
        url_title=job.get("urlTitle")

        link=f"https://jobs.teck.com/job/{url_title}/{job_id}/es_ES"

        if link in historial:
            continue

        nuevos.append(f"{titulo}\nTECK\n{link}")

        historial.append(link)

        count+=1

    return count

# ----------------------------
# KINROSS
# ----------------------------

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

        nuevos.append(f"{titulo}\nKinross\n{link}")

        historial.append(link)

        count+=1

    return count

# ----------------------------
# LUNDIN
# ----------------------------

def lundin():

    count=0

    base="https://jobs.lundinmining.com"

    url=base+"/tile-search-results/?q=&startrow=0"

    r=requests.get(url,headers=HEADERS,timeout=20)

    soup=BeautifulSoup(r.text,"html.parser")

    jobs=soup.find_all("li",class_="job-tile")

    for job in jobs:

        texto=job.get_text(" ",strip=True)

        if ", CL" not in texto:
            continue

        tag=job.find("a",class_="jobTitle-link")

        if not tag:
            continue

        titulo=tag.text.strip()

        if not cumple(titulo):
            continue

        link=base+tag["href"]

        if link in historial:
            continue

        nuevos.append(f"{titulo}\nLundin\n{link}")

        historial.append(link)

        count+=1

    return count

# ----------------------------
# FREEPORT
# ----------------------------

def freeport():

    count=0

    base="https://jobs.fcx.com"

    url="https://jobs.fcx.com/South-America/go/Oportunidades-Laborales-en-Chile/8009100/"

    r=requests.get(url,headers=HEADERS,timeout=20)

    soup=BeautifulSoup(r.text,"html.parser")

    for job in soup.find_all("a",class_="jobTitle-link"):

        titulo=job.get_text(strip=True)

        if not cumple(titulo):
            continue

        link=base+job["href"]

        if link in historial:
            continue

        nuevos.append(f"{titulo}\nFreeport\n{link}")

        historial.append(link)

        count+=1

    return count

# ----------------------------
# ANGLO AMERICAN
# ----------------------------

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

        nuevos.append(f"{titulo}\nAnglo American\n{link}")

        historial.append(link)

        count+=1

    return count

# ----------------------------
# INDEED
# ----------------------------

def indeed():

    count=0

    url="https://cl.indeed.com/jobs?q=supervisor+mineria&l=Chile"

    r=requests.get(url,headers=HEADERS,timeout=20)

    soup=BeautifulSoup(r.text,"html.parser")

    for a in soup.find_all("a",href=True):

        href=a["href"]

        if "/rc/clk" not in href:
            continue

        titulo=a.text.strip()

        if not cumple(titulo):
            continue

        link="https://cl.indeed.com"+href

        if link in historial:
            continue

        nuevos.append(f"{titulo}\nIndeed\n{link}")

        historial.append(link)

        count+=1

    return count

# ----------------------------
# EJECUCIÓN
# ----------------------------

ejecutar("Codelco",codelco)
ejecutar("BHP",bhp)
ejecutar("Teck",teck)
ejecutar("Kinross",kinross)
ejecutar("Lundin",lundin)
ejecutar("Freeport",freeport)
ejecutar("Anglo American",anglo)
ejecutar("Indeed",indeed)

# ----------------------------
# GUARDAR HISTORIAL
# ----------------------------

with open(HISTORIAL_FILE,"w") as f:
    json.dump(historial,f)

# ----------------------------
# TELEGRAM RESULTADOS
# ----------------------------

if nuevos:

    telegram("🚨 EMPLEOS DETECTADOS 🚨\n\n"+"\n\n".join(nuevos[:20]))

telegram("📡 REPORTE RADAR\n\n"+"\n".join(reporte))

print("RADAR TERMINADO")
