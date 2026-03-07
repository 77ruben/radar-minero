import requests
from bs4 import BeautifulSoup
import os
import json

print("RADAR MINERO SUPERVISIÓN V1")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

HEADERS = {"User-Agent": "Mozilla/5.0"}

HISTORIAL_FILE = "historial.json"

# ---------------------------------
# FILTRO DE CARGOS (TU PERFIL)
# ---------------------------------

KEYWORDS = [

"supervisor",
"supervisor de operaciones",

"administrador",
"administrador de contratos",
"contract manager",

"jefe",
"jefe de operaciones",

"subgerente",
"sub gerente",

"lider",
"líder",

"encargado",

"superintendent",
"superintendente",

"coordinator",
"coordinador",

"manager",
"site manager",

"operations supervisor",
"maintenance supervisor"
]

EXCLUIR = [
"practica",
"práctica",
"trainee",
"intern",
"alumno"
]

# ---------------------------------
# HISTORIAL
# ---------------------------------

if os.path.exists(HISTORIAL_FILE):
    with open(HISTORIAL_FILE,"r") as f:
        historial = json.load(f)
else:
    historial = []

nuevos = []

# ---------------------------------
# FILTRO
# ---------------------------------

def cumple(texto):

    t = texto.lower()

    if any(x in t for x in EXCLUIR):
        return False

    for palabra in KEYWORDS:
        if palabra in t:
            return True

    return False


# ---------------------------------
# TELEGRAM
# ---------------------------------

def enviar(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": msg[:4000]
        }
    )


# ---------------------------------
# CODELCO
# ---------------------------------

def codelco():

    try:

        url="https://empleos.codelco.cl/search/?q="

        r=requests.get(url,headers=HEADERS)

        soup=BeautifulSoup(r.text,"html.parser")

        for link in soup.find_all("a",href=True):

            titulo=link.get_text(strip=True)

            if "/job/" not in link["href"]:
                continue

            if not cumple(titulo):
                continue

            job_link="https://empleos.codelco.cl"+link["href"]

            if job_link in historial:
                continue

            nuevos.append(f"{titulo}\nCodelco\n{job_link}")

            historial.append(job_link)

    except Exception as e:

        print("Error Codelco:",e)


# ---------------------------------
# BHP
# ---------------------------------

def bhp():

    try:

        url="https://careers.bhp.com/search?location=chile"

        r=requests.get(url,headers=HEADERS)

        soup=BeautifulSoup(r.text,"html.parser")

        for link in soup.find_all("a",href=True):

            if "/job/" not in link["href"]:
                continue

            titulo=link.get_text(strip=True)

            if not cumple(titulo):
                continue

            job_link="https://careers.bhp.com"+link["href"]

            if job_link in historial:
                continue

            nuevos.append(f"{titulo}\nBHP\n{job_link}")

            historial.append(job_link)

    except Exception as e:

        print("Error BHP:",e)


# ---------------------------------
# TECK (API)
# ---------------------------------

def teck():

    try:

        url="https://jobs.teck.com/services/recruiting/v1/jobs"

        payload={"locale":"es_ES","pageNumber":0}

        r=requests.post(url,json=payload)

        data=r.json()

        jobs=data.get("jobSearchResult",[])

        for item in jobs:

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

    except Exception as e:

        print("Error Teck:",e)


# ---------------------------------
# KINROSS
# ---------------------------------

def kinross():

    try:

        url="https://jobs.kinross.com/search/?locationsearch=Chile"

        r=requests.get(url,headers=HEADERS)

        soup=BeautifulSoup(r.text,"html.parser")

        jobs=soup.find_all("tr",class_="data-row")

        for job in jobs:

            titulo_tag=job.find("a")

            if not titulo_tag:
                continue

            titulo=titulo_tag.text.strip()

            if not cumple(titulo):
                continue

            link="https://jobs.kinross.com"+titulo_tag["href"]

            if link in historial:
                continue

            nuevos.append(f"{titulo}\nKinross\n{link}")

            historial.append(link)

    except Exception as e:

        print("Error Kinross:",e)


# ---------------------------------
# LUNDIN
# ---------------------------------

def lundin():

    try:

        base="https://jobs.lundinmining.com"

        url=base+"/tile-search-results/?q=&startrow=0"

        r=requests.get(url,headers=HEADERS)

        soup=BeautifulSoup(r.text,"html.parser")

        jobs=soup.find_all("li",class_="job-tile")

        for job in jobs:

            texto=job.get_text(" ",strip=True)

            if ", CL" not in texto:
                continue

            titulo_tag=job.find("a",class_="jobTitle-link")

            if not titulo_tag:
                continue

            titulo=titulo_tag.text.strip()

            if not cumple(titulo):
                continue

            link=base+titulo_tag["href"]

            if link in historial:
                continue

            nuevos.append(f"{titulo}\nLundin\n{link}")

            historial.append(link)

    except Exception as e:

        print("Error Lundin:",e)


# ---------------------------------
# FREEPORT
# ---------------------------------

def freeport():

    try:

        base="https://jobs.fcx.com"

        url="https://jobs.fcx.com/South-America/go/Oportunidades-Laborales-en-Chile/8009100/"

        r=requests.get(url,headers=HEADERS)

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

    except Exception as e:

        print("Error Freeport:",e)


# ---------------------------------
# ANGLO AMERICAN (API)
# ---------------------------------

def anglo():

    try:

        url="https://www.angloamerican.com/site-services/search-and-apply-data-fetch"

        params={
        "aadata":"get-search-jobs",
        "languageCode":"en-GB",
        "country":"chile"
        }

        headers={
        "User-Agent":"Mozilla/5.0",
        "Accept":"application/json"
        }

        r=requests.get(url,params=params,headers=headers)

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

    except Exception as e:

        print("Error Anglo:",e)


# ---------------------------------
# EJECUCIÓN
# ---------------------------------

codelco()
bhp()
teck()
kinross()
lundin()
freeport()
anglo()

# ---------------------------------
# GUARDAR HISTORIAL
# ---------------------------------

with open(HISTORIAL_FILE,"w") as f:
    json.dump(historial,f)

# ---------------------------------
# MENSAJE
# ---------------------------------

if nuevos:

    mensaje="🚨 EMPLEOS MINEROS SUPERVISIÓN 🚨\n\n"

    mensaje+="\n\n".join(nuevos[:25])

else:

    mensaje="Radar minero activo.\nSin nuevos empleos de supervisión."

enviar(mensaje)

print("RADAR TERMINADO")
