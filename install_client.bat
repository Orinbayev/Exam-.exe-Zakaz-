@echo off
chcp 65001 > nul
title Smart Exam Client - O'rnatish

echo ============================================
echo   Smart Exam Client - Ishga tushirish
echo ============================================
echo.

cd /d "%~dp0client"

echo [1/2] Client kutubxonalari o'rnatilmoqda...
pip install -r requirements.txt -q
echo     OK

echo [2/2] Client ishga tushirilmoqda...
echo.
python run_client.py

pause
