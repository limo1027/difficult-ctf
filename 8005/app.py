import os
import random
from flask import Flask, request, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
if "FLAG" in os.environ:
    FLAG = os.environ["FLAG"]
elif os.path.exists("flag.txt"):
    FLAG = open("flag.txt").read()
else:
    FLAG = "ctfhub{" + "".join(random.choices("0123456789ABCDEF", k=20)) + "}"
    os.environ["FLAG"] = FLAG
    open("flag.txt", 'w').write(FLAG)

app = Flask(__name__)

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Upload</title>
<style>
body { background:#0a0a0a; color:#0f0; font-family:monospace; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
.box { border:2px solid #0f0; padding:40px; border-radius:10px; background:rgba(0,0,0,0.8); text-align:center; }
h1 { color:#f44; }
input[type=file] { color:#0f0; margin:10px 0; }
button { background:#0f0; color:#000; border:none; padding:10px 30px; font-weight:bold; cursor:pointer; border-radius:5px; }
.hint { color:#666; font-size:12px; margin-top:20px; }
</style></head>
<body>
<div class="box">
    <h1>📤 File Upload</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file"><br>
        <button type="submit">Upload</button>
    </form>
    <p class="hint">💡 This server reloads automatically.</p>
    <p class="hint">💡 Call likes curl -X POST -F "file=@/path/to/yourfile.txt" http://192.168.1.3:8005/upload</p>
</div>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(INDEX_HTML)


@app.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('file')
    if not f:
        return "No file", 400
    filename = f.filename
    path = os.path.join(UPLOAD_DIR, filename)
    f.save(path)
    return f"Saved to uploads/{filename}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8005, debug=True)
