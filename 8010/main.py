import os
import io
import time
import random
import sqlite3
import threading
import zipfile

import pyotp
import pyzipper
from PIL import Image
from flask import (
    Flask, request, render_template_string, send_file,
    session, redirect, make_response, url_for
)

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# ==================== Flag ====================
if os.path.exists("flag.txt"):
    FLAG = open("flag.txt").read().strip()
else:
    FLAG = "ctfhub{" + "".join(random.choices("0123456789ABCDEF", k=20)) + "}"
    with open("flag.txt", "w") as f:
        f.write(FLAG)

# ==================== TOTP ====================
TOTP_SECRET = pyotp.random_base32()

# ==================== ZIP 密码（= bot cookie 值）====================
ZIP_PASSWORD = "".join(random.choices(
    "abcdefghijklmnopqrstuvwxyz0123456789", k=24))
BOT_COOKIE_NAME = "zip_pass"

# ==================== 零宽字符隐写 ====================
ZW = {"0": "\u200B", "1": "\u200C"}


def zw_encode(text: str) -> str:
    bits = "".join(format(ord(c), "08b") for c in text)
    return "".join(ZW[b] for b in bits)


def zw_decode(text: str) -> str:
    bits = "".join(
        "0" if c == "\u200B" else "1" for c in text if c in ZW.values())
    out = []
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits):
            out.append(chr(int(bits[i:i + 8], 2)))
    return "".join(out)


HIDDEN = zw_encode(TOTP_SECRET)

# ==================== 数据库 ====================
DB_PATH = "users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT,
            content TEXT,
            created_at TEXT
        )
    """)
    c.execute("DELETE FROM users")
    c.execute("DELETE FROM comments")

    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              ("guest", "guest123"))
    admin_password = "".join(random.choices(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              ("admin", admin_password))
    conn.commit()
    conn.close()

    global ADMIN_PASSWORD
    ADMIN_PASSWORD = admin_password

    print("=" * 60)
    print(f"[*] Admin password : {admin_password}")
    print(f"[*] TOTP secret    : {TOTP_SECRET}")
    print(
        f"[*] ZIP password   : {ZIP_PASSWORD}  (bot cookie: {BOT_COOKIE_NAME})")
    print(f"[*] Flag           : {FLAG}")
    print("=" * 60)


init_db()

# ==================== 首页博客 ====================
BLOG_HTML = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>My Blog</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Georgia', serif; background: #fafafa; color: #222; line-height: 1.8; }}
    .navbar {{
        background: #2c3e50; padding: 18px 40px; display: flex;
        justify-content: space-between; align-items: center;
        position: sticky; top: 0; z-index: 100;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    }}
    .navbar .logo {{ color: #ecf0f1; font-size: 22px; font-weight: bold; letter-spacing: 1px; }}
    .navbar .logo span {{ color: #e74c3c; }}
    .navbar a {{ color: #ecf0f1; margin-left: 18px; text-decoration: none; }}
    .navbar .login-btn {{
        background: #e74c3c; color: #fff; border: none; padding: 10px 28px;
        font-size: 14px; border-radius: 25px; cursor: pointer; transition: 0.3s;
        text-decoration: none; font-weight: bold;
    }}
    .navbar .login-btn:hover {{ background: #c0392b; transform: scale(1.05); }}
    .container {{ max-width: 780px; margin: 50px auto; padding: 0 20px; }}
    .post {{
        background: #fff; padding: 45px 55px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    }}
    .post h1 {{
        font-size: 30px; color: #2c3e50; border-bottom: 2px solid #ecf0f1;
        padding-bottom: 12px; margin-bottom: 8px;
    }}
    .post .meta {{ color: #b0b0b0; font-size: 13px; margin-bottom: 25px; }}
    .post .meta span {{ margin-right: 18px; }}
    .post p {{ margin-bottom: 18px; font-size: 16.5px; color: #333; }}
    .post .footer-note {{
        margin-top: 30px; padding-top: 18px; border-top: 1px solid #eee;
        font-size: 13px; color: #bbb; text-align: center;
    }}
</style>
</head>
<body>
<nav class="navbar">
    <div class="logo">📖 My<span>Blog</span></div>
    <div>
        <a href="/comments">💬 Comments</a>
        <a href="/login" class="login-btn">🔑 Login</a>
    </div>
</nav>
<div class="container">
    <div class="post">
        <h1>My Trip to the Countryside</h1>
        <div class="meta">
            <span>📅 August 23, 2026</span>
            <span>✍️ Admin</span>
            <span>👁️ 124 reads</span>
            <span>💬 12 comments</span>
        </div>
        <p>Last weekend, I finally took a break from work and went to the countryside.</p>
        <p>The weather was perfect — not too hot, not too cold. I stayed at a small cottage near a lake.</p>
        <p>I spent most of my time walking along the lake, reading, and just watching the sunset.</p>
        <p>On the second day, I met a local farmer who showed me around his farm.</p>
        <p>I also visited a small village nearby. The people there were incredibly kind.</p>
        <p>By the end of the trip, I felt completely recharged.</p>
        <p style="margin-top:30px;font-style:italic;color:#888;">— Sometimes, the best things in life are the simplest.</p>
        <div class="footer-note">
            💡 If you're reading this, you probably have too much time on your hands.
        </div>
        <!-- {HIDDEN}Don't cost too time of this.-->
    </div>
</div>
</body>
</html>
"""

