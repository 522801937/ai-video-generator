"""
PyInstaller 打包脚本
用法: python build.py
输出: dist/AI视频生成器.exe
"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent


def build_frontend():
    """构建前端静态文件"""
    web_dir = PROJECT_DIR / "web"
    if not (web_dir / "node_modules").exists():
        print("[Build] 安装前端依赖...")
        subprocess.run(["npm", "install"], cwd=str(web_dir), check=True)

    print("[Build] 构建前端...")
    subprocess.run(["npm", "run", "build"], cwd=str(web_dir), check=True)

    dist_dir = web_dir / "dist"
    if dist_dir.exists():
        print(f"[Build] 前端构建完成: {dist_dir}")
    else:
        raise RuntimeError("前端构建失败: dist 目录不存在")


def build_exe():
    """PyInstaller 打包"""
    print("[Build] PyInstaller 打包...")

    # 确保 playwright 浏览器已安装
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                   check=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AI视频生成器",
        "--onefile",
        "--console",
        "--add-data", f"web/dist{';'}web/dist",
        "--add-data", f"renderer{';'}renderer",
        "--add-data", f"server{';'}server",
        "--add-data", f"tts_engine.py{';'}.",
        "--add-data", f"subtitle_generator.py{';'}.",
        "--add-data", f"video_utils.py{';'}.",
        "--add-binary", f"ffi.dll{';'}.",
        "--add-binary", f"ffmpeg.exe{';'}.",
        "--exclude-module", "matplotlib",
        "--exclude-module", "pandas",
        "--exclude-module", "numba",
        "--exclude-module", "scipy",
        "--exclude-module", "PIL",
        "--exclude-module", "moviepy",
        "--exclude-module", "imageio",
        "--exclude-module", "imageio_ffmpeg",
        "--exclude-module", "tcl",
        "--exclude-module", "tkinter",
        "--exclude-module", "_tkinter",
        "--exclude-module", "sqlalchemy",
        "--exclude-module", "sqlite3",
        "--exclude-module", "openpyxl",
        "--exclude-module", "lxml",
        "--exclude-module", "jinja2",
        "--exclude-module", "rich",
        "--exclude-module", "pygments",
        "--exclude-module", "pytest",
        "--exclude-module", "setuptools",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "fastapi",
        "--hidden-import", "playwright",
        "--hidden-import", "edge_tts",
        "app.py",
    ]

    subprocess.run(cmd, cwd=str(PROJECT_DIR), check=True)
    print(f"[Build] 打包完成: {PROJECT_DIR}/dist/AI视频生成器.exe")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-frontend", action="store_true",
                        help="跳过前端构建 (如果已手动构建)")
    args = parser.parse_args()

    if not args.skip_frontend:
        build_frontend()
    build_exe()
