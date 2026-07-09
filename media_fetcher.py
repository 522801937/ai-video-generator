"""
素材爬取模块 - 从网络获取图片和 GIF
支持: Bing 图片搜索 (主力) + Unsplash API (可选) + Giphy (可选)
"""
import os
import hashlib
import time
import shutil
import sys
from pathlib import Path
from urllib.parse import quote_plus, urlparse
import requests
from bs4 import BeautifulSoup

# Fix Windows GBK encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# 缓存目录
CACHE_DIR = Path(__file__).parent / "cache"
IMAGE_CACHE = CACHE_DIR / "images"
GIF_CACHE = CACHE_DIR / "gifs"

# 默认背景图目录
BACKGROUNDS_DIR = Path(__file__).parent / "backgrounds"

# User-Agent (模拟浏览器)
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


def _cache_key(keywords, suffix=""):
    """生成缓存文件名"""
    raw = "+".join(sorted(keywords)) + suffix
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def _download(url, dest_path, timeout=15):
    """下载文件到指定路径，返回是否成功"""
    try:
        resp = SESSION.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return os.path.getsize(dest_path) > 1024  # 至少 1KB
    except Exception:
        return False


# ─── Bing 图片搜索 ───────────────────────────────────────────

def search_bing_images(keyword, count=10):
    """
    从 Bing 图片搜索获取图片 URL 列表
    返回: [(url, thumbnail_url), ...]
    """
    url = f"https://www.bing.com/images/search?q={quote_plus(keyword)}&first=1"
    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Bing 将图片 URL 放在 <a class="iusc"> 的 m 属性中
        results = []
        for a_tag in soup.find_all("a", class_="iusc"):
            m_attr = a_tag.get("m")
            if not m_attr:
                continue
            import json
            try:
                meta = json.loads(m_attr)
                img_url = meta.get("murl") or meta.get("turl")
                if img_url and img_url.startswith("http"):
                    results.append(img_url)
            except json.JSONDecodeError:
                continue
            if len(results) >= count:
                break

        return results
    except Exception as e:
        print(f"  [Bing] 搜索 '{keyword}' 失败: {e}")
        return []


# ─── Unsplash (无需 API Key 的 scraping) ─────────────────────

def search_unsplash(keyword, count=5):
    """从 Unsplash 搜索图片 URL"""
    url = f"https://unsplash.com/s/photos/{quote_plus(keyword)}"
    try:
        resp = SESSION.get(url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        for img in soup.find_all("img", {"srcset": True}):
            srcset = img.get("srcset", "")
            # 取最高分辨率版本
            parts = srcset.split(",")
            if parts:
                largest = parts[-1].strip().split(" ")[0]
                if largest.startswith("https://images.unsplash.com/"):
                    # 去掉 URL 参数获得原图
                    base = largest.split("?")[0]
                    if base not in results:
                        results.append(base)
            if len(results) >= count:
                break

        return results
    except Exception as e:
        print(f"  [Unsplash] 搜索 '{keyword}' 失败: {e}")
        return []


# ─── 公开接口 ──────────────────────────────────────────────────
# 各 API 的可用状态
_AVAILABLE_SOURCES = {
    "bing": True,      # Bing 始终可用
    "unsplash": True,  # 尝试 scraping
}


def fetch_image(keywords, resolution=(1920, 1080)):
    """
    根据关键词获取一张背景图，带缓存
    返回: (本地路径, 来源名称)
    """
    cache_name = _cache_key(keywords, "img") + ".jpg"
    cache_path = IMAGE_CACHE / cache_name

    if cache_path.exists():
        print(f"  [缓存] 使用已缓存的图片: {cache_path.name}")
        return str(cache_path), "cache"

    # 尝试多个关键词组合
    queries = [keywords[0]] if keywords else ["technology"]
    if len(keywords) > 1:
        queries.append(" ".join(keywords[:2]))
        queries.append(keywords[0] + " background")

    image_url = None
    source = "none"

    for query in queries:
        print(f"  [搜索] 图片关键词: '{query}'")

        # Bing
        urls = search_bing_images(query, count=10)
        if urls:
            for u in urls[:5]:
                if _download(u, cache_path):
                    image_url = u
                    source = "bing"
                    break
        if image_url:
            break

        # Unsplash
        urls = search_unsplash(query, count=5)
        if urls:
            for u in urls[:3]:
                if _download(u, cache_path):
                    image_url = u
                    source = "unsplash"
                    break
        if image_url:
            break

    if image_url:
        print(f"  [OK] 图片下载成功 ({source})")
        return str(cache_path), source

    # Fallback: 使用默认背景
    default_bg = BACKGROUNDS_DIR / "default.jpg"
    if default_bg.exists():
        print(f"  [!] 使用默认背景图")
        return str(default_bg), "default"

    print(f"  [FAIL] 无法获取图片，将使用纯色背景")
    return None, "none"


def fetch_gif(keywords):
    """
    根据关键词获取一张 GIF 动图，带缓存
    返回: 本地路径 或 None
    """
    cache_name = _cache_key(keywords, "gif") + ".gif"
    cache_path = GIF_CACHE / cache_name

    if cache_path.exists():
        print(f"  [缓存] 使用已缓存的 GIF: {cache_path.name}")
        return str(cache_path)

    query = " ".join(keywords) + " gif"

    # Bing GIF 搜索
    bing_url = f"https://www.bing.com/images/search?q={quote_plus(query)}&qft=+filterui:photo-animatedgif&first=1"
    try:
        resp = SESSION.get(bing_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        import json
        for a_tag in soup.find_all("a", class_="iusc"):
            m_attr = a_tag.get("m")
            if not m_attr:
                continue
            try:
                meta = json.loads(m_attr)
                gif_url = meta.get("murl")
                if gif_url and gif_url.endswith(".gif") and gif_url.startswith("http"):
                    if _download(gif_url, cache_path, timeout=20):
                        size_mb = os.path.getsize(cache_path) / 1024 / 1024
                        if size_mb < 15:  # GIF 不超过 15MB
                            print(f"  [OK] GIF 下载成功 ({size_mb:.1f}MB)")
                            return str(cache_path)
                        else:
                            os.remove(cache_path)
                            print(f"  [!] GIF 太大 ({size_mb:.1f}MB)，跳过")
            except (json.JSONDecodeError, Exception):
                continue
    except Exception as e:
        print(f"  [GIF] 搜索失败: {e}")

    print(f"  [FAIL] 未找到合适 GIF")
    return None


# ─── 工具函数 ──────────────────────────────────────────────────

def clear_cache(media_type=None):
    """清空缓存"""
    if media_type in (None, "images"):
        for f in IMAGE_CACHE.glob("*"):
            f.unlink()
        print(f"已清空图片缓存 ({IMAGE_CACHE})")
    if media_type in (None, "gifs"):
        for f in GIF_CACHE.glob("*"):
            f.unlink()
        print(f"已清空 GIF 缓存 ({GIF_CACHE})")


if __name__ == "__main__":
    # 测试
    print("=== 测试图片搜索 ===")
    path, src = fetch_image(["neural network", "AI"])
    print(f"结果: {path} (来源: {src})")

    print("\n=== 测试 GIF 搜索 ===")
    path = fetch_gif(["robot", "automation"])
    print(f"结果: {path}")
