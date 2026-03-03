import requests
import re
import time

BASE_URL   = "https://career8.successfactors.com"
CAREER_URL = f"{BASE_URL}/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"
DWR_URL    = f"{BASE_URL}/xi/ajax/remoting/call/plaincall/careerJobSearchControllerProxy.getInitialJobSearchData.dwr"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
})

# Paso 1: obtener página principal
print("🔄 Paso 1: cargando página...")
r1 = session.get(CAREER_URL, timeout=30)
print(f"   Status: {r1.status_code}")
print(f"   Cookies: {dict(session.cookies)}")

# Buscar scriptSessionId en el HTML
patterns = [
    r'BATCH_ID\s*=\s*["\']?(\w+)',
    r'scriptSessionId["\s=:]+([A-F0-9]{30,})',
    r'dwr\.engine\.setSessionId\(["\']([^"\']+)',
    r'dwr\.engine\._sessionId\s*=\s*["\']([^"\']+)',
    r'"sessionId"\s*:\s*"([^"]+)"',
]

print("\n🔍 Buscando scriptSessionId en el HTML...")
found = False
for pat in patterns:
    m = re.search(pat, r1.text, re.IGNORECASE)
    if m:
        print(f"   ✅ Encontrado con patrón '{pat}': {m.group(1)}")
        found = True

if not found:
    print("   ❌ No encontrado en HTML")

# Buscar cualquier referencia a DWR en el HTML
dwr_refs = re.findall(r'(dwr[^\s"\'<>]{0,80})', r1.text, re.IGNORECASE)
print(f"\n🔍 Referencias DWR en HTML ({len(dwr_refs)} encontradas):")
for ref in dwr_refs[:10]:
    print(f"   {ref}")

# Paso 2: intentar cargar el JS de DWR para obtener el sessionId
print("\n🔄 Paso 2: cargando engine.js de DWR...")
engine_urls = [
    f"{BASE_URL}/xi/ajax/remoting/util/dwr/engine.js",
    f"{BASE_URL}/dwr/engine.js",
    f"{BASE_URL}/xi/dwr/engine.js",
]
for url in engine_urls:
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200 and len(r.text) > 100:
            print(f"   ✅ engine.js encontrado en: {url} ({len(r.text)} chars)")
            # Buscar sessionId en el engine
            m = re.search(r'sessionId["\s=:]+([A-F0-9]{20,})', r.text)
            if m:
                print(f"   scriptSessionId: {m.group(1)}")
            break
        else:
            print(f"   ❌ {url} → {r.status_code}")
    except Exception as e:
        print(f"   ❌ {url} → {e}")

# Paso 3: intentar llamada DWR con httpSessionId de la cookie JSESSIONID
jsessionid = session.cookies.get("JSESSIONID", "")
script_id  = re.sub(r'[^A-F0-9]', '', jsessionid.upper())[:32] + "8" if jsessionid else f"{int(time.time()*1000)}8"

print(f"\n🔄 Paso 3: llamando DWR con scriptSessionId derivado de JSESSIONID...")
print(f"   JSESSIONID: {jsessionid}")
print(f"   scriptSessionId: {script_id}")

session.headers.update({
    "Content-Type": "text/plain",
    "Origin": BASE_URL,
    "Referer": CAREER_URL,
})

payload = (
    "callCount=1\n"
    f"page={CAREER_URL}\n"
    f"httpSessionId={jsessionid}\n"
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

r3 = session.post(DWR_URL, data=payload, timeout=30)
print(f"\n   Status: {r3.status_code}")
print(f"📄 Respuesta (primeros 500 chars):")
print(r3.text[:500])
