import re
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery

from config import CATEGORIES, MOVIES_PER_PAGE, CODE_MIN_LEN, CODE_MAX_LEN
from database import db
from utils.subscription import get_unsubscribed_channels
from keyboards.user_kb import (
    main_reply_kb,
    welcome_inline_kb,
    subscribe_kb,
    categories_kb,
    build_numbered_kb,
    movie_caption,
    episode_caption,
)

router = Router(name="user")

WELCOME_TEXT = (
    "📺 Eski Televizorga xush kelibsiz!\n\n"
    "3 xil yo'l bilan filmni tomosha qiling:\n"
    "🎯 Tez qidirish tugmasini bosing va kerakli filmni tanlang\n"
    "🔢 Maxsus kodni yuboring\n"
    "📂 Menyudan qidiring"
)

HELP_TEXT = (
    "ℹ️ <b>Botdan foydalanish qo'llanmasi</b>\n\n"
    "🎯 <b>Tez qidirish</b> — tugmani bosing, ochilgan qatorga kino yoki serial nomini yozing, "
    "chiqqan natijalardan birini tanlang.\n\n"
    "🔢 <b>Kod orqali</b> — kino/qism tagida yozilgan kodni botga yuboring.\n\n"
    "📂 <b>Menyu orqali</b> — \"📂 Menyu\" tugmasini bosib, bo'limlardan birini tanlang. "
    "Serial tanlasangiz, avval serial nomi, so'ng uning qismlari chiqadi."
)

CODE_RE = re.compile(rf"^\d{{{CODE_MIN_LEN},{CODE_MAX_LEN}}}$")


async def send_movie(bot: Bot, chat_id: int, movie_row):
    movie_id, code, name, category, fmt, language, subtitle, file_id, downloads = movie_row
    label = CATEGORIES.get(category, category)
    await bot.send_video(
        chat_id=chat_id,
        video=file_id,
        caption=movie_caption(name, category, fmt, language, subtitle, code, downloads + 1, label),
    )
    await db.increment_movie_downloads(movie_id)


async def send_episode(bot: Bot, chat_id: int, episode_row):
    (ep_id, code, episode_label, fmt, language, subtitle, file_id, downloads,
     series_id, series_title) = episode_row
    await bot.send_video(
        chat_id=chat_id,
        video=file_id,
        caption=episode_caption(series_title, episode_label, fmt, language, subtitle, code, downloads + 1),
    )
    await db.increment_episode_downloads(ep_id)


async def send_by_found(bot: Bot, chat_id: int, found: dict):
    if found["kind"] == "movie":
        movie = await db.get_movie_by_id(found["id"])
        await send_movie(bot, chat_id, movie)
    else:
        episode = await db.get_episode_by_id(found["id"])
        await send_episode(bot, chat_id, episode)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot, command: CommandObject):
    await db.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    unsubscribed = await get_unsubscribed_channels(bot, message.from_user.id)
    if unsubscribed and not await db.is_admin(message.from_user.id):
        await message.answer(
            "⛔️ Botdan foydalanish uchun quyidagi kanal/guruhlarga obuna bo'ling, "
            "so'ng \"✅ Obuna bo'ldim\" tugmasini bosing.",
            reply_markup=subscribe_kb(unsubscribed),
        )
        return

    if command.args and command.args.startswith("film_"):
        code = command.args.replace("film_", "")
        found = await db.find_by_code(code)
        if found:
            await send_by_found(bot, message.chat.id, found)

    await message.answer(WELCOME_TEXT, reply_markup=welcome_inline_kb())
    await message.answer("Quyidagi tugmalardan foydalanishingiz mumkin 👇", reply_markup=main_reply_kb())


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    unsubscribed = await get_unsubscribed_channels(bot, callback.from_user.id)
    if unsubscribed:
        await callback.answer("❌ Siz hali barcha kanallarga obuna bo'lmagansiz!", show_alert=True)
        return
    await callback.message.delete()
    await callback.message.answer(WELCOME_TEXT, reply_markup=welcome_inline_kb())
    await callback.message.answer("Quyidagi tugmalardan foydalanishingiz mumkin 👇", reply_markup=main_reply_kb())


@router.message(F.text == "ℹ️ Yordam")
async def help_handler(message: Message):
    await message.answer(HELP_TEXT)


@router.message(F.text == "📂 Menyu")
async def menu_handler(message: Message):
    await message.answer("Kerakli bo'limni tanlang 👇", reply_markup=categories_kb())


