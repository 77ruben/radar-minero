import os
import asyncio
from playwright.async_api import async_playwright
import requests

print("INICIANDO RADAR ANTOFAGASTA MINERALS (PLAYWRIGHT V2)")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

URL = "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(8000)

        # Buscar todos los links que contengan jobReqId
        links = await page.query_selector_all("a[href*='jobReqId']")

        message = ""
        count = 0
        seen = set()

        for link in links:
            href = await link.get_attribute("href")
            title = await link.inner_text()

            if not href or href in seen:
                continue

            seen.add(href)

            if not href.startswith("http"):
                href = "https://career8.successfactors.com" + href

            if title.strip() == "":
                continue

            message += f"{title.strip()}\n{href}\n\n"
            count += 1

        await browser.close()

    if count == 0:
        message = "Radar Antofagasta Minerals activo.\nNo se detectaron empleos."
    else:
        message = f"🚨 EMPLEOS ANTOFAGASTA MINERALS ({count}) 🚨\n\n" + message

    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(telegram_url, data={
        "chat_id": CHAT_ID,
        "text": message[:4000]
    })

    print(f"Se detectaron {count} empleos")

asyncio.run(run())
