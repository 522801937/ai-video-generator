#!/usr/bin/env python3
"""
AI 视频自动生成器
输入主题 + 内容 → 自动爬图 → 生成幻灯片 → TTS 配音 → 字幕 → 合成 MP4

用法:
    python generate_video.py --config my_video.json
    python generate_video.py --title "深度学习入门" --content script.txt
    python generate_video.py --preview xiaoxiao --text "试听文本"
    python generate_video.py --interactive

AI 辅助模式 (在 Claude 对话中使用):
    from generate_video import ai_make_video
    ai_make_video(title="标题", slides=[...], voice="xiaoxiao")
"""
import argparse
import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

# Fix Windows GBK encoding for emoji output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 设置项目根目录
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

from slide_generator import generate_all_slides
from tts_engine import generate_all_slides_audio, resolve_voice, generate_audio
from subtitle_generator import generate_srt
from video_composer import compose_video, burn_subtitles


# ─── 配置处理 ──────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    """加载并验证 JSON 配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # 设置默认值
    config.setdefault("resolution", [1920, 1080])
    config.setdefault("fps", 30)
    config.setdefault("speed", "+10%")
    config.setdefault("output", "output")

    # 验证 slides
    if "slides" not in config or not config["slides"]:
        raise ValueError("配置文件中缺少 'slides' 字段或为空")

    for i, slide in enumerate(config["slides"]):
        slide.setdefault("type", "content")
        slide.setdefault("keywords", [])
        slide.setdefault("background", "auto")
        slide.setdefault("gif", "none")

        if slide["type"] == "title":
            slide.setdefault("title", config.get("title", "未命名"))
            slide.setdefault("subtitle", "")
        elif slide["type"] == "content":
            if "text" not in slide:
                raise ValueError(f"第 {i+1} 页 content 类型缺少 'text' 字段")

    return config


def load_content_from_txt(txt_path: str, title: str) -> dict:
    """
    从纯文本文件读取内容，每行或每个空行分隔的段落作为一页

    txt 格式:
        # 标题行 (可选，作为 title slide)
        第一页内容...
        (空行)
        第二页内容...
        ...
    """
    with open(txt_path, "r", encoding="utf-8") as f:
        raw = f.read().strip()

    # 按空行分割段落
    paragraphs = [p.strip() for p in raw.split("\n\n") if p.strip()]

    slides = []
    first_is_title = False

    for i, para in enumerate(paragraphs):
        lines = para.split("\n")

        if i == 0 and lines[0].startswith("#"):
            # 标题页：第一行是 # 标题，后续行是内容
            title_text = lines[0].lstrip("#").strip()
            body_text = " ".join(lines[1:]).strip() if len(lines) > 1 else ""

            slides.append({
                "type": "title",
                "title": title_text,
                "subtitle": body_text or title,
                "keywords": [title_text, title],
                "background": "auto",
            })
            first_is_title = True
        else:
            text = " ".join(lines).strip()
            slides.append({
                "type": "content",
                "text": text,
                "keywords": _extract_keywords(text),
                "background": "auto",
            })

    return {
        "title": title,
        "voice": "xiaoxiao",
        "speed": "+10%",
        "resolution": [1920, 1080],
        "fps": 30,
        "output": "output",
        "slides": slides,
    }


def _extract_keywords(text: str, max_kw=5) -> list:
    """从文本中简单提取关键词 (取较长词汇)"""
    import re
    # 提取中文词 (2-4字) 和英文词 (3+字母)
    words = re.findall(r"[一-鿿]{2,4}|[a-zA-Z]{3,}", text)
    # 按长度排序，取前几个
    seen = set()
    keywords = []
    for w in sorted(words, key=len, reverse=True):
        if w.lower() not in seen:
            keywords.append(w)
            seen.add(w.lower())
        if len(keywords) >= max_kw:
            break
    return keywords if keywords else ["technology"]


# ─── 主流程 ────────────────────────────────────────────────────

