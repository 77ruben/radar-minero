import requests
from bs4 import BeautifulSoup
import telegram

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

bot = telegram.Bot(token=TOKEN)

KEYWORDS_CARGO = [
    "supervisor",
    "administrador de contrato",
    "jefe de turno",
    "supervisor mantencion",
    "planner",
    "confiabilidad",
    "mantenimiento"
]

KEYWORDS_TURNO = [
    "14x14",
    "10x10",
    "7x7",
    "4x3"
]

KEYWORDS_MINERIA = [
    "minera",
    "mineria",
    "faena",
    "codelco",
    "bhp",
    "kinross",
    "collahuasi",
    "candelaria",
    "antofagasta minerals",
    "anglo american",
    "teck"
]


def cumple_filtro(texto):

    texto = texto.lower()

    cargo = any(k in texto for k in KEYWORDS_CARGO)

    turno = any(k in texto for k in KEYWORDS_TURNO)

    mineria = any(k in texto for k in KEYWORDS_MINERIA)

    return cargo and mineria


def buscar_indeed():

    url = "https://cl.indeed.com/jobs?q=mineria&l=Chile"

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    trabajos = soup.select("h2.jobTitle")

    encontrados = []

    for trabajo in trabajos:

        titulo = trabajo.get_text()

        if cumple_filtro(titulo):

            encontrados.append("Indeed: " + titulo)

    return encontrados


def buscar_chiletrabajos():

    url = "https://www.chiletrabajos.cl/busqueda?q=mineria"

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    trabajos = soup.select(".job-title")

    encontrados = []

    for trabajo in trabajos:

        titulo = trabajo.get_text()

        if cumple_filtro(titulo):

            encontrados.append("Chiletrabajos: " + titulo)

    return encontrados


def buscar_laborum():

    url = "https://www.laborum.cl/empleos-busqueda-mineria.html"

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    trabajos = soup.select("h2")

    encontrados = []

    for trabajo in trabajos:

        titulo = trabajo.get_text()

        if cumple_filtro(titulo):

            encontrados.append("Laborum: " + titulo)

    return encontrados


def enviar_telegram(lista):

    if not lista:

        print("Sin resultados")

        return

    mensaje = "🚨 RADAR MINERO PRO\n\n"

    for item in lista:

        mensaje += item + "\n"

    bot.send_message(chat_id=CHAT_ID, text=mensaje)


def main():

    resultados = []

    resultados.extend(buscar_indeed())

    resultados.extend(buscar_chiletrabajos())

    resultados.extend(buscar_laborum())

    print("Encontrados:", len(resultados))

    enviar_telegram(resultados)


if __name__ == "__main__":

    main()
