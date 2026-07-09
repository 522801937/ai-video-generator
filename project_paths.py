"""项目路径工具 — 正确解析项目根目录（兼容 PyInstaller 打包后的临时目录）"""
import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """
    获取项目根目录（可写入）

    - 正常 Python 运行: 此文件所在目录
    - PyInstaller onefile: exe 所在目录
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller: exe 所在目录（可写入）
        return Path(os.path.dirname(sys.executable))

    # 正常 Python：此文件在项目根目录
    return Path(__file__).parent


def get_data_dir() -> Path:
    """
    获取只读数据文件目录

    - PyInstaller onefile: sys._MEIPASS 临时解压目录（--add-data 的文件在这里）
    - 正常 Python: 项目根目录
    """
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)

    return Path(__file__).parent


def get_output_dir() -> Path:
    """获取视频输出目录（始终在可写入位置）"""
    return get_project_root() / "output"


def get_web_dist_dir() -> Path:
    """获取前端构建产物目录"""
    return get_data_dir() / "web" / "dist"


def find_ffmpeg() -> str:
    """
    查找 ffmpeg 可执行文件

    优先级:
    1. 项目目录/数据目录下的 ffmpeg.exe
    2. 系统 PATH 中的 ffmpeg
    """
    # 检查数据目录（PyInstaller 下是 _MEIPASS）
    bundled = get_data_dir() / "ffmpeg.exe"
    if bundled.exists():
        return str(bundled)

    # 检查项目根目录
    proj = get_project_root() / "ffmpeg.exe"
    if proj.exists():
        return str(proj)

    # 回退到 PATH
    return "ffmpeg"
