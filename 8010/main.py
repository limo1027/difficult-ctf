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
BLOG_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>My Blog</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Georgia', serif; background: #fafafa; color: #222; line-height: 1.8; }
    .navbar {
        background: #2c3e50; padding: 18px 40px; display: flex;
        justify-content: space-between; align-items: center;
        position: sticky; top: 0; z-index: 100;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    }
    .navbar .logo { color: #ecf0f1; font-size: 22px; font-weight: bold; letter-spacing: 1px; }
    .navbar .logo span { color: #e74c3c; }
    .navbar a { color: #ecf0f1; margin-left: 18px; text-decoration: none; }
    .navbar a:hover { color: #e74c3c; }
    .navbar .login-btn {
        background: #e74c3c; color: #fff; border: none; padding: 10px 28px;
        font-size: 14px; border-radius: 25px; cursor: pointer; transition: 0.3s;
        text-decoration: none; font-weight: bold;
    }
    .navbar .login-btn:hover { background: #c0392b; transform: scale(1.05); }
    .container { max-width: 780px; margin: 50px auto; padding: 0 20px; }
    .card {
        background: #fff; padding: 45px 55px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    }
    .card h1 {
        font-size: 30px; color: #2c3e50; border-bottom: 2px solid #ecf0f1;
        padding-bottom: 12px; margin-bottom: 8px;
    }
    .meta { color: #b0b0b0; font-size: 13px; margin-bottom: 25px; }
    .meta span { margin-right: 18px; }
    .card p { margin-bottom: 18px; font-size: 16.5px; color: #333; }
    .footer-note {
        margin-top: 30px; padding-top: 18px; border-top: 1px solid #eee;
        font-size: 13px; color: #bbb; text-align: center;
    }
    a { color: #e74c3c; }
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
    <div class="card">
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
        <!-- %HIDDEN%Don't cost too time of this.-->
    </div>
</div>
</body>
</html>
""".replace("%HIDDEN%", HIDDEN)

# ==================== 登录页（三合一表单）====================
LOGIN_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Login</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Georgia', serif; background: #fafafa; color: #222; line-height: 1.8; }
    .navbar {
        background: #2c3e50; padding: 18px 40px; display: flex;
        justify-content: space-between; align-items: center;
        position: sticky; top: 0; z-index: 100;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    }
    .navbar .logo { color: #ecf0f1; font-size: 22px; font-weight: bold; letter-spacing: 1px; }
    .navbar .logo span { color: #e74c3c; }
    .navbar a { color: #ecf0f1; margin-left: 18px; text-decoration: none; }
    .navbar a:hover { color: #e74c3c; }
    .navbar .login-btn {
        background: #e74c3c; color: #fff; border: none; padding: 10px 28px;
        font-size: 14px; border-radius: 25px; cursor: pointer; transition: 0.3s;
        text-decoration: none; font-weight: bold;
    }
    .navbar .login-btn:hover { background: #c0392b; transform: scale(1.05); }
    .container { max-width: 780px; margin: 50px auto; padding: 0 20px; }
    .card {
        background: #fff; padding: 45px 55px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        max-width: 460px; margin: 0 auto;
    }
    .card h2 { font-size: 22px; color: #2c3e50; margin-bottom: 10px; }
    .meta { color: #b0b0b0; font-size: 13px; margin-bottom: 25px; }
    .field { text-align: left; margin-bottom: 18px; }
    .field label { display: block; font-size: 13px; color: #888; margin-bottom: 6px; }
    input {
        width: 100%; padding: 12px 14px; background: #fff;
        border: 1px solid #ddd; color: #222; font-size: 15px;
        border-radius: 6px; outline: none; font-family: inherit;
        transition: border-color 0.2s;
    }
    input:focus { border-color: #e74c3c; }
    input.code { text-align: center; letter-spacing: 4px; font-family: monospace; }
    button {
        width: 100%; padding: 12px; margin-top: 8px; background: #e74c3c;
        color: #fff; border: none; font-size: 16px; font-weight: bold;
        border-radius: 6px; cursor: pointer; transition: 0.2s;
    }
    button:hover { background: #c0392b; }
    .error { color: #e74c3c; margin-top: 12px; font-size: 14px; }
    a { color: #e74c3c; }
</style>
</head><body>
<nav class="navbar">
    <div class="logo">📖 My<span>Blog</span></div>
    <div>
        <a href="/comments">💬 Comments</a>
        <a href="/login" class="login-btn">🔑 Login</a>
    </div>
</nav>
<div class="container">
<div class="card">
<h2>🔐 Authentication</h2>
<p class="meta">Enter your credentials</p>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
  <div class="field">
    <label>① Username</label>
    <input type="text" name="username" placeholder="Username" autofocus>
  </div>
  <div class="field">
    <label>② Password</label>
    <input type="password" name="password" placeholder="Password">
  </div>
  <div class="field">
    <label>③ Two-Factor Code</label>
    <input type="text" name="code" class="code" placeholder="123456" maxlength="6">
  </div>
  <button type="submit">Verify</button>
</form>
<p style="margin-top:18px;text-align:center;font-size:14px;"><a href="/">← Back to blog</a></p>
</div>
</div>
</body></html>
"""

# ==================== 仪表盘 ====================
DASHBOARD_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Dashboard</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Georgia', serif; background: #fafafa; color: #222; line-height: 1.8; }
    .navbar {
        background: #2c3e50; padding: 18px 40px; display: flex;
        justify-content: space-between; align-items: center;
        position: sticky; top: 0; z-index: 100;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    }
    .navbar .logo { color: #ecf0f1; font-size: 22px; font-weight: bold; letter-spacing: 1px; }
    .navbar .logo span { color: #e74c3c; }
    .navbar a { color: #ecf0f1; margin-left: 18px; text-decoration: none; }
    .navbar a:hover { color: #e74c3c; }
    .navbar .login-btn {
        background: #e74c3c; color: #fff; border: none; padding: 10px 28px;
        font-size: 14px; border-radius: 25px; cursor: pointer; transition: 0.3s;
        text-decoration: none; font-weight: bold;
    }
    .navbar .login-btn:hover { background: #c0392b; transform: scale(1.05); }
    .container { max-width: 780px; margin: 50px auto; padding: 0 20px; }
    .card {
        background: #fff; padding: 45px 55px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        text-align: center;
    }
    .card h2 { font-size: 24px; color: #2c3e50; margin-bottom: 10px; }
    .meta { color: #b0b0b0; font-size: 14px; margin-bottom: 25px; }
    .btn {
        display: inline-block; margin: 8px; padding: 12px 35px;
        background: #e74c3c; color: #fff; text-decoration: none;
        border-radius: 25px; font-weight: bold; transition: 0.2s;
    }
    .btn:hover { background: #c0392b; }
    .btn.logout { background: #95a5a6; }
    .btn.logout:hover { background: #7f8c8d; }
    .hint {
        color: #e67e22; font-size: 14px; margin-top: 22px;
        line-height: 1.8; background: #fef5e7; padding: 15px 20px;
        border-radius: 8px; border-left: 4px solid #e67e22; text-align: left;
    }
    a { color: #e74c3c; }
</style>
</head><body>
<nav class="navbar">
    <div class="logo">📖 My<span>Blog</span></div>
    <div>
        <a href="/comments">💬 Comments</a>
        <a href="/login" class="login-btn">🔑 Login</a>
    </div>
</nav>
<div class="container">
<div class="card">
<h2>✅ Welcome, admin</h2>
<p class="meta">You are logged in as administrator.</p>
<a class="btn" href="/download">📥 Download Avatar (ZIP, AES)</a>
<br><br>
<a class="btn logout" href="/logout">🚪 Logout</a>
<div class="hint">
    ⚠️ The ZIP is AES-encrypted.<br>
    Only the admin bot holds the key cookie <code>zip_pass</code>.<br>
    Maybe the <a href="/comments">💬 comment section</a> can help you get it.
</div>
</div>
</div>
</body></html>
"""

# ==================== 评论页 ====================
COMMENTS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Comments</title>
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Georgia', serif; background: #fafafa; color: #222; line-height: 1.8; }
    .navbar {
        background: #2c3e50; padding: 18px 40px; display: flex;
        justify-content: space-between; align-items: center;
        position: sticky; top: 0; z-index: 100;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    }
    .navbar .logo { color: #ecf0f1; font-size: 22px; font-weight: bold; letter-spacing: 1px; }
    .navbar .logo span { color: #e74c3c; }
    .navbar a { color: #ecf0f1; margin-left: 18px; text-decoration: none; }
    .navbar a:hover { color: #e74c3c; }
    .navbar .login-btn {
        background: #e74c3c; color: #fff; border: none; padding: 10px 28px;
        font-size: 14px; border-radius: 25px; cursor: pointer; transition: 0.3s;
        text-decoration: none; font-weight: bold;
    }
    .navbar .login-btn:hover { background: #c0392b; transform: scale(1.05); }
    .container { max-width: 780px; margin: 50px auto; padding: 0 20px; }
    .card {
        background: #fff; padding: 45px 55px; border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
    }
    .card h2 { font-size: 22px; color: #2c3e50; margin-bottom: 10px; }
    .field { margin-bottom: 15px; }
    input, textarea {
        width: 100%; padding: 12px 14px; background: #fff;
        border: 1px solid #ddd; color: #222; font-size: 15px;
        border-radius: 6px; outline: none; font-family: inherit;
        transition: border-color 0.2s;
    }
    input:focus, textarea:focus { border-color: #e74c3c; }
    button {
        padding: 10px 30px; background: #e74c3c; color: #fff;
        border: none; font-size: 15px; font-weight: bold;
        border-radius: 6px; cursor: pointer; transition: 0.2s;
    }
    button:hover { background: #c0392b; }
    .comment { border-bottom: 1px solid #eee; padding: 16px 0; }
    .comment:last-child { border-bottom: none; }
    .comment .author { color: #2c3e50; font-weight: bold; }
    .comment .time { color: #b0b0b0; font-size: 12px; margin-left: 8px; }
    .comment .body { margin-top: 6px; color: #333; }
    hr { border: none; border-top: 1px solid #eee; margin: 25px 0; }
    a { color: #e74c3c; }
</style>
</head><body>
<nav class="navbar">
    <div class="logo">📖 My<span>Blog</span></div>
    <div>
        <a href="/comments">💬 Comments</a>
        <a href="/login" class="login-btn">🔑 Login</a>
    </div>
</nav>
<div class="container">
<div class="card">
<h2>💬 Comments</h2>
<form method="post" style="margin: 20px 0;">
  <div class="field">
    <input name="author" placeholder="Name" value="guest" maxlength="50">
  </div>
  <div class="field">
    <textarea name="content" placeholder="Say something..." rows="3" maxlength="2000"></textarea>
  </div>
  <button type="submit">Post</button>
</form>
<hr>
{% for c in comments %}
  <div class="comment">
    <span class="author">{{ c[0] }}</span>
    <span class="time">{{ c[2] }}</span>
    <div class="body">{{ c[1]|safe }}</div>
  </div>
{% endfor %}
<p style="margin-top:25px;text-align:center;font-size:14px;"><a href="/">← Back to blog</a></p>
</div>
</div>
</body></html>
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
        password = request.form.get("password", "").strip()
        code = request.form.get("code", "").strip()

        # ---------- 反 UNION 检测（逼盲注） ----------
        if "union" in username.lower():
            print(f"[WARN] UNION attempt blocked: {username}")
            return render_template_string(
                LOGIN_HTML, error="❌ Suspicious input detected")

        # ---------- 第一步：用户名（SQL 注入点） ----------
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        query = f"SELECT password FROM users WHERE username = '{username}'"
        print(f"[DEBUG] SQL: {query}")
        try:
            c.execute(query)
            result = c.fetchone()
            conn.close()
        except Exception as e:
            conn.close()
            return render_template_string(LOGIN_HTML, error=f"❌ Error: {e}")

        if not result:
            return render_template_string(LOGIN_HTML, error="❌ User not found")

        db_password = result[0]

        # ---------- 第二步：密码 ----------
        if password != db_password:
            return render_template_string(LOGIN_HTML, error="❌ Incorrect password")

        # ---------- 第三步：TOTP ----------
        totp = pyotp.TOTP(TOTP_SECRET)
        if not totp.verify(code):
            return render_template_string(LOGIN_HTML, error="❌ Invalid code")

        # 全部通过
        session["admin"] = True
        session["username"] = username
        return redirect("/dashboard")

    return render_template_string(LOGIN_HTML, error=error)


@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")
    return render_template_string(DASHBOARD_HTML)


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
                    "httpOnly": False,
                    "secure": False,
                    "sameSite": "Lax",
                }])
                page = ctx.new_page()
                page.goto("http://127.0.0.1:8010/comments", timeout=10000)
                page.wait_for_timeout(4000)
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
