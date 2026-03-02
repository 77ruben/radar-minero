import os
import asyncio
from playwright.async_api import async_playwright
import requests

print("INICIANDO RADAR ANTOFAGASTA MINERALS (CLICK MODE)")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URL = "https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115 Safari/537.36"
        )

        page = await context.new_page()

        jobs_data = None

        async def handle_response(response):
            nonlocal jobs_data
            if "jobsearch" in response.url and response.request.method == "POST":
                try:
                    jobs_data = await response.json()
                except:
                    pass

        page.on("response", handle_response)

        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(5000)

        # Forzar clic en botón Buscar
        try:
            await page.click("button")
        except:
            pass

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

            link = f"https://career8.successfactors.com/career?company=AMSAP&career_ns=job_listing_summary&jobReqId={job_id}"

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
