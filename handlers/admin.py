import asyncio
import datetime
import re

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import CATEGORIES, MAIN_ADMIN_ID, CODE_MIN_LEN, CODE_MAX_LEN, MOVIES_PER_PAGE
from database import db
from states.admin_states import (
    AddMovie, EditMovie, DeleteMovie, AddChannel, AddAdmin, Broadcast, SeriesManage,
)
from keyboards.admin_kb import (
    admin_main_kb, cancel_kb, category_choice_kb, channels_menu_kb,
    admins_menu_kb, edit_field_kb, edit_episode_field_kb, confirm_broadcast_kb,
    series_choice_kb, series_manage_kb, confirm_delete_kb,
)
from utils.filters import IsAdmin
from utils.subscription import is_bot_admin_in_chat

router = Router(name="admin")
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

CODE_RE = re.compile(rf"^\d{{{CODE_MIN_LEN},{CODE_MAX_LEN}}}$")


# ==================== ASOSIY PANEL ====================

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🛠 <b>Admin panel</b>\n\nKerakli bo'limni tanlang:", reply_markup=admin_main_kb())


@router.callback_query(F.data == "adm:back")
async def adm_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🛠 <b>Admin panel</b>\n\nKerakli bo'limni tanlang:", reply_markup=admin_main_kb())


@router.callback_query(F.data == "adm:cancel")
async def adm_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.\n\n🛠 <b>Admin panel</b>", reply_markup=admin_main_kb())


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


# ==================== KINO / MULTFILM / SERIAL QO'SHISH ====================

@router.callback_query(F.data == "adm:add_movie")
async def add_movie_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.category)
    await callback.message.edit_text("📁 Qo'shmoqchi bo'lgan kontent turini tanlang:", reply_markup=category_choice_kb("newcat"))


@router.callback_query(AddMovie.category, F.data.startswith("newcat:"))
async def add_movie_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    await state.update_data(category=category)

    if category == "series":
        series_list = await db.get_all_series(0, 50)
        await state.set_state(AddMovie.choose_series)
        await callback.message.edit_text(
            "📺 Bu qism qaysi serialga tegishli? Mavjudlardan tanlang yoki yangi serial yarating:",
            reply_markup=series_choice_kb(series_list),
        )
        return

    await state.set_state(AddMovie.name)
    label = CATEGORIES.get(category, category)
    await callback.message.edit_text(f"🎬 {label} nomini yuboring:", reply_markup=cancel_kb())


@router.callback_query(AddMovie.choose_series, F.data.startswith("chooseseries:"))
async def add_movie_choose_series(callback: CallbackQuery, state: FSMContext):
    series_id = int(callback.data.split(":")[1])
    series = await db.get_series_by_id(series_id)
    await state.update_data(series_id=series_id, series_title=series[1])
    await state.set_state(AddMovie.name)
    await callback.message.edit_text(
        f"📺 Serial: {series[1]}\n\n🔢 Qism nomi/raqamini kiriting (masalan: \"1-qism\" yoki \"Fasl 2, 5-qism\"):",
        reply_markup=cancel_kb(),
    )


@router.callback_query(AddMovie.choose_series, F.data == "newseries")
async def add_movie_new_series(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddMovie.new_series_title)
    await callback.message.edit_text("📺 Yangi serial nomini kiriting:", reply_markup=cancel_kb())


@router.message(AddMovie.new_series_title)
async def add_movie_new_series_title(message: Message, state: FSMContext):
    title = message.text.strip()
    series_id = await db.add_series(title)
    await state.update_data(series_id=series_id, series_title=title)
    await state.set_state(AddMovie.name)
    await message.answer(
        f"✅ \"{title}\" serial sifatida yaratildi.\n\n🔢 Qism nomi/raqamini kiriting (masalan: \"1-qism\"):",
        reply_markup=cancel_kb(),
    )


@router.message(AddMovie.name)
async def add_movie_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddMovie.video)
    await message.answer("🎞 Endi video faylni yuboring (video yoki fayl shaklida):")


@router.message(AddMovie.video, F.video | F.document)
async def add_movie_video(message: Message, state: FSMContext):
    file_id = message.video.file_id if message.video else message.document.file_id
    await state.update_data(file_id=file_id)
    await state.set_state(AddMovie.format)
    await message.answer("🎞 Format nomini kiriting (masalan: HD 720p, MP4):")


@router.message(AddMovie.video)
async def add_movie_video_invalid(message: Message):
    await message.answer("❗️ Iltimos, video yoki fayl shaklida yuboring.")


