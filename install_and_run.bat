@echo off
chcp 65001 > nul
title Smart Exam System - O'rnatish va ishga tushirish

echo ============================================
echo   Smart Exam System - Tezkor ishga tushirish
echo ============================================
echo.
echo Bu skript kerakli kutubxonalarni o'rnatib,
echo serverini to'g'ridan-to'g'ri ishga tushiradi.
echo (.exe yasash kerak bo'lmagan holat uchun)
echo.

cd /d "%~dp0server"

echo [1/2] Kutubxonalar o'rnatilmoqda...
pip install -r requirements.txt -q
echo     OK

echo [2/2] Server ishga tushirilmoqda...
echo.
python run_server.py

pause
