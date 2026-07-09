"""
Playwright 渲染引擎
将场景列表编译为 HTML 页面 → 无头浏览器逐帧截图 → 输出 PNG 序列 → FFmpeg 合成 MP4
"""
import json
import os
import subprocess
from project_paths import find_ffmpeg
from pathlib import Path


# 场景 HTML 模板 — 精简版动画引擎 (CSS transitions, 不依赖 anime.js)
SCENE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Microsoft YaHei','PingFang SC',sans-serif;overflow:hidden}}
.scene{{width:{W}px;height:{H}px;position:relative;overflow:hidden}}
@keyframes kenBurns{{
  0%{{transform:scale(1)}}
  100%{{transform:scale(1.06)}}
}}
</style>
</head>
<body>
<div id="scene" class="scene"></div>
<script>
const SCENE = {scene_json};
const W = {W}, H = {H};

// 动画工具
function anim(el, props, duration, delay) {{
  setTimeout(() => {{
    Object.assign(el.style, props);
    el.style.transition = Object.keys(props)
      .filter(k => k !== 'background' && k !== 'color')
      .map(k => `${{k}} ${{duration}}ms ease-out`)
      .join(', ');
  }}, delay || 0);
}}

function fadeIn(el, d, delay) {{ anim(el, {{opacity: '1'}}, d || 800, delay || 0); }}
function scaleIn(el, d, delay) {{ anim(el, {{opacity: '1', transform: 'scale(1)'}}, d || 800, delay || 0); }}
function slideIn(el, d, delay) {{ anim(el, {{opacity: '1', transform: 'translate(0,0)'}}, d || 700, delay || 0); }}

function renderScene() {{
  const c = document.getElementById('scene');
  const s = SCENE;

  // 背景样式：优先用爬取的图片，否则用渐变
  const bgStyle = s.config && s.config.bgImage
    ? `url('${{s.config.bgImage.replace(/\\\\/g,'/')}}') center/cover no-repeat`
    : 'linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d1b2a 100%)';

  if (s.type === 'title') {{
    c.style.background = bgStyle;
    c.style.animation = 'kenBurns 15s ease-in-out infinite alternate';
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.alignItems = 'center'; c.style.justifyContent = 'center';

    const deco = document.createElement('div');
    deco.style.cssText = 'width:160px;height:3px;background:linear-gradient(90deg,transparent,#00c8ff,transparent);margin-bottom:40px;opacity:0';
    c.appendChild(deco);
    fadeIn(deco, 600, 0);

    const title = document.createElement('h1');
    title.textContent = s.title || s.text;
    title.style.cssText = 'font-size:72px;color:#fff;text-align:center;max-width:80%;text-shadow:0 2px 20px rgba(0,200,255,0.3);opacity:0;transform:scale(0.3)';
    c.appendChild(title);
    scaleIn(title, 800, 300);

    if (s.text && s.title) {{
      const sub = document.createElement('p');
      sub.textContent = s.text;
      sub.style.cssText = 'font-size:28px;color:rgba(255,255,255,0.7);margin-top:24px;text-align:center;opacity:0;transform:translateY(40px)';
      c.appendChild(sub);
      slideIn(sub, 600, 1200);
    }}
  }}

  else if (s.type === 'bullets') {{
    c.style.background = bgStyle;
    c.style.animation = 'kenBurns 18s ease-in-out infinite alternate';
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.justifyContent = 'center'; c.style.padding = '100px 140px';

    if (s.title) {{
      const h2 = document.createElement('h2');
      h2.textContent = s.title;
      h2.style.cssText = 'font-size:48px;color:#00c8ff;margin-bottom:40px;opacity:0;transform:translateX(-60px)';
      c.appendChild(h2);
      slideIn(h2, 600, 0);
    }}

    const items = s.text.split(/[\\n；;]/).map(x => x.trim()).filter(Boolean);
    const ul = document.createElement('ul');
    ul.style.cssText = 'list-style:none;padding:0';
    items.forEach((item, i) => {{
      const li = document.createElement('li');
      li.innerHTML = '<span style="position:absolute;left:0;color:#00c8ff">●</span>' + item;
      li.style.cssText = 'font-size:32px;color:#e6edf3;margin-bottom:20px;padding-left:40px;position:relative;opacity:0;transform:translateY(30px)';
      ul.appendChild(li);
      slideIn(li, 500, 500 + i * 250);
    }});
    c.appendChild(ul);
  }}

  else if (s.type === 'image') {{
    c.style.background = bgStyle;
    c.style.animation = 'kenBurns 20s ease-in-out infinite alternate';
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.alignItems = 'center'; c.style.justifyContent = 'center';

    // 暗色遮罩提升文字可读性
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;background:linear-gradient(180deg,rgba(0,0,0,0.5) 0%,rgba(0,0,0,0.7) 100%);z-index:1';
    c.appendChild(overlay);

    const caption = document.createElement('div');
    caption.style.cssText = 'position:relative;z-index:2;text-align:center;max-width:80%;opacity:0;transform:translateY(40px)';
    if (s.keywords?.[0]) {{
      caption.innerHTML = '<div style="font-size:18px;color:rgba(255,255,255,0.5);margin-bottom:16px">🔍 ' + s.keywords[0] + '</div>';
    }}
    caption.innerHTML += '<p style="font-size:36px;color:#fff;line-height:1.6;text-shadow:0 2px 10px rgba(0,0,0,0.5)">' + s.text + '</p>';
    c.appendChild(caption);
    slideIn(caption, 800, 300);
  }}

  else if (s.type === 'outro') {{
    c.style.background = 'linear-gradient(135deg, #0a0a2e 0%, #0d1b2a 100%)';
    c.style.animation = 'kenBurns 12s ease-in-out infinite alternate';
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.alignItems = 'center'; c.style.justifyContent = 'center';

    const line = document.createElement('div');
    line.style.cssText = 'width:120px;height:3px;background:linear-gradient(90deg,transparent,#00c8ff,transparent);margin-bottom:32px;opacity:0';
    c.appendChild(line);
    fadeIn(line, 600, 0);

    const text = document.createElement('h1');
    text.textContent = s.title || s.text || '感谢观看';
    text.style.cssText = 'font-size:56px;color:#fff;text-align:center;opacity:0;transform:scale(0.3)';
    c.appendChild(text);
    scaleIn(text, 1000, 500);
  }}
}}

