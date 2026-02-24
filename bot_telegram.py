"""
BOT TELEGRAM V15 - Radar Minero
Comandos:
  /carta  -> envia la carta de presentacion del ultimo aviso con carta disponible
  /stats  -> resumen del dia
Botones:
  Visto    -> cambia visual del mensaje, quita botones
  Eliminar -> borra el mensaje completamente
  Ver Carta -> envia la carta en mensaje separado
"""

import requests
import os, json, re
from datetime import datetime

TOKEN       = os.environ["TOKEN"]
CHAT_ID     = os.environ["CHAT_ID"]
SEEN_FILE   = "seen_jobs.json"
CARTA_FILE  = "cartas_pendientes.json"
OFFSET_FILE = "bot_offset.json"
STATS_FILE  = "bot_stats.json"

print(f"BOT TELEGRAM V15 - {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ─────────────────────────────────────────
# PERSISTENCIA
# ─────────────────────────────────────────
def cargar_vistos():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f: return set(json.load(f))
    return set()

def guardar_vistos(v):
    with open(SEEN_FILE, "w") as f: json.dump(list(v), f, indent=2)

def cargar_cartas():
    if os.path.exists(CARTA_FILE):
        with open(CARTA_FILE) as f: return json.load(f)
    return {}

def cargar_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f: return json.load(f).get("offset", 0)
    return 0

def guardar_offset(offset):
    with open(OFFSET_FILE, "w") as f: json.dump({"offset": offset}, f)

def cargar_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE) as f: return json.load(f)
    return {"vistos": 0, "eliminados": 0, "cartas_enviadas": 0, "total_recibidos": 0}

def guardar_stats(s):
    with open(STATS_FILE, "w") as f: json.dump(s, f, indent=2)

# ─────────────────────────────────────────
# TELEGRAM API
# ─────────────────────────────────────────
def api(method, data=None):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        r = requests.post(url, json=data or {}, timeout=12)
        return r.json()
    except Exception as e:
        print(f"  API {method} error: {e}")
        return {}

def responder_callback(callback_id, texto):
    api("answerCallbackQuery", {"callback_query_id": callback_id, "text": texto, "show_alert": False})

def editar_a_visto(chat_id, message_id, texto_original):
    """Cambia el mensaje visualmente a 'REVISADO' sin botones."""
    lineas = texto_original.split("\n")
    nuevas = []
    for i, linea in enumerate(lineas):
        if i == 0:
            nuevas.append("<b>REVISADO</b>")
        elif linea.startswith("<b>") and "Compatibilidad" not in linea and i < 3:
            # Titulo - poner en cursiva
            txt = re.sub(r"<[^>]+>", "", linea).strip()
            nuevas.append(f"<i>{txt}</i>")
        else:
            nuevas.append(linea)
    nuevas.append("")
    nuevas.append(f"Marcado como visto el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}")

    api("editMessageText", {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": "\n".join(nuevas),
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        # Sin reply_markup -> desaparecen botones
    })

