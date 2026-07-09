"""
桌面壳入口 — PyInstaller 打包入口
启动后端 → 打开浏览器 → 保持运行
"""
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path


def find_chromium() -> str | None:
    """查找系统中可用的 Chromium/Chrome"""
    candidates = []
    if sys.platform == 'win32':
        import glob
        # Playwright Chromium
        local_app = os.path.expandvars(r"%LOCALAPPDATA%")
        pw_patterns = [
            os.path.join(local_app, "ms-playwright", "chromium-*"),
        ]
        for pat in pw_patterns:
            for m in sorted(glob.glob(pat), reverse=True):
                chrome_exe = os.path.join(m, "chrome.exe")
                if os.path.exists(chrome_exe):
                    return chrome_exe

        # System Chrome / Edge
        for prog in [
            r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe",
            r"%PROGRAMFILES(x86)%\Google\Chrome\Application\chrome.exe",
            r"%PROGRAMFILES(x86)%\Microsoft\Edge\Application\msedge.exe",
        ]:
            expanded = os.path.expandvars(prog)
            if os.path.exists(expanded):
                return expanded

    return None


def main():
    print("=" * 50)
    print("  AI 科普视频生成器 V2")
    print("=" * 50)
    print()

    # 查找浏览器
    browser_path = find_chromium()
    if browser_path:
        os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"] = browser_path
        print(f"[Browser] {browser_path}")

    # 启动 FastAPI 服务器 (在后台线程)
    def run_server():
        import uvicorn
        from server.main import app
        uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 等待服务器就绪
    time.sleep(2)

    # 打开浏览器
    url = "http://127.0.0.1:8765"
    print(f"[App] 打开浏览器: {url}")
    webbrowser.open(url)

    print("[App] 服务器运行中，关闭此窗口即可退出")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[App] 正在退出...")


if __name__ == "__main__":
    main()
