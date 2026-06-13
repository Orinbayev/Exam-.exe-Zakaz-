"""
Server ishga tushirish nuqtasi.
PyInstaller bilan .exe qilish uchun ham ishlaydi.
"""
import sys
import os

# PyInstaller frozen muhitda yo'llarni sozlash
if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

import uvicorn
import socket
import threading


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def print_banner(host: str, port: int):
    ip = get_local_ip()
    print("=" * 55)
    print("  🎓 SMART EXAM SYSTEM - SERVER")
    print("=" * 55)
    print(f"  📡 Lokal IP    : http://{ip}:{port}")
    print(f"  🌐 Localhost   : http://127.0.0.1:{port}")
    print(f"  📖 API hujjat  : http://{ip}:{port}/docs")
    print("=" * 55)
    print("  ✅ Default login: admin / admin123")
    print("  ⚠️  Parolni birinchi kirishda o'zgartiring!")
    print("=" * 55)
    print("  Server to'xtatish: Ctrl+C")
    print("=" * 55)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"

    print_banner(host, port)

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="warning",
        access_log=False,
    )