@router.message(F.text == "🔢 Kod orqali qidirish")
async def ask_code_handler(message: Message):
    await message.answer("🔢 Kino yoki qism kodini yuboring, masalan: <code>47</code>")


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    await callback.message.edit_text("Kerakli bo'limni tanlang 👇", reply_markup=categories_kb())


# ==================== KINO / MULTFILM (oddiy kategoriyalar) ====================

@router.callback_query(F.data.startswith("cat:"))
async def category_page(callback: CallbackQuery):
    _, category, page_str = callback.data.split(":")
    page = int(page_str)
    offset = page * MOVIES_PER_PAGE
    movies = await db.get_movies_by_category(category, offset, MOVIES_PER_PAGE)
    total = await db.count_movies_by_category(category)

    if not movies:
        await callback.answer("Bu bo'limda hozircha kino yo'q.", show_alert=True)
        return

    label = CATEGORIES.get(category, category)
    items = [(movie_id, name) for movie_id, code, name in movies]
    listing, kb = build_numbered_kb(items, "pick", page, total, f"cat:{category}", "back_to_categories")
    text = f"{label} bo'limi ({total} ta):\n\n{listing}\n\nKerakli raqamni tanlang 👇"
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("pick:"))
async def pick_movie(callback: CallbackQuery, bot: Bot):
    movie_id = int(callback.data.split(":")[1])
    movie = await db.get_movie_by_id(movie_id)
    if not movie:
        await callback.answer("Kino topilmadi.", show_alert=True)
        return
    await callback.answer()
    await send_movie(bot, callback.from_user.id, movie)


# ==================== SERIALLAR (katalog -> qismlar) ====================

@router.callback_query(F.data.startswith("seriescat:"))
async def series_catalog_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])
    offset = page * MOVIES_PER_PAGE
    series_list = await db.get_all_series(offset, MOVIES_PER_PAGE)
    total = await db.count_series()

    if not series_list:
        await callback.answer("Hozircha seriallar mavjud emas.", show_alert=True)
        return

    items = [(sid, title) for sid, title in series_list]
    listing, kb = build_numbered_kb(items, "pickseries", page, total, "seriescat", "back_to_categories")
    text = f"📺 Seriallar ({total} ta):\n\n{listing}\n\nKerakli serialni tanlang 👇"
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("pickseries:"))
async def pick_series(callback: CallbackQuery):
    series_id = int(callback.data.split(":")[1])
    await show_episodes_page(callback, series_id, 0)


@router.callback_query(F.data.startswith("epcat:"))
async def episodes_page_cb(callback: CallbackQuery):
    _, series_id, page = callback.data.split(":")
    await show_episodes_page(callback, int(series_id), int(page))


async def show_episodes_page(callback: CallbackQuery, series_id: int, page: int):
    series = await db.get_series_by_id(series_id)
    if not series:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return
    offset = page * MOVIES_PER_PAGE
    episodes = await db.get_episodes_by_series(series_id, offset, MOVIES_PER_PAGE)
    total = await db.count_episodes_by_series(series_id)

    if not episodes:
        await callback.answer("Bu serialda hozircha qism yo'q.", show_alert=True)
        return

    items = [(ep_id, label) for ep_id, code, label in episodes]
    listing, kb = build_numbered_kb(items, "pickepisode", page, total, f"epcat:{series_id}", "seriescat:0")
    text = f"📺 {series[1]}\n\nQismlar ({total} ta):\n\n{listing}\n\nKerakli qismni tanlang 👇"
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("pickepisode:"))
async def pick_episode(callback: CallbackQuery, bot: Bot):
    episode_id = int(callback.data.split(":")[1])
    episode = await db.get_episode_by_id(episode_id)
    if not episode:
        await callback.answer("Qism topilmadi.", show_alert=True)
        return
    await callback.answer()
    await send_episode(bot, callback.from_user.id, episode)


# ==================== KOD ORQALI QIDIRUV ====================

@router.message(F.text.regexp(CODE_RE.pattern))
async def code_search_handler(message: Message, bot: Bot):
    code = message.text.strip()
    found = await db.find_by_code(code)
    if not found:
        await message.answer("❌ Bunday kodga ega kino yoki qism topilmadi. Kodni tekshirib qaytadan yuboring.")
        return
    await send_by_found(bot, message.chat.id, found)
