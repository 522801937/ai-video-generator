"""
字幕生成器 - 从 Edge TTS 词级时间戳生成 SRT 字幕
支持智能断句，确保每句长度适中、自然断点
"""
import os
import re
from pathlib import Path


# 中文标点断句规则
_SENTENCE_END = re.compile(r"[。！？；\n]")
_CLAUSE_PAUSE = re.compile(r"[，、：]")
# 可以自然断开的短语级停顿 (如 "的" "是" "在" 后)
_PHRASE_BOUNDARY = re.compile(r"(?<=[的了吗呢啊])")

# 每行字幕最大字符数
MAX_CHARS_PER_LINE = 22


def _smart_split(words: list, max_chars: int = MAX_CHARS_PER_LINE) -> list:
    """
    将词列表智能拆分为字幕行

    断句优先级:
    1. 句末标点 (。！？)
    2. 逗号类标点 (，、：)
    3. 达到 max_chars 时在最近的短语边界断开

    返回: [{"text": "...", "start": 0.0, "end": 5.0}, ...]
    """
    if not words:
        return []

    subtitles = []
    current_text = ""
    current_start = words[0]["start"]
    current_end = words[0]["end"]

    for i, w in enumerate(words):
        text = w["text"]
        is_last = (i == len(words) - 1)

        new_text = current_text + text
        current_end = w["end"]

        # 判断是否需要在此断开
        should_split = False

        if _SENTENCE_END.search(text):
            should_split = True
        elif _CLAUSE_PAUSE.search(text) and len(new_text) >= max_chars * 0.6:
            should_split = True
        elif len(new_text) >= max_chars:
            # 在最近的自然断点断开
            should_split = True

        if should_split and current_text.strip():
            subtitles.append({
                "text": current_text.strip(),
                "start": current_start,
                "end": current_end,
            })
            current_text = text
            current_start = w["start"]
        else:
            current_text = new_text

    # 最后一段
    if current_text.strip():
        subtitles.append({
            "text": current_text.strip(),
            "start": current_start,
            "end": current_end,
        })

    return subtitles


def _format_time(seconds: float) -> str:
    """秒 → SRT 时间格式 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt_from_words(
    all_words: list,
    output_path: str,
    max_chars: int = MAX_CHARS_PER_LINE,
) -> str:
    """
    从词级时间戳生成 SRT 字幕文件

    参数:
        all_words: [{"text": "...", "start": 0.0, "end": 0.5}, ...]
                   所有幻灯片的词合并列表，时间应已按音频拼接偏移
        output_path: SRT 输出路径
        max_chars: 每行最大字符数

    返回: output_path
    """
    subtitles = _smart_split(all_words, max_chars)

    lines = []
    for i, sub in enumerate(subtitles, 1):
        start_str = _format_time(sub["start"])
        end_str = _format_time(sub["end"])
        lines.append(str(i))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(sub["text"])
        lines.append("")  # 空行

    srt_content = "\n".join(lines)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    print(f"  [字幕] 生成 {len(subtitles)} 条字幕 → {output_path}")
    return output_path


def merge_slide_word_boundaries(
    slide_results: list,
    silence_between: float = 0.3,
) -> list:
    """
    合并多页幻灯片的词级时间戳，加上页面间静音偏移

    参数:
        slide_results: [{"meta": {"words": [...]}, "audio_path": "...", ...}, ...]
        silence_between: 幻灯片间静音间隔(秒)

    返回: 合并后带偏移的词列表
    """
    all_words = []
    time_offset = 0.0

    for i, result in enumerate(slide_results):
        meta = result.get("meta", {})
        words = meta.get("words", [])

        for w in words:
            all_words.append({
                "text": w["text"],
                "start": time_offset + w["start"],
                "end": time_offset + w["end"],
                "duration": w["duration"],
            })

        # 时间偏移: 本页时长 + 静音间隔
        if words:
            time_offset += words[-1]["end"] + silence_between

    return all_words


# ─── 简便接口 ──────────────────────────────────────────────────

def generate_srt(
    slide_results: list,
    output_path: str,
    silence_between: float = 0.3,
    max_chars: int = MAX_CHARS_PER_LINE,
):
    """
    一站式: 从 slide_results 生成 SRT 字幕

    参数:
        slide_results: TTS 引擎返回的结果列表
        output_path: SRT 文件路径
        silence_between: 幻灯片的静音间隔
        max_chars: 每行最大字符数
    """
    all_words = merge_slide_word_boundaries(slide_results, silence_between)
    return generate_srt_from_words(all_words, output_path, max_chars)


if __name__ == "__main__":
    # 测试
    print("=== 字幕生成测试 ===\n")

    # 模拟词数据
    test_words = [
        {"text": "你好", "start": 0.0, "end": 0.4, "duration": 0.4},
        {"text": "，", "start": 0.4, "end": 0.5, "duration": 0.1},
        {"text": "这是", "start": 0.5, "end": 0.8, "duration": 0.3},
        {"text": "一个", "start": 0.8, "end": 1.1, "duration": 0.3},
        {"text": "测试", "start": 1.1, "end": 1.4, "duration": 0.3},
        {"text": "。", "start": 1.4, "end": 1.5, "duration": 0.1},
        {"text": "人工智能", "start": 1.5, "end": 2.2, "duration": 0.7},
        {"text": "正在", "start": 2.2, "end": 2.5, "duration": 0.3},
        {"text": "改变", "start": 2.5, "end": 2.8, "duration": 0.3},
        {"text": "世界", "start": 2.8, "end": 3.1, "duration": 0.3},
        {"text": "。", "start": 3.1, "end": 3.2, "duration": 0.1},
    ]

    path = generate_srt_from_words(test_words, "test_output/test.srt")
    with open(path, "r", encoding="utf-8") as f:
        print(f.read())
