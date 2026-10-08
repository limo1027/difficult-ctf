import os
import io
import time
import random
import platform
import subprocess
import threading
import queue
import re
import fnmatch
import contextlib

from flask import Flask, request, render_template_string, session

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

IS_WINDOWS = platform.system() == "Windows"

# ==================== Flag ====================
if os.path.exists("flag.txt"):
    FLAG = open("flag.txt").read().strip()
else:
    FLAG = "ctfhub{" + "".join(random.choices("0123456789ABCDEF", k=20)) + "}"
    with open("flag.txt", "w") as f:
        f.write(FLAG)

# ==================== 文件系统 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CTF_DIR = os.path.join(BASE_DIR, "ctf_8009")
FLAG_FILE = os.path.join(CTF_DIR, "flag.txt")

os.makedirs(CTF_DIR, exist_ok=True)

with open(FLAG_FILE, "w") as f:
    f.write(f"🏁 {FLAG}\n")

with open(os.path.join(CTF_DIR, "hello.txt"), "w") as f:
    f.write("Hello, world!\nTry to find the flag.")

with open(os.path.join(CTF_DIR, "secret.txt"), "w") as f:
    f.write("This is a secret. But not the flag.")

with open(os.path.join(CTF_DIR, "hint.py"), "w") as f:
    f.write("""
# Hint: The flag is in flag.txt
# But you can't read it directly!
print("Try to escape the sandbox!")
""")

with open(os.path.join(CTF_DIR, "notes.txt"), "w") as f:
    f.write("Nothing interesting here.")

# ==================== 持久 Shell ====================


class PersistentCmd:
    def __init__(self, cwd=None):
        self.cwd = cwd or CTF_DIR
        self.process = None
        self.output_queue = queue.Queue()
        self._start()

    def _start(self):
        if IS_WINDOWS:
            shell_cmd = "cmd.exe"
        else:
            shell_cmd = "/bin/sh"

        self.process = subprocess.Popen(
            shell_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=self.cwd,
            bufsize=0,
        )
        self.reader_thread = threading.Thread(
            target=self._reader, daemon=True)
        self.reader_thread.start()

    def _reader(self):
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            self.output_queue.put(line)

    def execute(self, cmd):
        self.process.stdin.write(cmd + "\n")
        self.process.stdin.flush()
        time.sleep(0.15)  # 给 shell 一点时间输出

        output = []
        while not self.output_queue.empty():
            output.append(self.output_queue.get())

        result = "".join(output)
        return result.strip() or "执行完成"

    def close(self):
        if self.process:
            self.process.terminate()
            self.process = None


shell = PersistentCmd(CTF_DIR)

# ==================== Python 沙箱 ====================


def run_python_code(code):
    """在受限沙箱中执行 Python 代码"""
    blacklist = [
        "__import__", "exec", "eval", "compile",
        "open", "file", "__builtins__", "__globals__",
        "subprocess", "os", "system", "popen",
        "__class__", "__bases__", "__subclasses__",
        "__closure__", "cell_contents", "__dict__",
        "globals", "locals", "vars", "dir",
        "getattr", "setattr", "hasattr", "__getattr__",
        "FLAG", "flag", "mro", "__mro__",
    ]
    for word in blacklist:
        if word in code:
            return f"🚫 Access denied: '{word}' is blocked"

    safe_builtins = {
        "print": print,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "range": range,
        "zip": zip,
        "enumerate": enumerate,
        "sum": sum,
        "max": max,
        "min": min,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "reversed": reversed,
        "chr": chr,
        "ord": ord,
        "hex": hex,
        "oct": oct,
        "bin": bin,
        "type": type,
        "isinstance": isinstance,
        "issubclass": issubclass,
    }

    safe_globals = {
        "__builtins__": safe_builtins,
        "__name__": "__main__",
        "CTF_DIR": CTF_DIR,
    }

    def fake_open(path, *args, **kwargs):
        raise PermissionError(f"Permission denied: {path}")

    safe_globals["open"] = fake_open

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, safe_globals)
        return output.getvalue() or "✅ 执行完成"
    except Exception as e:
        return f"❌ 错误: {e}"

# ==================== 通配符展开 + 权限检查 ====================


def expand_wildcards(pattern):
    """展开 shell 通配符，返回匹配的文件列表"""
    try:
        all_files = os.listdir(CTF_DIR)
    except Exception:
        return []
    matched = []
    for f in all_files:
        if fnmatch.fnmatch(f, pattern):
            matched.append(f)
    return matched


def check_flag_access(file_pattern):
    """检查文件模式是否匹配 flag.txt（包括通配符展开）"""
    # 直接包含 flag 字样
    if re.search(r"flag", file_pattern, re.IGNORECASE):
        return True

    # 通配符展开后是否命中 flag
    matched = expand_wildcards(file_pattern)
    for f in matched:
        if re.search(r"flag", f, re.IGNORECASE):
            return True

    return False

# ==================== 命令执行 ====================


def execute_real_command(cmd):
    """在持久 shell 中执行命令（有限制）"""
    parts = cmd.split()
    if not parts:
        return ""

    base_cmd = parts[0].lower()

    if IS_WINDOWS:
        allowed_commands = ["dir", "cd", "type", "echo", "whoami"]
        read_cmd = "type"
    else:
        allowed_commands = ["ls", "cd", "cat", "echo", "whoami", "pwd"]
        read_cmd = "cat"

    if base_cmd not in allowed_commands:
        return f"Command not allowed: {base_cmd}"

    # 读文件命令：检查参数是否命中 flag
    if base_cmd == read_cmd and len(parts) > 1:
        for arg in parts[1:]:
            if check_flag_access(arg):
                return f"{read_cmd}: {arg} - Permission denied"

    return shell.execute(cmd)

