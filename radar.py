import requests
import os
import json
import re
import time
from datetime import datetime

TOKEN      = os.environ["TOKEN"]
CHAT_ID    = os.environ["CHAT_ID"]
GEMINI_KEY = os.environ.get("GEMINI_KEY", "")

TELEGRAM_URL   = f"https://api.telegram.org/bot{TOKEN}"
SEEN_FILE      = "seen_jobs.json"
MEMORIA_FILE   = "memoria.json"
HISTORIAL_FILE = "historial.json"

def cargar_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def guardar_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ── SCRAPER ANGLO AMERICAN ──────────────────────────────────────────
AA_URL = "https://www.angloamerican.com/site-services/search-and-apply-data-fetch"
AA_PARAMS = {
    "aadata": "get-search-jobs",
    "languageCode": "en-GB",
    "workType": "", "businessUnitOrGroupFunction": "",
    "discipline": "", "experience": "",
    "searchText": "", "city": "", "country": "chile"
}
AA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.angloamerican.com/careers/job-opportunities",
}

def fetch_anglo_jobs():
    try:
        r = requests.get(AA_URL, params=AA_PARAMS, headers=AA_HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        jobs = []
        for item in data.get("jobs", []):
            loc = item.get("location", {})
            job_id = item.get("id") or item.get("jobId") or item.get("uuid", "")
            jobs.append({
                "id": f"aa_{job_id}",
                "title": item.get("jobTitle", "Sin título"),
                "date": item.get("releasedDate", "")[:10] if item.get("releasedDate") else "N/A",
                "closing": item.get("closingDate", "N/A"),
                "ciudad": loc.get("city", "Chile"),
                "faena": loc.get("address", ""),
                "url": item.get("applyUrl", "https://www.angloamerican.com/careers/job-opportunities"),
                "empresa": "Anglo American",
            })
        print(f"✅ Anglo American: {len(jobs)} empleos encontrados")
        return jobs
    except Exception as e:
        print(f"❌ Error Anglo American: {e}")
        return []

# ── GEMINI IA ───────────────────────────────────────────────────────
def analizar_con_gemini(job, memoria):
    if not GEMINI_KEY:
        return None
    prompt = f"""Analiza esta oferta minera y decide si es relevante para el usuario.
OFERTA: {job['title']} | {job['empresa']} | {job['faena']} {job['ciudad']} | Cierra: {job['closing']}
PREFERENCIAS: turnos_buenos={memoria.get('turnos_buenos',[])} empresas_malas={memoria.get('empresas_malas',[])} ciudades_malas={memoria.get('ciudades_malas',[])} rechazados={memoria.get('rechazados',[])[-5:]} aceptados={memoria.get('aceptados',[])[-5:]}
Responde SOLO con JSON sin markdown: {{"relevante": true, "razon": "texto corto"}}"""
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=20
        )
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(re.sub(r"```json|```", "", text).strip())
    except Exception as e:
        print(f"⚠️ Gemini error: {e}")
        return None

# ── TELEGRAM ────────────────────────────────────────────────────────
def enviar_telegram(mensaje):
    try:
        requests.get(f"{TELEGRAM_URL}/sendMessage", params={
            "chat_id": CHAT_ID, "text": mensaje,
            "parse_mode": "HTML", "disable_web_page_preview": False
        }, timeout=15).raise_for_status()
        print(f"✅ Enviado: {mensaje[:60]}...")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def formatear_mensaje(job, gemini=None):
    msg = (
        f"⛏️ <b>NUEVO EMPLEO MINERO</b>\n\n"
        f"🏢 <b>{job['empresa']}</b>\n"
        f"📋 <b>{job['title']}</b>\n"
        f"📍 {job['faena']} — {job['ciudad']}\n"
        f"📅 Publicado: {job['date']}  |  Cierra: {job['closing']}\n"
    )
    if gemini:
        msg += f"{'✅' if gemini.get('relevante') else '⚠️'} IA: {gemini.get('razon','')}\n"
    msg += f"🔗 <a href='{job['url']}'>Ver oferta</a>"
    return msg

# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando Radar Minero...")

    seen      = set(cargar_json(SEEN_FILE, []))
    memoria   = cargar_json(MEMORIA_FILE, {
        "rechazados": [], "aceptados": [],
        "empresas_buenas": [], "empresas_malas": [],
        "ciudades_malas": [], "turnos_buenos": ["7x7", "10x10", "14x14", "4x3"]
    })
    historial = cargar_json(HISTORIAL_FILE, [])

    todos_jobs = fetch_anglo_jobs()
    # todos_jobs += fetch_otra_empresa()  # agregar más fuentes aquí

    print(f"📊 Total encontrados: {len(todos_jobs)}")
    nuevos = [j for j in todos_jobs if j["id"] not in seen]
    print(f"🆕 Nuevos: {len(nuevos)}")

    enviados = 0
    for job in nuevos:
        gemini = analizar_con_gemini(job, memoria)
        enviar_telegram(formatear_mensaje(job, gemini))
        historial.append({
            "id": job["id"], "title": job["title"],
            "empresa": job["empresa"], "ciudad": job["ciudad"],
            "date": job["date"], "enviado": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ia_relevante": gemini.get("relevante") if gemini else None
        })
        seen.add(job["id"])
        enviados += 1
        time.sleep(1)

    guardar_json(SEEN_FILE, list(seen))
    guardar_json(HISTORIAL_FILE, historial[-500:])
    print(f"✅ Sin empleos nuevos." if enviados == 0 else f"📬 {enviados} empleos enviados.")

if __name__ == "__main__":
    main()
