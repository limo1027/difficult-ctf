#!/usr/bin/env bash
# CTF Launcher (Linux/macOS)

echo "========================================"
echo "   CTF Launcher"
echo "========================================"
sudo apt update
PYVER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
sudo apt install -y python3-pip "python3.${PYVER}-venv"
# ============ 获取脚本所在目录（绝对路径） ============
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============ 构建环境 ============"
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    python3 -m venv "$SCRIPT_DIR/venv"
fi

VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

if [ -x "$VENV_PYTHON" ]; then
    echo "[VENV] $VENV_PYTHON"
else
    echo "[WARN] Virtual environment not found: $VENV_PYTHON"
    echo "[WARN] Using system Python"
    VENV_PYTHON="python3"
fi

# ============ 检查依赖 ============
if ! "$VENV_PYTHON" -c "import flask" >/dev/null 2>&1; then
    export PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
    "$VENV_PYTHON" -m pip install -r "$SCRIPT_DIR/install.txt"
fi

"$SCRIPT_DIR/venv/bin/playwright" install chromium

if [ ! -d "$SCRIPT_DIR/logs" ]; then
    mkdir -p "$SCRIPT_DIR/logs"
fi

echo
echo "Starting services..."

for i in $(seq 8001 8013); do
    if [ -f "$SCRIPT_DIR/$i/main.py" ]; then
        echo "[OK] Port $i"
        cd "$SCRIPT_DIR/$i" || continue
        nohup "$VENV_PYTHON" "main.py" > "$SCRIPT_DIR/logs/$i.log" 2>&1 &
        cd "$SCRIPT_DIR" || exit 1
    else
        echo "[NO] $i/main.py not found"
    fi
done

echo
echo "All services started."
echo "Logs saved to $SCRIPT_DIR/logs/"
read -rp "Press Enter to continue..."