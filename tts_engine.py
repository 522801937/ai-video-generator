"""
TTS 配音引擎 - 基于 Edge TTS 的神经网络语音合成
支持音色选择、语速调节、词级时间戳输出
"""
import asyncio
import json
import os
import re
from pathlib import Path

import edge_tts
from project_paths import find_ffmpeg

# 音色映射表
VOICE_MAP = {
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",
    "xiaoyi":   "zh-CN-XiaoyiNeural",
    "yunjian":  "zh-CN-YunjianNeural",
    "yunxi":    "zh-CN-YunxiNeural",
    "yunxia":   "zh-CN-YunxiaNeural",
    "yunyang":  "zh-CN-YunyangNeural",
    # 方言
    "xiaobei":  "zh-CN-liaoning-XiaobeiNeural",
    "xiaoni":   "zh-CN-shaanxi-XiaoniNeural",
}


def resolve_voice(voice_name: str) -> str:
    """解析音色名 → Edge TTS 的完整 Voice ID"""
    voice_name = voice_name.lower().strip()
    if voice_name in VOICE_MAP:
        return VOICE_MAP[voice_name]
    # 如果已经是完整名称 (如 zh-CN-XiaoxiaoNeural)
    if voice_name.startswith("zh-CN-"):
        return voice_name
    # fallback
    print(f"  [!] 未知音色 '{voice_name}'，使用默认 xiaoxiao")
    return VOICE_MAP["xiaoxiao"]


async def generate_audio(
    text: str,
    output_path: str,
    voice: str = "xiaoxiao",
    speed: str = "+10%",
) -> dict:
    """
    使用 Edge TTS 生成音频并记录词级时间戳

    参数:
        text: 要朗读的文本 (纯文本，不要传 SSML)
        output_path: 音频输出路径 (.mp3)
        voice: 音色名称
        speed: 语速，如 "+10%", "-5%", "+0%"

    返回:
        {
            "duration": float,          # 音频总时长(秒)
            "words": [
                {"text": "你好", "start": 0.0, "end": 0.25, "duration": 0.25},
                ...
            ]
        }
    """
    full_voice = resolve_voice(voice)

    # 关键：boundary="WordBoundary" 获取逐词时间戳
    communicate = edge_tts.Communicate(
        text, full_voice,
        rate=speed,
        boundary="WordBoundary",
    )
    submaker = edge_tts.SubMaker()

    # 收集音频数据和词边界
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            submaker.feed(chunk)

    # 写入音频文件
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(audio_data)

    # 解析词级时间戳 (SubMaker.cues 是 List[Subtitle])
    # Subtitle 有 .content (str), .start (timedelta), .end (timedelta)
    words = []
    for sub in submaker.cues:
        start_sec = sub.start.total_seconds()
        end_sec = sub.end.total_seconds()
        words.append({
            "text": sub.content.strip(),
            "start": start_sec,
            "end": end_sec,
            "duration": end_sec - start_sec,
        })

    # 总时长
    duration = words[-1]["end"] if words else 0.0

    # 保存元数据
    meta_path = output_path.replace(".mp3", "_meta.json")
    meta = {
        "voice": full_voice,
        "speed": speed,
        "text": text,
        "duration": duration,
        "word_count": len(words),
        "words": words,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


async def generate_silence(output_path: str, duration_sec: float = 0.3):
    """生成静音片段"""
    # edge-tts 不能生成静音，用 FFmpeg 生成
    import subprocess
    subprocess.run([
        find_ffmpeg(), "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration_sec),
        "-c:a", "libmp3lame", "-q:a", "9",
        output_path,
    ], capture_output=True, encoding='utf-8', errors='replace')
    return output_path


# ─── 批量生成 ──────────────────────────────────────────────────

async def generate_all_slides_audio(
    slides: list,
    output_dir: str,
    voice: str = "xiaoxiao",
    speed: str = "+10%",
    silence_between: float = 0.3,
) -> list:
    """
    为所有幻灯片生成配音

    参数:
        slides: [{"text": "...", "index": 0}, ...]
        output_dir: 输出目录
        voice: 音色
        speed: 语速
        silence_between: 幻灯片间的静音间隔(秒)

    返回:
        [
            {
                "index": 0,
                "audio_path": "...",
                "meta": {...},
                "silence_path": "...",
            },
            ...
        ]
    """
    results = []
    os.makedirs(output_dir, exist_ok=True)

    for i, slide in enumerate(slides):
        text = slide.get("text", "") or slide.get("title", "")
        if not text:
            continue

        print(f"  [TTS] 第 {i+1}/{len(slides)} 页: {text[:40]}...")

        audio_path = os.path.join(output_dir, f"audio_{i:02d}.mp3")
        meta = await generate_audio(text, audio_path, voice, speed)

        # 生成静音间隔
        silence_path = os.path.join(output_dir, f"silence_{i:02d}.mp3")
        await generate_silence(silence_path, silence_between)

        duration_str = f"{meta['duration']:.1f}s"
        print(f"        时长: {duration_str}, 词数: {meta['word_count']}")

        results.append({
            "index": i,
            "audio_path": audio_path,
            "meta": meta,
            "silence_path": silence_path,
        })

    return results


# ─── 试听 ──────────────────────────────────────────────────────

async def preview_voices(text: str, voices: list = None):
    """试听不同音色的朗读效果"""
    if voices is None:
        voices = ["xiaoxiao", "yunyang", "yunxi"]

    for v in voices:
        out = f"preview_{v}.mp3"
        print(f"生成试听: {v} → {out}")
        await generate_audio(text, out, v)
        print(f"  完成: {out}")


if __name__ == "__main__":
    async def test():
        print("=== TTS 测试 ===\n")
        meta = await generate_audio(
            "你好，这是一个测试。人工智能正在改变世界。",
            "test_tts.mp3",
            voice="xiaoxiao",
        )
        print(f"\n时长: {meta['duration']:.2f}s")
        print(f"词数: {meta['word_count']}")
        print(f"前5个词的时间戳:")
        for w in meta["words"][:5]:
            print(f"  {w['text']}: {w['start']:.2f}s - {w['end']:.2f}s")

    asyncio.run(test())
