# main.py - Flask CTF 入口

import os
import sqlite3
import secrets
import string
from flask import Flask, request, render_template_string, send_file, session, redirect, abort, send_from_directory
import init_flag  # noqa

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'users.db')
PACK_PATH = os.path.join(BASE_DIR, 'pack.zip')
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
# ==================== 生成随机内容 ====================


def generate_admin_username():
    chars = string.ascii_letters + string.digits
    username = (
        secrets.choice(string.ascii_uppercase) +
        secrets.choice(string.ascii_lowercase) +
        secrets.choice(string.digits) +
        ''.join(secrets.choice(chars) for _ in range(9))
    )
    lst = list(username)
    secrets.SystemRandom().shuffle(lst)
    return ''.join(lst)
# ==================== 数据库 ====================


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 用户表 - 加上 has_file 列
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'guest',
            has_file INTEGER DEFAULT 0
        )
    ''')

    # flag 表（误导）
    c.execute('''
        CREATE TABLE IF NOT EXISTS flags (
            id INTEGER PRIMARY KEY,
            flag TEXT NOT NULL
        )
    ''')
    c.execute('INSERT OR IGNORE INTO flags (id, flag) VALUES (1, ?)',
              ('Where is it?',))

    # 生成用户
    admin_user = generate_admin_username()
    admin_pass = "admin123"
    guest_pass = 'guest123'

    # 插入用户（如果已存在则忽略）
    c.execute('INSERT OR IGNORE INTO users (username, password, role, has_file) VALUES (?, ?, ?, ?)',
              ("admin1", admin_pass, 'admin', 0))
    c.execute('INSERT OR IGNORE INTO users (username, password, role, has_file) VALUES (?, ?, ?, ?)',
              ('guest', guest_pass, 'guest', 0))
    c.execute('INSERT OR IGNORE INTO users (username, password, role, has_file) VALUES (?, ?, ?, ?)',
              (admin_user, admin_pass, 'admin', 1))

    conn.commit()
    conn.close()


def get_user_unsafe(username, password):
    """不安全查询 - SQL注入点"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 先把密码参数化，但放在整个WHERE子句前面
    query = f"SELECT id, username, role, has_file FROM users WHERE password = ? AND username = '{username}'"
    print(f"[DEBUG] SQL: {query}")
    try:
        c.execute(query, (password,))
        user = c.fetchone()
    except Exception as e:
        print(f"[ERROR] {e}")
        user = None
    conn.close()
    return user


init_db()

# ==================== 模板 ====================

INDEX = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>CTF</title>
<style>
body{background:#0a0a0a;color:#00ff00;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;flex-direction:column}
.container{border:2px solid #00ff00;padding:40px;max-width:600px;text-align:center;background:rgba(0,0,0,0.8);border-radius:10px}
.title{font-size:28px;color:#ff4444;text-shadow:0 0 20px #ff4444}
.info{margin:20px 0;font-size:14px;color:#88ff88}
.btn{display:inline-block;padding:15px 40px;background:#00ff00;color:#000;text-decoration:none;border-radius:5px;font-weight:bold;font-size:18px;margin-top:20px}
.btn:hover{background:#00cc00;box-shadow:0 0 30px #00ff00}
.hint{margin-top:30px;font-size:12px;color:#666;border-top:1px solid #333;padding-top:20px}
.blink{animation:blink 1s step-end infinite}
@keyframes blink{0%,50%{opacity:1}50.1%,100%{opacity:0}}
.cipher{font-size:16px;color:#ff8844;word-break:break-all;background:#111;padding:15px;border-radius:5px;margin:15px 0}
</style>
</head>
<body>
<div class="container">
<div class="title">⚠️ Encryption System</div>
<div class="info">
<p>Requires <strong style="color:#ff4444;">administrator</strong> login to access</p>
<p style="font-size:12px;color:#666;">Known guest password: <strong>guest123</strong></p>
</div>
<a href="/login" class="btn">🔑 login</a>
<div class="hint"><span class="blink">▶</span> Only users with files can download pack.zip</div>
</div>
</body>
</html>'''

