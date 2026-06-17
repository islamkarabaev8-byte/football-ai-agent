@echo off
echo === Установка зависимостей ===
pip install -r requirements.txt

echo.
echo === Запуск Football AI Agent ===
echo Отправьте /start боту в Telegram чтобы узнать ваш chat_id
echo Затем пропишите его в config.py (строка CHAT_ID)
echo.
python agent.py
pause
