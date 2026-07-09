"""
Playwright 渲染引擎
将场景列表编译为 HTML 页面 → 无头浏览器逐帧截图 → 输出 PNG 序列 → FFmpeg 合成 MP4
"""
import json
import os
import subprocess
from project_paths import find_ffmpeg
from pathlib import Path


# 场景 HTML 模板 — 高级动画引擎 (粒子系统 + 几何浮动 + 发光效果 + 弹性动画)
SCENE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Microsoft YaHei','PingFang SC','Noto Sans SC',sans-serif;overflow:hidden;background:#0a0a1a}

.scene{width:{W}px;height:{H}px;position:relative;overflow:hidden}

/* ─── Keyframes ─── */
@keyframes kenBurnsSlow{{0%{{transform:scale(1)}}100%{{transform:scale(1.03)}}}}
@keyframes kenBurns{{0%{{transform:scale(1)}}100%{{transform:scale(1.06)}}}}
@keyframes kenBurnsFast{{0%{{transform:scale(1)}}100%{{transform:scale(1.1)}}}}
@keyframes gradientFlow{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
@keyframes glowPulse{{0%,100%{{text-shadow:0 0 20px rgba(0,200,255,0.3),0 0 40px rgba(0,200,255,0.1),0 0 80px rgba(0,200,255,0.05)}}50%{{text-shadow:0 0 35px rgba(0,200,255,0.6),0 0 70px rgba(0,200,255,0.25),0 0 120px rgba(0,200,255,0.1)}}}}
@keyframes particleRise{{0%{{transform:translateY(0) scale(0);opacity:0}}15%{{opacity:1}}85%{{opacity:0.6}}100%{{transform:translateY(-110vh) scale(1);opacity:0}}}}
@keyframes rotateSlow{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
@keyframes lineGrow{{from{{width:0;opacity:0}}to{{width:160px;opacity:1}}}}
@keyframes shimmer{{0%{{background-position:-200% center}}100%{{background-position:200% center}}}}
@keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-15px)}}}}

/* Particle */
.particle{{position:absolute;border-radius:50%;pointer-events:none;z-index:0;animation:particleRise var(--dur) var(--delay) ease-in infinite;opacity:0}}
/* Floating geometry */
.geo{{position:absolute;pointer-events:none;z-index:0;animation:rotateSlow var(--dur) linear infinite;opacity:0.06}}
/* Content layer */
.content-layer{{position:relative;z-index:2;width:100%;height:100%}}

