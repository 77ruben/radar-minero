import os
import asyncio
from playwright.async_api import async_playwright
import requests

print("INICIANDO RADAR ANTOFAGASTA MINERALS (PLAYWRIGHT)")

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
        await page.wait_for_timeout(5000)

        content = await page.content()

        jobs = await page.query_selector_all("a.jobTitle")

        message = ""
        count = 0

        for job in jobs:
            title = await job.inner_text()
            link = await job.get_attribute("href")

            if link and not link.startswith("http"):
                link = "https://career8.successfactors.com" + link

            message += f"{title}\n{link}\n\n"
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

    print("Radar ejecutado correctamente")

asyncio.run(run())
