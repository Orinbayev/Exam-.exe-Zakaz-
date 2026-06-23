"""
Reklama (broadcast) paneli — barcha ota-onalarga xabar yuborish.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from .states import BroadcastState
from .texts import T
from .keyboards import confirm_kb, back_admin_kb
from .helpers import get_or_create_bot_user, is_bot_admin
from ..database import SessionLocal
from ..models import BotUser

router = Router()


def _lang(tid: str) -> str:
    user = get_or_create_bot_user(tid)
    return user["lang"]


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    tid = str(call.from_user.id)
    lang = _lang(tid)
    if not is_bot_admin(tid):
        await call.answer(T(lang, "not_admin"), show_alert=True)
        return
    await state.set_state(BroadcastState.text)
    await call.message.edit_text(T(lang, "broadcast_ask"), parse_mode="HTML")
    await call.answer()


@router.message(BroadcastState.text)
async def got_broadcast_text(message: Message, state: FSMContext):
    tid = str(message.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        parents = db.query(BotUser).filter(BotUser.role == "parent").all()
        n = len(parents)
    finally:
        db.close()

    await state.update_data(text=message.text)
    await state.set_state(BroadcastState.confirm)
    await message.answer(
        T(lang, "broadcast_confirm", n=n, text=message.text[:200]),
        reply_markup=confirm_kb(lang, yes_cb="bc_yes", no_cb="bc_no"),
        parse_mode="HTML",
    )


@router.callback_query(BroadcastState.confirm, F.data == "bc_yes")
async def send_broadcast(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    tid = str(call.from_user.id)
    lang = _lang(tid)

    db = SessionLocal()
    try:
        parents = db.query(BotUser).filter(BotUser.role == "parent").all()
        parent_ids = [p.telegram_id for p in parents]
        total = len(parent_ids)
    finally:
        db.close()

    bot = call.bot
    ok = 0
    for pid in parent_ids:
        try:
            await bot.send_message(pid, data["text"], parse_mode="HTML")
            ok += 1
        except Exception:
            pass

    await call.message.edit_text(
        T(lang, "broadcast_sent", ok=ok, total=total),
        reply_markup=back_admin_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()


@router.callback_query(F.data == "bc_no")
async def cancel_broadcast(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tid = str(call.from_user.id)
    lang = _lang(tid)
    await call.message.edit_text(
        T(lang, "broadcast_cancel"),
        reply_markup=back_admin_kb(lang),
        parse_mode="HTML",
    )
    await call.answer()
