import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

CARGOS = [
"supervisor",
"mantencion",
"mantenimiento",
"planificador",
"confiabilidad",
"administrador de contrato"
]

MINERIA = [
"minera",
"faena",
"minero",
"contrato minero"
]

EXCLUIR = [
"sueldo",
"salario",
"blog",
"noticia"
]

URLS = [

"https://www.chiletrabajos.cl/trabajo/minera",
"https://cl.indeed.com/jobs?q=minera",
"https://www.bne.cl/ofertas"

]

def enviar(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url,data={
    "chat_id":CHAT_ID,
    "text":msg
})


def analizar(texto):

    texto = texto.lower()

    if any(e in texto for e in EXCLUIR):
        return "DESCARTADO: basura"

    if not any(c in texto for c in CARGOS):
        return "DESCARTADO: no es cargo objetivo"

    if not any(m in texto for m in MINERIA):
        return "DESCARTADO: no es mineria"

    return "VALIDO"


total = 0
validos = 0
descartados = 0

enviar("RADAR MINERO V6 INICIADO")


for url in URLS:

    html = requests.get(url).text

    soup = BeautifulSoup(html,"html.parser")

    links = soup.find_all("a")

    for link in links:

        texto = link.get_text().strip()

        if texto == "":
            continue

        total += 1

        resultado = analizar(texto)

        if resultado == "VALIDO":

            validos += 1

            enviar(
f"""⛏ EMPLEO DETECTADO

{texto}

{link.get('href')}
"""
)

        else:

            descartados += 1


enviar(f"""

RADAR FINALIZADO

Revisados: {total}

Validos: {validos}

Descartados: {descartados}

""")
