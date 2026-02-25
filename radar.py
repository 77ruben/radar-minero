import requests
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

MEMORIA_FILE = "memoria.json"

# Cargar memoria
try:
    with open(MEMORIA_FILE,"r") as f:
        memoria = json.load(f)
except:
    memoria = []

def enviar(msg):

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id":CHAT_ID,"text":msg}
    )

enviar("RADAR MINERO V10 INICIADO")

nuevos = 0
revisados = 0

# FUENTE 1 — Indeed JSON real

url = "https://cl.indeed.com/jobs?q=minera&l=Chile&format=json"

headers = {
"User-Agent":"Mozilla/5.0"
}

try:

    resp = requests.get(url,headers=headers)

    data = resp.text

    if "title" in data:

        lineas = data.split("title")

        for linea in lineas:

            if "min" in linea.lower():

                titulo = linea.strip()

                revisados += 1

                if titulo not in memoria:

                    memoria.append(titulo)

                    nuevos += 1

                    enviar(f"""

EMPLEO MINERO DETECTADO

{titulo}

Fuente: Indeed

""")

except:

    enviar("Error leyendo Indeed")


# GUARDAR MEMORIA

with open(MEMORIA_FILE,"w") as f:

    json.dump(memoria,f)


enviar(f"""

RADAR FINALIZADO

Revisados: {revisados}

Nuevos: {nuevos}

Memoria: {len(memoria)}

""")
