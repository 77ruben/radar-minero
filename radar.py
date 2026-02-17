import requests
from bs4 import BeautifulSoup
import os

print("INICIO RADAR MINERO PRO")

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

KEYWORDS = [

    "supervisor",
    "mantencion",
    "mantenimiento",
    "planner",
    "planificador",
    "ingeniero",
    "confiabilidad",
    "administrador",
    "contrato",
    "maintenance",
    "jefe",
    "scheduler"

]

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

encontrados = []

# =====================
# INDEED (FUNCIONA 100%)
# =====================

print("Buscando Indeed")

for pagina in range(0, 50, 10):

    URL = f"https://cl.indeed.com/jobs?q=mineria&l=Chile&sort=date&start={pagina}"

    response = requests.get(URL, headers=HEADERS)

    soup = BeautifulSoup(response.text, "html.parser")

    jobs = soup.select(".job_seen_beacon")

    for job in jobs:

        titulo = job.select_one("h2").text.strip()

        titulo_lower = titulo.lower()

        link = job.select_one("a")["href"]

        link = "https://cl.indeed.com" + link

        if any(p in titulo_lower for p in KEYWORDS):

            encontrados.append(

                "INDEED\n" +
                titulo + "\n" +
                link

            )


# =====================
# TRABAJANDO.CL
# =====================

print("Buscando Trabajando")

try:

    URL = "https://www.trabajando.cl/trabajo-empleo/mineria"

    response = requests.get(URL, headers=HEADERS)

    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.find_all("a")

    for link in links:

        titulo = link.text.strip()

        href = link.get("href")

        if titulo and href:

            titulo_lower = titulo.lower()

            if any(p in titulo_lower for p in KEYWORDS):

                encontrados.append(

                    "TRABAJANDO\n" +
                    titulo + "\n" +
                    href

                )

except:

    print("Trabajando bloqueado")


# =====================
# LIMPIAR DUPLICADOS
# =====================

encontrados = list(dict.fromkeys(encontrados))

print("Total encontrados:", len(encontrados))


# =====================
# MENSAJE
# =====================

if encontrados:

    mensaje = "🚨 RADAR MINERO PRO 🚨\n\n"

    for e in encontrados[:15]:

        mensaje += e + "\n\n"

else:

    mensaje = "Radar activo.\nSin empleos nuevos."


# =====================
# TELEGRAM
# =====================

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {

    "chat_id": CHAT_ID,
    "text": mensaje

}

requests.post(url, data=data)

print("FIN RADAR")
encontrados = []

# =========================
# INDEED CHILE (3 paginas)
# =========================

print("Buscando en Indeed")

for pagina in range(0, 30, 10):

    URL = f"https://cl.indeed.com/jobs?q=mineria&l=Chile&sort=date&start={pagina}"

    try:

        response = requests.get(URL, headers=headers)

        soup = BeautifulSoup(response.text, "html.parser")

        jobs = soup.select(".job_seen_beacon")

        for job in jobs:

            titulo = job.select_one("h2").text.strip()

            titulo_lower = titulo.lower()

            link = job.select_one("a")["href"]

            link = "https://cl.indeed.com" + link

            if any(p in titulo_lower for p in KEYWORDS):

                encontrados.append(
                    "INDEED\n" +
                    titulo + "\n" +
                    link
                )

    except:

        print("Error Indeed")


# =========================
# CHILETRABAJOS
# =========================

print("Buscando en Chiletrabajos")

try:

    URL = "https://www.chiletrabajos.cl/trabajos/?q=mineria"

    response = requests.get(URL, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.select("a")

    for link in links:

        titulo = link.text.strip()

        href = link.get("href")

        if titulo and href:

            titulo_lower = titulo.lower()

            if any(p in titulo_lower for p in KEYWORDS):

                encontrados.append(

                    "CHILETRABAJOS\n" +
                    titulo + "\n" +
                    href
                )

except:

    print("Error Chiletrabajos")


# =========================
# LABORUM
# =========================

print("Buscando en Laborum")

try:

    URL = "https://www.laborum.cl/empleos-industria-mineria.html"

    response = requests.get(URL, headers=headers)

    soup = BeautifulSoup(response.text, "html.parser")

    links = soup.select("a")

    for link in links:

        titulo = link.text.strip()

        href = link.get("href")

        if titulo and href:

            titulo_lower = titulo.lower()

            if any(p in titulo_lower for p in KEYWORDS):

                encontrados.append(

                    "LABORUM\n" +
                    titulo + "\n" +
                    href
                )

except:

    print("Error Laborum")


# =========================
# ELIMINAR DUPLICADOS
# =========================

encontrados = list(dict.fromkeys(encontrados))

print("Total encontrados:", len(encontrados))


# =========================
# MENSAJE TELEGRAM
# =========================

if encontrados:

    mensaje = "🚨 RADAR MINERO PRO 🚨\n\n"

    for e in encontrados[:15]:

        mensaje += e + "\n\n"

else:

    mensaje = "Radar Minero activo.\nSin empleos nuevos compatibles."


# =========================
# ENVIAR TELEGRAM
# =========================

urlTelegram = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {

    "chat_id": CHAT_ID,
    "text": mensaje

}

requests.post(urlTelegram, data=data)

print("FIN RADAR MINERO PRO")


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
