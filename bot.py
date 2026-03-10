"""
Telegram Mini App — Vibro Controller
Запуск: python bot.py
Нужен публичный HTTPS URL (ngrok или VPS).
"""

import os
import asyncio
import threading
import queue
import json
from flask import Flask, Response, request, jsonify, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# ─────────────────────────────────────────────────────────────
#  Конфиг — задай через переменные окружения или .env
# ─────────────────────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN",  "ВСТАВЬ_ТОКЕН_БОТА_СЮДА")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://ТВОЙ_NGROK_ИЛИ_VPS.ngrok.io")
PORT       = int(os.getenv("PORT", 5000))

# ─────────────────────────────────────────────────────────────
#  Flask — HTTP сервер
# ─────────────────────────────────────────────────────────────
flask_app = Flask(__name__, static_folder="static")

# Очереди SSE для каждого user_id
_queues: dict[str, queue.Queue] = {}

def _get_q(uid: str) -> queue.Queue:
    if uid not in _queues:
        _queues[uid] = queue.Queue(maxsize=20)
    return _queues[uid]


@flask_app.route("/")
def index():
    return send_from_directory(".", "index.html")


@flask_app.route("/api/vibrate", methods=["POST"])
def api_vibrate():
    """ПК нажимает кнопку → отправляем событие на iPhone через SSE."""
    data = request.get_json(force=True, silent=True) or {}
    uid     = str(data.get("user_id", ""))
    pattern = data.get("pattern", "medium")

    if not uid:
        return jsonify({"ok": False, "error": "no user_id"}), 400

    try:
        _get_q(uid).put_nowait(pattern)
        return jsonify({"ok": True})
    except queue.Full:
        return jsonify({"ok": False, "error": "queue full"}), 429


@flask_app.route("/api/events/<uid>")
def api_events(uid: str):
    """SSE-стрим для iPhone — слушает вибро-команды."""
    def generate():
        q = _get_q(uid)
        yield "data: connected\n\n"
        while True:
            try:
                pattern = q.get(timeout=25)
                payload = json.dumps({"pattern": pattern})
                yield f"data: {payload}\n\n"
            except queue.Empty:
                yield "data: ping\n\n"   # keep-alive

    headers = {
        "Cache-Control":    "no-cache",
        "X-Accel-Buffering": "no",
        "Connection":       "keep-alive",
    }
    return Response(generate(), mimetype="text/event-stream", headers=headers)


# ─────────────────────────────────────────────────────────────
#  Telegram Bot
# ─────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[
        InlineKeyboardButton(
            "📳 Открыть Vibro Controller",
            web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]]
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Как пользоваться:\n"
        "1️⃣ Открой приложение ниже на **iPhone** — он станет приёмником\n"
        "2️⃣ Открой на **ПК** — появится пульт управления\n"
        "3️⃣ Нажимай кнопки на ПК — iPhone завибрирует!\n\n"
        "_Приложение само определяет устройство_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def _run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    loop.run_until_complete(application.run_polling(close_loop=False))


# ─────────────────────────────────────────────────────────────
#  Запуск обоих сервисов
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🤖 Bot token : {BOT_TOKEN[:12]}...")
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    print(f"🚀 Flask port: {PORT}\n")

    # Бот в отдельном потоке
    bot_thread = threading.Thread(target=_run_bot, daemon=True)
    bot_thread.start()

    # Flask — основной поток
    flask_app.run(host="0.0.0.0", port=PORT, threaded=True)
