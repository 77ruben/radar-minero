import requests
from bs4 import BeautifulSoup
import telegram
import os

# =========================
# CONFIGURACION
# =========================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telegram.Bot(token=TOKEN)

# Palabras clave
KEYWORDS = [
    "supervisor",
    "administrador",
    "contrato",
    "planificacion",
    "planificador",
    "mantencion",
    "mantenimiento",
    "ingeniero",
]

# Sitios a revisar
URLS = {

    "Trabajando": "https://www.trabajando.cl/trabajo-empleo/mineria",

    "Laborum": "https://www.laborum.cl/empleos-industria-mineria.html",

    "Chiletrabajos": "https://www.chiletrabajos.cl/trabajos/?q=mineria",

    "BNE": "https://www.bne.cl/ofertas?textoBusqueda=mineria",

}

# =========================
# FUNCIONES
# =========================

def cumple(texto):

    texto = texto.lower()

    return any(k in texto for k in KEYWORDS)


def buscar():

    encontrados = []

    for nombre, url in URLS.items():

        try:

            r = requests.get(url, timeout=15)

            soup = BeautifulSoup(r.text, "html.parser")

            links = soup.find_all("a")

            for link in links:

                titulo = link.get_text().strip()

                href = link.get("href")

                if titulo and href:

                    if cumple(titulo):

                        if href.startswith("/"):

                            href = url + href

                        encontrados.append(
                            f"{nombre}\n{titulo}\n{href}"
                        )

        except Exception as e:

            print("Error en", nombre, e)

    return encontrados


def enviar(lista):

    if not lista:

        print("Sin resultados")

        return

    for item in lista:

        bot.send_message(

            chat_id=CHAT_ID,

            text="🚨 Radar Minero\n\n" + item

        )


# =========================
# EJECUCION
# =========================

resultado = buscar()

print("Encontrados:", len(resultado))

enviar(resultado)

print("Finalizado")    "anglo american",
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
