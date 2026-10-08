from flask import (
    Flask, request, session, redirect, url_for,
    render_template_string
)
import secrets
import time
import threading
import os
import random

from playwright.sync_api import sync_playwright

app = Flask(__name__)
app.secret_key = "flag-vault-secret-key"

# ============ 配置 ============
BASE_URL = "http://127.0.0.1:8013"
ADMIN_USER = "admin"
ADMIN_PASS = "admin_password_you_cant_guess"
if os.path.exists("flag.txt"):
    FLAG = open("flag.txt").read().strip()
else:
    FLAG = "ctfhub{" + "".join(random.choices("0123456789ABCDEF", k=20)) + "}"
    with open("flag.txt", "w") as f:
        f.write(FLAG)
ENABLE_CSRF = True

# ============ 数据 ============
USERS = {ADMIN_USER: ADMIN_PASS, "guest": "guest"}
BALANCE = {ADMIN_USER: 999999, "guest": 100}
FLAGS = {ADMIN_USER: FLAG, "guest": None}
MESSAGES = []

# ============ 工具 ============


def current_user():
    return session.get("user")


def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


def check_csrf():
    if not ENABLE_CSRF:
        return True
    token = request.form.get(
        "csrf_token") or request.headers.get("X-CSRF-Token")
    return token and token == session.get("csrf_token")


# ============ 页面模板 ============
BASE = """
<!DOCTYPE html>
<html>
<head><title>Flag Vault</title></head>
<body>
<h1>🏦 Flag Vault</h1>
{% if user %}
  <p>当前用户: <b>{{ user }}</b> | 余额: <b>{{ balance }}</b>
     | <a href="/logout">退出</a></p>
  <p><a href="/">首页</a> | <a href="/board">留言板</a></p>
{% endif %}
<hr>
{% block content %}{% endblock %}
</body>
</html>
"""

LOGIN = BASE.replace("{% block content %}{% endblock %}", """
{% block content %}
<h2>登录</h2>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="POST">
  用户名: <input name="username"><br>
  密码: <input name="password" type="password"><br>
  <button>登录</button>
</form>
<p>提示: guest/guest</p>
{% endblock %}
""")

INDEX = BASE.replace("{% block content %}{% endblock %}", """
{% block content %}
<h2>首页</h2>
{% if flag %}
  <p style="color:green">🎉 你的 Flag: <code>{{ flag }}</code></p>
{% endif %}
<h3>转账</h3>
<form method="POST" action="/transfer">
  收款人: <input name="to"><br>
  金额: <input name="amount"><br>
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
  <button>转账</button>
</form>
<p style="color:gray">CSRF 防御: {{ '开启' if csrf_enabled else '关闭' }}</p>
{% endblock %}
""")

BOARD = BASE.replace("{% block content %}{% endblock %}", """
{% block content %}
<h2>留言板</h2>
<form method="POST">
  <textarea name="content" rows="3" cols="50" placeholder="留下你的祝福..."></textarea><br>
  <button>提交</button>
</form>
<hr>
<h3>所有留言</h3>
{% for m in messages %}
  <div style="border:1px solid #ccc;padding:8px;margin:5px 0">
    <b>{{ m.user }}</b>: {{ m.content|safe }}
  </div>
{% endfor %}
{% endblock %}
""")

# ============ 路由 ============


@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template_string(
        INDEX,
        user=user,
        balance=BALANCE.get(user, 0),
        flag=FLAGS.get(user),
        csrf_token=get_csrf_token(),
        csrf_enabled=ENABLE_CSRF,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if USERS.get(u) == p:
            session["user"] = u
            get_csrf_token()
            return redirect(url_for("index"))
        return render_template_string(LOGIN, user=None, error="登录失败")
    return render_template_string(LOGIN, user=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/transfer", methods=["POST"])
def transfer():
    user = current_user()
    if not user:
        return "未登录", 401
    if not check_csrf():
        return "CSRF Token 无效", 403
    to = request.form.get("to", "")
    try:
        amount = int(request.form.get("amount", 0))
    except ValueError:
        return "金额非法", 400
    if BALANCE.get(user, 0) < amount:
        return "余额不足", 400
    BALANCE[user] -= amount
    BALANCE[to] = BALANCE.get(to, 0) + amount
    return f"转账成功: {user} -> {to}, 金额 {amount}. 余额: {BALANCE[user]}"


@app.route("/board", methods=["GET", "POST"])
def board():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        content = request.form.get("content", "")
        if content:
            MESSAGES.append({
                "id": len(MESSAGES) + 1,
                "user": user,
                "content": content,
                "ts": time.time(),
            })
        return redirect(url_for("board"))
    return render_template_string(BOARD, user=user, balance=BALANCE.get(user, 0),
                                  messages=MESSAGES)

# ============ Admin Bot (Playwright) ============


def admin_bot():
    """用 Playwright 登录 admin，访问留言板触发存储型 XSS"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 1. 登录 admin
            page.goto(f"{BASE_URL}/login")
            page.fill('input[name="username"]', ADMIN_USER)
            page.fill('input[name="password"]', ADMIN_PASS)
            page.click('button')
            page.wait_for_load_state("networkidle")

            # 2. 访问留言板，触发 XSS
            page.goto(f"{BASE_URL}/board")
            page.wait_for_load_state("networkidle")

            # 3. 等 XSS 里的 fetch 跑完
            try:
                page.wait_for_function(
                    "document.title.startsWith('LEAKED:')",
                    timeout=5000
                )
                print("[bot] XSS 结果:", page.title())
            except Exception:
                page.wait_for_timeout(3000)
                print("[bot] 标题未变化，当前:", page.title())

            # 4. 截图调试
            page.screenshot(path="/tmp/bot_board.png", full_page=True)
            print("[bot] 截图已保存 /tmp/bot_board.png")

        except Exception as e:
            print("[bot] error:", e)
        finally:
            browser.close()


def bot_loop():
    """每隔 N 秒跑一次 bot，模拟管理员定时查看"""
    time.sleep(3)
    while True:
        try:
            admin_bot()
        except Exception as e:
            print("[bot] loop error:", e)
        time.sleep(20)


# ============ 启动 ============
if __name__ == "__main__":
    t = threading.Thread(target=bot_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=8013, debug=False)
