"""
╔══════════════════════════════════════════════════════════╗
║       BOT TELEGRAM - Radar Minero V9 PRO                 ║
║                                                          ║
║  Funciones:                                              ║
║  ► Responde botones ✅ Postulé / 🔖 Guardar / ❌ Descarta║
║  ► Registra fecha y estado en Google Sheets              ║
║  ► Comando /stats — resumen de tu búsqueda               ║
║  ► Corre en GitHub Actions cada 30 min (separado)        ║
╚══════════════════════════════════════════════════════════╝
"""

import requests
import os, json, time
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

TOKEN              = os.environ["TOKEN"]
CHAT_ID            = os.environ["CHAT_ID"]
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS")
SHEET_NAME         = "Radar Minero - Postulaciones"
OFFSET_FILE        = "bot_offset.json"

# ─────────────────────────────────────────────────────────
# GOOGLE SHEETS
# ─────────────────────────────────────────────────────────
def conectar_sheets():
    if not GOOGLE_CREDENTIALS:
        return None
    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS)
        scopes = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        print(f"⚠️  Sheets: {e}")
        return None

def actualizar_estado(sheet, hid, nuevo_estado):
    """Busca la fila por hash en notas y actualiza el estado."""
    if not sheet:
        return False
    try:
        # Buscar en columna de Link (col 8) o Notas (col 11)
        celdas = sheet.findall(hid)
        if celdas:
            fila = celdas[0].row
            sheet.update_cell(fila, 9, nuevo_estado)  # col 9 = Estado
            if "postulé" in nuevo_estado.lower() or "postule" in nuevo_estado.lower():
                sheet.update_cell(fila, 10, datetime.now().strftime("%d/%m/%Y %H:%M"))
            return True
        return False
    except Exception as e:
        print(f"⚠️  Error actualizando Sheets: {e}")
        return False

def obtener_stats(sheet):
    """Retorna estadísticas de la búsqueda."""
    if not sheet:
        return None
    try:
        datos = sheet.get_all_values()
        if len(datos) <= 1:
            return {"total": 0, "pendiente": 0, "postule": 0, "guardado": 0, "descartado": 0, "entrevista": 0}
        filas = datos[1:]  # Sin encabezado
        stats = {
            "total":       len(filas),
            "pendiente":   sum(1 for f in filas if len(f) > 8 and f[8] == "Pendiente"),
            "postule":     sum(1 for f in filas if len(f) > 8 and "Postulé" in f[8]),
            "guardado":    sum(1 for f in filas if len(f) > 8 and "Guardado" in f[8]),
            "descartado":  sum(1 for f in filas if len(f) > 8 and "Descartado" in f[8]),
            "entrevista":  sum(1 for f in filas if len(f) > 8 and "Entrevista" in f[8]),
        }
        return stats
    except Exception as e:
        print(f"⚠️  Stats: {e}")
        return None

# ─────────────────────────────────────────────────────────
# TELEGRAM API
# ─────────────────────────────────────────────────────────
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

def editar_mensaje(chat_id, message_id, nuevo_texto):
    api("editMessageText", {
        "chat_id":    chat_id,
        "message_id": message_id,
        "text":       nuevo_texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })

def enviar_mensaje(texto):
    api("sendMessage", {
        "chat_id":   CHAT_ID,
        "text":      texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })

def menu_estado(hid):
    """Keyboard para elegir estado del proceso."""
    return {
        "inline_keyboard": [
            [
                {"text": "📞 En proceso",    "callback_data": f"estado:proceso:{hid}"},
                {"text": "🤝 Entrevista",    "callback_data": f"estado:entrevista:{hid}"},
            ],
            [
                {"text": "✅ Oferta recibida","callback_data": f"estado:oferta:{hid}"},
                {"text": "❌ Rechazado",      "callback_data": f"estado:rechazado:{hid}"},
            ],
        ]
    }

# ─────────────────────────────────────────────────────────
# OFFSET (para no reprocesar updates)
# ─────────────────────────────────────────────────────────
def cargar_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            return json.load(f).get("offset", 0)
    return 0

def guardar_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)

