import requests
from bs4 import BeautifulSoup
import os

TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

url = "https://cl.indeed.com/jobs?q=mineria&l=Chile"

page = requests.get(url)

soup = BeautifulSoup(page.content,"html.parser")

jobs = soup.select(".tapItem")

mensaje = "🚨 Radar Minero:\n\n"

for job in jobs[:5]:

    titulo = job.select_one("h2").text.strip()

    link = "https://cl.indeed.com" + job.select_one("a")["href"]

    mensaje += titulo + "\n" + link + "\n\n"


requests.post(

f"https://api.telegram.org/bot{TOKEN}/sendMessage",

data={"chat_id":CHAT_ID,"text":mensaje}

)

print("Radar ejecutado")
