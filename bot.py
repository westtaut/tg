"""
Telegram Mini App — Vibro Controller
"""

import os
import asyncio
import threading
import queue
import json
from flask import Flask, Response, request, jsonify, send_from_directory
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN  = os.getenv("BOT_TOKEN",  "8401113714:AAF5twOGm-mU_NXPzOdtdpv2UT--8IfVLqE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://tg-production-b635.up.railway.app")
PORT       = int(os.getenv("PORT", 5000))

flask_app = Flask(__name__, static_folder="static")

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
    def generate():
        q = _get_q(uid)
        yield "data: connected\n\n"
        while True:
            try:
                pattern = q.get(timeout=25)
                payload = json.dumps({"pattern": pattern})
                yield f"data: {payload}\n\n"
            except queue.Empty:
                yield "data: ping\n\n"

    headers = {
        "Cache-Control":     "no-cache",
        "X-Accel-Buffering": "no",
        "Connection":        "keep-alive",
    }
    return Response(generate(), mimetype="text/event-stream", headers=headers)


# Flask в отдельном потоке
def _run_flask():
    flask_app.run(host="0.0.0.0", port=PORT, threaded=True)


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


if __name__ == "__main__":
    print(f"🤖 Bot token : {BOT_TOKEN[:12]}...")
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    print(f"🚀 Flask port: {PORT}\n")

    # Flask — в отдельном потоке
    flask_thread = threading.Thread(target=_run_flask, daemon=True)
    flask_thread.start()

    # Бот — в главном потоке (fix для Python 3.13)
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.run_polling()
