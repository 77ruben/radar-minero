from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import time

CAREER_URL = "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

print("🌐 Iniciando Chrome...")
driver = webdriver.Chrome(options=options)

try:
    driver.get(CAREER_URL)
    time.sleep(8)

    logs = driver.get_log("performance")
    print(f"📊 Total logs de performance: {len(logs)}")

    for entry in logs:
        try:
            msg = json.loads(entry["message"])["message"]
            if msg.get("method") == "Network.responseReceived":
                url = msg.get("params", {}).get("response", {}).get("url", "")
                if "getInitialJobSearchData" in url:
                    req_id = msg["params"]["requestId"]
                    body = driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": req_id})
                    text = body.get("body", "")
                    print(f"\n✅ DWR encontrado! ({len(text)} chars)")
                    print(f"📄 Contenido completo:\n{text[:2000]}")
        except:
            pass

finally:
    driver.quit()
