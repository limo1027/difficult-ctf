import os
import time
import random
import threading
import requests
from flask import Flask, request

# ==================== Flag ====================
if os.path.exists("flag.txt"):
    FLAG = open("flag.txt").read().strip()
else:
    FLAG = "ctfhub{" + "".join(random.choices("0123456789ABCDEF", k=20)) + "}"
    with open("flag.txt", "w") as f:
        f.write(FLAG)

# ==================== 内网服务（只监听 127.0.0.1:5000）====================
internal = Flask('internal')


@internal.route('/')
def secret():
    return FLAG


# ==================== 外部服务（监听 0.0.0.0:8005）====================
external = Flask('external')

# 黑名单：拦截常见的内网地址写法
BLACKLIST = [
    '127.0.0.1',
    'localhost',
    '0.0.0.0',
    '127.1',
    '0x7f',
    '2130706433',
    '[::1]',
    '::1',
    '0177.0.0.1',
    '127.0.0.1.nip.io',
    '127.0.0.1.xip.io',
    'localtest.me',
    'lvh.me',
]


@external.route('/')
def index():
    return """
    <h1>Question 5</h1>
    <p>There's a secret service running on this machine.</p>
    <p>Try <code>/fetch?url=...</code></p>
    <p style="color:#666;font-size:12px;">maybe 5000 is an interesting number</p>
    """


@external.route('/fetch')
def fetch():
    url = request.args.get('url', '')
    if not url:
        return "Usage: /fetch?url=..."

    # 黑名单检查
    lower = url.lower()
    for b in BLACKLIST:
        if b.lower() in lower:
            return "🚫 Blocked: suspicious address detected."

    # 只允许 http:// 和 https://
    if not (url.startswith('http://') or url.startswith('https://')):
        return "🚫 Blocked: only http:// and https:// are allowed."

    try:
        r = requests.get(url, timeout=3, allow_redirects=False)
        return r.text
    except Exception as e:
        return f"Error: {e}"

# ==================== 启动 ====================


def run(app, host, port):
    app.run(host=host, port=port, debug=False, threaded=True)


if __name__ == '__main__':
    t1 = threading.Thread(target=run, args=(
        internal, '127.0.0.1', 5000), daemon=True)
    t2 = threading.Thread(target=run, args=(
        external, '0.0.0.0', 8005), daemon=True)
    t1.start()
    t2.start()
    print("[*] internal: http://127.0.0.1:5000")
    print("[*] external: http://0.0.0.0:8005")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] stopped")
