import requests
import time
import re

BASE_URL = "https://career8.successfactors.com"
CAREER_URL = f"{BASE_URL}/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"
DWR_URL = f"{BASE_URL}/xi/ajax/remoting/call/plaincall/careerJobSearchControllerProxy.getInitialJobSearchData.dwr"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
})

# Paso 1: obtener sesión visitando la página principal
print("🔄 Paso 1: obteniendo sesión...")
r1 = session.get(CAREER_URL, timeout=30)
print(f"   Status: {r1.status_code}")
print(f"   Cookies: {dict(session.cookies)}")

# Extraer scriptSessionId si viene en el HTML
script_session = re.search(r'scriptSessionId["\s:=]+([A-F0-9]+)', r1.text)
if script_session:
    script_id = script_session.group(1) + "8"
    print(f"   scriptSessionId encontrado: {script_id}")
else:
    script_id = f"{int(time.time()*1000)}8"
    print(f"   scriptSessionId generado: {script_id}")

# Paso 2: llamar al DWR con la sesión activa
print("\n🔄 Paso 2: llamando DWR...")
session.headers.update({
    "Content-Type": "text/plain",
    "Origin": BASE_URL,
    "Referer": CAREER_URL,
})

payload = (
    "callCount=1\n"
    "page=/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH\n"
    "httpSessionId=\n"
    f"scriptSessionId={script_id}\n"
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

r2 = session.post(DWR_URL, data=payload, timeout=30)
print(f"   Status: {r2.status_code}")
print(f"\n📄 Respuesta (primeros 2000 chars):")
print(r2.text[:2000])
