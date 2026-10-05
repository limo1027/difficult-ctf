import os
import random
from flask import Flask


app = Flask(__name__)
if os.path.exists("flag.txt"):
    flag = open("flag.txt").read()
else:
    flag = \
        "ctfhub{" + "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
with open("flag.txt", mode='w') as f:
    f.write(flag)
html = f"""
<html>
<head>
<title>hidden flag</title>
</head>
<body>
<p>flag is not here.</p>
</body>
<!-- {flag} -->
</html>"""


@app.route("/")
def index():
    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