async def generate(config: dict):
    """
    完整视频生成流程

    1. 爬取素材 (图片 + GIF)
    2. 生成幻灯片
    3. 生成配音
    4. 生成字幕
    5. 视频合成
    6. 烧录字幕
    """
    title = config["title"]
    slides = config["slides"]
    resolution = tuple(config["resolution"])
    voice = config["voice"]
    speed = config["speed"]

    # 输出目录
    safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)
    safe_title = safe_title.strip().replace(" ", "_")[:50]
    out_dir = Path(config["output"]) / safe_title
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*60}")
    print(f"  视频生成: {title}")
    print(f"  输出目录: {out_dir}")
    print(f"  页数: {len(slides)} | 音色: {voice} | 分辨率: {resolution}")
    print(f"{'='*60}\n")

    # ── Step 1: 准备素材 ──
    print("📷 Step 1/5: 准备素材...")
    bg_paths = [None] * len(slides)
    gif_paths = [None] * len(slides)

    # ── Step 2: 生成幻灯片 ──
    print(f"\n🎨 Step 2/5: 生成幻灯片...")
    slide_paths = generate_all_slides(slides, str(out_dir), resolution, bg_paths)

    # ── Step 3: 生成配音 ──
    print(f"\n🔊 Step 3/5: 生成配音 (edge-tts, {voice})...")
    slide_results = await generate_all_slides_audio(
        slides, str(out_dir), voice=voice, speed=speed, silence_between=0.3
    )

    # ── Step 4: 生成字幕 ──
    print(f"\n📝 Step 4/5: 生成字幕...")
    srt_path = str(out_dir / "subtitles.srt")
    generate_srt(slide_results, srt_path, silence_between=0.3)

    # ── Step 5: 视频合成 ──
    print(f"\n🎬 Step 5/5: 视频合成 (MoviePy + FFmpeg)...")

    audio_files = [r["audio_path"] for r in slide_results]

    temp_video = str(out_dir / "temp_video.mp4")
    compose_video(
        slide_paths=slide_paths,
        audio_paths=audio_files,
        output_path=temp_video,
        gif_paths=gif_paths,
        resolution=resolution,
        fps=config["fps"],
        crossfade=0.4,
    )

    # 烧录字幕
    final_video = str(out_dir / f"{safe_title}.mp4")
    burn_subtitles(temp_video, srt_path, final_video)

    # 清理临时文件
    if os.path.exists(temp_video):
        os.remove(temp_video)

    # ── 输出摘要 ──
    total_duration = sum(r["meta"]["duration"] for r in slide_results)
    file_size = os.path.getsize(final_video) / 1024 / 1024

    print(f"\n{'='*60}")
    print(f"  ✅ 视频生成完成！")
    print(f"  📁 {final_video}")
    print(f"  ⏱  总时长: {int(total_duration // 60)}分{total_duration % 60:.0f}秒")
    print(f"  📦 文件大小: {file_size:.1f} MB")
    print(f"{'='*60}\n")

    return final_video


# ─── AI 辅助模式 ──────────────────────────────────────────────

def ai_make_video(title: str, slides: list, voice: str = "xiaoxiao",
                  speed: str = "+10%", output: str = "output"):
    """
    AI 辅助制作视频 (在 Claude 对话中调用)

    用法: 在对话中告诉我主题，我写好稿子后自动生成视频

    参数:
        title: 视频标题
        slides: 幻灯片列表 [{"type":"title","title":"...","subtitle":"...","keywords":[...]},
                           {"type":"content","text":"...","keywords":[...]}, ...]
        voice: 音色 (xiaoxiao/yunyang/yunxi)
        speed: 语速
        output: 输出根目录

    返回: 生成的视频文件路径
    """
    config = {
        "title": title,
        "voice": voice,
        "speed": speed,
        "resolution": [1920, 1080],
        "fps": 30,
        "output": output,
        "slides": slides,
    }

    # 保存配置文件
    safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)
    safe_title = safe_title.strip().replace(" ", "_")[:30]
    config_path = PROJECT_DIR / f"ai_config_{safe_title}.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"[AI] 配置已保存: {config_path.name}")
    print(f"[AI] 开始生成视频...")

    # 运行生成
    return asyncio.run(generate(config))


