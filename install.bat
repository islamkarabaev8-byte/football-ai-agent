@echo off
echo ============================================
echo   Football AI Agent - Установка
echo ============================================
echo.

REM Проверяем Python
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python найден
    py -m pip install -r requirements.txt
    goto :run
)

python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Python найден
    python -m pip install -r requirements.txt
    goto :run
)

echo [!] Python не найден. Скачиваем и устанавливаем...
curl -o python_installer.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
del python_installer.exe
echo.
echo [OK] Python установлен. Перезапустите этот файл.
pause
exit

:run
echo.
echo [OK] Зависимости установлены
echo.
echo ============================================
echo   Запуск агента...
echo   Отправьте /start боту в Telegram
echo ============================================
echo.
python agent.py
pause
