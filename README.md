# ⚽ Football AI Report

Бот автоматически присылает в Telegram дайджест **самых интересных** футбольных
результатов каждый день в **22:00 по Алматы**.

Работает на **GitHub Actions** — компьютер держать включённым НЕ нужно.

## Что присылает
- ТОП-5 лиг Европы: АПЛ, Ла Лига, Бундеслига, Серия А, Лига 1
- Турниры сборных: ЧМ, Евро, Лига наций, квалификации

Реальные результаты берутся через Gemini 2.5 Flash с поиском Google.

## Как это работает
1. GitHub Actions по расписанию (`cron: 0 17 * * *` = 22:00 Алматы) запускает `send_report.py`
2. Скрипт спрашивает у Gemini актуальные результаты и шлёт их в Telegram

## Настройка секретов
В репозитории: **Settings → Secrets and variables → Actions** должны быть заданы:
- `TELEGRAM_TOKEN` — токен Telegram-бота
- `GEMINI_API_KEY` — ключ Gemini API
- `CHAT_ID` — ваш Telegram chat_id

## Ручной запуск
Вкладка **Actions → Daily Football Report → Run workflow**

## Локальный запуск (для теста)
```bash
pip install requests
# задайте переменные окружения TELEGRAM_TOKEN, GEMINI_API_KEY, CHAT_ID
python send_report.py
```