# ==================== 登录 / 密码 / TOTP ====================
LOGIN_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Login</title>
<style>
body{font-family:monospace;min-height:100vh;display:flex;justify-content:center;align-items:center;background:#0a0a0a;color:#0f0;}
.container{background:#111;padding:50px 60px;border-radius:12px;border:1px solid #0f0;text-align:center;max-width:420px;width:100%;}
h2{font-size:22px;margin-bottom:10px;} .sub{color:#888;font-size:13px;margin-bottom:25px;}
input{width:100%;padding:12px;background:#1a1a1a;border:1px solid #0f0;color:#0f0;font-size:16px;border-radius:6px;outline:none;font-family:monospace;}
button{width:100%;padding:12px;margin-top:15px;background:#0f0;color:#000;border:none;font-size:16px;font-weight:bold;border-radius:6px;cursor:pointer;}
button:hover{background:#0c0;} .error{color:#f44;margin-top:12px;font-size:14px;}
a{color:#0f0;}
</style></head><body>
<div class="container">
<h2>🔐 Authentication</h2>
<p class="sub">Enter your username</p>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
<input type="text" name="username" placeholder="Username" autofocus>
<button type="submit">Verify</button>
</form>
<p style="margin-top:15px"><a href="/">← Back to blog</a></p>
</div></body></html>
"""

PASSWORD_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Login</title>
<style>
body{font-family:monospace;min-height:100vh;display:flex;justify-content:center;align-items:center;background:#0a0a0a;color:#0f0;}
.container{background:#111;padding:50px 60px;border-radius:12px;border:1px solid #0f0;text-align:center;max-width:420px;width:100%;}
h2{font-size:22px;margin-bottom:10px;} .sub{color:#888;font-size:13px;margin-bottom:25px;}
input{width:100%;padding:12px;background:#1a1a1a;border:1px solid #0f0;color:#0f0;font-size:16px;border-radius:6px;outline:none;font-family:monospace;}
button{width:100%;padding:12px;margin-top:15px;background:#0f0;color:#000;border:none;font-size:16px;font-weight:bold;border-radius:6px;cursor:pointer;}
button:hover{background:#0c0;} .error{color:#f44;margin-top:12px;font-size:14px;}
a{color:#0f0;}
</style></head><body>
<div class="container">
<h2>🔐 Authentication</h2>
<p class="sub">Enter your password</p>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
<input type="password" name="password" placeholder="Password" autofocus>
<button type="submit">Verify</button>
</form>
<p style="margin-top:15px"><a href="/login">← Back</a></p>
</div></body></html>
"""

TOTP_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>TOTP</title>
<style>
body{font-family:monospace;min-height:100vh;display:flex;justify-content:center;align-items:center;background:#0a0a0a;color:#0f0;}
.container{background:#111;padding:50px 60px;border-radius:12px;border:1px solid #0f0;text-align:center;max-width:420px;width:100%;}
h2{font-size:22px;margin-bottom:10px;} .sub{color:#888;font-size:13px;margin-bottom:25px;}
input{width:100%;padding:12px;background:#1a1a1a;border:1px solid #0f0;color:#0f0;font-size:16px;border-radius:6px;outline:none;font-family:monospace;text-align:center;letter-spacing:4px;}
button{width:100%;padding:12px;margin-top:15px;background:#0f0;color:#000;border:none;font-size:16px;font-weight:bold;border-radius:6px;cursor:pointer;}
button:hover{background:#0c0;} .error{color:#f44;margin-top:12px;font-size:14px;}
a{color:#0f0;}
</style></head><body>
<div class="container">
<h2>🔐 Two-Factor</h2>
<p class="sub">Enter the 6-digit code</p>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
<input type="text" name="code" placeholder="123456" maxlength="6" autofocus>
<button type="submit">Verify</button>
</form>
<p style="margin-top:15px"><a href="/password">← Back</a></p>
</div></body></html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Dashboard</title>
<style>
body{font-family:monospace;min-height:100vh;display:flex;justify-content:center;align-items:center;background:#0a0a0a;color:#0f0;}
.container{background:#111;padding:50px 60px;border-radius:12px;border:1px solid #0f0;text-align:center;max-width:560px;width:100%;}
h2{font-size:24px;margin-bottom:10px;} .sub{color:#888;font-size:14px;margin-bottom:25px;}
a.btn{display:inline-block;margin:8px;padding:12px 35px;background:#0f0;color:#000;text-decoration:none;border-radius:6px;font-weight:bold;}
a.btn:hover{background:#0c0;}
.logout{background:#f44;color:#fff;} .logout:hover{background:#c00;}
.hint{color:#fa0;font-size:13px;margin-top:20px;line-height:1.6;}
</style></head><body>
<div class="container">
<h2>✅ Welcome, admin</h2>
<p class="sub">You are logged in as administrator.</p>
<a class="btn" href="/download">📥 Download Avatar (ZIP, AES)</a>
<br><br>
<a class="btn logout" href="/logout">🚪 Logout</a>
<p class="hint">
    ⚠️ The ZIP is AES-encrypted.<br>
    Only the admin bot holds the key cookie <code>zip_pass</code>.<br>
    Maybe the <a href="/comments" style="color:#0f0">💬 comment section</a> can help you get it.
</p>
</div></body></html>
"""

# ==================== 路由 ====================


@app.route("/")
def index():
    return render_template_string(BLOG_HTML)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"SELECT password FROM users WHERE username = '{username}'"
        print(f"[DEBUG] SQL: {query}")
        try:
            c.execute(query)
            result = c.fetchone()
            conn.close()
            if result:
                session["password"] = result[0]
                session["username"] = username
                return redirect("/password")
            error = "❌ User not found"
        except Exception as e:
            conn.close()
            error = f"❌ Error: {e}"
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/password", methods=["GET", "POST"])
def password_check():
    if "password" not in session:
        return redirect("/login")
    error = None
    if request.method == "POST":
        password = request.form.get("password", "").strip()
        if password == session["password"]:
            session["totp_secret"] = TOTP_SECRET
            return redirect("/totp")
        error = "❌ Incorrect password"
    return render_template_string(PASSWORD_HTML, error=error)


@app.route("/totp", methods=["GET", "POST"])
def totp_check():
    if "totp_secret" not in session:
        return redirect("/login")
    error = None
    if request.method == "POST":
        code = request.form.get("code", "").strip()
        totp = pyotp.TOTP(session["totp_secret"])
        if totp.verify(code):
            session["admin"] = True
            return redirect("/dashboard")
        error = "❌ Invalid code"
    return render_template_string(TOTP_HTML, error=error)


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    return render_template_string(DASHBOARD_HTML)


# ==================== 评论（存储型 XSS）====================
COMMENTS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Comments</title>
<style>
body{font-family:monospace;background:#0a0a0a;color:#0f0;padding:30px;}
.box{max-width:760px;margin:auto;background:#111;border:1px solid #0f0;padding:25px;border-radius:10px;}
h2{color:#0f0;} .c{border-bottom:1px solid #333;padding:12px 0;}
input,textarea{width:100%;background:#1a1a1a;border:1px solid #0f0;color:#0f0;padding:8px;margin:5px 0;font-family:monospace;}
button{background:#0f0;color:#000;border:none;padding:8px 20px;font-weight:bold;cursor:pointer;}
a{color:#0f0;}
</style></head><body>
<div class="box">
<h2>💬 Comments</h2>
<form method="post">
  <input name="author" placeholder="Name" value="guest" maxlength="50">
  <textarea name="content" placeholder="Say something..." rows="3" maxlength="2000"></textarea>
  <button type="submit">Post</button>
</form>
<hr>
{% for c in comments %}
  <div class="c">
    <b>{{ c[0] }}</b> <small style="color:#666">({{ c[2] }})</small><br>
    {{ c[1]|safe }}
  </div>
{% endfor %}
<p style="margin-top:20px"><a href="/">← Back to blog</a></p>
</div>
</body></html>
"""


@app.route("/comments", methods=["GET", "POST"])
def comments():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == "POST":
        author = (request.form.get("author") or "anonymous")[:50]
        content = (request.form.get("content") or "")[:2000]
        c.execute(
            'INSERT INTO comments (author, content, created_at) VALUES (?, ?, datetime("now","localtime"))',
            (author, content)
        )
        conn.commit()
        conn.close()
        return redirect("/comments")
    c.execute("SELECT author, content, created_at FROM comments ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return render_template_string(COMMENTS_HTML, comments=rows)

# ==================== LSB PNG + AES ZIP ====================


def make_flag_png() -> bytes:
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    pixels = img.load()
    bits = "".join(format(ord(ch), "08b") for ch in FLAG)
    idx = 0
    for y in range(img.height):
        for x in range(img.width):
            if idx < len(bits):
                r, g, b = pixels[x, y]
                r = (r & 0xFE) | int(bits[idx])
                pixels[x, y] = (r, g, b)
                idx += 1
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read()


def make_locked_zip() -> bytes:
    png_bytes = make_flag_png()
    zip_buf = io.BytesIO()
    with pyzipper.AESZipFile(
        zip_buf, "w",
        compression=pyzipper.ZIP_DEFLATED,
        encryption=pyzipper.WZ_AES,
    ) as zf:
        zf.setpassword(ZIP_PASSWORD.encode())
        zf.writestr("avatar.png", png_bytes)
    zip_buf.seek(0)
    return zip_buf.read()


@app.route("/download")
def download():
    if not session.get("admin"):
        return redirect("/login")

    provided = request.cookies.get(BOT_COOKIE_NAME, "")
    if provided != ZIP_PASSWORD:
        return (
            "❌ ZIP is locked.\n"
            "The bot's cookie 'zip_pass' is required to decrypt the archive.\n"
            "Hint: comments are rendered without escaping...\n",
            403,
        )

    zip_bytes = make_locked_zip()
    return send_file(
        io.BytesIO(zip_bytes),
        mimetype="application/zip",
        as_attachment=True,
        download_name="avatar_locked.zip",
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ==================== 后台 Bot 线程（Playwright）====================


def bot_worker():
    """
    管理员 bot：
    每 30 秒打开一次 /comments 页面，浏览器里带有 cookie:
        zip_pass = ZIP_PASSWORD
    如果评论里存在 XSS，就能把 zip_pass 外带出去。
    """
    from playwright.sync_api import sync_playwright

    while True:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
                ctx = browser.new_context()
                ctx.add_cookies([{
                    "name": BOT_COOKIE_NAME,
                    "value": ZIP_PASSWORD,
                    "domain": "127.0.0.1",
                    "path": "/",
                    "httpOnly": False,   # 让 document.cookie 可读，XSS 才能偷到
                    "secure": False,
                    "sameSite": "Lax",
                }])
                page = ctx.new_page()
                page.goto("http://127.0.0.1:8010/comments", timeout=10000)
                page.wait_for_timeout(4000)   # 给 XSS 时间执行
                browser.close()
        except Exception as e:
            print(f"[bot] error: {e}")
        time.sleep(30)


def start_bot():
    t = threading.Thread(target=bot_worker, daemon=True)
    t.start()
    print("[*] Bot thread started (visits /comments every 30s)")


# ==================== 入口 ====================
if __name__ == "__main__":
    start_bot()
    app.run(host="0.0.0.0", port=8010, debug=False)
