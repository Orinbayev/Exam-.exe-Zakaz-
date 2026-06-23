"""
/start komandasi va til tanlash.
"""
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from .texts import T
from .keyboards import lang_kb, parent_main_kb, admin_main_kb
from .helpers import get_or_create_bot_user, set_user_lang, is_bot_admin
from ..database import SessionLocal
from ..models import Student

router = Router()


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
