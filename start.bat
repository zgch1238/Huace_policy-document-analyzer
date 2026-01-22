@echo off
chcp 65001 >nul
echo ================================================
echo   华测导航政策文档分析助手 - 启动脚本
echo ================================================
echo.

REM 安装依赖
echo [1/4] 检查并安装 Python 依赖...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✓ 依赖安装完成
) else (
    echo     ✗ 依赖安装失败，请手动运行: pip install -r requirements.txt
    pause
    exit /b 1
)
echo.

REM 检查 OpenCode
echo [2/4] 检查 OpenCode 服务...
curl -s http://127.0.0.1:4096/session >nul 2>&1
if %errorlevel% equ 0 (
    echo     ✓ OpenCode 服务已运行 (端口 4096)
) else (
    echo     ⚠ OpenCode 服务未运行
    echo     请在新终端中运行: opencode serve --port 4096
    echo.
)
echo.

REM 启动 Flask
echo [3/4] 启动 Flask Web 应用...
echo     访问地址: http://localhost:5000
echo.
start "" http://localhost:5000
python app.py

echo.
echo [4/4] 应用已停止
pause
