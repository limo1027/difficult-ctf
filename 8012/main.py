from flask import Flask, send_file, render_template_string
import base64
import random
import os
import pyzipper
from PIL import Image
import threading
import time

# ==================== 全局配置 ====================
import os
if os.path.exists("flag.txt"):
    FLAG = open("flag.txt").read()
else:
    FLAG = \
        "ctfhub{" + "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
with open("flag.txt", mode='w') as f:
    f.write(FLAG)
KEY = "".join(random.choices(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", k=16))
PORT = random.randint(1000, 2000)
# ==================== XOR 加密/解密 ====================


def xor_encrypt(data, key):
    data_bytes = data.encode()
    return bytes([data_bytes[i] ^ ord(key[i % len(key)]) for i in range(len(data_bytes))])


# ==================== 零宽字符 ====================
ZW = {'0': '\u200B', '1': '\u200C'}


def zw_encode(text):
    bits = ''.join(format(ord(c), '08b') for c in text)
    return ''.join(ZW[b] for b in bits)

# ==================== LSB 隐写 ====================


def lsb_encode(img, data):
    pixels = img.load()
    bits = ''.join(format(ord(c), '08b') for c in data)
    idx = 0
    for y in range(img.height):
        for x in range(img.width):
            if idx < len(bits):
                r, g, b = pixels[x, y]
                r = (r & 0xFE) | int(bits[idx])
                pixels[x, y] = (r, g, b)
                idx += 1
    return img

# ==================== 生成挑战图片 ====================


def generate_challenge():
    # 1. 加密 FLAG → 得到大整数
    # 先把 "PORT" 转成二维码矩阵 → 二进制 → 大整数
    import qrcode
    import numpy as np

    qr = qrcode.QRCode(box_size=1, border=0,
                       error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(f"get flag on port {PORT}")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    # 转成 21x21 矩阵
    qr_array = np.array(qr_img.convert('L'))
    qr_binary = ''.join(
        ['1' if pixel < 128 else '0' for row in qr_array for pixel in row])
    big_int = int(qr_binary, 2)
    print(f"[*] 大整数: {big_int.bit_length()}")

    # 2. 用 KEY 加密大整数 → ciphertext
    ciphertext = base64.b64encode(xor_encrypt(str(big_int), KEY)).decode()
    print(f"[*] Ciphertext: {ciphertext[:50]}...")

    # 3. 创建 key.txt
    with open('key.txt', 'w') as f:
        f.write(KEY)

    # 4. 创建加密 ZIP
    zip_path = 'secret.zip'
    with pyzipper.AESZipFile(zip_path, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as zf:
        zf.setpassword(ciphertext.encode())
        zf.write('key.txt')
    print("[+] 已创建加密 ZIP")

    # 5. LSB 隐写 ciphertext 到图片
    img = Image.new('RGB', (400, 100), (255, 255, 255))
    img = lsb_encode(img, ciphertext)
    img.save('challenge.png')
    print("[+] 图片已生成: challenge.png")

    # 6. 追加 ZIP 到图片末尾
    with open('challenge.png', 'ab') as f:
        with open('secret.zip', 'rb') as z:
            f.write(z.read())
    print("[+] ZIP 已追加到图片末尾")

    os.remove('key.txt')
    os.remove('secret.zip')

    return ciphertext

# ==================== 创建 Flask 应用（端口 8011） ====================


def create_main_app():
    app = Flask(__name__)

    HTML_MAIN = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>🧩 图片隐写挑战</title>
        <style>
            body{background:#0a0a0a;color:#00ff00;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
            .container{border:2px solid #00ff00;padding:40px;text-align:center;background:rgba(0,0,0,0.8);border-radius:10px;max-width:600px}
            a{display:inline-block;padding:15px 40px;background:#00ff00;color:#000;text-decoration:none;border-radius:5px;font-weight:bold;margin-top:20px}
            a:hover{background:#00cc00;box-shadow:0 0 30px #00ff00}
            .hint{margin-top:20px;font-size:12px;color:#666}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧩 图片隐写挑战</h1>
            <p>下载图片，找到隐藏的信息</p>
            <a href="/download">📥 下载 challenge.png</a>
        </div>
    </body>
    </html>
    '''

    @app.route('/')
    def index():
        return render_template_string(HTML_MAIN)

    @app.route('/download')
    def download():
        return send_file('challenge.png', as_attachment=True)

    return app

# ==================== 创建 Flask 应用（端口 1025） ====================


def create_port1025_app():
    app = Flask('port1025')

    PORT_1025_HTML = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>🚫 Not Here</title>
        <style>
            body{{background:#0a0a0a;color:#00ff00;font-family:monospace;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}}
            .container{{border:2px solid #00ff00;padding:40px;text-align:center}}
            .hint{{margin-top:20px;font-size:12px;color:#666}}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>The flag is not here.</h1>
            <p>{zw_encode(FLAG)}</p>
        </div>
    </body>
    </html>
    '''

    @app.route('/')
    def index():
        return render_template_string(PORT_1025_HTML)

    return app

# ==================== 运行 Flask ====================


def run_app(port, app):
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


# ==================== 主程序 ====================
if __name__ == '__main__':
    if not os.path.exists('challenge.png'):
        print("[*] 生成挑战图片...")
        generate_challenge()
        print("[+] 挑战图片已生成")

    main_app = create_main_app()
    app1025 = create_port1025_app()

    t1 = threading.Thread(target=run_app, args=(8012, main_app), daemon=True)
    t2 = threading.Thread(target=run_app, args=(PORT, app1025), daemon=True)

    t1.start()
    t2.start()

    print("="*50)
    print("🚀 所有服务已启动！")
    print("="*50)
    print(f"📌 主页面: http://localhost:8012")
    print(f"📌 端口1025: http://localhost:{PORT} (零宽字符藏 flag)")
    print("="*50)
    print(f"🏁 Flag: {FLAG}")
    print(f"🔑 KEY: {KEY}")
    print("="*50)
    print("按 Ctrl+C 停止所有服务")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        print("✅ 已停止")
