"""
视频合成器 - 基于 MoviePy 合成最终视频
Ken Burns 效果、转场、GIF 画中画、音频同步
"""
import os
import subprocess
from pathlib import Path

import numpy as np
from moviepy import (
    ImageClip,
    VideoClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    vfx,
)


def _ken_burns_clip(image_path, duration, scale_from=1.0, scale_to=1.06):
    """
    创建带 Ken Burns 效果 (缓慢缩放) 的图片片段

    参数:
        image_path: 图片路径
        duration: 显示时长(秒)
        scale_from: 起始缩放比例
        scale_to: 结束缩放比例
    """
    clip = ImageClip(image_path, duration=duration)

    # 使用 transform 实现缩放动画
    def make_frame(t):
        # 线性插值缩放
        progress = t / duration if duration > 0 else 0
        scale = scale_from + (scale_to - scale_from) * progress

        # 获取当前帧
        frame = clip.get_frame(t)

        h, w = frame.shape[:2]
        new_w, new_h = int(w * scale), int(h * scale)
        from PIL import Image
        img = Image.fromarray(frame)
        img = img.resize((new_w, new_h), Image.LANCZOS)

        # 居中裁剪回原始尺寸
        left = (new_w - w) // 2
        top = (new_h - h) // 2
        img = img.crop((left, top, left + w, top + h))

        return np.array(img)

    animated = VideoClip(make_frame, duration=duration)
    return animated


def _crossfade_chain(clips, fade_duration=0.4):
    """
    将片段列表串接，片段间带 crossfade 转场

    MoviePy 2.x 方式: 用 concatenate 的 padding 参数
    """
    if len(clips) == 1:
        return clips[0]

    # 每对相邻片段之间应该有重叠的 fade 区域
    # 方法: 给每个片段加 crossfadein/crossfadeout
    processed = []
    for i, clip in enumerate(clips):
        if i > 0:
            clip = clip.with_effects([vfx.CrossFadeIn(fade_duration)])
        if i < len(clips) - 1:
            clip = clip.with_effects([vfx.CrossFadeOut(fade_duration)])
        processed.append(clip)

    # 使用负 padding 实现 overlap
    return concatenate_videoclips(processed, padding=-fade_duration)


def compose_video(
    slide_paths: list,
    audio_paths: list,
    output_path: str,
    gif_paths: list = None,
    resolution=(1920, 1080),
    fps=30,
    crossfade=0.4,
) -> str:
    """
    将幻灯片、音频、GIF 合成为视频 (不含字幕)

    参数:
        slide_paths: 幻灯片图片路径列表
        audio_paths: 每页的配音文件路径列表 (MP3)
        output_path: 输出视频路径 (MP4)
        gif_paths: 每页的 GIF 路径列表 (可为 None)
        resolution: (宽, 高)
        fps: 帧率
        crossfade: 转场时长(秒)

    返回: output_path
    """
    if gif_paths is None:
        gif_paths = [None] * len(slide_paths)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    W, H = resolution

    clips = []
    total_slides = len(slide_paths)

    for i, (slide, audio, gif) in enumerate(zip(slide_paths, audio_paths, gif_paths)):
        # 获取音频时长
        audio_clip = AudioFileClip(audio)
        duration = audio_clip.duration
        print(f"  [合成] 第 {i+1}/{total_slides} 页, 时长 {duration:.1f}s")

        # ── 背景层: Ken Burns 缩放 ──
        bg_clip = _ken_burns_clip(slide, duration, scale_from=1.0, scale_to=1.05)

        # ── GIF 画中画 (如果有) ──
        if gif and os.path.exists(gif):
            try:
                from moviepy import VideoFileClip
                gif_clip = VideoFileClip(gif, has_mask=True)

                # 限制 GIF 循环次数
                gif_duration = gif_clip.duration
                if gif_duration < duration:
                    # 循环 GIF
                    loops_needed = int(duration / gif_duration) + 1
                    gif_clip = concatenate_videoclips([gif_clip] * loops_needed)
                gif_clip = gif_clip.subclipped(0, duration)

                # 缩放 GIF 到画面的 1/3 宽度，放右下角
                gif_w = int(W * 0.35)
                gif_h = int(gif_clip.h * (gif_w / gif_clip.w))
                gif_clip = gif_clip.resized(width=gif_w)

                # 右下角位置
                margin = 40
                gif_clip = gif_clip.with_position((W - gif_w - margin, H - gif_h - margin))

                print(f"    [GIF] 画中画: {gif_w}×{gif_h}")
            except Exception as e:
                print(f"    [GIF] 加载失败: {e}")
                gif_clip = None
        else:
            gif_clip = None

        # ── 合成层 ──
        layers = [bg_clip]
        if gif_clip:
            layers.append(gif_clip)

        if len(layers) > 1:
            clip = CompositeVideoClip(layers, size=resolution)
        else:
            clip = bg_clip

        # 设置音频
        clip = clip.with_audio(audio_clip)
        clips.append(clip)

    # ── 串接所有片段 (带 crossfade) ──
    print(f"  [合成] 拼接 {len(clips)} 个片段 (转场 {crossfade}s)...")
    if len(clips) == 1:
        final = clips[0]
    else:
        # 给每个片段加转场效果
        processed = []
        for i, clip in enumerate(clips):
            if i > 0:
                clip = clip.with_effects([vfx.CrossFadeIn(crossfade)])
            if i < len(clips) - 1:
                clip = clip.with_effects([vfx.CrossFadeOut(crossfade)])
            processed.append(clip)
        final = concatenate_videoclips(processed, padding=-crossfade)

    # ── 渲染输出 ──
    print(f"  [渲染] 输出到 {output_path} ...")
    final.write_videofile(
        output_path,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        bitrate="3000k",
        threads=4,
        logger=None,
    )

    # 清理
    for clip in clips:
        try:
            if hasattr(clip, 'audio') and clip.audio:
                clip.audio.close()
        except Exception:
            pass

    print(f"  [OK] 视频合成完成: {output_path}")
    return output_path


