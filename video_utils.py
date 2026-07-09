"""视频工具 — 纯 FFmpeg 实现 (替代 V1 的 video_composer，无 moviepy 依赖)"""
import os
import subprocess
from pathlib import Path
from project_paths import find_ffmpeg


def concat_audio_files(audio_paths: list, silence_paths: list, output_path: str):
    """将多个 MP3 文件与静音间隔拼接成一个完整音频文件"""
    concat_list = []
    for i, (audio, silence) in enumerate(zip(audio_paths, silence_paths)):
        concat_list.append(audio)
        if i < len(audio_paths) - 1:
            concat_list.append(silence)

    list_path = output_path + ".txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for p in concat_list:
            f.write(f"file '{p.replace(chr(92), '/')}'\n")

    result = subprocess.run([
        find_ffmpeg(), "-y", "-f", "concat", "-safe", "0",
        "-i", list_path, "-c:a", "libmp3lame", "-q:a", "2",
        output_path,
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')
    os.remove(list_path)

    if result.returncode == 0:
        print(f"  [音频合并] -> {output_path}")
    else:
        print(f"  [!] 音频合并失败: {result.stderr[-200:]}")

    return output_path


def burn_subtitles(
    video_path: str,
    srt_path: str,
    output_path: str,
    font_path: str = "C:/Windows/Fonts/msyh.ttc",
    font_size: int = 18,
) -> str:
    """用 FFmpeg 将 SRT 字幕烧录到视频中"""
    srt_path_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    font_path_escaped = font_path.replace("\\", "/").replace(":", "\\:")

    style = (
        f"FontName={Path(font_path).stem},"
        f"FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"Outline=2,"
        f"Shadow=1,"
        f"MarginV=20,"
        f"Alignment=2"
    )

    filter_str = f"subtitles='{srt_path_escaped}':force_style='{style}'"

    cmd = [
        find_ffmpeg(), "-y",
        "-i", video_path,
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-c:a", "copy",
        output_path,
    ]

    print(f"  [字幕烧录] FFmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')

    if result.returncode != 0:
        print(f"  [!] 字幕烧录失败，使用无字幕版本:")
        print(f"      {result.stderr[-300:]}")
        import shutil
        shutil.copy(video_path, output_path)
    else:
        print(f"  [OK] 字幕烧录完成: {output_path}")

    return output_path