def eliminar_mensaje(chat_id, message_id):
    result = api("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    if not result.get("result"):
        print(f"  No se pudo eliminar msg {message_id}: {result.get('description','')}")

def enviar_mensaje(chat_id, texto):
    api("sendMessage", {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    })

# ─────────────────────────────────────────
# COMANDOS
# ─────────────────────────────────────────
def cmd_carta(chat_id, args, cartas):
    """Envia la carta de un aviso especifico o el mas reciente."""
    if not cartas:
        enviar_mensaje(chat_id, "No hay cartas disponibles aun.\nEjecuta el radar primero.")
        return

    # Si hay argumento, buscar por numero de orden
    target = None
    lista_cartas = list(cartas.items())

    if args and args[0].isdigit():
        idx = int(args[0]) - 1
        if 0 <= idx < len(lista_cartas):
            target = lista_cartas[idx]
    else:
        # Mostrar lista de cartas disponibles
        if len(lista_cartas) == 1:
            target = lista_cartas[0]
        else:
            msg = "<b>Cartas disponibles:</b>\n\n"
            for i, (hid, info) in enumerate(lista_cartas[-10:], 1):  # ultimas 10
                msg += f"{i}. {info.get('empresa','?')} - {info.get('titulo','?')[:50]}\n"
                msg += f"   Fecha: {info.get('fecha','?')}\n\n"
            msg += "\nUsa /carta N para ver la carta especifica"
            enviar_mensaje(chat_id, msg)
            return

    if target:
        hid, info = target
        carta_txt = (
            f"<b>CARTA DE PRESENTACION</b>\n"
            f"Cargo: {info.get('titulo','?')}\n"
            f"Empresa: {info.get('empresa','?')}\n"
            f"Generada: {info.get('fecha','?')}\n\n"
            f"{'─'*30}\n\n"
            f"{info.get('carta','Carta no disponible')}"
        )
        enviar_mensaje(chat_id, carta_txt)
    else:
        enviar_mensaje(chat_id, "Numero de carta no encontrado. Usa /carta para ver la lista.")

def cmd_stats(chat_id):
    """Envia resumen de estadisticas."""
    vistos_set = cargar_vistos()
    cartas     = cargar_cartas()
    stats      = cargar_stats()

    msg = (
        f"<b>ESTADISTICAS DEL RADAR</b>\n"
        f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"Avisos en historial: {len(vistos_set)}\n"
        f"Cartas disponibles: {len(cartas)}\n"
        f"Avisos marcados visto: {stats.get('vistos',0)}\n"
        f"Avisos eliminados: {stats.get('eliminados',0)}\n"
        f"Cartas enviadas: {stats.get('cartas_enviadas',0)}\n\n"
        f"Ultima actualizacion: {datetime.now().strftime('%H:%M')}"
    )
    enviar_mensaje(chat_id, msg)

def cmd_ayuda(chat_id):
    msg = (
        "<b>COMANDOS DISPONIBLES</b>\n\n"
        "/carta - Ver lista de cartas disponibles\n"
        "/carta N - Ver carta especifica (ej: /carta 1)\n"
        "/stats - Ver estadisticas del radar\n"
        "/ayuda - Este mensaje\n\n"
        "<b>BOTONES EN CADA AVISO:</b>\n"
        "Visto - Marca como revisado, cambia el mensaje\n"
        "Eliminar - Borra el mensaje del chat\n"
        "Ver Carta - Envia la carta de presentacion personalizada"
    )
    enviar_mensaje(chat_id, msg)

# ─────────────────────────────────────────
# PROCESADOR PRINCIPAL
# ─────────────────────────────────────────
def procesar_updates():
    offset  = cargar_offset()
    vistos  = cargar_vistos()
    cartas  = cargar_cartas()
    stats   = cargar_stats()
    result  = api("getUpdates", {"offset": offset, "timeout": 10})
    updates = result.get("result", [])
    cambios_vistos = False

    for update in updates:
        uid = update["update_id"]

        # ── CALLBACK BUTTONS ────────────────────────────────
        if "callback_query" in update:
            cb      = update["callback_query"]
            cb_id   = cb["id"]
            data    = cb.get("data", "")
            msg     = cb.get("message", {})
            msg_id  = msg.get("message_id")
            chat_id = msg.get("chat", {}).get("id")
            txt     = msg.get("text") or msg.get("caption") or ""

            if data.startswith("visto:"):
                hid = data.split(":", 1)[1]
                vistos.add(hid)
                cambios_vistos = True
                stats["vistos"] = stats.get("vistos", 0) + 1
                responder_callback(cb_id, "Marcado como visto")
                editar_a_visto(chat_id, msg_id, txt)

            elif data.startswith("eliminar:"):
                hid = data.split(":", 1)[1]
                vistos.add(hid)
                cambios_vistos = True
                stats["eliminados"] = stats.get("eliminados", 0) + 1
                responder_callback(cb_id, "Aviso eliminado")
                eliminar_mensaje(chat_id, msg_id)

            elif data.startswith("carta:"):
                hid = data.split(":", 1)[1]
                chat_id_str = str(chat_id)
                if hid in cartas:
                    info = cartas[hid]
                    carta_txt = (
                        f"<b>CARTA DE PRESENTACION</b>\n"
                        f"Cargo: {info.get('titulo','?')}\n"
                        f"Empresa: {info.get('empresa','?')}\n\n"
                        f"{'─'*30}\n\n"
                        f"{info.get('carta','No disponible')}"
                    )
                    responder_callback(cb_id, "Carta enviada")
                    enviar_mensaje(chat_id, carta_txt)
                    stats["cartas_enviadas"] = stats.get("cartas_enviadas", 0) + 1
                else:
                    responder_callback(cb_id, "Carta no encontrada")

        # ── COMANDOS DE TEXTO ───────────────────────────────
        elif "message" in update:
            msg_obj = update["message"]
            chat_id = msg_obj.get("chat", {}).get("id")
            texto   = msg_obj.get("text", "").strip()
            partes  = texto.split()
            cmd     = partes[0].lower() if partes else ""
            args    = partes[1:] if len(partes) > 1 else []

            if cmd in ["/carta", "/carta@radarminerobot"]:
                cmd_carta(chat_id, args, cartas)
                stats["cartas_enviadas"] = stats.get("cartas_enviadas", 0) + 1

            elif cmd in ["/stats", "/stats@radarminerobot"]:
                cmd_stats(chat_id)

            elif cmd in ["/ayuda", "/ayuda@radarminerobot", "/start", "/help"]:
                cmd_ayuda(chat_id)

        offset = uid + 1
        guardar_offset(offset)

    if cambios_vistos:
        guardar_vistos(vistos)
    guardar_stats(stats)

    print(f"Updates procesados: {len(updates)}")

procesar_updates()
