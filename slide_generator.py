"""
幻灯片生成器 - 基于 Pillow 渲染视频幻灯片
支持标题页和内容页两种风格，自动字号适配、换行
"""
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── 字体配置 ──────────────────────────────────────────────────

# Windows 中文字体优先级
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑粗体
    "C:/Windows/Fonts/simhei.ttf",     # 黑体
    "C:/Windows/Fonts/simsun.ttc",     # 宋体
    "C:/Windows/Fonts/simkai.ttf",     # 楷体
]

_TITLE_FONT_PATH = None
_BODY_FONT_PATH = None


def _find_fonts():
    """查找可用字体"""
    global _TITLE_FONT_PATH, _BODY_FONT_PATH
    if _TITLE_FONT_PATH:
        return

    found = [f for f in _FONT_CANDIDATES if os.path.exists(f)]

    if not found:
        # Pillow 默认字体 (不支持中文，这里只是 fallback)
        _TITLE_FONT_PATH = _BODY_FONT_PATH = None
        print("  [!] 警告: 未找到中文字体，文字可能显示为方框")
        return

    # 微软雅黑粗体 → 标题, 普通 → 正文
    bold_path = "C:/Windows/Fonts/msyhbd.ttc"
    normal_path = "C:/Windows/Fonts/msyh.ttc"

    _TITLE_FONT_PATH = bold_path if os.path.exists(bold_path) else found[0]
    _BODY_FONT_PATH = normal_path if os.path.exists(normal_path) else found[0]

    print(f"  [字体] 标题: {os.path.basename(_TITLE_FONT_PATH)}, "
          f"正文: {os.path.basename(_BODY_FONT_PATH)}")


# ─── 颜色方案 ──────────────────────────────────────────────────

WHITE = (255, 255, 255, 255)
WHITE_90 = (255, 255, 255, 230)
DARK_OVERLAY = (0, 0, 0, 160)
ACCENT = (0, 200, 255, 255)       # 青色
ACCENT_DIM = (0, 150, 200, 200)


