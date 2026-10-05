import os
from flask import Flask, request
import sqlite3
import re
import random

app = Flask(__name__)

# ============ 生成随机 Flag ============
if os.path.exists("flag.txt"):
    flag = open("flag.txt").read()
else:
    flag = \
        "ctfhub{" + "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
with open("flag.txt", mode='w') as f:
    f.write(flag)
# ============ 初始化数据库 ============


def init_db():
    conn = sqlite3.connect('challenge.db')
    c = conn.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS users (id INTEGER, username TEXT, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS flags (flag TEXT)')
    c.execute('DELETE FROM flags')
    c.execute('INSERT INTO flags (flag) VALUES (?)', (flag,))
    c.execute('DELETE FROM users')
    for i, name in enumerate(['admin', 'guest', 'user1', 'user2']):
        c.execute('INSERT INTO users VALUES (?, ?, ?)', (i, name, f'pass{i}'))
    conn.commit()
    conn.close()


init_db()

# ============ WAF ============
BLACKLIST = [
    r'--', r'#', r'/\*', r'\*/',
    r'sleep', r'benchmark', r'pg_sleep',
    r'\sor\s', r'\sand\s', r'\|\|', r'&&',
    r'union', r'insert', r'update', r'delete', r'drop',
    r'load_file', r'into', r'outfile', r'dumpfile',
]


def waf(input_str):
    for pattern in BLACKLIST:
        if re.search(pattern, input_str, re.IGNORECASE):
            return True
    return False

# ============ 路由 ============


@app.route('/')
def index():
    q = request.args.get('q', '')

    # 如果有搜索参数，执行查询
    if q:
        if waf(q):
            return "🚫 Hacker detected!"

        conn = sqlite3.connect('challenge.db')
        c = conn.cursor()
        query = f"SELECT username FROM users WHERE username LIKE '{q}'"
        try:
            c.execute(query)
            results = c.fetchall()
            conn.close()
            if results:
                result_html = "<br>".join([f"👤 {row[0]}" for row in results])
            else:
                result_html = "No users found."
        except Exception as e:
            conn.close()
            result_html = ""
    else:
        result_html = ""

    return f'''
    <h1>🔍 User Search</h1>
    <form>
        <input type="text" name="q" placeholder="Search username..." value="{q}">
        <button type="submit">Search</button>
    </form>
    <p style="color:#666;font-size:12px;">Hint: There are some users, such as admin, guest, user1, user2</p>
    <hr>
    <div>{result_html}</div>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8006, debug=False)
