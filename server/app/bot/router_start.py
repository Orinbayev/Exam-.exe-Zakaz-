"""
/start komandasi va til tanlash.
"""
import json
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from .texts import T
from .keyboards import lang_kb, parent_main_kb, admin_main_kb
from .helpers import get_or_create_bot_user, set_user_lang, is_bot_admin
from ..database import SessionLocal
from ..models import Student, SystemSettings

router = Router()


# ── /myid — Telegram ID ni ko'rsatish ────────────────────────────────────────

@router.message(Command("myid"))
async def cmd_myid(message: Message):
    tid = str(message.from_user.id)
    name = message.from_user.full_name or ""
    is_admin = is_bot_admin(tid)
    status = "✅ Admin" if is_admin else "👤 Foydalanuvchi"
    await message.answer(
        f"📋 <b>Sizning Telegram ID:</b>\n"
        f"<code>{tid}</code>\n\n"
        f"👤 <b>Ism:</b> {name}\n"
        f"🔑 <b>Holat:</b> {status}\n\n"
        f"<i>Ushbu ID ni nusxalab admin panelga qo'shing.</i>",
        parse_mode="HTML",
    )


# ── /addadmin — Maxfiy parol orqali admin bo'lish ────────────────────────────

@router.message(Command("addadmin"))
async def cmd_addadmin(message: Message):
    tid  = str(message.from_user.id)
    args = message.text.split(maxsplit=1)

    if is_bot_admin(tid):
        await message.answer("✅ Siz allaqachon admin sifatida ro'yxatdan o'tgansiz.")
        return

    if len(args) < 2:
        await message.answer(
            "🔐 <b>Admin bo'lish uchun:</b>\n"
            "<code>/addadmin &lt;maxfiy_parol&gt;</code>\n\n"
            "<i>Parolni dastur egasidan oling.</i>",
            parse_mode="HTML",
        )
        return

    entered = args[1].strip()
    db = SessionLocal()
    try:
        s = db.query(SystemSettings).filter(
            SystemSettings.key == "bot_admin_secret"
        ).first()
        secret = s.value if s else "admin123"

        if entered != secret:
            await message.answer("❌ Parol noto'g'ri.")
            return

        # Admin sifatida qo'shish
        ids_row = db.query(SystemSettings).filter(
            SystemSettings.key == "bot_admin_ids"
        ).first()
        current = json.loads(ids_row.value) if ids_row and ids_row.value else []
        if tid not in current:
            current.append(tid)
            if ids_row:
                ids_row.value = json.dumps(current)
            else:
                db.add(SystemSettings(key="bot_admin_ids", value=json.dumps(current)))
            db.commit()

        name = message.from_user.full_name or ""
        await message.answer(
            f"✅ <b>{name}</b>, siz muvaffaqiyatli admin sifatida qo'shildingiz!\n\n"
            f"🆔 ID: <code>{tid}</code>\n\n"
            "Boshqaruv panelini ochish uchun /start yozing.",
            parse_mode="HTML",
        )
    finally:
        db.close()


def get_parent_children(telegram_id: str) -> list:
    db = SessionLocal()
    try:
        students = db.query(Student).filter(
            Student.parent_telegram_id == str(telegram_id)
        ).all()
        return [
            {
                "id": s.id,
                "first": s.first_name,
                "last": s.last_name,
                "cls": s.student_class.name if s.student_class else "?",
            }
            for s in students
        ]
    finally:
        db.close()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tid = str(message.from_user.id)
    user = get_or_create_bot_user(tid)
    lang = user["lang"]

    # Admin tekshirish
    if is_bot_admin(tid):
        await message.answer(
            T(lang, "start_welcome_admin"),
            reply_markup=admin_main_kb(lang),
            parse_mode="HTML",
        )
        return

    # Ota-ona farzandlari bormi?
    children = get_parent_children(tid)
    if children:
        name = message.from_user.first_name or ""
        await message.answer(
            T(lang, "start_welcome_parent", name=name),
            reply_markup=parent_main_kb(lang),
            parse_mode="HTML",
        )
    else:
        # Yangi foydalanuvchi — til tanlash
        await message.answer(
            T(lang, "start_new"),
            reply_markup=lang_kb(),
            parse_mode="HTML",
        )


@router.callback_query(F.data.startswith("setlang:"))
async def set_language(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    tid = str(call.from_user.id)
    set_user_lang(tid, lang)

    # Admin tekshirish
    if is_bot_admin(tid):
        await call.message.edit_text(
            T(lang, "start_welcome_admin"),
            reply_markup=admin_main_kb(lang),
            parse_mode="HTML",
        )
        await call.answer()
        return

    children = get_parent_children(tid)
    if children:
        name = call.from_user.first_name or ""
        await call.message.edit_text(
            T(lang, "start_welcome_parent", name=name),
            reply_markup=parent_main_kb(lang),
            parse_mode="HTML",
        )
    else:
        await call.message.edit_text(
            T(lang, "no_children", chat_id=tid),
            parse_mode="HTML",
        )
    await call.answer()
