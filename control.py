from http.server import HTTPServer, BaseHTTPRequestHandler
from webulits import render, serve_static
from users import (
    register_user, validate_login, set_login_session, current_user,
    logout_user, get_register_html, get_login_html, init_db,
    get_user_profile, update_profile
)
from explore import (
    get_explore_html, get_user_html, save_resume, 
    user_has_resume, get_resume_download_link
)
import urllib.parse
import os

admin = ["myhello"]
init_db()

class Myhandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/static/"):
            # نمایش فایل‌های استاتیک مثل عکس، pdf، css
            serve_static(self, self.path)
            return

        user = current_user(self)

        # صفحه اصلی
        if self.path == "/":
            is_admin = user in admin if user else False
            context = {
                "title": "صفحه اصلی",
                "page_url": self.path,
                "user": user,
                "admin": is_admin
            }
            html = render("index.html", context)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return
        elif self.path =="/dashboard":
            context={
                "title":"داشبورد",
                "page_url":self.path,
                "user":user
            }
            html = render("dashboard.html",context)
            self.send_response(200)
            self.send_header("Content-type","text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8",))
            return

        # نمایش همه کاربران
        elif self.path == "/panel/explore_user":
            html = get_explore_html({"user": user})
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # نمایش پروفایل یک کاربر خاص
        elif self.path.startswith("/user/"):
            username = self.path.split("/user/")[1].strip()
            html = get_user_html(username, {
                "user": user,
                "has_resume": user_has_resume(username),
                "resume_link": get_resume_download_link(username)
            })
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # فرم آپلود رزومه برای کاربر فعلی
        elif self.path == "/panel/resume":
            if not user:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            html = render("resume_upload.html", {
                "title": "آپلود رزومه",
                "user": user,
                "success": False,
                "resume_link": get_resume_download_link(user) if user_has_resume(user) else ""
            })
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # فرم ثبت‌نام
        elif self.path == "/register":
            html = get_register_html()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # فرم لاگین
        elif self.path == "/login":
            html = get_login_html()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # خروج از حساب
        elif self.path == "/logout":
            self.send_response(302)
            logout_user(self)
            self.send_header('Location', '/')
            self.end_headers()
            return

        # نمایش پنل پروفایل
        elif self.path == "/panel/profile":
            if not user:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            profile = get_user_profile(user)
            context = {
                "title": "پروفایل من",
                "page_url": self.path,
                "user": user,
                "profile": profile,
                "profile_username": profile["username"],
                "profile_fullname": profile["fullname"],
                "profile_email": profile["email"],
                "profile_address": profile["address"],
                "profile_skills": profile["skills"],
                "profile_avatar": profile["avatar"],
                "resume_link": get_resume_download_link(user) if user_has_resume(user) else "",
            }
            html = render("profile.html", context)
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # فرم ویرایش پروفایل
        elif self.path == "/panel/profile_edit":
            if not user:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            profile = get_user_profile(user)
            html = render("edit_profile.html", {
                "title": "ویرایش پروفایل",
                "page_url": self.path,
                "user": user,
                "profile": profile
            })
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        self.send_error(404)

    def do_POST(self):
        # ثبت‌نام کاربر
        if self.path == "/register":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = urllib.parse.parse_qs(body)
            username = data.get("username", [""])[0]
            password = data.get("password", [""])[0]

            msg = ""
            if not username or not password:
                msg = "همه فیلدها اجباری است."
            elif register_user(username, password):
                msg = "ثبت نام موفق بود. حالا وارد شوید."
            else:
                msg = "این نام کاربری قبلاً ثبت شده!"

            html = get_register_html({"msg": msg})
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # ورود کاربر
        elif self.path == "/login":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = urllib.parse.parse_qs(body)
            username = data.get("username", [""])[0]
            password = data.get("password", [""])[0]

            if validate_login(username, password):
                self.send_response(302)
                set_login_session(self, username)
                self.send_header("Location", "/")
                self.end_headers()
            else:
                msg = "نام کاربری یا رمز نادرست است."
                html = get_login_html({"msg": msg})
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            return

        # ویرایش پروفایل کاربر
        elif self.path == "/panel/profile_edit":
            user = current_user(self)
            if not user:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode()
            data = urllib.parse.parse_qs(body)
            profile = {
                "fullname": data.get("fullname", [""])[0],
                "email": data.get("email", [""])[0],
                "address": data.get("address", [""])[0],
                "skills": data.get("skills", [""])[0],
                "avatar": data.get("avatar", [""])[0],
            }
            update_profile(user, profile)
            self.send_response(302)
            self.send_header("Location", "/panel")
            self.end_headers()
            return

        # آپلود رزومه (PDF) توسط کاربر
        elif self.path == "/panel/resume":
            user = current_user(self)
            if not user:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            # دریافت multipart form data
            content_type = self.headers.get('Content-type', '')
            if not content_type.startswith('multipart/form-data'):
                self.send_response(400)
                self.end_headers()
                self.wfile.write("فرمت ارسال اشتباه است.".encode("utf-8"))
                return

            boundary = content_type.split("boundary=")[-1]
            remainbytes = int(self.headers['content-length'])
            line = self.rfile.readline()
            remainbytes -= len(line)
            if not boundary.encode() in line:
                self.send_response(400)
                self.end_headers()
                self.wfile.write("فرمت مرزی اشتباه است.".encode("utf-8"))
                return

            # خواندن نام فایل
            line = self.rfile.readline()
            remainbytes -= len(line)
            fn = ''
            if b'filename="' in line:
                fn = line.decode().split('filename="')[1].split('"')[0]
            # رد شدن از هدر Content-Type
            while True:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if line in (b'\r\n', b'\n'):
                    break

            # خواندن داده فایل
            file_data = b''
            prev_line = b''
            while remainbytes > 0:
                line = self.rfile.readline()
                remainbytes -= len(line)
                if boundary.encode() in line:
                    file_data = file_data[:-2]
                    break
                file_data += prev_line
                prev_line = line
            if prev_line:
                file_data += prev_line

            if not fn.lower().endswith('.pdf'):
                html = render("resume_upload.html", {
                    "user": user, "success": False,
                    "error": "فقط فایل PDF مجاز است."
                })
            else:
                save_resume(user, file_data)
                html = render("resume_upload.html", {
                    "user": user, "success": True,
                    "resume_link": get_resume_download_link(user)
                })
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # اگر به اینجا رسید، مسیر POST ناشناخته است
        self.send_error(404)

if __name__ == "__main__":
    port = 90
    server_address = ('', port)
    print(f"localhost Runed in port:http://localhost:{port}")
    httpd = HTTPServer(server_address, Myhandler)
    httpd.serve_forever()
