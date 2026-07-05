# 🎬 Kino Qidiruvchi Telegram Bot (@KINO_UZBEK_BOT)

aiogram 3.x + SQLite (aiosqlite) asosida qurilgan, to'liq funksional kino qidiruvchi bot.

## 📂 Loyiha tuzilishi

```
kino_bot/
├── main.py                  # Ishga tushirish nuqtasi
├── config.py                # Token, admin ID va sozlamalar
├── requirements.txt
├── database/
│   └── db.py                 # SQLite bilan ishlash (foydalanuvchilar, kinolar, kanallar, adminlar)
├── handlers/
│   ├── user.py               # /start, menyu, kod orqali qidiruv
│   ├── admin.py               # Admin panel: kino qo'shish/tahrirlash/o'chirish, kanallar, adminlar, statistika, xabar yuborish
│   └── inline.py              # "Tez qidirish" (inline mode)
├── keyboards/                # Inline/reply tugmalar
├── states/                   # FSM holatlar (admin qadamlari uchun)
├── middlewares/
│   ├── subscription.py        # Majburiy obuna tekshiruvi
│   └── throttling.py          # Spam/flooddan himoya
└── utils/
    ├── subscription.py        # Kanalga obuna tekshirish funksiyalari
    └── filters.py              # IsAdmin filter
```

## ⚙️ O'rnatish

```bash
pip install -r requirements.txt
python main.py
```

Bot tokeni va admin ID `config.py` ichida allaqachon kiritilgan:
- Token: sizning bot tokeningiz
- Bosh admin ID: `7861165622`
- Bot username: `@KINO_UZBEK_BOT`

Xohlasangiz, bularni Render/Pterodactyl kabi hostingda **Environment Variables** orqali ham berishingiz mumkin: `BOT_TOKEN`, `MAIN_ADMIN_ID`, `BOT_USERNAME`, `DB_PATH`, `PORT`.

Ma'lumotlar bazasi avtomatik ravishda `kino_bot.db` nomli SQLite faylida saqlanadi (bitta fayl, hech qanday tashqi baza server kerak emas).

## 🚀 Render.com'ga joylash

1. Loyihani GitHub'ga yuklang
2. Render'da **Web Service** yarating (Background Worker emas — health-check porti kerak, `main.py` buni o'zi ochadi)
3. Build command: `pip install -r requirements.txt`
4. Start command: `python main.py`
5. Kerak bo'lsa Environment Variables qo'shing (`BOT_TOKEN` va h.k.)

⚠️ Diqqat: Render'ning bepul tarifida disk vaqtinchalik bo'lgani uchun konteyner qayta ishga tushganda `kino_bot.db` fayli o'chib ketishi mumkin. Doimiy saqlash uchun Render'ning **Persistent Disk** (pullik) xizmatidan foydalaning yoki Pterodactyl/VPS kabi doimiy diskli hostingni tanlang.

## 🧭 Botning ishlash mantig'i

### Foydalanuvchi tomoni
1. `/start` bosilganda avval majburiy kanallarga obunalik tekshiriladi
2. Obuna bo'lmagan bo'lsa — kanallar ro'yxati va "✅ Obuna bo'ldim" tugmasi chiqadi
3. Obuna bo'lgandan keyin xush kelibsiz xabari va 3 ta qidiruv usuli taqdim etiladi:
   - **🎯 Tez qidirish** — inline tugma orqali, yozish maydonida kino nomi bo'yicha jonli qidiruv (inline mode)
   - **🔢 Kod orqali** — kodni yuborish (endi 3 xona bilan cheklanmaydi, 1-10 xonali istalgan raqamli kod bo'lishi mumkin)
   - **📂 Menyu**:
     - **Kino / Multfilm**: nomlar 1-10 tartibida matn ko'rinishida ko'rsatiladi, tagida shu raqamlar bo'yicha inline tugmalar chiqadi — raqamni bosish o'sha kinoni yuboradi. 10 tadan sahifalab "Keyingi/Oldingi" bilan varaqlanadi.
     - **Serial**: avval seriallar KATALOGI xuddi shu 1-10 raqamli ro'yxat ko'rinishida chiqadi. Serial tanlangach, uning QISMLARI xuddi shunday (1-10 raqamli ro'yxat) ko'rsatiladi — qism raqamini tanlash o'sha videoni yuboradi.

Har bir kino/qism yuborilganda: nomi (yoki serial nomi + qism), turi, formati, tili, subtitri, kodi va yuklab olingan soni ko'rsatiladi.

### Admin tomoni (`/admin`)
- ➕ **Kino/Serial qo'shish**:
  - Kino/Multfilm: nom → video → format → til → subtitr → kod so'raladi.
  - Serial: avval mavjud seriallar katalogidan biri tanlanadi YOKI "➕ Yangi serial yaratish" bilan yangisi ochiladi, so'ng shu serial uchun **qism nomi/raqami** (masalan "1-fasl 3-qism"), video, format, til, subtitr, kod so'raladi — bitta serialga istalgancha qism qo'shish mumkin.
- ✏️ **Tahrirlash (kod orqali)** — kod yuborilganda, agar bu alohida kino bo'lsa oddiy maydonlar, serial qismi bo'lsa qism nomi/format/til/subtitr/kod/video kabi tegishli maydonlar chiqadi.
- 🗑 **O'chirish (kod orqali)** — kino yoki alohida serial qismini kod orqali topib, tasdiqlash bilan o'chirish.
- 📺 **Seriallar katalogi** — barcha seriallar ro'yxati, har biri uchun: ➕ Qism qo'shish (tezkor), ✏️ Nomini tahrirlash, 🗑 Butun serialni (barcha qismlari bilan) o'chirish.
- 📢 Majburiy kanallar — forward yoki username orqali qo'shish (bot o'sha joyda admin bo'lishi shart), ochiq/yopiq kanal va guruhlar qo'llab-quvvatlanadi, o'chirish ham mumkin
- 👤 Adminlar — ID orqali admin qo'shish/o'chirish (bosh adminni o'chirib bo'lmaydi)
- 📊 Statistika — umumiy foydalanuvchilar, bugungi faollar, bugungi yangilar, kino/multfilm soni, seriallar soni, jami qismlar soni
- 📣 Xabar yuborish — barcha foydalanuvchilarga istalgan turdagi xabar (matn/rasm/video), yakunida nechta odamga yetganligi haqida hisobot
- Yangi kino yoki serial qismi qo'shilganda barcha foydalanuvchilarga avtomatik xabar boradi

## 💡 Qo'shilgan qo'shimcha professional funksiyalar
- Anti-flood (spamdan himoya) middleware
- Bloklangan foydalanuvchilarni avtomatik aniqlash va statistikadan chetlashtirish
- Xato bo'lgan holatlarda ham bot to'xtamasligi uchun keng qamrovli try/except
- Deep-link orqali kinoni to'g'ridan-to'g'ri ochish imkoniyati (`t.me/KINO_UZBEK_BOT?start=film_047`)
- Health-check server (Render kabi hostinglar uchun)

## 📝 Eslatma
- Kino/qism kodi **1-10 xonali raqam** bo'lishi va **takrorlanmas** bo'lishi kerak (kino va serial qismlari orasida ham) — bot buni avtomatik tekshiradi
- Kanal qo'shishdan oldin botni albatta o'sha kanal/guruhga **admin** qilib qo'ying