LOGIN = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>login</title>
<style>
body{background:#0a0a0a;color:#00ff00;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.container{border:2px solid #00ff00;padding:40px;width:350px;background:rgba(0,0,0,0.8);border-radius:10px}
.title{text-align:center;font-size:24px;margin-bottom:30px;color:#ff4444}
.error{color:#ff4444;background:#441111;padding:10px;border-radius:5px;margin-bottom:15px}
input{width:100%;padding:12px;margin:10px 0;background:#111;border:1px solid #00ff00;color:#00ff00;font-family:monospace;font-size:14px;border-radius:5px;box-sizing:border-box}
input:focus{outline:none;box-shadow:0 0 20px rgba(0,255,0,0.3)}
button{width:100%;padding:12px;background:#00ff00;color:#000;border:none;font-size:16px;font-weight:bold;border-radius:5px;cursor:pointer;margin-top:10px}
button:hover{background:#00cc00;box-shadow:0 0 30px #00ff00}
.info{margin-top:20px;text-align:center;font-size:12px;color:#666}
.info a{color:#00ff00;text-decoration:none}
</style>
</head>
<body>
<div class="container">
<div class="title">🔐 login</div>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<form method="post">
<input type="text" name="username" placeholder="username">
<input type="password" name="password" placeholder="password">
<button type="submit">login</button>
</form>
<div class="info">
<p>guest / guest123</p>
<p><a href="/">← return</a></p>
</div>
</div>
</body>
</html>
<!-- Login form submission method: POST /login, args: username, password -->'''

DOWNLOAD = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>download</title>
<style>
body{background:#0a0a0a;color:#00ff00;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;flex-direction:column}
.container{border:2px solid #00ff00;padding:40px;text-align:center;background:rgba(0,0,0,0.8);border-radius:10px}
.title{font-size:24px;color:#00ff00}
.info{margin:20px 0;font-size:14px;color:#88ff88}
.user{color:#ff4444}
.btn{display:inline-block;padding:15px 40px;background:#00ff00;color:#000;text-decoration:none;border-radius:5px;font-weight:bold;font-size:18px;margin-top:20px}
.btn:hover{background:#00cc00;box-shadow:0 0 30px #00ff00}
.logout{margin-top:30px;color:#666;font-size:12px}
.logout a{color:#ff4444;text-decoration:none}
</style>
</head>
<body>
<div class="container">
<div class="title">📦 file download</div>
<div class="info"><p>welcome <strong class="user">{{ username }}</strong>！</p><p>{{ size }}</p></div>
<a href="/download/file" class="btn">⬇ download pack.zip</a>
<div class="logout"><a href="/logout">Logout</a></div>
</div>
</body>
</html>'''

# ==================== 生成主页密文 ====================

# ==================== 路由 ====================


@app.route('/')
def index():
    return render_template_string(INDEX)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
    else:
        # 支持 GET 请求带参数
        username = request.args.get('username', '').strip()
        password = request.args.get('password', '').strip()

    if username and password:
        user = get_user_unsafe(username, password)
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[2]
            session['has_file'] = user[3]
            return redirect('/download')
        return render_template_string(LOGIN, error='username or password is incorrect..')
    return render_template_string(LOGIN, error=None)


@app.route('/download')
def download_page():
    if 'user_id' not in session:
        return redirect('/login')
    if session.get('has_file') != 1:
        return f'Current user: {session.get("username")}. This user has not file <a href="/logout">Logout</a>', 403
    return render_template_string(DOWNLOAD, username=session.get('username'), size='pack.zip is ready.')


@app.route('/download/file')
def download_file():
    if 'user_id' not in session:
        return redirect('/login')
    if session.get('has_file') != 1:
        return 'This user has no file.', 403
    return send_file(PACK_PATH, as_attachment=True, download_name='pack.zip')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/.git/', defaults={'path': ''})
@app.route('/.git/<path:path>')
def serve_git(path):
    git_dir = os.path.join(os.path.dirname(__file__), '.git')

    if not path:
        abort(403)

    try:
        return send_from_directory(git_dir, path)
    except FileNotFoundError:
        abort(404)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8011, debug=False, threaded=True)
