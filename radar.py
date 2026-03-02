import requests
from bs4 import BeautifulSoup

URL = "https://jobs.fcx.com/South-America/go/Oportunidades-Laborales-en-Chile/8009100/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

jobs = []

for job in soup.find_all("a", class_="jobTitle-link"):
    title = job.get_text(strip=True)
    link = "https://jobs.fcx.com" + job["href"]
    job_id = job["href"].split("/")[-2]

    jobs.append({
        "id": job_id,
        "title": title,
        "link": link
    })

for j in jobs:
    print(j)
