@echo off
title Football AI Bot

echo.
echo  ================================
echo    FOOTBALL AI BOT - ЗАПУСК
echo  ================================
echo.

REM === ШАГ 1: Проверяем Python ===
py --version >nul 2>&1
if %errorlevel% == 0 (
    set PY=py
    goto :install
)
python --version >nul 2>&1
if %errorlevel% == 0 (
    set PY=python
    goto :install
)

REM Python не найден — скачиваем автоматически
echo  [1/3] Устанавливаем Python...
curl -# -o "%TEMP%\python_setup.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
"%TEMP%\python_setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
del "%TEMP%\python_setup.exe"
set PY=py
echo  [OK] Python установлен
echo.

REM === ШАГ 2: Устанавливаем библиотеки ===
:install
echo  [2/3] Устанавливаем библиотеки...
%PY% -m pip install -q -r requirements.txt
echo  [OK] Библиотеки установлены
echo.

REM === ШАГ 3: Запускаем бота ===
echo  [3/3] Запускаем бота...
echo.
echo  Бот работает! Напишите /report в Telegram чтобы получить отчёт.
echo  Каждый день в 22:00 по Алматы отчёт придёт автоматически.
echo  Закройте это окно чтобы остановить бота.
echo.
echo  ================================
echo.
%PY% agent.py

echo.
echo  Бот остановлен.
pause
