import requests
import time

DWR_URL = "https://career8.successfactors.com/xi/ajax/remoting/call/plaincall/careerJobSearchControllerProxy.getInitialJobSearchData.dwr"

DWR_HEADERS = {
    "Content-Type": "text/plain",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://career8.successfactors.com",
    "Referer": "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH",
}

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

r = requests.post(DWR_URL, headers=DWR_HEADERS, data=payload, timeout=30)

print(f"Status code: {r.status_code}")
print(f"Primeros 2000 caracteres de la respuesta:")
print(r.text[:2000])