@router.message(AddMovie.format)
async def add_movie_format(message: Message, state: FSMContext):
    await state.update_data(format=message.text.strip())
    await state.set_state(AddMovie.language)
    await message.answer("🗣 Tilini kiriting (masalan: O'zbek tilida):")


@router.message(AddMovie.language)
async def add_movie_language(message: Message, state: FSMContext):
    await state.update_data(language=message.text.strip())
    await state.set_state(AddMovie.subtitle)
    await message.answer("💬 Subtitr haqida ma'lumot kiriting (yo'q bo'lsa \"yo'q\" deb yozing):")


@router.message(AddMovie.subtitle)
async def add_movie_subtitle(message: Message, state: FSMContext):
    await state.update_data(subtitle=message.text.strip())
    await state.set_state(AddMovie.code)
    await message.answer(
        f"🔑 Maxsus kod kiriting (raqamlardan iborat, {CODE_MIN_LEN}-{CODE_MAX_LEN} xonagacha, masalan: 47 yoki 1024):"
    )


@router.message(AddMovie.code)
async def add_movie_code(message: Message, state: FSMContext, bot: Bot):
    code = message.text.strip()
    if not CODE_RE.match(code):
        await message.answer(f"❗️ Kod faqat raqamlardan iborat bo'lishi va {CODE_MIN_LEN}-{CODE_MAX_LEN} xonada bo'lishi kerak. Qaytadan kiriting:")
        return
    if await db.code_exists(code):
        await message.answer("❗️ Bu kod band. Boshqa kod kiriting:")
        return

    data = await state.get_data()
    category = data["category"]

    if category == "series":
        await db.add_episode(
            series_id=data["series_id"],
            episode_label=data["name"],
            fmt=data["format"],
            language=data["language"],
            subtitle=data["subtitle"],
            code=code,
            file_id=data["file_id"],
        )
        await state.clear()
        await message.answer(
            f"✅ Yangi qism qo'shildi!\n\n📺 {data['series_title']}\n🎬 {data['name']}\n🔑 Kod: {code}",
            reply_markup=admin_main_kb(),
        )
        asyncio.create_task(
            notify_users_new_content(bot, f"{data['series_title']} — {data['name']}", "📺 Serial", code)
        )
    else:
        await db.add_movie(
            code=code, name=data["name"], category=category, fmt=data["format"],
            language=data["language"], subtitle=data["subtitle"], file_id=data["file_id"],
        )
        await state.clear()
        label = CATEGORIES.get(category, category)
        await message.answer(
            f"✅ Muvaffaqiyatli qo'shildi!\n\n🎬 {data['name']}\n📁 {label}\n🔑 Kod: {code}",
            reply_markup=admin_main_kb(),
        )
        asyncio.create_task(notify_users_new_content(bot, data["name"], label, code))


async def notify_users_new_content(bot: Bot, name: str, label: str, code: str):
    user_ids = await db.get_all_user_ids()
    text = (
        f"🆕 Yangi kontent qo'shildi!\n\n"
        f"🎬 {name}\n📁 {label}\n🔑 Kod: <code>{code}</code>\n\n"
        f"Ko'rish uchun kodni botga yuboring 👆"
    )
    for uid in user_ids:
        try:
            await bot.send_message(uid, text)
        except Exception:
            await db.mark_blocked(uid)
        await asyncio.sleep(0.04)


# ==================== SERIALLAR KATALOGI (admin panel bo'limi) ====================

@router.callback_query(F.data.startswith("adm:series_list:"))
async def series_list_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[2])
    offset = page * MOVIES_PER_PAGE
    series_list = await db.get_all_series(offset, MOVIES_PER_PAGE)
    total = await db.count_series()
    text = f"📺 Seriallar katalogi ({total} ta):" if series_list else "📺 Hozircha seriallar mavjud emas."
    await callback.message.edit_text(text, reply_markup=series_manage_kb(series_list, page, total))


@router.callback_query(F.data.startswith("adm:addepisode:"))
async def series_add_episode_shortcut(callback: CallbackQuery, state: FSMContext):
    series_id = int(callback.data.split(":")[2])
    series = await db.get_series_by_id(series_id)
    if not series:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return
    await state.update_data(category="series", series_id=series_id, series_title=series[1])
    await state.set_state(AddMovie.name)
    await callback.message.edit_text(
        f"📺 Serial: {series[1]}\n\n🔢 Qism nomi/raqamini kiriting (masalan: \"1-qism\"):",
        reply_markup=cancel_kb(),
    )


@router.callback_query(F.data.startswith("adm:renameseries:"))
async def rename_series_start(callback: CallbackQuery, state: FSMContext):
    series_id = int(callback.data.split(":")[2])
    await state.update_data(series_id=series_id)
    await state.set_state(SeriesManage.rename_title)
    await callback.message.edit_text("✏️ Serial uchun yangi nom kiriting:", reply_markup=cancel_kb())


