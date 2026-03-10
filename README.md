# 📳 Vibro Controller — Telegram Mini App

Нажимаешь кнопку на ПК → iPhone вибрирует прямо **внутри Telegram**, без уведомлений.  
Использует нативный `Telegram.WebApp.HapticFeedback` API.

---

## Как это работает

```
[ПК: кнопка в Mini App] → POST /api/vibrate → Flask сервер
                                                      ↓ SSE
                                            [iPhone: Mini App]
                                                      ↓
                                         tg.HapticFeedback.impactOccurred()
                                                      ↓
                                               💥 ВИБРАЦИЯ
```

Приложение **автоматически определяет платформу** через `Telegram.WebApp.platform`:
- `desktop` / `web` / `macos` → Панель управления (контроллер)
- `ios` / `android` → Приёмник вибраций

---

## Быстрый старт

### 1. Установи зависимости

```bash
pip install -r requirements.txt
```

### 2. Создай Telegram-бота

1. Напиши [@BotFather](https://t.me/botfather)
2. Команда `/newbot` → придумай имя
3. Скопируй **токен** (вида `123456789:AAFxxx...`)

### 3. Получи публичный HTTPS URL

Telegram требует HTTPS для Mini App. Используй **ngrok** (бесплатно):

```bash
# Установи ngrok: https://ngrok.com/download
ngrok http 5000
# Скопируй URL вида: https://abc123.ngrok.io
```

Или задеплой на VPS с доменом и SSL.

### 4. Задай переменные окружения

**Windows:**
```bat
set BOT_TOKEN=123456789:AAFxxx
set WEBAPP_URL=https://abc123.ngrok.io
```

**Linux / macOS:**
```bash
export BOT_TOKEN="123456789:AAFxxx"
export WEBAPP_URL="https://abc123.ngrok.io"
```

Или просто впиши прямо в `bot.py`:
```python
BOT_TOKEN  = "123456789:AAFxxx"
WEBAPP_URL = "https://abc123.ngrok.io"
```

### 5. Запусти

```bash
python bot.py
```

### 6. Открой приложение

1. Найди своего бота в Telegram
2. Напиши `/start`
3. Нажми **«Открыть Vibro Controller»**
4. Открой на **iPhone** — он станет приёмником (анимация сонара)
5. Открой на **ПК** — появится пульт управления
6. Нажимай кнопки на ПК → iPhone вибрирует!

---

## Паттерны вибрации

| Кнопка       | HapticFeedback вызов              | Ощущение            |
|-------------|-----------------------------------|---------------------|
| LIGHT        | `impactOccurred('light')`         | Лёгкое касание      |
| MEDIUM       | `impactOccurred('medium')`        | Средний удар        |
| HEAVY        | `impactOccurred('heavy')`         | Сильный удар        |
| SUCCESS ✅   | `notificationOccurred('success')` | Двойной тап         |
| ERROR ❌     | `notificationOccurred('error')`   | Тройной удар        |
| WARNING ⚠️  | `notificationOccurred('warning')` | Предупреждение      |
| × 3 ПОДРЯД  | medium × 3 с паузой 800мс         | Серия               |
| SOS (× 5)   | heavy × 5 с паузой 500мс          | Срочный сигнал      |

---

## Требования

- Python 3.10+
- Telegram-бот (бесплатно)
- ngrok или VPS с HTTPS
- iPhone с открытым Telegram

---

## Структура

```
vibro_miniapp/
├── bot.py           # Flask + Telegram bot
├── index.html       # Mini App (контроллер + приёмник)
├── requirements.txt
└── README.md
```