/* Shimmer text */
.shimmer-text{{
  background:linear-gradient(90deg,#fff 0%,#00c8ff 25%,#a78bfa 50%,#00c8ff 75%,#fff 100%);
  background-size:200% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;animation:shimmer 4s linear infinite;
}}
</style>
</head>
<body>
<div id="scene" class="scene"></div>
<script>
(function(){{
var SCENE = {scene_json};
var W = {W} - 0, H = {H} - 0;

// ─── Utilities ───
function anim(el, props, duration, delay, easing) {{
  setTimeout(function() {{
    Object.assign(el.style, props);
    var keys = Object.keys(props).filter(function(k) {{
      return k !== 'background' && k !== 'color' && k !== 'textShadow' && !k.startsWith('--');
    }});
    el.style.transition = keys.map(function(k) {{ return k + ' ' + duration + 'ms ' + (easing||'cubic-bezier(0.16,1,0.3,1)'); }}).join(',');
  }}, delay || 0);
}}

function fadeIn(el, d, delay) {{ anim(el, {{opacity:'1'}}, d||600, delay||0); }}
function scaleIn(el, d, delay) {{ anim(el, {{opacity:'1',transform:'scale(1)'}}, d||800, delay||0); }}
function slideUp(el, d, delay) {{ anim(el, {{opacity:'1',transform:'translateY(0)'}}, d||600, delay||0); }}
function slideIn(el, d, delay) {{ anim(el, {{opacity:'1',transform:'translate(0,0)'}}, d||700, delay||0); }}
function scaleBounce(el, d, delay) {{
  el.style.opacity = '0'; el.style.transform = 'scale(0.3)';
  setTimeout(function() {{
    el.style.transition = 'opacity '+(d*0.3)+'ms ease, transform '+d+'ms cubic-bezier(0.34,1.56,0.64,1)';
    el.style.opacity = '1'; el.style.transform = 'scale(1)';
  }}, delay||0);
}}

// ─── Background particles ───
function spawnParticles(count, colors) {{
  var scene = document.getElementById('scene');
  colors = colors || ['rgba(0,200,255,','rgba(120,140,255,','rgba(160,200,255,'];
  for (var i = 0; i < count; i++) {{
    var p = document.createElement('div');
    p.className = 'particle';
    var size = 2 + Math.random() * 5;
    var c = colors[Math.floor(Math.random() * colors.length)];
    p.style.cssText = 'left:'+(Math.random()*100)+'%;bottom:-'+(10+Math.random()*30)+'px;width:'+size+'px;height:'+size+'px;background:'+c+'0.5);box-shadow:0 0 '+(size*3)+'px '+c+'0.5);--dur:'+(3+Math.random()*7)+'s;--delay:-'+Math.random()*7+'s';
    scene.appendChild(p);
  }}
}}

// ─── Floating geometric shapes ───
function spawnGeo(count) {{
  var shapes = ['polygon(50% 0%,0% 100%,100% 100%)','circle(50% at 50% 50%)','polygon(0% 0%,100% 0%,100% 100%,0% 100%)'];
  var scene = document.getElementById('scene');
  for (var i = 0; i < count; i++) {{
    var g = document.createElement('div');
    g.className = 'geo';
    var s = 50 + Math.random() * 150;
    g.style.cssText = 'left:'+(Math.random()*90)+'%;top:'+(Math.random()*90)+'%;width:'+s+'px;height:'+s+'px;border:1px solid rgba(0,200,255,0.15);clip-path:'+shapes[Math.floor(Math.random()*3)]+';--dur:'+(15+Math.random()*30)+'s;'+(Math.random()>0.5?'animation-direction:reverse;':'');
    scene.appendChild(g);
  }}
}}

// ─── Gradient themes ───
var THEMES = {{
  deep: 'linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d1b2a 100%)',
  cosmic: 'linear-gradient(135deg, #0c0714 0%, #1a0a2e 30%, #0d1b3e 70%, #07101a 100%)',
  ocean: 'linear-gradient(135deg, #021b2e 0%, #0a3d5c 50%, #021a28 100%)',
  sunset: 'linear-gradient(135deg, #1a0a0a 0%, #3e1a2e 50%, #1a1228 100%)',
  forest: 'linear-gradient(135deg, #0a1a0a 0%, #1a3e1a 50%, #0d1a1a 100%)',
  aurora: 'linear-gradient(180deg, #0a0a1e 0%, #0d1e2e 30%, #0a1e1a 60%, #0a0a1e 100%)',
  slate: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #12121f 100%)',
  violet: 'linear-gradient(135deg, #0f0a1e 0%, #1e0a2e 50%, #1a0d2e 100%)'
}};

function getBg(s) {{
  if (s.config && s.config.bgImage) {{
    return 'url(\'' + s.config.bgImage.replace(/\\/g,'/') + '\') center/cover no-repeat';
  }}
  return THEMES[s.config && s.config.bgTheme] || THEMES.deep;
}}

// ─── Decorative accent line ───
function makeAccent(parent, delay) {{
  var line = document.createElement('div');
  line.style.cssText = 'width:0;height:3px;background:linear-gradient(90deg,transparent,#00c8ff,transparent);margin-bottom:36px;opacity:0;overflow:hidden';
  parent.appendChild(line);
  setTimeout(function() {{ line.style.width='160px'; line.style.opacity='1'; line.style.transition='width 0.8s cubic-bezier(0.16,1,0.3,1), opacity 0.4s'; }}, delay||0);
}}

// ─── Rendering ───
function render() {{
  var c = document.getElementById('scene');
  var s = SCENE;
  var bg = getBg(s);

  // Ambient effects for all scenes
  spawnParticles(30);
  spawnGeo(6);

  if (s.type === 'title') {{
    c.style.background = bg;
    c.style.backgroundSize = bg.indexOf('url')===0 ? 'cover' : '200% 200%';
    c.style.animation = 'kenBurns 15s ease-in-out infinite alternate' + (bg.indexOf('url')===-1 ? ', gradientFlow 10s ease infinite' : '');
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.alignItems = 'center'; c.style.justifyContent = 'center';

    makeAccent(c, 100);
    var accent = c.lastChild;

    var title = document.createElement('h1');
    title.textContent = s.title || s.text || '';
    title.style.cssText = 'font-size:76px;color:#fff;text-align:center;max-width:80%;line-height:1.2;text-shadow:0 2px 20px rgba(0,200,255,0.3);opacity:0;transform:scale(0.3);letter-spacing:2px';
    c.appendChild(title);
    setTimeout(function(){{ title.style.animation = 'glowPulse 3s ease-in-out 1s infinite'; }}, 1500);
    scaleBounce(title, 900, 400);

    if (s.text && s.title) {{
      var sub = document.createElement('p');
      sub.textContent = s.text;
      sub.style.cssText = 'font-size:28px;color:rgba(255,255,255,0.65);margin-top:28px;text-align:center;opacity:0;transform:translateY(40px);letter-spacing:1px';
      c.appendChild(sub);
      slideUp(sub, 600, 1300);
    }}
  }}

  else if (s.type === 'bullets') {{
    c.style.background = bg;
    c.style.backgroundSize = bg.indexOf('url')===0 ? 'cover' : '200% 200%';
    c.style.animation = 'kenBurns 18s ease-in-out infinite alternate' + (bg.indexOf('url')===-1 ? ', gradientFlow 12s ease infinite' : '');
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.justifyContent = 'center'; c.style.padding = '100px 160px';

    if (s.title) {{
      var h2 = document.createElement('h2');
      h2.textContent = s.title;
      h2.style.cssText = 'font-size:52px;font-weight:700;color:#00c8ff;margin-bottom:50px;opacity:0;transform:translateX(-60px);text-shadow:0 0 30px rgba(0,200,255,0.2)';
      c.appendChild(h2);
      slideIn(h2, 700, 0);
    }}

    var items = s.text.split(/[\\n；;]/).map(function(x) {{ return x.trim(); }}).filter(Boolean);
    var ul = document.createElement('ul');
    ul.style.cssText = 'list-style:none;padding:0';
    items.forEach(function(item, i) {{
      var li = document.createElement('li');
      li.innerHTML = '<span style="position:absolute;left:0;top:4px;font-size:22px;color:#00c8ff">▸</span>' + item;
      li.style.cssText = 'font-size:34px;color:#e6edf3;margin-bottom:24px;padding-left:40px;position:relative;opacity:0;transform:translateX(-30px);line-height:1.5';
      ul.appendChild(li);
      slideIn(li, 500, 600 + i * 280);
    }});
    c.appendChild(ul);
  }}

  else if (s.type === 'image') {{
    c.style.background = bg;
    c.style.backgroundSize = 'cover';
    c.style.animation = 'kenBurns 20s ease-in-out infinite alternate';
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.alignItems = 'center'; c.style.justifyContent = 'center';

    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:absolute;top:0;left:0;width:100%;height:100%;background:linear-gradient(180deg,rgba(0,0,0,0.45) 0%,rgba(0,0,0,0.75) 55%,rgba(0,0,0,0.85) 100%);z-index:1';
    c.appendChild(overlay);
    setTimeout(function(){{ overlay.style.opacity='1'; overlay.style.transition='opacity 1s'; }}, 0);
    if (overlay.style.opacity === '') overlay.style.opacity = '1';

    // Decorative top line
    var topLine = document.createElement('div');
    topLine.style.cssText = 'position:relative;z-index:2;width:0;height:2px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.4),transparent);margin-bottom:40px';
    c.appendChild(topLine);
    setTimeout(function(){{ topLine.style.width='200px'; topLine.style.transition='width 1s cubic-bezier(0.16,1,0.3,1)'; }}, 200);

    var caption = document.createElement('div');
    caption.style.cssText = 'position:relative;z-index:2;text-align:center;max-width:80%;opacity:0;transform:translateY(40px)';
    var html = '';
    if (s.keywords && s.keywords[0]) {{
      html += '<div style="font-size:18px;color:rgba(255,255,255,0.4);margin-bottom:20px;letter-spacing:3px;text-transform:uppercase">' + s.keywords[0] + '</div>';
    }}
    html += '<p style="font-size:38px;color:#fff;line-height:1.6;text-shadow:0 2px 15px rgba(0,0,0,0.6);font-weight:500">' + (s.text||'') + '</p>';
    caption.innerHTML = html;
    c.appendChild(caption);
    slideUp(caption, 800, 400);
  }}

  else if (s.type === 'outro') {{
    c.style.background = THEMES.cosmic;
    c.style.backgroundSize = '200% 200%';
    c.style.animation = 'kenBurnsSlow 12s ease-in-out infinite alternate, gradientFlow 8s ease infinite';
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.alignItems = 'center'; c.style.justifyContent = 'center';

    // Extra particles for outro
    spawnParticles(20, ['rgba(255,255,255,','rgba(180,200,255,','rgba(200,180,255,']);

    makeAccent(c, 100);

    var text = document.createElement('h1');
    text.textContent = s.title || s.text || '感谢观看';
    text.style.cssText = 'font-size:60px;color:#fff;text-align:center;opacity:0;transform:scale(0.3);font-weight:600;letter-spacing:4px';
    c.appendChild(text);
    scaleBounce(text, 1100, 600);
    setTimeout(function(){{ text.style.animation = 'glowPulse 4s ease-in-out 1.5s infinite'; }}, 1500);

    // Subtitle
    var sub = document.createElement('p');
    sub.textContent = s.text && s.title ? s.text : '';
    sub.style.cssText = 'font-size:24px;color:rgba(255,255,255,0.45);margin-top:20px;opacity:0;transform:translateY(20px);letter-spacing:2px';
    c.appendChild(sub);
    if (s.text && s.title) slideUp(sub, 500, 1600);
  }}

  else {{
    // Default / unknown scene type — simple centered text
    c.style.background = THEMES.deep;
    c.style.display = 'flex'; c.style.flexDirection = 'column';
    c.style.alignItems = 'center'; c.style.justifyContent = 'center';

    var t = document.createElement('h2');
    t.textContent = s.text || s.title || '';
    t.style.cssText = 'font-size:44px;color:#e6edf3;text-align:center;max-width:75%;opacity:0;transform:translateY(30px);line-height:1.5';
    c.appendChild(t);
    slideUp(t, 600, 200);
  }}
}}

window.addEventListener('DOMContentLoaded', function() {{
  setTimeout(render, 80);
}});
}})();
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
