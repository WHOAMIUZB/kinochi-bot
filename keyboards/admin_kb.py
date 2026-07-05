from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CATEGORIES


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Kino/Serial qo'shish", callback_data="adm:add_movie")],
            [InlineKeyboardButton(text="✏️ Tahrirlash (kod orqali)", callback_data="adm:edit_movie")],
            [InlineKeyboardButton(text="🗑 O'chirish (kod orqali)", callback_data="adm:delete_movie")],
            [InlineKeyboardButton(text="📺 Seriallar katalogi", callback_data="adm:series_list:0")],
            [InlineKeyboardButton(text="📢 Majburiy kanallar", callback_data="adm:channels")],
            [InlineKeyboardButton(text="👤 Adminlar", callback_data="adm:admins")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="adm:stats")],
            [InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="adm:broadcast")],
        ]
    )


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel")]]
    )


def category_choice_kb(prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=label, callback_data=f"{prefix}:{key}")] for key, label in CATEGORIES.items()]
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def channels_menu_kb(channels) -> InlineKeyboardMarkup:
    rows = []
    for _id, chat_id, title, username, invite_link, chat_type in channels:
        rows.append([InlineKeyboardButton(text=f"🗑 {title}", callback_data=f"adm:rmchannel:{chat_id}")])
    rows.append([InlineKeyboardButton(text="➕ Kanal/Guruh qo'shish", callback_data="adm:add_channel")])
    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admins_menu_kb(admins, main_admin_id) -> InlineKeyboardMarkup:
    rows = []
    for user_id, added_by, added_at in admins:
        if user_id == main_admin_id:
            rows.append([InlineKeyboardButton(text=f"👑 {user_id} (bosh admin)", callback_data="noop")])
        else:
            rows.append([InlineKeyboardButton(text=f"🗑 {user_id}", callback_data=f"adm:rmadmin:{user_id}")])
    rows.append([InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="adm:add_admin")])
    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_field_kb(movie_id: int) -> InlineKeyboardMarkup:
    fields = [
        ("Nomi", "name"), ("Turi", "category"), ("Format", "format"),
        ("Til", "language"), ("Subtitr", "subtitle"), ("Kod", "code"), ("Video fayl", "file_id"),
    ]
    rows = [[InlineKeyboardButton(text=f"✏️ {label}", callback_data=f"adm:editfield:movie:{movie_id}:{field}")] for label, field in fields]
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_episode_field_kb(episode_id: int) -> InlineKeyboardMarkup:
    fields = [
        ("Qism nomi/raqami", "episode_label"), ("Format", "format"), ("Til", "language"),
        ("Subtitr", "subtitle"), ("Kod", "code"), ("Video fayl", "file_id"),
    ]
    rows = [[InlineKeyboardButton(text=f"✏️ {label}", callback_data=f"adm:editfield:episode:{episode_id}:{field}")] for label, field in fields]
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_broadcast_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Yuborish", callback_data="adm:broadcast_confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel"),
        ]]
    )


def series_choice_kb(series_list) -> InlineKeyboardMarkup:
    """Kino qo'shish jarayonida mavjud seriallardan birini tanlash yoki yangisini yaratish."""
    rows = [[InlineKeyboardButton(text=f"📺 {title}", callback_data=f"chooseseries:{sid}")] for sid, title in series_list]
    rows.append([InlineKeyboardButton(text="➕ Yangi serial yaratish", callback_data="newseries")])
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def series_manage_kb(series_list, page, total) -> InlineKeyboardMarkup:
    """Admin panelidagi 'Seriallar katalogi' bo'limi: har bir serial uchun tahrirlash/o'chirish/qism qo'shish."""
    rows = []
    for sid, title in series_list:
        rows.append([
            InlineKeyboardButton(text=f"📺 {title}", callback_data="noop"),
        ])
        rows.append([
            InlineKeyboardButton(text="➕ Qism", callback_data=f"adm:addepisode:{sid}"),
            InlineKeyboardButton(text="✏️ Nomi", callback_data=f"adm:renameseries:{sid}"),
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"adm:delseries:{sid}"),
        ])
    nav_row = []
    from config import MOVIES_PER_PAGE
    offset = page * MOVIES_PER_PAGE
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"adm:series_list:{page-1}"))
    if offset + MOVIES_PER_PAGE < total:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"adm:series_list:{page+1}"))
    if nav_row:
        rows.append(nav_row)
    rows.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_delete_kb(callback_yes: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=callback_yes),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="adm:cancel"),
        ]]
    )
