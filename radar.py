import asyncio
from playwright.async_api import async_playwright

print("DIAGNOSTICO ANGLO AMERICAN")

URL = "https://www.angloamerican.com/careers/job-opportunities/apply"

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(8000)

        print("\nFRAMES DETECTADOS:\n")

        for frame in page.frames:
            print(frame.url)

        await browser.close()

asyncio.run(run())
