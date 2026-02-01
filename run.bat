@echo off
chcp 866 >nul

REM Check venv
if not exist .venv (
    echo ERROR: Virtual environment not found!
    echo.
    echo Run install.bat first
    pause
    exit /b 1
)

REM Check .env
if not exist .env (
    echo ERROR: .env file not found!
    echo.
    echo Create .env from .env.example and set TELEGRAM_BOT_TOKEN
    copy .env.example .env
    echo.
    echo .env created. Open it and set your token.
    pause
    exit /b 1
)

REM Activate venv
call .venv\Scripts\activate.bat

echo ========================================
echo   Starting STT Bot
echo ========================================
echo.
echo Press Ctrl+C to stop
echo.

REM Run bot
python -m bot.main

pause
