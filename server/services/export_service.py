"""视频导出编排服务 — 协调 TTS、渲染、合成、字幕全流程"""
import asyncio
import os
import subprocess
import threading
from pathlib import Path
from project_paths import get_project_root, get_output_dir, get_data_dir, find_ffmpeg

PROJECT_DIR = get_data_dir()  # 只读数据目录（PyInstaller 下是 _MEIPASS）
OUTPUT_ROOT = get_output_dir()  # 可写入输出目录

# 内存中的任务状态
_tasks: dict[str, dict] = {}


def queue_render(task_id: str, params: dict):
    """将渲染任务入队 (异步线程执行)"""
    _tasks[task_id] = {"status": "queued", "progress": 0}
    thread = threading.Thread(target=_run_render, args=(task_id, params), daemon=True)
    thread.start()


def get_status(task_id: str) -> dict:
    """查询渲染任务状态"""
    if task_id not in _tasks:
        return {"status": "not_found", "task_id": task_id}
    return {"task_id": task_id, "status": _tasks[task_id]["status"],
            "progress": _tasks[task_id].get("progress", 0),
            "output_path": _tasks[task_id].get("output_path"),
            "error": _tasks[task_id].get("error")}


def _run_render(task_id: str, params: dict):
    """同步渲染流程 — 在后台线程中运行"""
    try:
        slides = params["slides"]
        title = params["title"]
        voice = params.get("voice", "xiaoxiao")
        speed = params.get("speed", "+10%")
        resolution = tuple(params.get("resolution", [1920, 1080]))
        fps = params.get("fps", 30)

        # 文件名只用 ASCII 字/数字，避免 FFmpeg concat 的编码问题
        safe_title = "".join(c if c.isascii() and (c.isalnum() or c in "._-") else "_" for c in title)[:50]
        if not safe_title.strip("_"):
            safe_title = "video"
        out_dir = OUTPUT_ROOT / safe_title
        out_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: TTS 配音
        _tasks[task_id] = {"status": "generating_audio", "progress": 10}
        import sys
        sys.path.insert(0, str(PROJECT_DIR))
        from tts_engine import generate_all_slides_audio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        slide_results = loop.run_until_complete(
            generate_all_slides_audio(slides, str(out_dir), voice, speed)
        )
        loop.close()

        # Step 2: 渲染每个场景为帧序列 → 场景视频
        _tasks[task_id] = {"status": "rendering_frames", "progress": 30}
        from renderer.playwright_renderer import render_scene_frames, frames_to_video
        from media_fetcher import fetch_image

        scene_videos = []
        for i, (slide, result) in enumerate(zip(slides, slide_results)):
            # 有关键词的场景自动爬图
            if slide.get("keywords") and slide["type"] in ("image", "title", "bullets"):
                try:
                    img_path, _ = fetch_image(slide["keywords"], resolution)
                    if img_path:
                        slide["config"]["bgImage"] = img_path
                except Exception:
                    pass

            duration = result["meta"]["duration"] + 0.5  # 加 0.5s 避免音频截断
            scene_frame_dir = str(out_dir / f"scene_{i:02d}")
            os.makedirs(scene_frame_dir, exist_ok=True)

            render_scene_frames(slide, scene_frame_dir, duration, resolution, fps)

            scene_video = str(out_dir / f"scene_{i:02d}.mp4")
            frames_to_video(scene_frame_dir, scene_video, fps)
            scene_videos.append(scene_video)

            _tasks[task_id]["progress"] = 30 + int(40 * (i + 1) / len(slides))

        # Step 3: 拼接场景 + 合并音频
        _tasks[task_id] = {"status": "compositing", "progress": 75}

        # FFmpeg concat 拼接所有场景视频
        concat_list = str(out_dir / "concat.txt")
        with open(concat_list, "w") as f:
            for v in scene_videos:
                f.write(f"file '{v.replace(chr(92), '/')}'\n")

        temp_video = str(out_dir / "temp_merged.mp4")
        subprocess.run([
            find_ffmpeg(), "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list, "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", temp_video,
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

        # 合并音频
        from video_utils import concat_audio_files
        audio_paths = [r["audio_path"] for r in slide_results]
        silence_paths = [r["silence_path"] for r in slide_results]
        combined_audio = str(out_dir / "combined_audio.mp3")
        concat_audio_files(audio_paths, silence_paths, combined_audio)

        # 视频 + 音频合成
        final_video = str(out_dir / f"{safe_title}.mp4")
        subprocess.run([
            find_ffmpeg(), "-y", "-i", temp_video, "-i", combined_audio,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            final_video,
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

        # Step 4: 字幕烧录
        _tasks[task_id] = {"status": "compositing", "progress": 90}
        from subtitle_generator import generate_srt
        srt_path = str(out_dir / "subtitles.srt")
        generate_srt(slide_results, srt_path)

        from video_utils import burn_subtitles
        subtitled_video = str(out_dir / f"{safe_title}_subtitled.mp4")
        burn_subtitles(final_video, srt_path, subtitled_video)

        # 清理临时文件
        for v in scene_videos:
            try:
                os.remove(v)
            except Exception:
                pass
        try:
            os.remove(temp_video)
        except Exception:
            pass
        try:
            os.remove(concat_list)
        except Exception:
            pass

        _tasks[task_id] = {
            "status": "done",
            "progress": 100,
            "output_path": subtitled_video,
        }

    except Exception as e:
        _tasks[task_id] = {"status": "error", "progress": 0, "error": str(e)}
