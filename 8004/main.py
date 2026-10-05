import os
from flask import Flask, request, make_response, render_template_string
import jwt
import random
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"  # 故意暴露的密钥（但选手不知道）

if os.path.exists("flag.txt"):
    flag = open("flag.txt").read()
else:
    flag = \
        "ctfhub{" + "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
with open("flag.txt", mode='w') as f:
    f.write(flag)
print(flag)
# ============ 用户数据库（含弱密码） ============
USERS = {
    "admin": {
        "password": "admin123",  # ← 弱密码！但选手不会第一时间试
        "role": "admin"
    },
    "guest": {
        "password": "guest",
        "role": "guest"
    },
    "user": {
        "password": "password",
        "role": "user"
    }
}

# ============ 页面 ============
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔐 Secure Login</title>
    <style>
        body {
            background: #0a0a0a;
            color: #00ff00;
            font-family: monospace;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            border: 2px solid #00ff00;
            padding: 40px;
            width: 400px;
            text-align: center;
            background: rgba(0,0,0,0.8);
            border-radius: 10px;
        }
        h1 { color: #ff4444; }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: #111;
            border: 1px solid #00ff00;
            color: #00ff00;
            font-family: monospace;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #00ff00;
            color: #000;
            border: none;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover { background: #00cc00; }
        .error { color: #ff4444; margin-top: 10px; }
        .info {
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }
        .hint {
            margin-top: 10px;
            font-size: 12px;
            color: #444;
        }
        .token {
            margin-top: 20px;
            padding: 10px;
            background: #111;
            border-radius: 5px;
            font-size: 11px;
            color: #666;
            word-break: break-all;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🔐 Secure Login</h1>
    <p style="color:#88ff88;">Ultra-secure JWT authentication system</p>
    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}
    <form method="post">
        <input type="text" name="username" placeholder="Username">
        <input type="password" name="password" placeholder="Password">
        <button type="submit">Login</button>
    </form>
    {% if token %}
    <div class="token">
        <strong>Your JWT Token:</strong><br>
        {{ token }}
    </div>
    {% endif %}
    <div class="info">
        <p>🔑 Guest login: guest/guest</p>
        <p class="hint">💡 This system uses industry-standard JWT.</p>
        <p class="hint">Try to forge a token to become admin!</p>
    </div>
</div>
</body>
</html>
'''

# ============ JWT 辅助函数 ============


def generate_jwt(username, role):
    payload = {
        'username': username,
        'role': role,
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600
    }
    return jwt.encode(payload, app.secret_key, algorithm='HS256')


def verify_jwt(token):
    try:
        payload = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return payload
    except:
        return None

# ============ 路由 ============


@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    token = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # ==========================================
        # 🔥 陷阱1: 检查 JWT Cookie（如果有）
        # 选手可能先设置 Cookie 再来访问
        # ==========================================
        cookie_token = request.cookies.get('auth')
        if cookie_token:
            payload = verify_jwt(cookie_token)
            if payload and payload.get('role') == 'admin':
                return f"🎉 Welcome admin! Flag: {flag}"
            else:
                error = "❌ Invalid or expired token."

        # ==========================================
        # 🔥 陷阱2: 普通登录（这才是正解）
        # ==========================================
        if username in USERS:
            if USERS[username]['password'] == password:
                # 生成 JWT（但不告诉选手可以直接登录！）
                token = generate_jwt(username, USERS[username]['role'])

                # 如果登录的是 admin，返回 Flag！
                if username == 'admin':
                    resp = make_response(f"🎉 Welcome admin! Flag: {flag}")
                    resp.set_cookie('auth', token)
                    return resp
                else:
                    resp = make_response(render_template_string(
                        HTML,
                        error="✅ Login successful! But you need admin privileges.",
                        token=token
                    ))
                    resp.set_cookie('auth', token)
                    return resp

        error = "❌ Invalid username or password."

    return render_template_string(HTML, error=error, token=None)


@app.route('/flag')
def f():
    # ==========================================
    # 🔥 陷阱3: 选手可能会尝试直接访问 /flag
    # ==========================================
    token = request.cookies.get('auth')
    if token:
        payload = verify_jwt(token)
        if payload:
            if payload.get('role') == 'admin':
                return f"🎉 Flag: {flag}"
    return "🚫 Access denied. Please login as admin."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8004, debug=False)
