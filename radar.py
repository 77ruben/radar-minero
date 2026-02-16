import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

def enviar(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    requests.post(url, data=data)

def buscar_indeed():
    url = "https://cl.indeed.com/jobs?q=mining&l=Chile"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    resultados = []

    for job in soup.select("h2.jobTitle"):
        titulo = job.text.strip()
        link = "https://cl.indeed.com" + job.a["href"]
        resultados.append(f"{titulo}\n{link}")

    return resultados

def buscar_chiletrabajos():
    url = "https://www.chiletrabajos.cl/busqueda?search=minera"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    resultados = []

    for job in soup.select(".job-item a"):
        titulo = job.text.strip()
        link = job["href"]
        resultados.append(f"{titulo}\n{link}")

    return resultados

def main():

    resultados = []

    resultados.extend(buscar_indeed())
    resultados.extend(buscar_chiletrabajos())

    if resultados:
        enviar("⛏ RADAR MINERO\n\n" + "\n\n".join(resultados[:10]))
    else:
        enviar("Sin novedades hoy")

main()
