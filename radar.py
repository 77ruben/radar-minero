import requests
import re
import json
import time
import hashlib
import os
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIGURACIÓN TELEGRAM
# ─────────────────────────────────────────
TELEGRAM_TOKEN = "TU_TOKEN_AQUI"       # @BotFather
TELEGRAM_CHAT_ID = "TU_CHAT_ID_AQUI"  # tu chat ID

# ─────────────────────────────────────────
#  CONFIGURACIÓN SCRAPER
# ─────────────────────────────────────────
DWR_URL = "https://career8.successfactors.com/xi/ajax/remoting/call/plaincall/careerJobSearchControllerProxy.getInitialJobSearchData.dwr"
DETAIL_URL_PREFIX = "https://career8.successfactors.com/career?career_ns=job_listing&company=AMSAP&navBarLevel=JOB_SEARCH&rcm_site_locale=es_ES&career_job_req_id="
CACHE_FILE = "amsa_jobs_cache.json"

HEADERS = {
    "Content-Type": "text/plain",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://career8.successfactors.com",
    "Referer": "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH",
}

# ─────────────────────────────────────────
#  FUNCIONES PRINCIPALES
# ─────────────────────────────────────────

def get_script_session_id():
    """Genera un scriptSessionId válido"""
    return hashlib.md5(str(time.time()).encode()).hexdigest().upper() + "8"


def fetch_jobs():
    """Llama al endpoint DWR y retorna lista de empleos"""
    script_session_id = get_script_session_id()

    payload = (
        "callCount=1\n"
        "page=/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH\n"
        "httpSessionId=\n"
        f"scriptSessionId={script_session_id}\n"
        "c0-scriptName=careerJobSearchControllerProxy\n"
        "c0-methodName=getInitialJobSearchData\n"
        "c0-id=0\n"
        "c0-e1=string:\n"
        "c0-e2=string:\n"
        "c0-e3=string:\n"
        "c0-e4=string:America%2FSantiago\n"
        "c0-param0=Object_Object:{filterOnly:reference:c0-e1, jobAlertId:reference:c0-e2, returnToList:reference:c0-e3, browserTimeZone:reference:c0-e4}\n"
        "batchId=0\n"
    )

    try:
        response = requests.post(DWR_URL, headers=HEADERS, data=payload, timeout=30)
        response.raise_for_status()
        return parse_dwr_response(response.text)
    except requests.RequestException as e:
        print(f"❌ Error al conectar: {e}")
        return []


def parse_dwr_response(text):
    """Parsea la respuesta DWR y extrae los empleos"""
    jobs = []

    # Extraer todos los objetos s## que tienen .title
    title_pattern = re.compile(r'(s\d+)\.title\s*=\s*"([^"]+)"')
    id_pattern = re.compile(r'(s\d+)\.id\s*=\s*(\d+)')
    date_pattern = re.compile(r'(s\d+)\.postingDate\s*=\s*"([^"]+)"')

    titles = {m.group(1): m.group(2) for m in title_pattern.finditer(text)}
    ids = {m.group(1): m.group(2) for m in id_pattern.finditer(text)}
    dates = {m.group(1): m.group(2) for m in date_pattern.finditer(text)}

    # Unir por variable (s27, s28, etc.)
    all_vars = set(titles.keys()) & set(ids.keys())
    for var in all_vars:
        job = {
            "id": ids[var],
            "title": titles[var].replace("\\u00F3", "ó").replace("\\u00FA", "ú").replace("\\u00E9", "é"),
            "date": dates.get(var, "N/A"),
            "url": DETAIL_URL_PREFIX + ids[var],
            "source": "Antofagasta Minerals"
        }
        jobs.append(job)

    # Ordenar por fecha descendente
    jobs.sort(key=lambda x: x["date"], reverse=True)
    return jobs


def load_cache():
    """Carga los IDs de empleos ya enviados"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_cache(seen_ids):
    """Guarda los IDs de empleos ya enviados"""
    with open(CACHE_FILE, "w") as f:
        json.dump(list(seen_ids), f)


def send_telegram(message):
    """Envía mensaje a Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        print(f"✅ Telegram enviado: {message[:60]}...")
    except requests.RequestException as e:
        print(f"❌ Error Telegram: {e}")


def format_job_message(job):
    """Formatea el mensaje de Telegram para un empleo"""
    return (
        f"⛏️ <b>NUEVO EMPLEO MINERO</b>\n\n"
        f"🏢 <b>{job['source']}</b>\n"
        f"📋 {job['title']}\n"
        f"📅 Publicado: {job['date']}\n"
        f"🔗 <a href='{job['url']}'>Ver oferta completa</a>"
    )


# ─────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────

def run():
    print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Buscando empleos en Antofagasta Minerals...")

    seen_ids = load_cache()
    jobs = fetch_jobs()

    if not jobs:
        print("⚠️  No se encontraron empleos o hubo un error.")
        return

    print(f"📊 Total empleos encontrados: {len(jobs)}")
    new_jobs = [j for j in jobs if j["id"] not in seen_ids]
    print(f"🆕 Nuevos empleos: {len(new_jobs)}")

    for job in new_jobs:
        msg = format_job_message(job)
        send_telegram(msg)
        seen_ids.add(job["id"])
        time.sleep(1)  # pausa entre mensajes

    save_cache(seen_ids)

    if not new_jobs:
        print("✅ Sin novedades.")


if __name__ == "__main__":
    # Ejecutar cada 4 horas
    while True:
        run()
        print(f"\n⏳ Próxima revisión en 4 horas...")
        time.sleep(4 * 60 * 60)
