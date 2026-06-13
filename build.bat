@echo off
chcp 65001 > nul
title Smart Exam System - Build

echo ============================================
echo   Smart Exam System - Build Script
echo ============================================
echo.

:: Python tekshirish
python --version 2>nul
if errorlevel 1 (
    echo [XATO] Python topilmadi! python.org dan yuklab oling.
    pause
    exit /b 1
)

:: Server dependencies
echo [1/5] Server kutubxonalari o'rnatilmoqda...
cd /d "%~dp0server"
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [XATO] Server requirements o'rnatilmadi!
    pause
    exit /b 1
)
echo     OK

:: Client dependencies
echo [2/5] Client kutubxonalari o'rnatilmoqda...
cd /d "%~dp0client"
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [XATO] Client requirements o'rnatilmadi!
    pause
    exit /b 1
)
pip install pyinstaller -q
echo     OK

:: Build server
echo [3/5] Server .exe yasalmoqda...
cd /d "%~dp0server"
pyinstaller --noconfirm --onefile --console ^
    --name "ExamServer" ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.protocols.http.h11_impl ^
    --hidden-import=uvicorn.protocols.http.httptools_impl ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=uvicorn.lifespan.on ^
    --hidden-import=sqlalchemy.dialects.sqlite ^
    --hidden-import=passlib.handlers.bcrypt ^
    --hidden-import=jose ^
    --hidden-import=aiohttp ^
    --add-data "app;app" ^
    run_server.py
if errorlevel 1 (
    echo [XATO] Server build xato!
    pause
    exit /b 1
)
echo     OK

:: Build client
echo [4/5] Client .exe yasalmoqda...
cd /d "%~dp0client"
pyinstaller --noconfirm --onefile --windowed ^
    --name "ExamClient" ^
    --hidden-import=PyQt6.QtCharts ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=matplotlib.backends.backend_qtagg ^
    --add-data "app;app" ^
    run_client.py
if errorlevel 1 (
    echo [XATO] Client build xato!
    pause
    exit /b 1
)
echo     OK

:: Copy to output folder
echo [5/5] Fayllar output papkasiga ko'chirilmoqda...
set OUTPUT=%~dp0dist
if not exist "%OUTPUT%" mkdir "%OUTPUT%"

copy /Y "%~dp0server\dist\ExamServer.exe" "%OUTPUT%\"
copy /Y "%~dp0client\dist\ExamClient.exe" "%OUTPUT%\"

echo.
echo ============================================
echo   BUILD MUVAFFAQIYATLI YAKUNLANDI!
echo ============================================
echo.
echo   Fayllar joylashuvi:
echo   %OUTPUT%\ExamServer.exe  - SERVER
echo   %OUTPUT%\ExamClient.exe  - CLIENT
echo.
echo   Ishlatish tartibi:
echo   1. O'qituvchi kompyuterida ExamServer.exe ni ishga tushiring
echo   2. Server IP manzilini eslab qoling (ekranda ko'rinadi)
echo   3. Har bir o'quvchi kompyuterida ExamClient.exe ni oching
echo   4. Server IP manzilini kiriting va testni boshlang
echo.
pause
