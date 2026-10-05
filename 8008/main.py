import os
from flask import Flask, request, render_template_string
import random
import io
import contextlib

app = Flask(__name__)
app.secret_key = "ssti_challenge_secret"

# ==================== 随机种子 + Flag ====================
if os.path.exists("flag.txt"):
    SEED = open("flag.txt").read()
else:
    SEED = random.random()
with open("flag.txt", mode='w') as f:
    f.write(SEED)


class Flag:
    def __init__(self):
        random.seed(SEED)
        self.FLAG = "ctfhub{" + \
            "".join(random.choices("1234567890ABCDEF", k=20)) + "}"
        random.seed()


FLAG_OBJ = Flag()
# 关键：FLAG_OBJ 没有传递给模板！

# ==================== 沙箱执行 ====================


def safe_render(template, **kwargs):
    safe_builtins = {
        'print': print,
        'range': range,
        'len': len,
        'str': str,
        'int': int,
        'float': float,
        'bool': bool,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'zip': zip,
        'enumerate': enumerate,
        'sum': sum,
        'max': max,
        'min': min,
        'abs': abs,
        'round': round,
        'sorted': sorted,
        'reversed': reversed,
        'chr': chr,
        'ord': ord,
        'hex': hex,
        'oct': oct,
        'bin': bin,
        'type': type,
        'isinstance': isinstance,
        'issubclass': issubclass,
    }

    safe_globals = {
        '__builtins__': safe_builtins,
        # 注意：FLAG_OBJ 不在里面！
    }

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            result = render_template_string(template, **kwargs)
        return output.getvalue() + result
    except Exception as e:
        return f"❌ Error: {e}"

# ==================== 路由 ====================


@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    template = "Hello {{ name }}!"
    name = "world"

    if request.method == 'POST':
        template = request.form.get('template', 'Hello {{ name }}!')
        name = request.form.get('name', 'world')
        result = safe_render(template, name=name)

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>🧪 SSTI Playground</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
            }}
            .container {{
                background: #111;
                border: 2px solid #00ff00;
                border-radius: 10px;
                padding: 40px;
                width: 800px;
                max-width: 95%;
            }}
            h1 {{
                color: #ff4444;
                text-align: center;
                margin-bottom: 10px;
                font-size: 24px;
            }}
            .sub {{
                color: #666;
                text-align: center;
                font-size: 13px;
                margin-bottom: 25px;
            }}
            .demo {{
                background: #1a1a1a;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 20px;
                font-size: 13px;
                color: #888;
            }}
            .demo span {{ color: #ff8844; }}
            form {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            textarea {{
                background: #0a0a0a;
                border: 1px solid #00ff00;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                padding: 12px;
                border-radius: 5px;
                font-size: 14px;
                resize: vertical;
                min-height: 120px;
            }}
            textarea:focus {{
                outline: none;
                box-shadow: 0 0 20px rgba(0,255,0,0.1);
            }}
            .row {{
                display: flex;
                gap: 10px;
            }}
            .row input {{
                flex: 1;
                background: #0a0a0a;
                border: 1px solid #00ff00;
                color: #00ff00;
                padding: 10px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }}
            .row input:focus {{
                outline: none;
                box-shadow: 0 0 20px rgba(0,255,0,0.1);
            }}
            button {{
                padding: 10px 30px;
                background: #00ff00;
                color: #000;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                cursor: pointer;
                transition: 0.3s;
            }}
            button:hover {{
                background: #00cc00;
                box-shadow: 0 0 30px rgba(0,255,0,0.3);
            }}
            .output {{
                margin-top: 20px;
                background: #0a0a0a;
                border: 1px solid #333;
                border-radius: 5px;
                padding: 15px;
                min-height: 60px;
                white-space: pre-wrap;
                word-break: break-all;
                font-size: 14px;
                max-height: 300px;
                overflow-y: auto;
            }}
            .output::-webkit-scrollbar {{ width: 6px; }}
            .output::-webkit-scrollbar-track {{ background: #1a1a1a; }}
            .output::-webkit-scrollbar-thumb {{ background: #00ff00; border-radius: 3px; }}
            .hint {{
                margin-top: 15px;
                color: #666;
                font-size: 12px;
                text-align: center;
                border-top: 1px solid #222;
                padding-top: 15px;
            }}
            .hint a {{ color: #00ff00; text-decoration: none; }}
            .hint a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 SSTI Playground</h1>
            <p class="sub">🔒 Jinja2 Template Engine</p>

            <div class="demo">
                💡 <span>Example:</span> <code style="color:#00ff00;">Hello {{ name }}!</code>
            </div>

            <form method="post">
                <textarea name="template" placeholder="Enter your Jinja2 template here...">{template}</textarea>
                <div class="row">
                    <input type="text" name="name" placeholder="name variable (optional)" value="{name}">
                    <button type="submit">▶ Render</button>
                </div>
            </form>

            <div class="output">
                {result if result else '<span style="color:#444;">Click "Render" to see the output...</span>'}
            </div>

            <div class="hint">
                💡 The flag is in a <strong>global variable</strong>, but it's not passed to the template.
                <br>
                💡 Can you find a way to <strong>access it</strong>?
            </div>
        </div>
        <script>
            document.querySelector('textarea').focus();
        </script>
    </body>
    </html>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8008, debug=False)