@router.message(SeriesManage.rename_title)
async def rename_series_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.update_series_title(data["series_id"], message.text.strip())
    await state.clear()
    await message.answer("✅ Serial nomi yangilandi.", reply_markup=admin_main_kb())


@router.callback_query(F.data.startswith("adm:delseries:"))
async def delete_series_confirm(callback: CallbackQuery):
    series_id = int(callback.data.split(":")[2])
    series = await db.get_series_by_id(series_id)
    if not series:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return
    kb = confirm_delete_kb(f"adm:confirmdelseries:{series_id}")
    await callback.message.edit_text(
        f"📺 \"{series[1]}\"\n\n⚠️ Ushbu serial va uning BARCHA qismlari o'chiriladi. Rostdan ham davom etasizmi?",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("adm:confirmdelseries:"))
async def delete_series_do(callback: CallbackQuery):
    series_id = int(callback.data.split(":")[2])
    await db.delete_series(series_id)
    await callback.message.edit_text("✅ Serial va uning barcha qismlari o'chirildi.", reply_markup=admin_main_kb())


# ==================== TAHRIRLASH (kod orqali, kino yoki qism) ====================

@router.callback_query(F.data == "adm:edit_movie")
async def edit_movie_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditMovie.choose_item)
    await callback.message.edit_text("✏️ Tahrirlamoqchi bo'lgan kino/qism kodini yuboring:", reply_markup=cancel_kb())


@router.message(EditMovie.choose_item)
async def edit_movie_find(message: Message, state: FSMContext):
    code = message.text.strip()
    found = await db.find_by_code(code)
    if not found:
        await message.answer("❌ Bunday kodli kino/qism topilmadi. Qaytadan kiriting:")
        return
    await state.clear()

    if found["kind"] == "movie":
        label = CATEGORIES.get(found["category"], found["category"])
        text = (
            f"🎬 {found['name']}\n📁 {label}\n🎞 {found['format']}\n🗣 {found['language']}\n"
            f"💬 {found['subtitle']}\n🔑 {found['code']}\n📥 {found['downloads']}\n\nQaysi maydonni tahrirlaysiz?"
        )
        await message.answer(text, reply_markup=edit_field_kb(found["id"]))
    else:
        text = (
            f"📺 {found['series_title']}\n🎬 {found['episode_label']}\n🎞 {found['format']}\n"
            f"🗣 {found['language']}\n💬 {found['subtitle']}\n🔑 {found['code']}\n📥 {found['downloads']}\n\n"
            f"Qaysi maydonni tahrirlaysiz?"
        )
        await message.answer(text, reply_markup=edit_episode_field_kb(found["id"]))


@router.callback_query(F.data.startswith("adm:editfield:"))
async def edit_field_router(callback: CallbackQuery, state: FSMContext):
    _, _, kind, item_id, field = callback.data.split(":")
    item_id = int(item_id)

    if field == "category":
        await state.update_data(kind=kind, item_id=item_id, field=field)
        await state.set_state(EditMovie.new_value)
        await callback.message.edit_text("📁 Yangi turini tanlang:", reply_markup=category_choice_kb("editcat"))
        return
    if field == "file_id":
        await state.update_data(kind=kind, item_id=item_id, field=field)
        await state.set_state(EditMovie.new_video)
        await callback.message.edit_text("🎞 Yangi video faylni yuboring:")
        return

    await state.update_data(kind=kind, item_id=item_id, field=field)
    await state.set_state(EditMovie.new_value)
    await callback.message.edit_text("✏️ Yangi qiymatni kiriting:")


