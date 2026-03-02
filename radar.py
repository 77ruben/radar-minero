import os
import asyncio
from playwright.async_api import async_playwright
import requests
import json

print("INICIANDO RADAR ANTOFAGASTA MINERALS (NETWORK MODE)")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("TOKEN o CHAT_ID no configurados")

URL = "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        jobs_data = None

        async def handle_response(response):
            nonlocal jobs_data
            if "jobsearch" in response.url and response.status == 200:
                try:
                    jobs_data = await response.json()
                except:
                    pass

        page.on("response", handle_response)

        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(10000)

        await browser.close()

    message = ""
    count = 0

    if jobs_data and "jobSearchResult" in jobs_data:
        results = jobs_data["jobSearchResult"].get("results", [])

        for job in results:
            title = job.get("jobTitle")
            location = job.get("location")
            job_id = job.get("jobReqId")

            link = f"https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH&jobReqId={job_id}"

            message += f"{title} - {location}\n{link}\n\n"
            count += 1

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
