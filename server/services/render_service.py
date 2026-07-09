"""渲染服务 — 复用 V1 的 TTS 和字幕模块"""
import asyncio
import os
from project_paths import get_data_dir

PROJECT_DIR = get_data_dir()


async def generate_audio_for_slides(slides: list[dict], output_dir: str,
                                     voice: str = "xiaoxiao", speed: str = "+10%") -> list[dict]:
    """调用 V1 的 TTS 引擎为每页生成配音"""
    import sys
    sys.path.insert(0, str(PROJECT_DIR))
    from tts_engine import generate_all_slides_audio

    results = await generate_all_slides_audio(slides, output_dir, voice, speed)
    return results


def generate_subtitles(slide_results: list[dict], output_dir: str) -> str:
    """调用 V1 的字幕生成器"""
    import sys
    sys.path.insert(0, str(PROJECT_DIR))
    from subtitle_generator import generate_srt

    srt_path = os.path.join(output_dir, "subtitles.srt")
    generate_srt(slide_results, srt_path)
    return srt_path
