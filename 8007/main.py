import os
from flask import Flask, request
import time
import random

app = Flask(__name__)

app = Flask(__name__)
if os.path.exists("flag.txt"):
    flag = open("flag.txt").read()
else:
    flag = \
        "ctfhub{" + "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
with open("flag.txt", mode='w') as f:
    f.write(flag)
# 将 Flag 转为 ASCII 码列表
FLAG_CODES = [ord(c) for c in flag]

# 记录每个 IP 的访问次数和状态
visitor_data = {}


@app.route('/')
def index():
    ip = request.remote_addr
    now = time.time()

    # 初始化或获取访问记录
    if ip not in visitor_data:
        visitor_data[ip] = {
            'count': 0,
            'flag_index': 0,      # 当前要泄露的字符位置
            'last_access': now
        }

    record = visitor_data[ip]

    # 第一次访问：正常返回
    if record['count'] == 0:
        record['count'] += 1
        record['last_access'] = now
        return "Welcome! Come back again and see what happens :)"

    # 第二次及以后：根据 Flag 字符延时
    # 每次访问泄露一个字符（顺序推进）
    idx = record['flag_index'] % len(FLAG_CODES)
    delay = FLAG_CODES[idx] / 10.0

    # 记录本次访问
    record['count'] += 1
    record['flag_index'] += 1
    record['last_access'] = now

    # 核心：延时操作
    time.sleep(delay)

    return f"Welcome! Come back again and see what happens :)"


@app.route('/reset')
def reset():
    """重置当前 IP 的访问状态（方便选手调试）"""
    ip = request.remote_addr
    if ip in visitor_data:
        del visitor_data[ip]
        return "Reset successfully!"
    return "No record found"


if __name__ == "__main__":
    # 生产环境建议使用 Gunicorn 等 WSGI 服务器
    app.run(host="0.0.0.0", port=8007, debug=False, threaded=True)