def burn_subtitles(
    video_path: str,
    srt_path: str,
    output_path: str,
    font_path: str = "C:/Windows/Fonts/msyh.ttc",
    font_size: int = 28,
) -> str:
    """
    用 FFmpeg 将 SRT 字幕烧录到视频中

    参数:
        video_path: 输入视频
        srt_path: SRT 字幕文件
        output_path: 输出视频
        font_path: 字体文件路径
        font_size: 字号
    """
    # Windows 路径在 FFmpeg subtitles filter 中需要转义
    srt_path_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
    font_path_escaped = font_path.replace("\\", "/").replace(":", "\\:")

    # 字幕样式
    style = (
        f"FontName={Path(font_path).stem},"
        f"FontSize={font_size},"
        f"PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,"
        f"Outline=2,"
        f"Shadow=1,"
        f"MarginV=40,"
        f"Alignment=2"
    )

    filter_str = f"subtitles='{srt_path_escaped}':force_style='{style}'"

    cmd = [
        "ffmpeg", "-y",
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
        # 如果 FFmpeg 失败，尝试不烧录字幕直接复制
        print(f"  [!] 字幕烧录失败，使用无字幕版本:")
        print(f"      {result.stderr[-300:]}")
        import shutil
        shutil.copy(video_path, output_path)
    else:
        print(f"  [OK] 字幕烧录完成: {output_path}")

    return output_path


def concat_audio_files(audio_paths: list, silence_paths: list, output_path: str):
    """
    将多个 MP3 文件与静音间隔拼接成一个完整音频文件
    用于验证/预览
    """
    # 创建 FFmpeg concat 列表
    concat_list = []
    for i, (audio, silence) in enumerate(zip(audio_paths, silence_paths)):
        concat_list.append(audio)
        if i < len(audio_paths) - 1:
            concat_list.append(silence)

    # 写 concat 文件
    list_path = output_path + ".txt"
    with open(list_path, "w") as f:
        for p in concat_list:
            f.write(f"file '{p.replace(chr(92), '/')}'\n")

    result = subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path, "-c:a", "libmp3lame", "-q:a", "2",
        output_path,
    ], capture_output=True, text=True, encoding='utf-8', errors='replace')
    os.remove(list_path)

    if result.returncode == 0:
        print(f"  [音频合并] → {output_path}")
    else:
        print(f"  [!] 音频合并失败: {result.stderr[-200:]}")

    return output_path


if __name__ == "__main__":
    print("=== 视频合成测试 ===\n")

    # 简单测试：两张纯色"幻灯片"
    from PIL import Image
    test_dir = "test_output"
    os.makedirs(test_dir, exist_ok=True)

    # 生成测试图片
    for i, color in enumerate(["#1a1a2e", "#16213e"]):
        img = Image.new("RGB", (1280, 720), color)
        img.save(f"{test_dir}/test_slide_{i}.png")

    # 生成测试音频 (1秒静音)
    for i in range(2):
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            f"sine=frequency=440:duration=1.5",
            f"{test_dir}/test_audio_{i}.mp3",
        ], capture_output=True, encoding='utf-8', errors='replace')

    print("测试文件已准备，合成视频...")
    # (完整的合成测试需要更复杂的设置，这里只验证导入正确)
    print("video_composer 模块加载成功 [OK]")