def show_menu():
    """主菜单 (Python 实现，避免 bat 编码问题)"""
    while True:
        print()
        print("=" * 50)
        print("     AI 视频自动生成器")
        print("=" * 50)
        print()
        print("  [1] 从配置文件生成视频")
        print("  [2] 从文本文件快速生成")
        print("  [3] 创建新的配置模板")
        print("  [4] 交互式制作向导")
        print("  [5] 试听配音音色")
        print("  [6] 查看可用音色")
        print("  [7] 清空素材缓存")
        print("  [0] 退出")
        print()
        print("=" * 50)

        try:
            choice = input("请选择 (0-7): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if choice == "1":
            config_file = input("配置文件路径 (如 config.example.json): ").strip()
            if config_file:
                if os.path.exists(config_file):
                    asyncio.run(generate(load_config(config_file)))
                else:
                    print(f"[错误] 文件不存在: {config_file}")
            input("按回车继续...")

        elif choice == "2":
            title = input("视频标题: ").strip()
            content_file = input("内容文件路径: ").strip()
            if title and content_file and os.path.exists(content_file):
                asyncio.run(generate(load_content_from_txt(content_file, title)))
            else:
                print("[错误] 标题或文件路径无效")
            input("按回车继续...")

        elif choice == "3":
            name = input("配置模板名称 (默认 my_video): ").strip() or "my_video"
            if not name.endswith(".json"):
                name += ".json"
            template = {
                "title": name.replace(".json", ""),
                "voice": "xiaoxiao", "speed": "+10%",
                "resolution": [1920, 1080], "fps": 30, "output": "output",
                "slides": [
                    {"type": "title", "title": "在这里写标题", "subtitle": "副标题",
                     "keywords": ["关键词1"], "background": "auto"},
                    {"type": "content", "text": "在这里写正文内容...",
                     "keywords": ["关键词2"], "background": "auto"},
                ]
            }
            with open(name, "w", encoding="utf-8") as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            print(f"[OK] 模板已创建: {name}")
            input("按回车继续...")

        elif choice == "4":
            interactive_mode()

        elif choice == "5":
            text = input("试听文本: ").strip()
            voice = input("音色 (xiaoxiao/yunyang/yunxi, 默认 xiaoxiao): ").strip() or "xiaoxiao"
            if text:
                out = PROJECT_DIR / f"preview_{voice}.mp3"
                asyncio.run(generate_audio(text, str(out), voice))
                print(f"[OK] 试听文件: {out}")
            input("按回车继续...")

        elif choice == "6":
            print()
            print("  代码       名称      风格")
            print("  --------  --------  --------------")
            for code, desc in [
                ("xiaoxiao", "晓晓 (女)   温暖自然 [默认]"),
                ("yunyang",  "云扬 (男)   专业可靠"),
                ("yunxi",    "云希 (男)   阳光活泼"),
                ("yunjian",  "云健 (男)   激情澎湃"),
                ("xiaoyi",   "晓伊 (女)   活泼可爱"),
                ("yunxia",   "云夏 (男)   可爱童趣"),
            ]:
                print(f"  {code:10s} {desc}")
            input("\n按回车继续...")

        elif choice == "7":
            print("缓存已清空。")
            input("按回车继续...")

        elif choice == "0":
            print("再见!")
            break

        else:
            print("无效选项，请重新选择")


def interactive_mode():
    """交互式制作向导 (无 AI 辅助时使用)"""
    print("\n" + "=" * 50)
    print("  交互式视频制作向导")
    print("=" * 50)
    print()
    print("提示: 如果有 Claude/GPT 辅助，直接说 '帮我做一个关于 XX 的视频'")
    print("      我会自动写稿、分页、生成 — 无需手动操作")
    print()

    title = input("视频标题: ").strip()
    if not title:
        print("[错误] 标题不能为空")
        return

    voice = input("配音音色 (xiaoxiao/yunyang/yunxi，默认 xiaoxiao): ").strip()
    if not voice:
        voice = "xiaoxiao"

    print()
    print("请输入每页内容 (输入空行结束):")
    print("  格式: # 标题    → 作为标题页")
    print("        正文内容  → 作为内容页")
    print()

    lines = []
    while True:
        try:
            line = input()
            lines.append(line)
        except EOFError:
            break
        if lines and lines[-1] == "" and lines[-2] == "":
            break

    content = "\n".join(lines).strip()
    if not content:
        print("[错误] 内容不能为空")
        return

    # 保存为临时文件
    import tempfile
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.write(content)
    tmp.close()

    asyncio.run(generate(load_content_from_txt(tmp.name, title)))
    os.unlink(tmp.name)


# ─── CLI ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI 视频自动生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate_video.py --config my_video.json
  python generate_video.py --title "深度学习入门" --content script.txt
  python generate_video.py --preview xiaoxiao --text "测试语音"
  python generate_video.py --clear-cache
        """,
    )

    parser.add_argument("--config", "-c", help="JSON 配置文件路径")
    parser.add_argument("--title", "-t", help="视频标题 (与 --content 配合)")
    parser.add_argument("--content", help="文本内容文件路径 (.txt)")
    parser.add_argument("--voice", "-v", default="xiaoxiao",
                        help="配音音色 (xiaoxiao/yunyang/yunxi/yunjian/xiaoyi)")
    parser.add_argument("--speed", "-s", default="+10%", help="语速 (+10%%, -5%%, +0%%)")
    parser.add_argument("--output", "-o", default="output", help="输出根目录")
    parser.add_argument("--preview", action="store_true",
                        help="试听音色 (需配合 --text)")
    parser.add_argument("--text", help="试听文本")
    parser.add_argument("--clear-cache", action="store_true",
                        help="清空素材缓存")
    parser.add_argument("--list-voices", action="store_true",
                        help="列出可用音色")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="交互式制作向导")
    parser.add_argument("--menu", "-m", action="store_true",
                        help="显示主菜单 (推荐双击 run.bat 使用)")
    parser.add_argument("--new", nargs="?", const="my_video",
                        help="创建新的配置模板 (可选: 配置文件名)")

    args = parser.parse_args()

    # --menu: 显示主菜单
    if args.menu:
        show_menu()
        return

    # --new: 创建配置模板
    if args.new:
        name = args.new if args.new.endswith(".json") else args.new + ".json"
        template = {
            "title": name.replace(".json", ""),
            "voice": "xiaoxiao",
            "speed": "+10%",
            "resolution": [1920, 1080],
            "fps": 30,
            "output": "output",
            "slides": [
                {
                    "type": "title",
                    "title": "在这里写标题",
                    "subtitle": "在这里写副标题",
                    "keywords": ["关键词1", "关键词2"],
                    "background": "auto"
                },
                {
                    "type": "content",
                    "text": "在这里写第一页正文内容。AI Agent是能够自主感知环境、制定计划并执行任务的智能体。",
                    "keywords": ["关键词3", "关键词4"],
                    "background": "auto",
                    "gif": "auto"
                },
                {
                    "type": "content",
                    "text": "在这里写第二页正文内容。支持多页，每页自动匹配背景图和配音。",
                    "keywords": ["关键词5"],
                    "background": "auto"
                }
            ]
        }
        tmpl_path = PROJECT_DIR / name
        with open(tmpl_path, "w", encoding="utf-8") as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        print(f"[OK] 配置模板已创建: {tmpl_path}")
        print(f"     编辑这个文件，填入你的内容后运行:")
        print(f"     python generate_video.py --config {name}")
        return

    # --interactive
    if args.interactive:
        interactive_mode()
        return

    # --clear-cache
    if args.clear_cache:
        clear_cache()
        print("✅ 缓存已清空")
        return

    # --list-voices
    if args.list_voices:
        print("🎤 可用中文音色:")
        print("  代码       名称      风格")
        print("  ────────  ────────  ──────────────")
        for code, full in [
            ("xiaoxiao", "晓晓 (女)   温暖自然 ⭐"),
            ("yunyang",  "云扬 (男)   专业可靠"),
            ("yunxi",    "云希 (男)   阳光活泼"),
            ("yunjian",  "云健 (男)   激情澎湃"),
            ("xiaoyi",   "晓伊 (女)   活泼可爱"),
            ("yunxia",   "云夏 (男)   可爱童趣"),
        ]:
            print(f"  {code:10s} {full}")
        return

    # --preview
    if args.preview:
        if not args.text:
            print("❌ 试听需要 --text 参数")
            sys.exit(1)
        async def preview():
            for v in args.voice.split(","):
                out = PROJECT_DIR / f"preview_{v.strip()}.mp3"
                await generate_audio(args.text, str(out), v.strip(), args.speed)
                print(f"  → {out}")
        asyncio.run(preview())
        return

    # 读取配置
    if args.config:
        config = load_config(args.config)
        config["voice"] = args.voice
        config["speed"] = args.speed
        config["output"] = args.output
    elif args.title and args.content:
        config = load_content_from_txt(args.content, args.title)
        config["voice"] = args.voice
        config["speed"] = args.speed
        config["output"] = args.output
    else:
        parser.print_help()
        print("\n❌ 请提供 --config 或 (--title + --content)")
        sys.exit(1)

    # 执行生成
    asyncio.run(generate(config))


if __name__ == "__main__":
    main()
