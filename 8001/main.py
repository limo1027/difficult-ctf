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
    resp = make_response("The flag is hidden somewhere in the response.")
    resp.set_cookie('flag', flag)  # ← 设置 cookie
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001)
