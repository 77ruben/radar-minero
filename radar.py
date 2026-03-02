import os
import asyncio
from playwright.async_api import async_playwright
import requests
import json

print("INICIANDO RADAR ANGLO AMERICAN")

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

URL = "https://www.angloamerican.com/careers/job-opportunities/apply"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        jobs_json = None

        async def handle_response(response):
            nonlocal jobs_json
            try:
                if response.request.resource_type == "xhr":
                    if response.status == 200:
                        data = await response.text()
                        if "job" in data.lower():
                            jobs_json = data
            except:
                pass

        page.on("response", handle_response)

        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(10000)

        await browser.close()

    message = ""
    count = 0

    if jobs_json:
        try:
            data = json.loads(jobs_json)

            # Intento genérico (ajustaremos cuando veamos estructura real)
            for item in data:
                title = item.get("title")
                location = item.get("location")
                link = item.get("applyUrl") or item.get("url")

                if title:
                    message += f"{title} - {location}\n{link}\n\n"
                    count += 1

        except:
            message = "Se detectó respuesta pero estructura desconocida."
    else:
        message = "No se detectó respuesta JSON."

    if count == 0:
        message = "Radar Anglo American activo.\nNo se detectaron empleos o estructura no identificada."
    else:
        message = f"🚨 EMPLEOS ANGLO AMERICAN ({count}) 🚨\n\n" + message

    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(telegram_url, data={
        "chat_id": CHAT_ID,
        "text": message[:4000]
    })

    print("Proceso finalizado")

asyncio.run(run())
