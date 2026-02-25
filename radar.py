import requests
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA_FILE = "memoria.json"

try:
    with open(MEMORIA_FILE,"r") as f:
        memoria = json.load(f)
except:
    memoria = []

FUENTES = {

"Codelco":
"https://jobs.codelco.cl/search/?createNewAlert=false&q=&locationsearch=",

"Antofagasta Minerals":
"https://careers.antofagasta.co.uk/search/",

"Komatsu":
"https://komatsu.jobs/search-jobs",

"Finning":
"https://finning.com/es_CL/careers",

"Liebherr":
"https://www.liebherr.com/en/cll/career/job-vacancies/job-vacancies.html"

}

def enviar(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id":CHAT_ID,"text":msg}
    )

enviar("RADAR V11 MULTIMINERA INICIADO")

nuevos = 0
revisados = 0

headers = {"User-Agent":"Mozilla/5.0"}

for nombre,url in FUENTES.items():

    try:

        html = requests.get(url,headers=headers).text

        if "job" in html.lower():

            revisados += 1

            if url not in memoria:

                memoria.append(url)

                nuevos += 1

                enviar(f"""

EMPLEO MINERO DETECTADO

Empresa: {nombre}

Revisar en:

{url}

""")

    except:

        pass


with open(MEMORIA_FILE,"w") as f:

    json.dump(memoria,f)


enviar(f"""

RADAR FINALIZADO

Fuentes revisadas: {revisados}

Nuevos detectados: {nuevos}

Total memoria: {len(memoria)}

""")
