import requests
import json

URL = "https://bhp.wd3.myworkdayjobs.com/wday/cxs/bhp/BHP_Careers/jobs"

payload = {
    "limit": 20,
    "searchText": "Chile"
}

r = requests.post(URL, json=payload)

print("Status:", r.status_code)

if r.status_code == 200:
    data = r.json()
    jobs = data.get("jobPostings", [])
    print("Vacantes encontradas:", len(jobs))

    for job in jobs[:5]:
        print(job.get("title"))
        print("https://bhp.wd3.myworkdayjobs.com" + job.get("externalPath"))
        print("-" * 40)
else:
    print("Error al conectar")
