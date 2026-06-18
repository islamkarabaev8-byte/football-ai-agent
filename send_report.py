"""
Football AI Report — отправляет в Telegram дайджест самых интересных
футбольных результатов. Запускается один раз (для GitHub Actions cron).
Использует Gemini 2.5 Flash с поиском Google для получения РЕАЛЬНЫХ результатов.
"""
import os
import re
import sys
import time
import requests
from datetime import datetime, timezone, timedelta


def _load_env_file():
    """Подхватываем .env рядом со скриптом, если переменные не заданы
    (нужно для локального запуска через Планировщик Windows).
    На GitHub Actions .env нет — там используются настоящие переменные окружения."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

# === Настройки из переменных окружения (GitHub Secrets или .env) ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
CHAT_ID = os.environ["CHAT_ID"]

ALMATY_TZ = timezone(timedelta(hours=5))
GEMINI_MODEL = "gemini-2.5-flash"

PROMPT = """Сегодня {date}. Используй поиск Google и найди РЕАЛЬНЫЕ результаты футбольных матчей,
которые завершились за последние 24 часа.

Охвати:
- ТОП-5 лиг Европы: АПЛ, Ла Лига, Бундеслига, Серия А, Лига 1
- Турниры сборных: ЧМ, Евро, Лига наций UEFA, квалификации, товарищеские матчи сборных
- 🇰🇿 Казахстанский футбол: Казахстанская Премьер-лига (КПЛ), сборная Казахстана,
  казахстанские клубы в еврокубках (Лига чемпионов/Лига Европы/Лига конференций)

Отбери ТОЛЬКО САМЫЕ ИНТЕРЕСНЫЕ матчи (крупный счёт, топ-команды, сенсации, важные игры).
Не больше 8-10 матчей из мирового футбола.
ОТДЕЛЬНЫМ блоком в конце всегда добавляй казахстанский футбол (🇰🇿) — все результаты КПЛ
и сборной Казахстана за последние сутки, даже если их немного.

ВАЖНО по оформлению (текст идёт в Telegram как обычный текст, БЕЗ markdown):
- НЕ используй символы #, *, ** для заголовков и списков
- Заголовок турнира пиши с эмодзи в начале строки, например: 🏆 Чемпионат мира 2026
- Каждый матч с новой строки в формате: ⚽ Команда1 X:Y Команда2 — короткий комментарий

Пиши на русском. Если за сутки матчей не было — честно напиши об этом
и укажи ближайшие интересные матчи. Не выдумывай результаты — только реальные данные из поиска."""


def clean_text(text: str) -> str:
    """Убираем markdown-разметку, которая в Telegram выглядит как мусор."""
    text = re.sub(r"#{1,6}\s*", "", text)        # ### заголовки
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **жирный**
    text = re.sub(r"(?m)^\s*[\*\-]\s+", "", text)  # маркеры списков * -
    text = re.sub(r"\n{3,}", "\n\n", text)         # лишние пустые строки
    return text.strip()


def generate_report() -> str:
    today = datetime.now(ALMATY_TZ).strftime("%d.%m.%Y")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": PROMPT.format(date=today)}]}],
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 4000,
            # отключаем "размышления" — иначе модель может потратить все токены
            # на thinking и вернуть ответ без текста (ошибка 'parts')
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    last_err = None
    # до 4 попыток на случай временной перегрузки сервера (503/429/500)
    for attempt in range(1, 5):
        try:
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                last_err = f"{r.status_code} {r.reason}"
                wait = attempt * 10
                print(f"Попытка {attempt}: сервер занят ({last_err}), жду {wait}с...", file=sys.stderr)
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()

            candidates = data.get("candidates", [])
            if not candidates:
                last_err = f"нет ответа (возможно блокировка: {data.get('promptFeedback')})"
                time.sleep(attempt * 5)
                continue

            cand = candidates[0]
            parts = cand.get("content", {}).get("parts", [])
            texts = [p["text"] for p in parts if "text" in p]

            if not texts:
                # модель не выдала текст (например finishReason=MAX_TOKENS)
                last_err = f"пустой ответ (finishReason={cand.get('finishReason')})"
                print(f"Попытка {attempt}: {last_err}", file=sys.stderr)
                time.sleep(attempt * 5)
                continue

            return clean_text("".join(texts))

        except Exception as e:
            last_err = str(e)
            print(f"Попытка {attempt} не удалась: {e}", file=sys.stderr)
            time.sleep(attempt * 10)

    raise RuntimeError(f"Не удалось получить ответ после 4 попыток. Последняя ошибка: {last_err}")


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
        report = f"⚠️ Не удалось получить данные о матчах. Попробуйте позже.\n\n({e})"
        print(f"Ошибка генерации: {e}", file=sys.stderr)

    header = f"⚽ ФУТБОЛЬНЫЙ ДАЙДЖЕСТ\n📅 {now} (Алматы)\n" + "─" * 25 + "\n\n"
    send_telegram(header + report)
    print("Отчёт отправлен!")


if __name__ == "__main__":
    main()
