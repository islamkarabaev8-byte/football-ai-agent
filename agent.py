import logging
import asyncio
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import google.generativeai as genai
from config import TELEGRAM_TOKEN, GEMINI_API_KEY, CHAT_ID, REPORT_HOUR_UTC, REPORT_MINUTE_UTC

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ALMATY_TZ = timezone(timedelta(hours=5))

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """
Ты спортивный аналитик. Предоставь актуальную информацию о футболе на сегодня ({date}) по следующим соревнованиям:

**ТОП-5 ЕВРОПЕЙСКИХ ЛИГ:**
1. 🏴󠁧󠁢󠁥󠁮󠁧󠁿 Английская Премьер-лига
2. 🇪🇸 Ла Лига (Испания)
3. 🇩🇪 Бундеслига (Германия)
4. 🇮🇹 Серия А (Италия)
5. 🇫🇷 Лига 1 (Франция)

**ТУРНИРЫ СБОРНЫХ:**
6. 🏆 Лига наций UEFA
7. 🌍 Квалификация ЧМ/ЧЕ (если идёт)
8. 🌐 Другие турниры сборных

Для каждого соревнования укажи:
- Результаты матчей сегодня (если были)
- Ближайшие матчи (следующие 2-3 дня)
- Текущее положение в таблице (топ-5 команд)
- Главные новости и трансферы

Отвечай на русском языке, используй эмодзи, форматируй красиво с разделителями.
Если точных данных нет — дай общую аналитику и прогнозы на основе текущего сезона.
"""


def get_football_report() -> str:
    today = datetime.now(ALMATY_TZ).strftime("%d.%m.%Y")
    try:
        response = model.generate_content(
            PROMPT.format(date=today),
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=3000,
                temperature=0.7,
            )
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return f"❌ Ошибка при получении данных: {e}"


async def send_report(bot, chat_id: int):
    logger.info("Generating football report...")
    report = get_football_report()
    header = f"⚽ *ФУТБОЛЬНЫЙ ДАЙДЖЕСТ* — {datetime.now(ALMATY_TZ).strftime('%d.%m.%Y 22:00 Алматы')}\n\n"
    full_text = header + report

    # Разбиваем на части если длинный текст
    for i in range(0, len(full_text), 4000):
        await bot.send_message(
            chat_id=chat_id,
            text=full_text[i:i+4000],
            parse_mode="Markdown"
        )
    logger.info("Report sent successfully")


async def daily_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await send_report(context.bot, chat_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (
        f"⚽ *Футбольный AI Агент*\n\n"
        f"Ваш Chat ID: `{chat_id}`\n\n"
        f"Каждый день в *22:00 по Алматы* я буду отправлять:\n"
        f"• Результаты матчей топ-5 лиг\n"
        f"• Информацию о турнирах сборных\n"
        f"• Таблицы и главные новости\n\n"
        f"Команды:\n"
        f"/report — получить отчёт прямо сейчас\n"
        f"/start — информация\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Генерирую отчёт через AI, подождите 10-20 секунд...")
    await send_report(context.bot, update.effective_chat.id)


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", report_command))

    # Определяем chat_id для рассылки
    chat_id = CHAT_ID

    # Если CHAT_ID не задан — будем отправлять всем кто написал /start
    # Для автоматической рассылки нужен chat_id
    if chat_id:
        report_time = datetime.strptime(
            f"{REPORT_HOUR_UTC:02d}:{REPORT_MINUTE_UTC:02d}", "%H:%M"
        ).replace(tzinfo=timezone.utc).timetz()

        app.job_queue.run_daily(
            daily_job,
            time=report_time,
            data=chat_id,
            name="daily_football_report"
        )
        logger.info(f"Daily report scheduled at {REPORT_HOUR_UTC:02d}:{REPORT_MINUTE_UTC:02d} UTC (22:00 Almaty) for chat {chat_id}")
    else:
        logger.warning("CHAT_ID not set in config.py! Send /start to the bot to get your chat_id, then update config.py")

    logger.info("Football AI Agent started. Send /start to the bot.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
