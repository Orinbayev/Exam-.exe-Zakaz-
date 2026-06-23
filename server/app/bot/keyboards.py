"""
Inline klaviaturalar — aiogram v3.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def lang_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang:uz"),
    )
    builder.adjust(2)
    return builder.as_markup()


def lang_change_kb(lang: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="setlang:uz"),
    )
    builder.row(InlineKeyboardButton(text="⬅️", callback_data="parent_main"))
    return builder.as_markup()


def parent_main_kb(lang: str) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=T(lang, "children_btn"), callback_data="parent_children"))
    builder.row(InlineKeyboardButton(text=T(lang, "lang_btn"), callback_data="parent_settings"))
    return builder.as_markup()


def admin_main_kb(lang: str) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=T(lang, "stats_btn"), callback_data="admin_stats"))
    builder.row(
        InlineKeyboardButton(text=T(lang, "students_btn"), callback_data="admin_students"),
        InlineKeyboardButton(text=T(lang, "top_btn"), callback_data="admin_top"),
    )
    builder.row(
        InlineKeyboardButton(text=T(lang, "subjects_btn"), callback_data="admin_subjects"),
        InlineKeyboardButton(text=T(lang, "questions_btn"), callback_data="admin_questions"),
    )
    builder.row(InlineKeyboardButton(text=T(lang, "broadcast_btn"), callback_data="admin_broadcast"))
    builder.row(InlineKeyboardButton(text=T(lang, "admins_btn"), callback_data="admin_admins"))
    builder.row(InlineKeyboardButton(text=T(lang, "lang_btn"), callback_data="parent_settings"))
    return builder.as_markup()


def back_students_kb(lang: str) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=T(lang, "back"), callback_data="admin_students"))
    return builder.as_markup()


def class_detail_kb(lang: str, class_id: int) -> InlineKeyboardMarkup:
    """Sinf tafsiloti — o'quvchi qo'shish + orqaga."""
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text=T(lang, "std_add_btn"),
        callback_data=f"std_add:{class_id}"
    ))
    builder.row(InlineKeyboardButton(text=T(lang, "back"), callback_data="admin_students"))
    return builder.as_markup()


def skip_kb(lang: str) -> InlineKeyboardMarkup:
    """Ota-ona TG ID ni o'tkazib yuborish uchun."""
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=T(lang, "std_add_skip_btn"), callback_data="std_skip_parent"))
    return builder.as_markup()


def back_admin_kb(lang: str) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=T(lang, "back"), callback_data="admin_menu"))
    return builder.as_markup()


def back_kb(lang: str) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=T(lang, "back"), callback_data="parent_main"))
    return builder.as_markup()


def back_children_kb(lang: str) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=T(lang, "back"), callback_data="parent_children"))
    return builder.as_markup()


def children_kb(lang: str, children: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in children:
        text = f"👤 {c['last']} {c['first']} ({c['cls']})"
        builder.row(InlineKeyboardButton(text=text, callback_data=f"child:{c['id']}"))
    builder.row(InlineKeyboardButton(text="⬅️", callback_data="parent_main"))
    return builder.as_markup()


def confirm_kb(lang: str, yes_cb: str = "q_confirm_yes", no_cb: str = "q_confirm_no") -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=T(lang, "confirm_btn"), callback_data=yes_cb),
        InlineKeyboardButton(text=T(lang, "cancel_btn"), callback_data=no_cb),
    )
    builder.adjust(2)
    return builder.as_markup()


def subjects_kb(cats: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in cats:
        name = c["name"][:30]
        builder.row(InlineKeyboardButton(text=f"📚 {name}", callback_data=f"qsubj:{c['id']}:{name}"))
    builder.row(InlineKeyboardButton(text="❌", callback_data="q_cancel"))
    return builder.as_markup()


def correct_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for letter in ["A", "B", "C", "D"]:
        builder.add(InlineKeyboardButton(text=letter, callback_data=f"correct:{letter}"))
    builder.adjust(4)
    return builder.as_markup()


def difficulty_kb(lang: str) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=T(lang, "q_diff_easy"), callback_data="diff:easy"),
        InlineKeyboardButton(text=T(lang, "q_diff_med"), callback_data="diff:medium"),
        InlineKeyboardButton(text=T(lang, "q_diff_hard"), callback_data="diff:hard"),
    )
    return builder.as_markup()


def classes_kb(lang: str, cls_list: list) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    for c in cls_list:
        builder.row(InlineKeyboardButton(
            text=f"🏫 {c['name']} ({c['n']} {T(lang, 'students_btn')})",
            callback_data=f"cls:{c['id']}"
        ))
    builder.row(InlineKeyboardButton(text=T(lang, "back"), callback_data="admin_menu"))
    return builder.as_markup()


def admin_questions_kb(lang: str, cats: list) -> InlineKeyboardMarkup:
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=T(lang, "add_question_btn"), callback_data="q_add_start"))
    builder.row(InlineKeyboardButton(text=T(lang, "back"), callback_data="admin_menu"))
    return builder.as_markup()


def admin_subjects_kb(lang: str) -> InlineKeyboardMarkup:
    """Fanlar ro'yxati uchun — qo'shish tugmasi bilan."""
    from .texts import T
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=T(lang, "fan_add_btn"), callback_data="fan_add_start"))
    builder.row(InlineKeyboardButton(text=T(lang, "back"), callback_data="admin_menu"))
    return builder.as_markup()


def admin_classes_kb(lang: str, cls_list: list) -> InlineKeyboardMarkup:
    """Sinflar ro'yxati uchun — qo'shish tugmasi bilan."""
    from .texts import T
    builder = InlineKeyboardBuilder()
    for c in cls_list:
        builder.row(InlineKeyboardButton(
            text=f"🏫 {c['name']} ({c['n']})",
            callback_data=f"cls:{c['id']}"
        ))
    builder.row(InlineKeyboardButton(text=T(lang, "cls_add_btn"), callback_data="cls_add_start"))
    builder.row(InlineKeyboardButton(text=T(lang, "back"), callback_data="admin_menu"))
    return builder.as_markup()
