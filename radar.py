import requests
from bs4 import BeautifulSoup
import telegram
import os

# ==========================
# TELEGRAM
# ==========================

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = telegram.Bot(token=TOKEN)

# ==========================
# PALABRAS CLAVE (OPTIMIZADAS PARA TU PERFIL)
# ==========================

KEYWORDS = [

    "supervisor",
    "mantencion",
    "mantenimiento",
    "contrato",
    "contratos",
    "planificacion",
    "planificador",
    "ingeniero",
    "mineria",
    "minero",
    "confiabilidad"

]

# ==========================
# PAGINAS REALES MINERAS
# ==========================

URLS = {

    "Laborum":

    "https://www.laborum.cl/empleos-busqueda-mineria.html",


    "Chiletrabajos":

    "https://www.chiletrabajos.cl/buscar/mineria",


    "Trabajando":

    "https://www.trabajando.cl/trabajo-empleo/mineria"

}


# ==========================
# BUSCAR EMPLEOS
# ==========================

def cumple(texto):

    texto = texto.lower()

    return any(k in texto for k in KEYWORDS)



def buscar():

    encontrados = []

    headers = {

        "User-Agent":

        "Mozilla/5.0"

    }


    for nombre, url in URLS.items():

        try:

            r = requests.get(url, headers=headers)

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

                            f"{titulo}\n{href}\n"

                        )

        except Exception as e:

            print("Error en", nombre, e)


    return encontrados



# ==========================
# ENVIAR TELEGRAM
# ==========================

def enviar():

    empleos = buscar()


    if empleos:

        mensaje = "🚨 EMPLEOS MINEROS ENCONTRADOS 🚨\n\n"

        mensaje += "\n".join(empleos[:10])

    else:

        mensaje = "⚠️ No encontró empleos nuevos según el filtro"


    bot.send_message(

        chat_id=CHAT_ID,

        text=mensaje

    )



# ==========================

# EJECUTAR

# ==========================

if __name__ == "__main__":

    enviar()