window.addEventListener('DOMContentLoaded', () => {{
  setTimeout(renderScene, 100);
}});
</script>
</body>
</html>"""


def build_scene_html(slide: dict, width: int = 1920, height: int = 1080) -> str:
    """将单个场景 JSON 编译为自包含 HTML 页面"""
    return SCENE_HTML_TEMPLATE.format(
        W=width, H=height,
        scene_json=json.dumps(slide, ensure_ascii=False),
    )


def _get_chromium_launch_args() -> dict:
    """获取 Chromium 启动参数 — 优先用系统 Chrome/Edge，避免打包 Chromium"""
    import sys

    # 1. 环境变量指定路径
    env_path = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
    if env_path and os.path.exists(env_path):
        return {"headless": True, "executable_path": env_path}

    # 2. 用系统已安装的 Chrome
    chrome_paths = []
    if sys.platform == "win32":
        chrome_paths = [
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    else:
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
        ]

    for p in chrome_paths:
        if os.path.exists(p):
            return {"headless": True, "executable_path": p}

    # 3. 回退：让 Playwright 自己找
    return {"headless": True}


def render_scene_frames(
    slide: dict,
    output_dir: str,
    duration: float = 4.0,
    resolution: tuple = (1920, 1080),
    fps: int = 30,
) -> list[str]:
    """
    用 Playwright 渲染一个场景的每一帧为 PNG

    返回: [frame_0001.png, frame_0002.png, ...]
    """
    from playwright.sync_api import sync_playwright

    W, H = resolution
    html = build_scene_html(slide, W, H)
    html_path = os.path.join(output_dir, f"scene_{slide.get('type', 'unknown')}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    os.makedirs(output_dir, exist_ok=True)
    frame_paths = []

    with sync_playwright() as p:
        launch_args = _get_chromium_launch_args()
        browser = p.chromium.launch(**launch_args)
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(f"file:///{html_path.replace(chr(92), '/')}")

        total_frames = int(duration * fps)
        for frame_idx in range(total_frames):
            frame_path = os.path.join(output_dir, f"frame_{frame_idx:04d}.png")
            page.screenshot(path=frame_path)
            frame_paths.append(frame_path)
            page.wait_for_timeout(int(1000 / fps))

        browser.close()

    return frame_paths


def frames_to_video(
    frame_dir: str,
    output_path: str,
    fps: int = 30,
    crf: int = 18,
) -> str:
    """用 FFmpeg 将 PNG 帧序列合成为 MP4"""
    cmd = [
        find_ffmpeg(), "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frame_dir, "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg frame-to-video failed: {result.stderr[-500:]}")
    return output_path
