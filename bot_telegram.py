import requests
import os
import json

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

URL = f"https://api.telegram.org/bot{TOKEN}"

OFFSET_FILE = "bot_offset.json"
MEMORIA_FILE = "memoria.json"


def cargar_json(file, default):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def guardar_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


offset_data = cargar_json(OFFSET_FILE, {"offset": 0})
offset = offset_data.get("offset", 0)

memoria = cargar_json(MEMORIA_FILE, {
    "rechazados": [],
    "aceptados": [],
    "empresas_buenas": [],
    "empresas_malas": [],
    "ciudades_malas": [],
    "turnos_buenos": ["7x7", "10x10", "14x14", "4x3"]
})

response = requests.get(f"{URL}/getUpdates?offset={offset+1}").json()

for update in response.get("result", []):

    offset = update["update_id"]

    try:

        texto = update["message"]["text"].lower()

        if texto.startswith("malo"):
            memoria["rechazados"].append(texto)

            requests.get(
                f"{URL}/sendMessage",
                params={
                    "chat_id": CHAT_ID,
                    "text": "Aprendido ❌"
                }
            )

        elif texto.startswith("bueno"):
            memoria["aceptados"].append(texto)

            requests.get(
                f"{URL}/sendMessage",
                params={
                    "chat_id": CHAT_ID,
                    "text": "Aprendido ✅"
                }
            )

        elif texto.startswith("/turno"):

            turno = texto.split(" ")[1]

            if turno not in memoria["turnos_buenos"]:
                memoria["turnos_buenos"].append(turno)

        guardar_json(MEMORIA_FILE, memoria)

    except:
        pass


guardar_json(OFFSET_FILE, {"offset": offset})
