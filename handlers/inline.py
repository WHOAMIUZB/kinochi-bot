from aiogram import Router, Bot
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, ChosenInlineResult

from config import CATEGORIES, INLINE_RESULT_LIMIT
from database import db
from utils.subscription import get_unsubscribed_channels
from handlers.user import send_by_found

router = Router(name="inline")

THUMB_URL = "https://cdn-icons-png.flaticon.com/512/2965/2965358.png"


@router.inline_query()
async def inline_search(inline_query: InlineQuery, bot: Bot):
    user_id = inline_query.from_user.id

    if not await db.is_admin(user_id):
        unsubscribed = await get_unsubscribed_channels(bot, user_id)
        if unsubscribed:
            result = InlineQueryResultArticle(
                id="need_sub",
                title="⛔️ Avval kanallarga obuna bo'ling!",
                description="Qidiruvdan foydalanish uchun botga /start bosing va obuna bo'ling.",
                input_message_content=InputTextMessageContent(
                    message_text="⛔️ Qidiruvdan foydalanish uchun avval majburiy kanallarga obuna bo'ling. /start"
                ),
                thumbnail_url=THUMB_URL,
            )
            await inline_query.answer([result], cache_time=1, is_personal=True)
            return

    query_text = inline_query.query.strip()
    if not query_text:
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    found_items = await db.search_all_by_name(query_text, limit=INLINE_RESULT_LIMIT)
    results = []
    for item in found_items:
        label = CATEGORIES.get(item["category"], item["category"])
        results.append(
            InlineQueryResultArticle(
                id=f"{item['kind']}_{item['id']}",
                title=item["name"],
                description=f"{label} | Format: {item['format']} | Kod: {item['code']}",
                input_message_content=InputTextMessageContent(
                    message_text=f"🎬 {item['name']}\n🔑 Kod: {item['code']}\n⏳ Yuklanmoqda..."
                ),
                thumbnail_url=THUMB_URL,
            )
        )

    if not results:
        results.append(
            InlineQueryResultArticle(
                id="not_found",
                title="❌ Hech narsa topilmadi",
                description="Boshqa nom bilan qidirib ko'ring",
                input_message_content=InputTextMessageContent(message_text=f"❌ \"{query_text}\" bo'yicha hech narsa topilmadi."),
                thumbnail_url=THUMB_URL,
            )
        )

    await inline_query.answer(results, cache_time=1, is_personal=True)


@router.chosen_inline_result()
async def chosen_result(chosen: ChosenInlineResult, bot: Bot):
    if "_" not in chosen.result_id:
        return
    kind, raw_id = chosen.result_id.split("_", 1)
    if kind not in ("movie", "episode") or not raw_id.isdigit():
        return
    found = {"kind": kind, "id": int(raw_id)}
    try:
        await send_by_found(bot, chosen.from_user.id, found)
    except Exception:
        pass
