@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ================================================
echo   AI 科普视频生成器 V2
echo ================================================
echo.

REM 检查并构建前端
if not exist "web\dist\index.html" (
    echo [1/3] 构建前端...
    cd web
    call npm run build
    cd ..
) else (
    echo [1/3] 前端已就绪
)

echo [2/3] 启动服务...
start "" http://127.0.0.1:8765

echo [3/3] 打开浏览器...
echo.
echo 服务运行中... 关闭此窗口即可退出
echo ================================================
echo.

python -m server.main

pause
