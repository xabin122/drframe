# explore.py
import os
import sqlite3
from users import DB_NAME, get_user_profile
from webulits import render

def list_users():
    """بازگرداندن لیست کاربران همراه با اطلاعات ضروری برای اکسپلور"""
    with sqlite3.connect(DB_NAME) as conn:
        cur = conn.cursor()
        cur.execute("SELECT username, fullname, skills, avatar FROM users")
        rows = cur.fetchall()
    users = []
    for row in rows:
        users.append({
            "username": row[0],
            "fullname": row[1] or row[0],
            "skills": row[2] or '',
            "avatar": row[3] or '/static/avatar.png',
        })
    return users

def get_explore_html(context=None):
    """صفحه اکسپلور کاربران"""
    users = list_users()
    return render("explore_users.html", {"users": users, **(context or {})})

def get_user_html(username, context=None):
    """نمایش کامل پروفایل یک کاربر"""
    profile = get_user_profile(username)
    if not profile:  # کاربر پیدا نشد
        return render("404.html", {"title": "کاربر پیدا نشد"})
    return render("user_profile.html", {**profile, **(context or {})})

def get_resume_path(username):
    return f"resumes/{username}.pdf"  # فقط PDF. اگر می‌خواهی دیگر فرمت‌ها باشد گسترش بده

def user_has_resume(username):
    return os.path.isfile(get_resume_path(username))

def save_resume(username, file_content):
    os.makedirs("resumes", exist_ok=True)
    with open(get_resume_path(username), "wb") as f:
        f.write(file_content)
    return True

def get_resume_download_link(username):
    if user_has_resume(username):
        return f"/static/resumes/{username}.pdf"
    return ""

