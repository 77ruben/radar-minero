import requests
import re
import os
import json
import time
from datetime import datetime

# ─────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────
TOKEN    = os.environ["TOKEN"]
CHAT_ID  = os.environ["CHAT_ID"]
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")

TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}"
SEEN_FILE    = "seen_jobs.json"
MEMORIA_FILE = "memoria.json"
HISTORIAL_FILE = "historial.json"

# ─────────────────────────────────────────
#  HELPERS JSON
# ─────────────────────────────────────────
def cargar_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def guardar_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────
#  SCRAPER ANTOFAGASTA MINERALS (DWR)
# ─────────────────────────────────────────
DWR_URL = "https://career8.successfactors.com/xi/ajax/remoting/call/plaincall/careerJobSearchControllerProxy.getInitialJobSearchData.dwr"
DETAIL_PREFIX = "https://career8.successfactors.com/career?career_ns=job_listing&company=AMSAP&navBarLevel=JOB_SEARCH&rcm_site_locale=es_ES&career_job_req_id="

DWR_HEADERS = {
    "Content-Type": "text/plain",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://career8.successfactors.com",
    "Referer": "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH",
}

def fetch_amsa_jobs():
    """Scrapea empleos de Antofagasta Minerals vía DWR"""
    payload = (
        "callCount=1\n"
        "page=/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH\n"
        "httpSessionId=\n"
        f"scriptSessionId={int(time.time()*1000)}8\n"
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
        r = requests.post(DWR_URL, headers=DWR_HEADERS, data=payload, timeout=30)
        r.raise_for_status()
        return parse_dwr(r.text)
    except Exception as e:
        print(f"❌ Error AMSA: {e}")
        return []

def parse_dwr(text):
    """Parsea respuesta DWR y extrae empleos"""
    jobs = []
    titles = {m.group(1): m.group(2) for m in re.finditer(r'(s\d+)\.title\s*=\s*"([^"]+)"', text)}
    ids    = {m.group(1): m.group(2) for m in re.finditer(r'(s\d+)\.id\s*=\s*(\d+)', text)}
    dates  = {m.group(1): m.group(2) for m in re.finditer(r'(s\d+)\.postingDate\s*=\s*"([^"]+)"', text)}

    # Extraer empresa/mina por variable
    companies = {}
    for m in re.finditer(r'(s\d+)\.shortVal\s*=\s*"([^"]+)"', text):
        companies[m.group(1)] = m.group(2)

    for var in set(titles.keys()) & set(ids.keys()):
        title = titles[var]
        # Decodificar unicode escapes
        title = title.encode().decode('unicode_escape') if '\\u' in title else title
        jobs.append({
            "id": f"amsa_{ids[var]}",
            "title": title,
            "date": dates.get(var, "N/A"),
            "url": DETAIL_PREFIX + ids[var],
            "empresa": "Antofagasta Minerals",
            "fuente": "AMSA"
        })

    jobs.sort(key=lambda x: x["date"], reverse=True)
    return jobs

# ─────────────────────────────────────────
#  ANÁLISIS CON GEMINI IA
# ─────────────────────────────────────────
def analizar_con_gemini(job, memoria):
    """Usa Gemini para evaluar si el empleo es relevante según memoria"""
    if not GEMINI_KEY:
        return None

    prompt = f"""Eres un asistente de búsqueda de empleo minero en Chile.
Analiza esta oferta y decide si es relevante para el usuario.

OFERTA:
- Título: {job['title']}
- Empresa: {job['empresa']}
- Fecha: {job['date']}

PREFERENCIAS DEL USUARIO:
- Turnos buenos: {memoria.get('turnos_buenos', [])}
- Empresas buenas: {memoria.get('empresas_buenas', [])}
- Empresas malas: {memoria.get('empresas_malas', [])}
- Ciudades malas: {memoria.get('ciudades_malas', [])}
- Cargos rechazados antes: {memoria.get('rechazados', [])[-10:]}
- Cargos aceptados antes: {memoria.get('aceptados', [])[-10:]}

Responde SOLO con un JSON así:
{{"relevante": true/false, "razon": "texto corto explicando por qué"}}"""

    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20
        )
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        return None

# ─────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────
def enviar_telegram(mensaje):
    try:
        r = requests.get(
            f"{TELEGRAM_URL}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": mensaje,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            },
            timeout=15
        )
        r.raise_for_status()
        print(f"✅ Telegram: {mensaje[:60]}...")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def formatear_mensaje(job, gemini_result=None):
    msg = (
        f"⛏️ <b>NUEVO EMPLEO MINERO</b>\n\n"
        f"🏢 <b>{job['empresa']}</b>\n"
        f"📋 <b>{job['title']}</b>\n"
        f"📅 Publicado: {job['date']}\n"
    )
    if gemini_result:
        emoji = "✅" if gemini_result.get("relevante") else "⚠️"
        msg += f"{emoji} IA: {gemini_result.get('razon', '')}\n"

    msg += f"🔗 <a href='{job['url']}'>Ver oferta</a>"
    return msg

# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
def main():
    print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando Radar Minero...")

    seen     = set(cargar_json(SEEN_FILE, []))
    memoria  = cargar_json(MEMORIA_FILE, {
        "rechazados": [], "aceptados": [],
        "empresas_buenas": [], "empresas_malas": [],
        "ciudades_malas": [], "turnos_buenos": ["7x7", "10x10", "14x14", "4x3"]
    })
    historial = cargar_json(HISTORIAL_FILE, [])

    # --- Scraping ---
    todos_jobs = fetch_amsa_jobs()
    # Aquí puedes agregar más fuentes: todos_jobs += fetch_codelco_jobs(), etc.

    print(f"📊 Total encontrados: {len(todos_jobs)}")
    nuevos = [j for j in todos_jobs if j["id"] not in seen]
    print(f"🆕 Nuevos: {len(nuevos)}")

    enviados = 0
    for job in nuevos:
        # Análisis IA
        gemini = analizar_con_gemini(job, memoria)

        # Enviar a Telegram (si IA dice no relevante, igual envía pero con advertencia)
        msg = formatear_mensaje(job, gemini)
        enviar_telegram(msg)

        # Guardar en historial
        historial.append({
            "id": job["id"],
            "title": job["title"],
            "empresa": job["empresa"],
            "date": job["date"],
            "enviado": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ia_relevante": gemini.get("relevante") if gemini else None
        })

        seen.add(job["id"])
        enviados += 1
        time.sleep(1)

    # Guardar estado
    guardar_json(SEEN_FILE, list(seen))
    guardar_json(HISTORIAL_FILE, historial[-500:])  # máximo 500 registros

    if enviados == 0:
        print("✅ Sin empleos nuevos esta vez.")
    else:
        print(f"📬 {enviados} empleos enviados a Telegram.")

if __name__ == "__main__":
    main()
