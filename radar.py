import requests
import os
import json
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup

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

# ── SCRAPER ANGLO AMERICAN (API directa) ────────────────────────────
def fetch_anglo_jobs():
    url = "https://www.angloamerican.com/site-services/search-and-apply-data-fetch"
    params = {
        "aadata": "get-search-jobs", "languageCode": "en-GB",
        "workType": "", "businessUnitOrGroupFunction": "",
        "discipline": "", "experience": "",
        "searchText": "", "city": "", "country": "chile"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://www.angloamerican.com/careers/job-opportunities",
    }
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        jobs = []
        for item in r.json().get("jobs", []):
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

# ── SCRAPER ANTOFAGASTA MINERALS (Selenium + HTML) ───────────────────
def fetch_amsa_jobs():
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        CAREER_URL    = "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"
        BASE_URL      = "https://career8.successfactors.com"
        DETAIL_PREFIX = f"{BASE_URL}/career?career_ns=job_listing&company=AMSAP&navBarLevel=JOB_SEARCH&rcm_site_locale=es_ES&career_job_req_id="

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")

        print("   🌐 Iniciando Chrome con Selenium...")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(CAREER_URL)
            print("   ⏳ Esperando carga completa (15s)...")
            time.sleep(15)
            html = driver.page_source
            print(f"   📄 HTML obtenido: {len(html)} chars")
        finally:
            driver.quit()

        soup = BeautifulSoup(html, "html.parser")
        jobs = []

        # Buscar links de empleos — patron tipico de SuccessFactors
        # Los empleos suelen estar en elementos con career_job_req_id en la URL
        links = soup.find_all("a", href=re.compile(r"career_job_req_id=\d+"))
        print(f"   🔍 Links con career_job_req_id: {len(links)}")

        seen_ids = set()
        for link in links:
            href = link.get("href", "")
            m = re.search(r"career_job_req_id=(\d+)", href)
            if not m:
                continue
            job_id = m.group(1)
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                # buscar texto en elementos cercanos
                parent = link.find_parent()
                if parent:
                    title = parent.get_text(strip=True)[:100]

            url = href if href.startswith("http") else BASE_URL + href

            jobs.append({
                "id": f"amsa_{job_id}",
                "title": title,
                "date": "N/A",
                "closing": "N/A",
                "ciudad": "Chile",
                "faena": "Antofagasta Minerals",
                "url": url,
                "empresa": "Antofagasta Minerals",
            })

        # Si no encontramos con ese patrón, buscar por clases típicas de SuccessFactors
        if not jobs:
            print("   🔍 Intentando búsqueda por clases CSS...")
            # Buscar elementos con clase que contenga 'job' o 'posting'
            for cls in ["jobTitle", "job-title", "posting-title", "rcm-job-title"]:
                elements = soup.find_all(class_=re.compile(cls, re.IGNORECASE))
                if elements:
                    print(f"   Encontrados {len(elements)} elementos con clase '{cls}'")
                    for el in elements[:5]:
                        print(f"   → {el.get_text(strip=True)[:80]}")
                    break

            # Buscar cualquier texto que parezca título de trabajo minero
            all_text = soup.get_text()
            job_matches = re.findall(r'((?:Ingeniero|Técnico|Operador|Supervisor|Jefe|Gerente|Analista|Especialista)[^\n]{10,80})', all_text)
            print(f"   🔍 Posibles títulos en texto: {len(job_matches)}")
            for t in job_matches[:5]:
                print(f"   → {t.strip()}")

        print(f"✅ Antofagasta Minerals: {len(jobs)} empleos encontrados")
        return jobs

    except Exception as e:
        print(f"❌ Error AMSA Selenium: {e}")
        return []

# ── GEMINI IA ────────────────────────────────────────────────────────
def analizar_con_gemini(job, memoria):
    if not GEMINI_KEY:
        return None
    prompt = f"""Analiza esta oferta minera en Chile y decide si es relevante.
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

# ── TELEGRAM ─────────────────────────────────────────────────────────
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

# ── MAIN ──────────────────────────────────────────────────────────────
def main():
    print(f"\n🔍 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando Radar Minero...")

    seen      = set(cargar_json(SEEN_FILE, []))
    memoria   = cargar_json(MEMORIA_FILE, {
        "rechazados": [], "aceptados": [],
        "empresas_buenas": [], "empresas_malas": [],
        "ciudades_malas": [], "turnos_buenos": ["7x7", "10x10", "14x14", "4x3"]
    })
    historial = cargar_json(HISTORIAL_FILE, [])

    print("\n--- Anglo American ---")
    todos_jobs = fetch_anglo_jobs()

    print("\n--- Antofagasta Minerals ---")
    todos_jobs += fetch_amsa_jobs()

    print(f"\n📊 Total encontrados: {len(todos_jobs)}")
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
    print(f"\n✅ Sin empleos nuevos." if enviados == 0 else f"\n📬 {enviados} empleos enviados.")

if __name__ == "__main__":
    main()
