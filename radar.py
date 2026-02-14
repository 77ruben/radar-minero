import requests
import os

TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['CHAT_ID']

mensaje = "ok, radar minero opertaivoy conectado correctamente"

    requests.post(

    f"https://api.telegram.org/bot{TOKEN}/sendMessage",

    data={"chat_id":CHAT_ID,"text":mensaje}

    )

print("OK")
