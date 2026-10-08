@echo off
chcp 65001 >nul

echo ========================================
echo    CTF Launcher
echo ========================================

REM ============ 获取脚本所在目录（绝对路径） ============
set SCRIPT_DIR=%~dp0
REM 去掉末尾的反斜杠
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%

echo ============ 构建环境 ============ 
if not exist %SCRIPT_DIR%\venv python -m venv venv


set VENV_PYTHON=%SCRIPT_DIR%\venv\Scripts\python.exe

if exist "%VENV_PYTHON%" (
    echo [VENV] %VENV_PYTHON%
) else (
    echo [WARN] Virtual environment not found: %VENV_PYTHON%
    echo [WARN] Using system Python
    set VENV_PYTHON=python
)

REM ============ 检查依赖 ============
%VENV_PYTHON% -c "import flask" >nul 2>&1
if errorlevel 1 (
%VENV_PYTHON% -m pip install -r install.txt
)
venv\Scripts\playwright install chromium
if not exist "%SCRIPT_DIR%\logs" mkdir "%SCRIPT_DIR%\logs"

echo.
echo Starting services...

for /l %%i in (8001,1,8013) do (
    if exist "%SCRIPT_DIR%\%%i\main.py" (
        echo [OK] Port %%i
        cd /d "%SCRIPT_DIR%\%%i"
        start /b %VENV_PYTHON% "main.py" > "%SCRIPT_DIR%\logs\%%i.log" 2>&1
        cd /d "%SCRIPT_DIR%"
    ) else (
        echo [NO] %%i/main.py not found
    )
)

echo.
echo All services started.
echo Logs saved to %SCRIPT_DIR%\logs\
pause