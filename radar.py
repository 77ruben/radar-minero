import requests
from bs4 import BeautifulSoup
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA_FILE = "memoria.json"

# ---------- MEMORIA ----------
try:
    with open(MEMORIA_FILE,"r") as f:
        memoria = json.load(f)
except:
    memoria = []

# ---------- FILTRO RUBEN ----------
CARGOS_OBJETIVO = [
"supervisor",
"maintenance supervisor",
"supervisor mantencion",
"jefe mantencion",
"planificador",
"planner",
"administrador de contrato",
"contract administrator",
"contract manager"
]

PALABRAS_MINERIA = [
"mining",
"minera",
"faena",
"mine"
]

# ---------- FUENTES REALES ----------
FUENTES = {

"Codelco":
"https://jobs.codelco.cl/search/?q=",

"BHP":
"https://careers.bhp.com/search/?q=",

"Antofagasta Minerals":
"https://careers.antofagasta.co.uk/search/?q=",

"Collahuasi":
"https://www.collahuasi.cl/trabaja-con-nosotros/",

"Kinross":
"https://jobs.kinross.com/search/?q=",

"Komatsu":
"https://komatsu.jobs/search-jobs?acm=ALL",

"Finning":
"https://finning.taleo.net/careersection/finning_external/jobsearch.ftl",

"Liebherr":
"https://www.liebherr.com/en/cll/career/job-vacancies/job-vacancies.html",

"Sandvik":
"https://jobs.smartrecruiters.com/Sandvik",

"Epiroc":
"https://epiroc.com/en-us/jobs",

"Indeed":
"https://cl.indeed.com/jobs?q=minera",

"LinkedIn":
"https://www.linkedin.com/jobs/search/?keywords=mining"

}

# ---------- TELEGRAM ----------
def enviar(msg):

    requests.post(

        f"https://api.telegram.org/bot{TOKEN}/sendMessage",

        data={"chat_id":CHAT_ID,"text":msg}

    )

# ---------- ANALISIS IA ----------
def analizar(texto):

    t = texto.lower()

    if any(c in t for c in CARGOS_OBJETIVO):

        if any(m in t for m in PALABRAS_MINERIA):

            return "VALIDO"

        else:

            return "DESCARTADO: No menciona minería"

    return "DESCARTADO: No es cargo objetivo"

# ---------- INICIO ----------
enviar("RADAR V13 COBERTURA TOTAL INICIADO")

revisados = 0
validos = 0
descartados = 0

headers = {"User-Agent":"Mozilla/5.0"}

for empresa,url in FUENTES.items():

    try:

        html = requests.get(url,headers=headers,timeout=15).text

        soup = BeautifulSoup(html,"html.parser")

        links = soup.find_all("a")

        for link in links:

            titulo = link.get_text().strip()

            href = link.get("href")

            if titulo and href:

                revisados += 1

                resultado = analizar(titulo)

                if resultado == "VALIDO":

                    if titulo not in memoria:

                        memoria.append(titulo)

                        validos += 1

                        if href.startswith("/"):

                            href = url + href

                        enviar(f"""

NUEVO EMPLEO MINERO DETECTADO

Empresa: {empresa}

Cargo:
{titulo}

Link:
{href}

Analisis IA:
Coincide con Supervisor / Administrador de Contratos

""")

                else:

                    descartados += 1

    except:

        enviar(f"Error leyendo {empresa}")

# ---------- GUARDAR MEMORIA ----------
with open(MEMORIA_FILE,"w") as f:

    json.dump(memoria,f)

# ---------- REPORTE FINAL ----------
enviar(f"""

RADAR FINALIZADO

Revisados: {revisados}

Validos: {validos}

Descartados: {descartados}

Memoria total: {len(memoria)}

""")
