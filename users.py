# users.py
import sqlite3
import hashlib
import uuid
import http.cookies
from webulits import render

DB_NAME = "users.db"
SESSIONS = {}  # session_id: username

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        # ایجاد جدول کاربران با ستون‌های جدید
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                fullname TEXT,
                email TEXT,
                address TEXT,
                skills TEXT,
                avatar TEXT
            );'''
        )
        conn.commit()

def register_user(username, password):
    """ثبت کاربر جدید. اگر موفق True، اگر قبلاً بود False"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password))
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def validate_login(username, password):
    """بررسی نام کاربری و پسورد"""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT password_hash FROM users WHERE username=?",
            (username,)
        )
        row = cur.fetchone()
        if row and row[0] == hash_password(password):
            return True
        return False

def set_login_session(handler, username):
    """ست کردن سشن (کوکی) برای لاگین"""
    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = username
    handler.send_header('Set-Cookie', f'session_id={session_id}; HttpOnly; Path=/')

def current_user(handler):
    """برگرداندن نام کاربری کاربر فعلی اگر لاگین است، وگرنه None"""
    if "Cookie" in handler.headers:
        cookie = http.cookies.SimpleCookie(handler.headers["Cookie"])
        session_id = cookie.get("session_id")
        if session_id:
            return SESSIONS.get(session_id.value)
    return None

def logout_user(handler):
    """پاک کردن سشن و کوکی"""
    if "Cookie" in handler.headers:
        cookie = http.cookies.SimpleCookie(handler.headers["Cookie"])
        session_id = cookie.get("session_id")
        if session_id and session_id.value in SESSIONS:
            del SESSIONS[session_id.value]
    handler.send_header('Set-Cookie', 'session_id=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/')

def get_register_html(context=None):
    return render("register.html", context or {})

def get_login_html(context=None):
    return render("login.html", context or {})

def get_user_profile(username):
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute(
            '''SELECT username, fullname, email, address, skills, avatar 
               FROM users WHERE username=?''', (username,))
        row = cur.fetchone()
    if row:
        return {
            "username": row[0],
            "fullname": row[1] or '',
            "email": row[2] or '',
            "address": row[3] or '',
            "skills": row[4] or '',
            "avatar": row[5] or ''
        }
    return None

def update_profile(username, profile):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('''UPDATE users SET
            fullname=?,
            email=?,
            address=?,
            skills=?,
            avatar=?
            WHERE username=?''',
            (
                profile.get("fullname"),
                profile.get("email"),
                profile.get("address"),
                profile.get("skills"),
                profile.get("avatar"),
                username,
            )
        )
        conn.commit()
