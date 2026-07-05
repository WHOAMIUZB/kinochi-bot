from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from config import CATEGORIES, MOVIES_PER_PAGE, BOT_USERNAME


def main_reply_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📂 Menyu"), KeyboardButton(text="🔢 Kod orqali qidirish")],
            [KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True,
    )


def welcome_inline_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Tez qidirish", switch_inline_query_current_chat="")]
        ]
    )


def subscribe_kb(channels) -> InlineKeyboardMarkup:
    rows = []
    for _id, chat_id, title, username, invite_link, chat_type in channels:
        url = f"https://t.me/{username}" if username else invite_link
        rows.append([InlineKeyboardButton(text=f"📢 {title}", url=url)])
    rows.append([InlineKeyboardButton(text="✅ Obuna bo'ldim", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def categories_kb() -> InlineKeyboardMarkup:
    rows = []
    for key, label in CATEGORIES.items():
        if key == "series":
            rows.append([InlineKeyboardButton(text=label, callback_data="seriescat:0")])
        else:
            rows.append([InlineKeyboardButton(text=label, callback_data=f"cat:{key}:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_numbered_kb(items, select_prefix: str, page: int, total: int,
                       page_callback_prefix: str, back_callback: str):
    """
    items: [(id, label), ...] (bitta sahifadagi elementlar, odatda <=10 ta)
    Har bir element uchun matnli qator ("1. Nomi") va tagida 1..N raqamli tugmalar.
    """
    lines = []
    number_buttons = []
    for idx, (item_id, label) in enumerate(items, start=1):
        lines.append(f"{idx}. {label}")
        number_buttons.append(InlineKeyboardButton(text=str(idx), callback_data=f"{select_prefix}:{item_id}"))

    rows = [number_buttons[i:i + 5] for i in range(0, len(number_buttons), 5)]

    nav_row = []
    offset = page * MOVIES_PER_PAGE
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"{page_callback_prefix}:{page-1}"))
    if offset + MOVIES_PER_PAGE < total:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"{page_callback_prefix}:{page+1}"))
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_callback)])

    text = "\n".join(lines) if lines else "Ro'yxat hozircha bo'sh."
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def movie_caption(name, category, fmt, language, subtitle, code, downloads, category_label):
    return (
        f"🎬 <b>{name}</b>\n\n"
        f"📁 Turi: {category_label}\n"
        f"🎞 Format: {fmt}\n"
        f"🗣 Til: {language}\n"
        f"💬 Subtitr: {subtitle}\n"
        f"🔑 Kino kodi: <code>{code}</code>\n"
        f"📥 Yuklab olingan: {downloads} marta\n\n"
        f"🤖 @{BOT_USERNAME}"
    )


def episode_caption(series_title, episode_label, fmt, language, subtitle, code, downloads):
    return (
        f"📺 <b>{series_title}</b>\n"
        f"🎬 Qism: {episode_label}\n\n"
        f"🎞 Format: {fmt}\n"
        f"🗣 Til: {language}\n"
        f"💬 Subtitr: {subtitle}\n"
        f"🔑 Kod: <code>{code}</code>\n"
        f"📥 Yuklab olingan: {downloads} marta\n\n"
        f"🤖 @{BOT_USERNAME}"
    )
