import aiosqlite
import datetime
from config import DB_PATH, MAIN_ADMIN_ID

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    joined_at   TEXT,
    last_active TEXT,
    is_blocked  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS admins (
    user_id   INTEGER PRIMARY KEY,
    added_by  INTEGER,
    added_at  TEXT
);

CREATE TABLE IF NOT EXISTS channels (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id      INTEGER UNIQUE,
    title        TEXT,
    username     TEXT,
    invite_link  TEXT,
    chat_type    TEXT,
    added_at     TEXT
);

-- Alohida kino/multfilm (seriyasiz)
CREATE TABLE IF NOT EXISTS movies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT UNIQUE,
    name        TEXT,
    category    TEXT,
    format      TEXT,
    language    TEXT,
    subtitle    TEXT,
    file_id     TEXT,
    downloads   INTEGER DEFAULT 0,
    created_at  TEXT
);

-- Seriallar katalogi (nomi bo'yicha papka)
CREATE TABLE IF NOT EXISTS series (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT,
    created_at  TEXT
);

-- Har bir serialning qismlari
CREATE TABLE IF NOT EXISTS episodes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id     INTEGER,
    episode_label TEXT,
    code          TEXT UNIQUE,
    format        TEXT,
    language      TEXT,
    subtitle      TEXT,
    file_id       TEXT,
    downloads     INTEGER DEFAULT 0,
    created_at    TEXT,
    FOREIGN KEY (series_id) REFERENCES series (id)
);

CREATE TABLE IF NOT EXISTS broadcasts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sent_by     INTEGER,
    total_sent  INTEGER,
    total_fail  INTEGER,
    sent_at     TEXT
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, added_by, added_at) VALUES (?, ?, ?)",
            (MAIN_ADMIN_ID, MAIN_ADMIN_ID, datetime.datetime.utcnow().isoformat()),
        )
        await db.commit()


def _now():
    return datetime.datetime.utcnow().isoformat()


# ==================== USERS ====================

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        now = _now()
        if row:
            await db.execute(
                "UPDATE users SET last_active=?, username=?, full_name=? WHERE user_id=?",
                (now, username, full_name, user_id),
            )
        else:
            await db.execute(
                "INSERT INTO users (user_id, username, full_name, joined_at, last_active) VALUES (?,?,?,?,?)",
                (user_id, username, full_name, now, now),
            )
        await db.commit()
        return row is None


async def touch_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET last_active=? WHERE user_id=?", (_now(), user_id))
        await db.commit()


async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM users WHERE is_blocked=0")
        rows = await cur.fetchall()
        return [r[0] for r in rows]