@router.callback_query(EditMovie.new_value, F.data.startswith("editcat:"))
async def edit_category_value(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[1]
    data = await state.get_data()
    await db.update_movie_field(data["item_id"], "category", category)
    await state.clear()
    await callback.message.edit_text("✅ Turi yangilandi.", reply_markup=admin_main_kb())


@router.message(EditMovie.new_video, F.video | F.document)
async def edit_video_value(message: Message, state: FSMContext):
    file_id = message.video.file_id if message.video else message.document.file_id
    data = await state.get_data()
    if data["kind"] == "movie":
        await db.update_movie_field(data["item_id"], "file_id", file_id)
    else:
        await db.update_episode_field(data["item_id"], "file_id", file_id)
    await state.clear()
    await message.answer("✅ Video fayl yangilandi.", reply_markup=admin_main_kb())


@router.message(EditMovie.new_value)
async def edit_text_value(message: Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    value = message.text.strip()

    if field == "code":
        if not CODE_RE.match(value):
            await message.answer(f"❗️ Kod {CODE_MIN_LEN}-{CODE_MAX_LEN} xonali raqam bo'lishi kerak. Qaytadan kiriting:")
            return
        if await db.code_exists(value):
            await message.answer("❗️ Bu kod band. Boshqa kod kiriting:")
            return

    if data["kind"] == "movie":
        await db.update_movie_field(data["item_id"], field, value)
    else:
        db_field = "episode_label" if field == "episode_label" else field
        await db.update_episode_field(data["item_id"], db_field, value)

    await state.clear()
    await message.answer("✅ Muvaffaqiyatli yangilandi.", reply_markup=admin_main_kb())


# ==================== O'CHIRISH (kod orqali, kino yoki qism) ====================

@router.callback_query(F.data == "adm:delete_movie")
async def delete_movie_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(DeleteMovie.choose_item)
    await callback.message.edit_text("🗑 O'chirmoqchi bo'lgan kino/qism kodini yuboring:", reply_markup=cancel_kb())


@router.message(DeleteMovie.choose_item)
async def delete_movie_find(message: Message, state: FSMContext):
    code = message.text.strip()
    found = await db.find_by_code(code)
    if not found:
        await message.answer("❌ Bunday kodli kino/qism topilmadi. Qaytadan kiriting:")
        return
    await state.clear()

    if found["kind"] == "movie":
        label = f"{found['name']} (kod: {found['code']})"
        kb = confirm_delete_kb(f"adm:confirmdelmovie:{found['id']}")
    else:
        label = f"{found['series_title']} — {found['episode_label']} (kod: {found['code']})"
        kb = confirm_delete_kb(f"adm:confirmdelepisode:{found['id']}")

    await message.answer(f"🎬 {label}\n\nRostdan ham o'chirmoqchimisiz?", reply_markup=kb)


@router.callback_query(F.data.startswith("adm:confirmdelmovie:"))
async def delete_movie_confirm(callback: CallbackQuery):
    movie_id = int(callback.data.split(":")[2])
    await db.delete_movie(movie_id)
    await callback.message.edit_text("✅ Kino o'chirildi.", reply_markup=admin_main_kb())


@router.callback_query(F.data.startswith("adm:confirmdelepisode:"))
async def delete_episode_confirm(callback: CallbackQuery):
    episode_id = int(callback.data.split(":")[2])
    await db.delete_episode(episode_id)
    await callback.message.edit_text("✅ Qism o'chirildi.", reply_markup=admin_main_kb())


# ==================== MAJBURIY KANALLAR ====================

@router.callback_query(F.data == "adm:channels")
async def channels_menu(callback: CallbackQuery):
    channels = await db.get_channels()
    text = "📢 Majburiy obuna kanal/guruhlari:" if channels else "📢 Hozircha majburiy kanal qo'shilmagan."
    await callback.message.edit_text(text, reply_markup=channels_menu_kb(channels))


@router.callback_query(F.data == "adm:add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddChannel.waiting_forward_or_username)
    await callback.message.edit_text(
        "📢 Kanal yoki guruhni qo'shish uchun:\n\n"
        "1️⃣ O'sha kanal/guruhdan istalgan xabarni shu yerga forward qiling\n"
        "YOKI\n"
        "2️⃣ Kanal username'ini yuboring (masalan: @mychannel)\n\n"
        "⚠️ Bot avval o'sha kanal/guruhda admin qilib qo'yilgan bo'lishi shart!",
        reply_markup=cancel_kb(),
    )


@router.message(AddChannel.waiting_forward_or_username)
async def add_channel_process(message: Message, state: FSMContext, bot: Bot):
    chat = None
    if message.forward_from_chat:
        chat = message.forward_from_chat
    elif message.text and message.text.startswith("@"):
        try:
            chat = await bot.get_chat(message.text.strip())
        except Exception:
            await message.answer("❌ Bunday username topilmadi. Qaytadan urinib ko'ring:")
            return
    else:
        await message.answer("❗️ Xabarni forward qiling yoki @username yuboring:")
        return

    if not await is_bot_admin_in_chat(bot, chat.id):
        await message.answer(
            "❌ Bot ushbu kanal/guruhda admin emas. Avval botni admin qiling, so'ng qaytadan urinib ko'ring."
        )
        return

    invite_link = None
    username = chat.username
    if not username:
        try:
            invite_link = await bot.export_chat_invite_link(chat.id)
        except Exception:
            invite_link = None

    await db.add_channel(chat.id, chat.title or chat.full_name or "Nomsiz", username, invite_link, chat.type)
    await state.clear()
    await message.answer(f"✅ \"{chat.title}\" majburiy obuna ro'yxatiga qo'shildi.", reply_markup=admin_main_kb())


@router.callback_query(F.data.startswith("adm:rmchannel:"))
async def remove_channel_cb(callback: CallbackQuery):
    chat_id = int(callback.data.split(":")[2])
    await db.remove_channel(chat_id)
    channels = await db.get_channels()
    text = "📢 Majburiy obuna kanal/guruhlari:" if channels else "📢 Hozircha majburiy kanal qo'shilmagan."
    await callback.message.edit_text(text, reply_markup=channels_menu_kb(channels))


# ==================== ADMINLAR ====================

@router.callback_query(F.data == "adm:admins")
async def admins_menu(callback: CallbackQuery):
    admins = await db.list_admins()
    await callback.message.edit_text("👤 Adminlar ro'yxati:", reply_markup=admins_menu_kb(admins, MAIN_ADMIN_ID))


@router.callback_query(F.data == "adm:add_admin")
async def add_admin_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddAdmin.waiting_id)
    await callback.message.edit_text("👤 Yangi adminning Telegram ID raqamini yuboring:", reply_markup=cancel_kb())


@router.message(AddAdmin.waiting_id)
async def add_admin_process(message: Message, state: FSMContext):
    if not message.text.strip().isdigit():
        await message.answer("❗️ Faqat raqam (ID) yuboring:")
        return
    new_admin_id = int(message.text.strip())
    await db.add_admin(new_admin_id, message.from_user.id)
    await state.clear()
    await message.answer(f"✅ {new_admin_id} admin sifatida qo'shildi.", reply_markup=admin_main_kb())


@router.callback_query(F.data.startswith("adm:rmadmin:"))
async def remove_admin_cb(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[2])
    if user_id == MAIN_ADMIN_ID:
        await callback.answer("❌ Bosh adminni o'chirib bo'lmaydi.", show_alert=True)
        return
    await db.remove_admin(user_id)
    admins = await db.list_admins()
    await callback.message.edit_text("👤 Adminlar ro'yxati:", reply_markup=admins_menu_kb(admins, MAIN_ADMIN_ID))


# ==================== STATISTIKA ====================

@router.callback_query(F.data == "adm:stats")
async def stats_handler(callback: CallbackQuery):
    today = datetime.datetime.utcnow().date().isoformat()
    total_users = await db.total_users_count()
    active_today = await db.active_users_count(today)
    new_today = await db.new_users_count(today)
    total_movies = await db.total_movies_count()
    total_series = await db.count_series()
    total_episodes = await db.total_episodes_count()

    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Umumiy foydalanuvchilar: <b>{total_users}</b>\n"
        f"🟢 Bugun faol bo'lganlar: <b>{active_today}</b>\n"
        f"🆕 Bugun qo'shilganlar: <b>{new_today}</b>\n"
        f"🎬 Kino/multfilmlar soni: <b>{total_movies}</b>\n"
        f"📺 Seriallar soni: <b>{total_series}</b>\n"
        f"🎞 Serial qismlari soni: <b>{total_episodes}</b>\n"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm:back")]])
    await callback.message.edit_text(text, reply_markup=kb)


# ==================== XABAR YUBORISH (BROADCAST) ====================

@router.callback_query(F.data == "adm:broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Broadcast.waiting_content)
    await callback.message.edit_text(
        "📣 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring "
        "(matn, rasm, video - istalgan turda bo'lishi mumkin):",
        reply_markup=cancel_kb(),
    )


@router.message(Broadcast.waiting_content)
async def broadcast_preview(message: Message, state: FSMContext):
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(Broadcast.confirm)
    await message.answer("👆 Xabar shunday ko'rinishda yuboriladi. Tasdiqlaysizmi?", reply_markup=confirm_broadcast_kb())


@router.callback_query(Broadcast.confirm, F.data == "adm:broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    await callback.message.edit_text("⏳ Xabar yuborilmoqda, iltimos kuting...")

    user_ids = await db.get_all_user_ids()
    sent, failed = 0, 0
    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=data["chat_id"], message_id=data["message_id"])
            sent += 1
        except Exception:
            failed += 1
            await db.mark_blocked(uid)
        await asyncio.sleep(0.04)

    await db.log_broadcast(callback.from_user.id, sent, failed)
    await callback.message.answer(
        f"✅ Xabar yuborish yakunlandi!\n\n📤 Yuborildi: {sent}\n❌ Yuborilmadi: {failed}",
        reply_markup=admin_main_kb(),
    )
