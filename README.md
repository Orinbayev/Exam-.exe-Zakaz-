# 🎓 Smart Exam System

**Maktab, o'quv markazi va bog'chalar uchun professional test tizimi**

---

## 📋 Loyiha haqida

Smart Exam System — lokal tarmoq (LAN/WiFi) orqali ishlaydigan client-server arxitekturasidagi test tizimi. Internet talab etilmaydi.

---

## 🏗️ Arxitektura

```
[Server - O'qituvchi kompyuteri]
    FastAPI + SQLite
    Port: 8000

[Client - O'quvchi kompyuterlari]
    PyQt6 Desktop App
    Serverga HTTP orqali ulanadi
```

---

## 👥 Rollar

| Rol | Huquqlar |
|-----|----------|
| **Super Admin** | Hammasi: foydalanuvchilar, testlar, natijalar, sozlamalar, loglar |
| **Teacher** | O'z testlari va savollari, natijalar, statistika |
| **Student** | Test yechish (token talab etilmaydi) |

---

## 🚀 Ishga tushirish

### Variant 1: To'g'ridan-to'g'ri Python bilan

**Server (O'qituvchi kompyuterida):**
```bash
install_and_run.bat
```

**Client (Har bir o'quvchi kompyuterida):**
```bash
install_client.bat
```

### Variant 2: .exe yasash

```bash
build.bat
```
`dist/` papkasida `ExamServer.exe` va `ExamClient.exe` paydo bo'ladi.

---

## 🔑 Default kirish

```
Username: admin
Password: admin123
```
⚠️ **Birinchi kirishda parolni o'zgartiring!**

---

## 📁 Loyiha tuzilmasi

```
Exam .exe/
├── server/               # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI ilovasi
│   │   ├── models.py     # SQLAlchemy modellari
│   │   ├── schemas.py    # Pydantic sxemalari
│   │   ├── auth.py       # JWT autentifikatsiya
│   │   ├── excel_export.py
│   │   ├── telegram_bot.py
│   │   └── routers/      # API endpointlar
│   └── run_server.py
│
├── client/               # PyQt6 desktop client
│   ├── app/
│   │   ├── api_client.py # HTTP client
│   │   ├── config.py     # Server manzili
│   │   ├── styles.py     # QSS stillari
│   │   └── windows/
│   │       ├── login_window.py
│   │       ├── teacher/  # O'qituvchi paneli
│   │       ├── superadmin/
│   │       └── student/  # O'quvchi test oynasi
│   └── run_client.py
│
├── build.bat             # .exe yasash skripti
├── install_and_run.bat   # Server ishga tushirish
└── install_client.bat    # Client ishga tushirish
```

---

## ⚙️ Texnologiyalar

| Qism | Texnologiya |
|------|-------------|
| Backend | Python + FastAPI |
| Database | SQLite |
| Desktop UI | PyQt6 |
| Auth | JWT (python-jose) |
| Excel | openpyxl |
| Telegram | aiogram |
| Charts | matplotlib |
| Packaging | PyInstaller |

---

## 🌟 Asosiy xususiyatlar

### O'qituvchi uchun
- ✅ Savollar CRUD (qo'shish, tahrirlash, o'chirish)
- ✅ Excel orqali savollar import
- ✅ Testlar yaratish va boshqarish
- ✅ Test nusxalash
- ✅ Baholash tizimini sozlash (5=90%, 4=70%, ...)
- ✅ O'tish foizini belgilash
- ✅ Natijalar jadval va diagrammalar
- ✅ Excel eksport
- ✅ Top 10 o'quvchilar reytingi

### O'quvchi uchun
- ✅ Ism/Familiya/Sinf kiritish
- ✅ Test tanlash
- ✅ Fullscreen rejim
- ✅ Klaviatura shortcut (1,2,3,4 yoki F1,F2,F3,F4)
- ✅ Countdown timer
- ✅ Progress bar
- ✅ Konfetti animatsiyasi (o'tsa)
- ✅ Animatsion natija oynasi

### Super Admin uchun
- ✅ Foydalanuvchi yaratish/o'chirish
- ✅ Telegram bot sozlamalari
- ✅ Audit loglar
- ✅ Barcha natijalar

---

## 🔒 Xavfsizlik

- JWT token autentifikatsiya
- BCrypt parol hashing
- Rollarga asosida kirish cheklovi
- Audit log (barcha harakatlar yoziladi)
- Test paytida fullscreen (ESC bilan chiqishga tasdiq so'raladi)

---

## 📊 API hujjat

Server ishga tushgandan keyin:
```
http://[SERVER_IP]:8000/docs
```

---

## 📱 Telegram bot sozlash

1. `@BotFather` orqali bot yarating
2. Bot tokenini oling
3. Super Admin panelidagi "Sozlamalar" ga token kiriting
4. O'qituvchi profilida Telegram Chat ID kiriting
5. Har bir test natijasi avtomatik yuboriladi

---

## ❓ Muammolar va yechimlar

**Server ishlamayapti:**
- Firewall da 8000 portni oching
- Windows Defender xabari kelsa "Allow access" ni bosing

**Client serverga ulanmayapti:**
- Server va client bir tarmoqda bo'lishi kerak
- Server ekranidagi IP manzilni to'g'ri kiriting
- `http://` qo'shib kiriting

**Excel import ishlamayapti:**
- Fayl formati: .xlsx
- Ustunlar tartibi: Savol | A | B | C | D | To'g'ri javob | Qiyinlik

---

## 📞 Yordam

Muammolar uchun server loglarini tekshiring yoki developer bilan bog'laning.
