@echo off
chcp 65001 >nul
title AI 视频生成器 - 安装依赖

echo.
echo ============================================
echo    AI 视频自动生成器 - 环境安装
echo ============================================
echo.

echo [1/3] 检查 Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

echo [2/3] 检查 FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未找到 FFmpeg，视频合成功能将不可用
    echo 下载地址: https://ffmpeg.org/download.html
) else (
    ffmpeg -version | findstr "version"
)
echo.

echo [3/3] 安装 Python 依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [警告] 清华源安装失败，尝试默认源...
    pip install -r requirements.txt
)

echo.
echo ============================================
echo    安装完成！
echo    请运行 "制作视频.bat" 开始使用
echo ============================================
pause
