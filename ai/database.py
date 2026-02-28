import sqlite3
from datetime import datetime

DB_NAME = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            messages_count INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_message TEXT,
            bot_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_queries (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            city TEXT,
            temperature REAL,
            wind_speed REAL,
            query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    conn.commit()
    conn.close()


def save_user(name, username=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM users WHERE name = ?", (name,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE users 
            SET last_seen = CURRENT_TIMESTAMP, messages_count = messages_count + 1 
            WHERE user_id = ?
        """, (existing[0],))
        user_id = existing[0]
    else:
        cursor.execute("""
            INSERT INTO users (name, username, messages_count) 
            VALUES (?, ?, 1)
        """, (name, username))
        user_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return user_id


def get_user_id_by_name(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE name = ?", (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def log_message_to_db(user_message, bot_response, user_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO chat_log (user_id, user_message, bot_response) 
        VALUES (?, ?, ?)
    """, (user_id, user_message, bot_response))

    conn.commit()
    conn.close()


def log_weather_query(user_id, city, temperature, wind_speed):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO weather_queries (user_id, city, temperature, wind_speed) 
        VALUES (?, ?, ?, ?)
    """, (user_id, city, temperature, wind_speed))

    conn.commit()
    conn.close()


def get_user_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, first_seen, last_seen, messages_count 
        FROM users WHERE user_id = ?
    """, (user_id,))
    user_info = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) FROM weather_queries WHERE user_id = ?
    """, (user_id,))
    weather_count = cursor.fetchone()[0]

    conn.close()

    if user_info:
        return {
            "name": user_info[0],
            "first_seen": user_info[1],
            "last_seen": user_info[2],
            "messages_count": user_info[3],
            "weather_queries": weather_count
        }
    return None