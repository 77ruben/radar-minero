import requests
from bs4 import BeautifulSoup

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

KEYWORDS = [
    "supervisor",
    "mantencion",
    "maintenance",
    "planner",
    "planificador",
    "contrato",
    "contract",
    "minera",
    "mining"
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

    try:
        r = requests.post(url, data=data)

        print("TELEGRAM STATUS:", r.status_code)
        print("TELEGRAM RESPUESTA:", r.text)

    except Exception as e:

        print("ERROR TELEGRAM:", e)


# =========================

def cumple(texto):

    texto = texto.lower()

    return any(k in texto for k in KEYWORDS)


# =========================

def buscar():

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(URL, headers=headers)

        soup = BeautifulSoup(response.text, "html.parser")

        trabajos = soup.select("h2.jobTitle")

        encontrados = []

        for trabajo in trabajos:

            titulo = trabajo.get_text()

            if cumple(titulo):

                encontrados.append(titulo)


        if len(encontrados) == 0:

            enviar_telegram(
                "📡 Radar Minero\n\n❌ No hay empleos según tus requerimientos hoy"
            )

        else:

            mensaje = "📡 Radar Minero\n\n✅ Empleos encontrados:\n\n"

            for e in encontrados:

                mensaje += f"• {e}\n"

            enviar_telegram(mensaje)


    except Exception as e:

        enviar_telegram(
            f"⚠️ Radar Minero ERROR:\n\n{e}"
        )


# =========================

if __name__ == "__main__":

    enviar_telegram("🤖 Radar Minero iniciado")

    buscar()

