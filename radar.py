import requests
from bs4 import BeautifulSoup

# =========================
# CONFIGURACION
# =========================

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

KEYWORDS = [
    "mining",
    "minera",
    "miner",
    "supervisor",
    "planner",
    "planificador",
    "mantencion",
    "maintenance",
    "contratos",
    "contract"
]

URL = "https://cl.indeed.com/jobs?q=mining&l=Chile"

# =========================
# TELEGRAM
# =========================

def enviar_telegram(texto):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": texto
    }

    requests.post(url, data=data)


# =========================
# FILTRO
# =========================

def cumple(texto):

    texto = texto.lower()

    return any(k in texto for k in KEYWORDS)


# =========================
# BUSQUEDA
# =========================

def buscar():

    response = requests.get(URL)

    soup = BeautifulSoup(response.text, "html.parser")

    trabajos = soup.select("h2.jobTitle")

    encontrados = []

    for trabajo in trabajos:

        titulo = trabajo.get_text()

        if cumple(titulo):

            encontrados.append(titulo)


    # =========================
    # RESULTADO
    # =========================

    if len(encontrados) == 0:

        enviar_telegram(
            "📡 Radar Minero\n\n❌ No hay empleos según tus requerimientos hoy"
        )

    else:

        mensaje = "📡 Radar Minero\n\n✅ Empleos encontrados:\n\n"

        for e in encontrados:

            mensaje += f"• {e}\n"

        enviar_telegram(mensaje)


# =========================

if __name__ == "__main__":

    buscar()
