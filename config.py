import os

# ==================== ASOSIY SOZLAMALAR ====================

# Bot tokeni (Render.com'da Environment Variable sifatida BOT_TOKEN qo'yish tavsiya etiladi)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8879911814:AAHP5i81akaGmZfQmM2OA9yVJkobosZ3E_I")

# Bot username (@ belgisiz)
BOT_USERNAME = os.getenv("BOT_USERNAME", "KINO_UZBEK_BOT")

# Bosh admin (bot birinchi marta ishga tushganda avtomatik admin sifatida qo'shiladi)
MAIN_ADMIN_ID = int(os.getenv("MAIN_ADMIN_ID", "7861165622"))

# SQLite baza fayli manzili
DB_PATH = os.getenv("DB_PATH", "kino_bot.db")

# Har bir sahifada nechta kino ko'rsatilishi (menyu orqali qidiruv)
MOVIES_PER_PAGE = 10

# Kino/qism kodi - faqat raqamlardan iborat, uzunligi cheklanmagan (ko'p kino/serial joylash uchun)
CODE_MIN_LEN = 1
CODE_MAX_LEN = 12

# Inline qidiruvda ko'rsatiladigan natijalar soni
INLINE_RESULT_LIMIT = 20

# Kino turlari
CATEGORIES = {
    "movie": "🎬 Kino",
    "series": "📺 Serial",
    "cartoon": "🧸 Multfilm",
}

# Health-check server porti (Render.com uchun)
PORT = int(os.getenv("PORT", "8080"))