def _load_bg(resolution, bg_path=None, blur_radius=0):
    """
    加载背景图，缩放并裁剪到目标分辨率
    返回 RGBA 模式的 Image
    """
    W, H = resolution

    if bg_path and os.path.exists(bg_path):
        img = Image.open(bg_path).convert("RGBA")
    else:
        # 纯色渐变背景
        img = Image.new("RGBA", (W, H), (15, 20, 30, 255))
        # 简单径向渐变
        draw = ImageDraw.Draw(img)
        for r in range(max(W, H), 0, -4):
            alpha = int(40 * (1 - r / max(W, H)))
            draw.ellipse([W//2 - r, H//2 - r, W//2 + r, H//2 + r],
                         fill=(30, 50, 80, alpha))
        return img

    # 缩放填充满画面 (cover 模式)
    iw, ih = img.size
    scale = max(W / iw, H / ih)
    new_w, new_h = int(iw * scale), int(ih * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 居中裁剪
    left = (new_w - W) // 2
    top = (new_h - H) // 2
    img = img.crop((left, top, left + W, top + H))

    if blur_radius > 0:
        img = img.filter(ImageFilter.GaussianBlur(blur_radius))

    return img


def _draw_overlay(draw, W, H, alpha=180):
    """绘制从上到下的渐变暗色遮罩，提升文字可读性"""
    steps = 40
    bar_h = H // steps
    for i in range(steps):
        a = int(alpha * (0.4 + 0.6 * i / steps))  # 上方更暗
        y = i * bar_h
        draw.rectangle([0, y, W, y + bar_h + 1], fill=(0, 0, 0, a))


def _draw_accent_line(draw, x, y, width, height=3):
    """在文字下方画一条装饰线"""
    draw.rectangle([x, y, x + width, y + height], fill=ACCENT)


def _wrap_text(text, font, max_width, draw):
    """智能换行 - 中文优先按字符换行，英文按单词换行"""
    lines = []
    # 先按已有的换行符分割
    paragraphs = text.replace("\\n", "\n").split("\n")

    for para in paragraphs:
        if not para.strip():
            lines.append("")
            continue

        # 按字符逐个尝试
        current_line = ""
        for char in para:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = char
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)

    return lines


def _fit_font_size(text, font_path, max_width, max_height, draw, min_size=30, max_size=100):
    """二分查找最佳字号，使文字恰好填满可用区域"""
    lo, hi = min_size, max_size
    best = min_size

    for _ in range(15):  # 最多 15 次迭代
        mid = (lo + hi) // 2
        font = ImageFont.truetype(font_path, mid)
        lines = _wrap_text(text, font, max_width, draw)

        line_height = mid * 1.4
        total_h = line_height * len(lines)

        if total_h <= max_height and mid > best:
            best = mid

        if total_h > max_height:
            hi = mid - 1
        else:
            lo = mid + 1

    return best


# ─── 公开接口 ──────────────────────────────────────────────────

def generate_slide(
    text: str,
    output_path: str,
    resolution=(1920, 1080),
    bg_path=None,
    slide_type="content",
    title="",
    subtitle="",
    blur_bg=8,
) -> str:
    """
    生成单张幻灯片图片

    参数:
        text: 内容文本 (content 类型)
        output_path: 输出 PNG 路径
        resolution: (宽, 高)
        bg_path: 背景图路径 (可为 None)
        slide_type: "title" | "content"
        title: 标题 (title 类型 + content 类型的顶部标题)
        subtitle: 副标题 (title 类型)
        blur_bg: 背景模糊半径

    返回: output_path
    """
    _find_fonts()
    W, H = resolution

    # 加载背景 + 模糊
    img = _load_bg(resolution, bg_path, blur_radius=blur_bg)
    draw = ImageDraw.Draw(img)

    # 暗色遮罩
    overlay_alpha = 160 if slide_type == "title" else 140
    _draw_overlay(draw, W, H, overlay_alpha)

    # 标题页布局
    if slide_type == "title":
        title_font_size = _fit_font_size(
            title, _TITLE_FONT_PATH, W - 200, H * 0.3, draw, min_size=60, max_size=120
        )
        title_font = ImageFont.truetype(_TITLE_FONT_PATH, title_font_size)

        # 标题居中偏上
        title_lines = _wrap_text(title, title_font, W - 200, draw)
        line_h = title_font_size * 1.5
        total_h = line_h * len(title_lines)
        start_y = int(H * 0.38 - total_h / 2)

        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            tw = bbox[2] - bbox[0]
            x = (W - tw) // 2
            # 文字阴影
            draw.text((x + 2, start_y + 2), line, font=title_font, fill=(0, 0, 0, 160))
            draw.text((x, start_y), line, font=title_font, fill=WHITE)
            start_y += line_h

        # 装饰线
        line_y = start_y + 20
        _draw_accent_line(draw, W // 2 - 120, line_y, 240, 4)

        # 副标题
        if subtitle:
            sub_font_size = min(title_font_size * 0.45, 48)
            sub_font = ImageFont.truetype(_BODY_FONT_PATH, int(sub_font_size))
            bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
            sw = bbox[2] - bbox[0]
            sx = (W - sw) // 2
            draw.text((sx + 1, line_y + 40), subtitle, font=sub_font, fill=(0, 0, 0, 120))
            draw.text((sx, line_y + 40), subtitle, font=sub_font, fill=WHITE_90)

    # 内容页布局
    else:
        # 如果有标题，在顶部偏左显示
        top_offset = 100
        if title:
            title_font = ImageFont.truetype(_TITLE_FONT_PATH, 56)
            draw.text((120, top_offset + 2), title, font=title_font, fill=(0, 0, 0, 120))
            draw.text((120, top_offset), title, font=title_font, fill=ACCENT)
            _draw_accent_line(draw, 120, top_offset + 70, 80, 3)
            text_top = top_offset + 110
        else:
            text_top = int(H * 0.18)

        max_text_h = H - text_top - 120

        # 自适应字号
        body_font_size = _fit_font_size(
            text, _BODY_FONT_PATH, W - 240, max_text_h, draw, min_size=38, max_size=72
        )
        body_font = ImageFont.truetype(_BODY_FONT_PATH, body_font_size)

        lines = _wrap_text(text, body_font, W - 240, draw)
        line_h = body_font_size * 1.55

        # 左对齐，垂直居中
        total_h = line_h * len(lines)
        y = text_top + (max_text_h - total_h) // 2

        for line in lines:
            if not line.strip():
                y += line_h * 0.5
                continue
            # 文字阴影
            draw.text((122, y + 2), line, font=body_font, fill=(0, 0, 0, 160))
            draw.text((120, y), line, font=body_font, fill=WHITE)
            y += line_h

    # 底部水印线
    _draw_accent_line(draw, W // 2 - 40, H - 40, 80, 2)

    # 保存
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img = img.convert("RGB")
    img.save(output_path, "PNG", optimize=True)

    return output_path


def generate_all_slides(slides: list, output_dir: str, resolution=(1920, 1080),
                        bg_paths: list = None) -> list:
    """
    批量生成幻灯片

    参数:
        slides: [{"type":"title"|"content", "text":"...", "title":"...", ...}, ...]
        output_dir: 输出目录
        resolution: 分辨率
        bg_paths: 每页的背景图路径列表 (可为 None)

    返回: [slide_path_0, slide_path_1, ...]
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    for i, slide in enumerate(slides):
        bg = bg_paths[i] if bg_paths and i < len(bg_paths) else None
        out = os.path.join(output_dir, f"slide_{i:02d}.png")

        slide_type = slide.get("type", "content")

        print(f"  [幻灯片] 第 {i+1}/{len(slides)} 页 "
              f"({slide_type})" + (f": {slide.get('title', slide.get('text', ''))[:30]}..." if slide_type == "title" else ""))

        generate_slide(
            text=slide.get("text", ""),
            output_path=out,
            resolution=resolution,
            bg_path=bg,
            slide_type=slide_type,
            title=slide.get("title", ""),
            subtitle=slide.get("subtitle", ""),
        )
        paths.append(out)

    return paths


if __name__ == "__main__":
    # 测试
    print("=== 幻灯片生成测试 ===\n")
    test_slides = [
        {"type": "title", "title": "测试标题", "subtitle": "副标题在这里"},
        {"type": "content", "title": "内容标题", "text": "这是一段测试内容文本，用来验证自动换行和字号适配功能是否正常工作。人工智能正在改变世界。"},
    ]
    paths = generate_all_slides(test_slides, "test_output")
    print(f"\n生成 {len(paths)} 张幻灯片:")
    for p in paths:
        print(f"  {p}")
