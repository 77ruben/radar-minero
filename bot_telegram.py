"""
BOT TELEGRAM - Radar Minero
✅ Visto  → cambia apariencia del mensaje (título en cursiva + sello de revisado)
🗑 Eliminar → BORRA el mensaje completamente de Telegram
"""

import requests
import os, json
from datetime import datetime

TOKEN       = os.environ["TOKEN"]
CHAT_ID     = os.environ["CHAT_ID"]
SEEN_FILE   = "seen_jobs.json"
OFFSET_FILE = "bot_offset.json"

print(f"BOT TELEGRAM — {datetime.now().strftime('%d/%m/%Y %H:%M')}")

def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def guardar_vistos(vistos):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(vistos), f, indent=2)

def cargar_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            return json.load(f).get("offset", 0)
    return 0

def guardar_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)

def api(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        r = requests.post(url, json=data or {}, timeout=10)
        return r.json()
    except Exception as e:
        print(f"⚠️  API {method}: {e}")
        return {}

def responder_callback(callback_id, texto):
    api("answerCallbackQuery", {
        "callback_query_id": callback_id,
        "text": texto,
        "show_alert": False,
    })

def editar_a_visto(chat_id, message_id, texto_original):
    """
    Reemplaza el mensaje con versión 'leída':
    - Encabezado cambia a 👁 YA REVISADO
    - Título pasa a cursiva
    - Se agrega sello con hora al final
    - Los botones desaparecen (no se envía reply_markup)
    """
    lineas = texto_original.split("\n")
    nuevas = []
    for i, linea in enumerate(lineas):
        if i == 0:
            # Reemplazar encabezado (🔔/🔥/🚨) por estado leído
            nuevas.append("👁 <b>REVISADO</b>")
        elif linea.startswith("📋"):
            # Sacar el texto del título y ponerlo en cursiva
            txt = re.sub(r"<[^>]+>", "", linea).replace("📋 ", "").strip()
            nuevas.append(f"📋 <i>{txt}</i>")
        else:
            nuevas.append(linea)
    nuevas.append(f"\n─────────────────────")
    nuevas.append(f"✅ Visto el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}")

    api("editMessageText", {
        "chat_id":    chat_id,
        "message_id": message_id,
        "text":       "\n".join(nuevas),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        # Sin reply_markup → los botones desaparecen
    })

def eliminar_mensaje(chat_id, message_id):
    """Borra el mensaje completamente del chat."""
    result = api("deleteMessage", {
        "chat_id":    chat_id,
        "message_id": message_id,
    })
    if not result.get("result"):
        print(f"  ⚠️  No se pudo eliminar msg {message_id}: {result.get('description','')}")

def procesar_updates():
    import re
    offset  = cargar_offset()
    vistos  = cargar_vistos()
    result  = api("getUpdates", {"offset": offset, "timeout": 10})
    updates = result.get("result", [])
    cambios = False

    for update in updates:
        uid = update["update_id"]

        if "callback_query" in update:
            cb      = update["callback_query"]
            cb_id   = cb["id"]
            data    = cb.get("data", "")
            msg     = cb.get("message", {})
            msg_id  = msg.get("message_id")
            chat_id = msg.get("chat", {}).get("id")
            # Telegram puede enviar text o caption
            txt = msg.get("text") or msg.get("caption") or ""

            # ── ✅ VISTO ──────────────────────────────────
            if data.startswith("visto:"):
                hid = data.split(":", 1)[1]
                vistos.add(hid)
                cambios = True
                responder_callback(cb_id, "✅ Marcado como visto")
                editar_a_visto(chat_id, msg_id, txt)

            # ── 🗑 ELIMINAR ───────────────────────────────
            elif data.startswith("eliminar:"):
                hid = data.split(":", 1)[1]
                vistos.add(hid)
                cambios = True
                responder_callback(cb_id, "🗑 Aviso eliminado")
                eliminar_mensaje(chat_id, msg_id)

        offset = uid + 1
        guardar_offset(offset)

    if cambios:
        guardar_vistos(vistos)

    print(f"✅ {len(updates)} updates procesados")

procesar_updates()
