#!/bin/bash
# Smart Exam System — Build skripti
# Ishlatish: cd "Exam .exe" && bash build.sh

set -e
cd "$(dirname "$0")/client"

echo "========================================"
echo "  Smart Exam System — Build"
echo "========================================"

# PyInstaller bormi?
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller topilmadi. O'rnatilmoqda..."
    pip3 install pyinstaller
fi

echo ""
echo "1) O'quvchi paneli qurilmoqda..."
pyinstaller --clean --noconfirm student.spec

echo ""
echo "2) O'qituvchi paneli qurilmoqda..."
pyinstaller --clean --noconfirm teacher.spec

echo ""
echo "========================================"
echo "  BUILD MUVAFFAQIYATLI YAKUNLANDI!"
echo ""
echo "  Tayyor fayllar:"
echo "  dist/OquvchiPanel.app     <- o'quvchi uchun"
echo "  dist/OqituvchiPanel.app   <- o'qituvchi/admin uchun"
echo ""
echo "  TARQATISH UCHUN:"
echo "  1. dist/ papkasidagi .app faylini nusxalang"
echo "  2. Boshqa Mac-ga ko'chiring — ishga tushadi!"
echo "========================================"
