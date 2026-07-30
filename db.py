import os
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    spot_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
    finally:
        conn.close()


def create_user(username, password):
    password_hash = generate_password_hash(password)
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            return cur.lastrowid
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()


def verify_login(username, password):
    user = get_user_by_username(username)
    if user is None:
        return None
    if check_password_hash(user["password_hash"], password):
        return user
    return None


def log_progress(user_id, spot_id, status):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO progress (user_id, spot_id, status, updated_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (user_id, spot_id, status),
            )
    finally:
        conn.close()


def get_progress_for_user(user_id):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM progress WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