# ==================== 命令解析 ====================


def execute_command(cmd):
    if not cmd.strip():
        return ""

    if cmd == "help":
        if IS_WINDOWS:
            return """
Available commands (Windows):
  dir                  List files
  cd <dir>             Change directory
  type <file>          Read file (flag.txt is protected)
  whoami               Show current user
  python <code>        Execute Python code (sandboxed!)
  help                 Show this message
  clear                Clear screen
  exit                 Exit terminal

💡 The flag is in flag.txt, but you can't read it directly.
💡 type flag.txt will return "Permission denied"
💡 Python's open() is also blocked.
💡 Try to find a way around it!
"""
        else:
            return """
Available commands (Linux):
  ls                   List files
  cd <dir>             Change directory
  cat <file>           Read file (flag.txt is protected)
  whoami               Show current user
  pwd                  Show current directory
  python <code>        Execute Python code (sandboxed!)
  help                 Show this message
  clear                Clear screen
  exit                 Exit terminal

💡 The flag is in flag.txt, but you can't read it directly.
💡 cat flag.txt will return "Permission denied"
💡 Python's open() is also blocked.
💡 Try to find a way around it!
"""

    if cmd == "clear":
        return "CLEAR"

    if cmd == "exit":
        return "EXIT"

    if cmd == "python":
        return "Python 3.11.0 (sandboxed)\n>>> 输入 'python <code>' 执行代码"

    if cmd.startswith("python "):
        code = cmd[7:].strip()
        return run_python_code(code)

    return execute_real_command(cmd)


# ==================== HTML 模板 ====================
TERMINAL = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🧑‍💻 CTF Terminal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0a;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .terminal {
            width: 900px;
            height: 600px;
            background: #111;
            border: 2px solid #00ff00;
            border-radius: 10px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 50px rgba(0,255,0,0.1);
        }
        .header {
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #666;
        }
        .header .user { color: #00ff00; }
        .header .path { color: #ff8844; }
        .output {
            flex: 1;
            overflow-y: auto;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-all;
            margin-bottom: 10px;
        }
        .output::-webkit-scrollbar { width: 6px; }
        .output::-webkit-scrollbar-track { background: #1a1a1a; }
        .output::-webkit-scrollbar-thumb { background: #00ff00; border-radius: 3px; }
        .input-line {
            display: flex;
            align-items: center;
            border-top: 1px solid #333;
            padding-top: 10px;
        }
        .prompt { color: #00ff00; margin-right: 10px; font-size: 14px; }
        .input-line input {
            flex: 1;
            background: transparent;
            border: none;
            color: #00ff00;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            outline: none;
        }
        .hint {
            color: #666;
            font-size: 11px;
            margin-top: 8px;
            border-top: 1px solid #1a1a1a;
            padding-top: 8px;
        }
        .hint a { color: #00ff00; text-decoration: none; }
        .hint a:hover { text-decoration: underline; }
    </style>
</head>
<body>
<div class="terminal">
    <div class="header">
        <span>🧑‍💻 <span class="user">guest</span>@ctf-{{ platform }}</span>
        <span class="path">{{ path }}</span>
    </div>
    <div class="output" id="output">
        {% for line in history %}
            <div>{{ line }}</div>
        {% endfor %}
        {% if output %}
            <div>{{ output|safe }}</div>
        {% endif %}
    </div>
    <div class="input-line">
        <span class="prompt">$</span>
        <form method="post" style="flex:1;display:flex;">
            <input type="text" name="cmd" autofocus>
        </form>
    </div>
    <div class="hint">
        💡 Type <strong>help</strong> |
        💡 <a href="/reset">Reset session</a>
    </div>
</div>
<script>
    const output = document.getElementById('output');
    output.scrollTop = output.scrollHeight;
    document.querySelector('input[name="cmd"]').focus();
</script>
</body>
</html>
"""

PLATFORM_NAME = "windows" if IS_WINDOWS else "linux"

# ==================== Flask 路由 ====================


@app.route("/", methods=["GET", "POST"])
def index():
    if "history" not in session:
        session["history"] = []
        session["path"] = CTF_DIR

    if request.method == "POST":
        cmd = request.form.get("cmd", "").strip()
        if cmd:
            history = session.get("history", [])
            history.append(f"$ {cmd}")

            result = execute_command(cmd)

            if result == "CLEAR":
                session["history"] = []
                session["path"] = CTF_DIR
                return render_template_string(
                    TERMINAL, history=[], output=None,
                    path=CTF_DIR, platform=PLATFORM_NAME)

            if result == "EXIT":
                session.clear()
                return render_template_string(
                    TERMINAL, history=[], output=None,
                    path=CTF_DIR, platform=PLATFORM_NAME)

            history.append(result)
            session["history"] = history
            session["path"] = CTF_DIR
            return render_template_string(
                TERMINAL, history=history, output=None,
                path=CTF_DIR, platform=PLATFORM_NAME)

    return render_template_string(
        TERMINAL, history=session.get("history", []),
        output=None, path=session.get("path", CTF_DIR),
        platform=PLATFORM_NAME)


@app.route("/reset")
def reset():
    session.clear()
    return render_template_string(
        TERMINAL, history=[], output=None,
        path=CTF_DIR, platform=PLATFORM_NAME)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8009, debug=False)
