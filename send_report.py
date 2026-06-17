"""
Football AI Report — отправляет в Telegram дайджест самых интересных
футбольных результатов. Запускается один раз (для GitHub Actions cron).
Использует Gemini 2.5 Flash с поиском Google для получения РЕАЛЬНЫХ результатов.
"""
import os
import sys
import requests
from datetime import datetime, timezone, timedelta

# === Настройки из переменных окружения (GitHub Secrets) ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CHAT_ID = os.environ["CHAT_ID"]

ALMATY_TZ = timezone(timedelta(hours=5))
GEMINI_MODEL = "gemini-2.5-flash"

PROMPT = """Сегодня {date}. Используй поиск Google и найди РЕАЛЬНЫЕ результаты футбольных матчей,
которые завершились за последние 24 часа.

Охвати:
- ТОП-5 лиг Европы: 🏴 АПЛ, 🇪🇸 Ла Лига, 🇩🇪 Бундеслига, 🇮🇹 Серия А, 🇫🇷 Лига 1
- Турниры сборных: ЧМ, Евро, Лига наций UEFA, квалификации, товарищеские матчи сборных

Отбери ТОЛЬКО САМЫЕ ИНТЕРЕСНЫЕ матчи (крупный счёт, топ-команды, сенсации, важные игры).
Не больше 8-10 матчей всего.

Формат каждого матча:
⚽ Команда1 X:Y Команда2 — короткий комментарий что было интересного (1 строка)

Сгруппируй по турнирам с заголовками. Используй эмодзи. Пиши на русском.
Если за сутки матчей не было — честно напиши об этом и укажи когда ближайшие интересные матчи.
Не выдумывай результаты — бери только реальные данные из поиска."""


def generate_report() -> str:
    today = datetime.now(ALMATY_TZ).strftime("%d.%m.%Y")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": PROMPT.format(date=today)}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2500},
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # Telegram limit ~4096 символов — режем на части
    for i in range(0, len(text), 4000):
        chunk = text[i:i + 4000]
        resp = requests.post(url, json={"chat_id": CHAT_ID, "text": chunk}, timeout=30)
        if not resp.ok:
            print(f"Telegram error: {resp.text}", file=sys.stderr)
            resp.raise_for_status()


def main():
    now = datetime.now(ALMATY_TZ).strftime("%d.%m.%Y %H:%M")
    print(f"[{now}] Генерирую отчёт...")
    try:
        report = generate_report()
    except Exception as e:
        report = f"Не удалось получить данные о матчах: {e}"
        print(f"Gemini error: {e}", file=sys.stderr)

    header = f"⚽ ФУТБОЛЬНЫЙ ДАЙДЖЕСТ\n📅 {now} (Алматы)\n" + "─" * 25 + "\n\n"
    send_telegram(header + report)
    print("Отчёт отправлен!")


if __name__ == "__main__":
    main()
