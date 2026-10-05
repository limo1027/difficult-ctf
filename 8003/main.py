import os
from flask import Flask, make_response
import random

app = Flask(__name__)
if os.path.exists("flag.txt"):
    flag = open("flag.txt").read()
else:
    flag = \
        "ctfhub{" + "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
with open("flag.txt", mode='w') as f:
    f.write(flag)


@app.route('/')
def index():
    resp = make_response("The flag is at a hidden location.")
    resp.headers['X-Flag'] = flag   # ← flag 藏在自定义响应头里
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)