async def mark_blocked(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_blocked=1 WHERE user_id=?", (user_id,))
        await db.commit()


async def total_users_count():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        return (await cur.fetchone())[0]


async def active_users_count(since_date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE last_active >= ?", (since_date,))
        return (await cur.fetchone())[0]


async def new_users_count(since_date: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (since_date,))
        return (await cur.fetchone())[0]


# ==================== ADMINS ====================

async def is_admin(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,))
        return (await cur.fetchone()) is not None


async def add_admin(user_id: int, added_by: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins (user_id, added_by, added_at) VALUES (?,?,?)",
            (user_id, added_by, _now()),
        )
        await db.commit()


async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
        await db.commit()


async def list_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id, added_by, added_at FROM admins")
        return await cur.fetchall()


# ==================== CHANNELS ====================

async def add_channel(chat_id: int, title: str, username: str, invite_link: str, chat_type: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO channels (chat_id, title, username, invite_link, chat_type, added_at) "
            "VALUES (?,?,?,?,?,?)",
            (chat_id, title, username, invite_link, chat_type, _now()),
        )
        await db.commit()


async def remove_channel(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channels WHERE chat_id=?", (chat_id,))
        await db.commit()


async def get_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, chat_id, title, username, invite_link, chat_type FROM channels")
        return await cur.fetchall()


# ==================== CODE (movies + episodes umumiy) ====================

async def code_exists(code: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id FROM movies WHERE code=?", (code,))
        if await cur.fetchone():
            return True
        cur = await db.execute("SELECT id FROM episodes WHERE code=?", (code,))
        return (await cur.fetchone()) is not None


async def find_by_code(code: str):
    """Kod bo'yicha kino yoki serial qismini qidiradi. Natija: dict yoki None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id,code,name,category,format,language,subtitle,file_id,downloads FROM movies WHERE code=?",
            (code,),
        )
        row = await cur.fetchone()
        if row:
            return {
                "kind": "movie",
                "id": row[0], "code": row[1], "name": row[2], "category": row[3],
                "format": row[4], "language": row[5], "subtitle": row[6],
                "file_id": row[7], "downloads": row[8],
            }
        cur = await db.execute(
            "SELECT e.id, e.code, e.episode_label, e.format, e.language, e.subtitle, e.file_id, e.downloads, "
            "s.id, s.title "
            "FROM episodes e JOIN series s ON e.series_id = s.id WHERE e.code=?",
            (code,),
        )
        row = await cur.fetchone()
        if row:
            return {
                "kind": "episode",
                "id": row[0], "code": row[1], "episode_label": row[2], "format": row[3],
                "language": row[4], "subtitle": row[5], "file_id": row[6], "downloads": row[7],
                "series_id": row[8], "series_title": row[9],
            }
        return None


# ==================== MOVIES (kino/multfilm) ====================

async def add_movie(code, name, category, fmt, language, subtitle, file_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO movies (code,name,category,format,language,subtitle,file_id,downloads,created_at) "
            "VALUES (?,?,?,?,?,?,?,0,?)",
            (code, name, category, fmt, language, subtitle, file_id, _now()),
        )
        await db.commit()


async def get_movie_by_id(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id,code,name,category,format,language,subtitle,file_id,downloads FROM movies WHERE id=?",
            (movie_id,),
        )
        return await cur.fetchone()


async def search_movies_by_name(query: str, limit: int = 20):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id,code,name,category,format,downloads FROM movies WHERE name LIKE ? ORDER BY name LIMIT ?",
            (f"%{query}%", limit),
        )
        return await cur.fetchall()


async def get_movies_by_category(category: str, offset: int, limit: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id,code,name FROM movies WHERE category=? ORDER BY name LIMIT ? OFFSET ?",
            (category, limit, offset),
        )
        return await cur.fetchall()


async def count_movies_by_category(category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM movies WHERE category=?", (category,))
        return (await cur.fetchone())[0]


async def increment_movie_downloads(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE movies SET downloads = downloads + 1 WHERE id=?", (movie_id,))
        await db.commit()


async def update_movie_field(movie_id: int, field: str, value):
    allowed = {"name", "category", "format", "language", "subtitle", "code", "file_id"}
    if field not in allowed:
        raise ValueError("Noto'g'ri maydon")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE movies SET {field}=? WHERE id=?", (value, movie_id))
        await db.commit()


async def delete_movie(movie_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM movies WHERE id=?", (movie_id,))
        await db.commit()


async def total_movies_count():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM movies")
        return (await cur.fetchone())[0]


# ==================== SERIES (serial katalogi) ====================

async def add_series(title: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO series (title, created_at) VALUES (?, ?)", (title, _now())
        )
        await db.commit()
        return cur.lastrowid


async def get_all_series(offset: int = 0, limit: int = 1000):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, title FROM series ORDER BY title LIMIT ? OFFSET ?", (limit, offset)
        )
        return await cur.fetchall()


async def count_series():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM series")
        return (await cur.fetchone())[0]


async def get_series_by_id(series_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, title FROM series WHERE id=?", (series_id,))
        return await cur.fetchone()


async def update_series_title(series_id: int, title: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE series SET title=? WHERE id=?", (title, series_id))
        await db.commit()


async def delete_series(series_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM episodes WHERE series_id=?", (series_id,))
        await db.execute("DELETE FROM series WHERE id=?", (series_id,))
        await db.commit()


# ==================== EPISODES (serial qismlari) ====================

async def add_episode(series_id, episode_label, fmt, language, subtitle, code, file_id) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO episodes (series_id, episode_label, code, format, language, subtitle, file_id, "
            "downloads, created_at) VALUES (?,?,?,?,?,?,?,0,?)",
            (series_id, episode_label, code, fmt, language, subtitle, file_id, _now()),
        )
        await db.commit()
        return cur.lastrowid


async def get_episodes_by_series(series_id: int, offset: int, limit: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id, code, episode_label FROM episodes WHERE series_id=? "
            "ORDER BY id LIMIT ? OFFSET ?",
            (series_id, limit, offset),
        )
        return await cur.fetchall()


async def count_episodes_by_series(series_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM episodes WHERE series_id=?", (series_id,))
        return (await cur.fetchone())[0]


async def get_episode_by_id(episode_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT e.id, e.code, e.episode_label, e.format, e.language, e.subtitle, e.file_id, e.downloads, "
            "s.id, s.title FROM episodes e JOIN series s ON e.series_id=s.id WHERE e.id=?",
            (episode_id,),
        )
        return await cur.fetchone()


async def update_episode_field(episode_id: int, field: str, value):
    allowed = {"episode_label", "format", "language", "subtitle", "code", "file_id"}
    if field not in allowed:
        raise ValueError("Noto'g'ri maydon")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE episodes SET {field}=? WHERE id=?", (value, episode_id))
        await db.commit()


async def delete_episode(episode_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM episodes WHERE id=?", (episode_id,))
        await db.commit()


async def increment_episode_downloads(episode_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE episodes SET downloads = downloads + 1 WHERE id=?", (episode_id,))
        await db.commit()


async def total_episodes_count():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM episodes")
        return (await cur.fetchone())[0]


# ==================== SEARCH (inline uchun, kino + serial qismlari) ====================

async def search_all_by_name(query: str, limit: int = 20):
    """Inline qidiruv uchun: kino/multfilm nomlari va serial(+qism) nomlari bo'yicha qidiradi."""
    results = []
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id,code,name,category,format,downloads FROM movies WHERE name LIKE ? ORDER BY name LIMIT ?",
            (f"%{query}%", limit),
        )
        for r in await cur.fetchall():
            results.append({
                "kind": "movie", "id": r[0], "code": r[1], "name": r[2],
                "category": r[3], "format": r[4], "downloads": r[5],
            })

        remaining = max(limit - len(results), 0)
        if remaining:
            cur = await db.execute(
                "SELECT e.id, e.code, e.episode_label, e.format, e.downloads, s.title "
                "FROM episodes e JOIN series s ON e.series_id = s.id "
                "WHERE s.title LIKE ? OR e.episode_label LIKE ? ORDER BY s.title LIMIT ?",
                (f"%{query}%", f"%{query}%", remaining),
            )
            for r in await cur.fetchall():
                results.append({
                    "kind": "episode", "id": r[0], "code": r[1],
                    "name": f"{r[5]} — {r[2]}", "category": "series",
                    "format": r[3], "downloads": r[4],
                })
    return results


# ==================== BROADCASTS LOG ====================

async def log_broadcast(sent_by: int, total_sent: int, total_fail: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO broadcasts (sent_by, total_sent, total_fail, sent_at) VALUES (?,?,?,?)",
            (sent_by, total_sent, total_fail, _now()),
        )
        await db.commit()