# ─────────────────────────────────────────────────────────
# PROCESAMIENTO DE UPDATES
# ─────────────────────────────────────────────────────────
def procesar_updates(sheet):
    offset  = cargar_offset()
    result  = api("getUpdates", {"offset": offset, "timeout": 10})
    updates = result.get("result", [])

    for update in updates:
        uid = update["update_id"]

        # ── Callbacks de botones ──────────────────────────
        if "callback_query" in update:
            cb       = update["callback_query"]
            cb_id    = cb["id"]
            data     = cb.get("data", "")
            msg      = cb.get("message", {})
            msg_id   = msg.get("message_id")
            chat_id  = msg.get("chat", {}).get("id")
            msg_text = msg.get("text", "")

            # ── ✅ Postulé ────────────────────────────────
            if data.startswith("postule:"):
                hid = data.split(":", 1)[1]
                actualizar_estado(sheet, hid, f"Postulé ✅ — {datetime.now().strftime('%d/%m/%Y')}")
                responder_callback(cb_id, "✅ Registrado como postulado")
                # Actualizar mensaje original con menú de estado
                nuevo_texto = msg_text + "\n\n✅ <b>POSTULADO</b> — ¿Cómo va el proceso?"
                api("editMessageText", {
                    "chat_id": chat_id, "message_id": msg_id,
                    "text": nuevo_texto, "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                    "reply_markup": json.dumps(menu_estado(hid)),
                })

            # ── 🔖 Guardar ────────────────────────────────
            elif data.startswith("guardar:"):
                hid = data.split(":", 1)[1]
                actualizar_estado(sheet, hid, "Guardado 🔖")
                responder_callback(cb_id, "🔖 Aviso guardado para revisar después")
                nuevo_texto = msg_text + "\n\n🔖 <b>GUARDADO</b>"
                editar_mensaje(chat_id, msg_id, nuevo_texto)

            # ── ❌ Descarta ────────────────────────────────
            elif data.startswith("descarta:"):
                hid = data.split(":", 1)[1]
                actualizar_estado(sheet, hid, "Descartado ❌")
                responder_callback(cb_id, "❌ Aviso descartado")
                nuevo_texto = msg_text + "\n\n❌ <b>DESCARTADO</b>"
                editar_mensaje(chat_id, msg_id, nuevo_texto)

            # ── Actualización de estado del proceso ───────
            elif data.startswith("estado:"):
                partes = data.split(":", 2)
                estado_key = partes[1] if len(partes) > 1 else ""
                hid        = partes[2] if len(partes) > 2 else ""
                estados = {
                    "proceso":    "En proceso 📞",
                    "entrevista": "Entrevista 🤝",
                    "oferta":     "Oferta recibida ✅🎉",
                    "rechazado":  "Rechazado ❌",
                }
                estado_str = estados.get(estado_key, estado_key)
                actualizar_estado(sheet, hid, estado_str)
                responder_callback(cb_id, f"Estado actualizado: {estado_str}")
                nuevo_texto = msg_text.split("\n\n✅")[0]  # limpiar texto anterior
                nuevo_texto += f"\n\n📌 Estado: <b>{estado_str}</b>"
                editar_mensaje(chat_id, msg_id, nuevo_texto)

        # ── Comandos de texto ─────────────────────────────
        elif "message" in update:
            msg      = update["message"]
            texto    = msg.get("text", "").strip()
            chat_id  = msg.get("chat", {}).get("id")

            if str(chat_id) != str(CHAT_ID):
                offset = uid + 1
                guardar_offset(offset)
                continue

            # ── /stats ────────────────────────────────────
            if texto in ["/stats", "/estadisticas"]:
                stats = obtener_stats(sheet)
                if stats:
                    enviar_mensaje(
                        f"📊 <b>ESTADÍSTICAS DE TU BÚSQUEDA</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📋 Total avisos registrados: <b>{stats['total']}</b>\n"
                        f"⏳ Pendientes de revisar:    <b>{stats['pendiente']}</b>\n"
                        f"✅ Postulados:               <b>{stats['postule']}</b>\n"
                        f"🔖 Guardados:               <b>{stats['guardado']}</b>\n"
                        f"🤝 En entrevista:            <b>{stats['entrevista']}</b>\n"
                        f"❌ Descartados:              <b>{stats['descartado']}</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                    )
                else:
                    enviar_mensaje("⚠️ No se pudo obtener estadísticas. Verifica la conexión con Google Sheets.")

            # ── /ayuda ────────────────────────────────────
            elif texto in ["/ayuda", "/help", "/start"]:
                enviar_mensaje(
                    "🤖 <b>RADAR MINERO V9 PRO — Comandos</b>\n\n"
                    "📊 /stats — Ver estadísticas de tu búsqueda\n"
                    "❓ /ayuda — Ver esta ayuda\n\n"
                    "En cada aviso que llega tienes 3 botones:\n"
                    "✅ <b>Postulé</b> — Registra la postulación con fecha\n"
                    "🔖 <b>Guardar</b> — Guarda para revisar después\n"
                    "❌ <b>No me interesa</b> — Descarta el aviso\n\n"
                    "Todo queda registrado automáticamente en Google Sheets 📋"
                )

        offset = uid + 1
        guardar_offset(offset)

    return len(updates)

# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────
print("=" * 50)
print("  BOT TELEGRAM — Radar Minero V9 PRO")
print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
print("=" * 50)

sheet = conectar_sheets()
print(f"📊 Sheets: {'conectado ✅' if sheet else 'no disponible ⚠️'}")

n = procesar_updates(sheet)
print(f"✅ {n} updates procesados")
