<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/python-3.10+-steelblue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/react-18-61DAFB?style=for-the-badge&logo=react" alt="React">
  <img src="https://img.shields.io/badge/desktop-exe-orange?style=for-the-badge" alt="Desktop">
</p>

<h1 align="center">🎬 AI Video Generator</h1>
<h3 align="center">Text → Beautiful Science Videos · One Click</h3>
<p align="center"><em>Write an article, get a professional video with voiceover, subtitles, animations & illustrations — fully automated.</em></p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-features">Features</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-usage">Usage</a> ·
  <a href="README_CN.md">中文文档</a>
</p>

---

## ✨ What Is This?

**AI Video Generator** is a desktop application that turns your text into beautifully animated science education (科普) videos. Write an article describing AI, biology, physics — anything — and in minutes you get a 1080p video complete with:

- 🎨 **Animated visual scenes** with Ken Burns effects, transitions, and dynamic layouts
- 🎙️ **Neural voiceover** (Microsoft Edge TTS, 8+ voice options, free)
- 📝 **Auto-generated subtitles** synced word-by-word from TTS timestamps
- 🖼️ **Auto-fetched background images** scraped from Bing/Unsplash for each scene
- 📦 **One-click .exe packaging** — no Python needed to run, just double-click

**🎯 Built for:** Science educators, content creators, students, and anyone who wants to explain complex ideas visually — without touching a video editor.

<p align="center">
  <sup><a href="README_CN.md">🇨🇳 点此查看中文完整文档</a></sup>
</p>

---

## 🎯 Features

| Feature | Description |
|---------|------------|
| 📝 **Text → Scenes** | Intelligent parsing splits your article into title, bullet, image, and outro scenes |
| 🎨 **4 Scene Types** | Title slide, bullet list, fullscreen image, closing credits (6 more planned) |
| 🎙️ **Edge TTS** | Microsoft neural voices — Xiaoxiao, Yunxi, Yunyang + dialects. Free & natural |
| 📝 **Word-level Subtitles** | SRT subtitles burned into video, precisely timed from TTS word boundaries |
| 🖼️ **Auto Image Search** | Each scene scrapes Bing/Unsplash for relevant background images |
| 🎬 **Ken Burns Effect** | Subtle zoom animation on every scene — no static slides |
| 📦 **Desktop .exe** | PyInstaller onefile package — ~68MB, zero dependencies for end users |
| ⚡ **Local Web UI** | React + TypeScript frontend served from local FastAPI server |

---

## 🚀 Quick Start

### Option 1: Run the Pre-built .exe (Windows)

Download `AI视频生成器.exe` from [Releases](https://github.com/522801937/ai-video-generator/releases), double-click, and you're ready.

> **Requirements:** Windows 10/11, Chrome or Edge browser installed

### Option 2: From Source

```bash
# 1. Clone
git clone https://github.com/522801937/ai-video-generator.git
cd ai-video-generator

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Playwright browser
python -m playwright install chromium

# 4. Download FFmpeg (required for video compositing)
#    Place ffmpeg.exe in the project root, or ensure it's on your PATH
#    https://ffmpeg.org/download.html

# 5. Start the app
python app.py
```

The server starts at `http://127.0.0.1:8765` and opens your browser automatically.

### Option 3: Development Mode

```bash
# Terminal 1: Backend
cd server
uvicorn main:app --host 127.0.0.1 --port 8765 --reload

# Terminal 2: Frontend
cd web
npm install
npm run dev
```

Open `http://localhost:5173` — hot reload for both frontend and backend.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Desktop App (.exe)                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐     ┌──────────────────┐              │
│  │  React + TS   │────▶│  FastAPI Server  │              │
│  │  (Frontend)   │◀────│  :8765           │              │
│  └──────────────┘     └──────┬───────────┘              │
│                              │                           │
│         ┌────────────────────┼─────────────────────┐     │
│         │                    │                     │     │
│         ▼                    ▼                     ▼     │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │  Edge TTS    │  │  Playwright    │  │    FFmpeg    │ │
│  │  Voice Sync  │  │  Frame Capture │  │  Compositing │ │
│  └──────────────┘  └────────────────┘  └──────────────┘ │
│                              │                           │
│                              ▼                           │
│                    ┌────────────────┐                   │
│                    │  Media Fetcher │                   │
│                    │  Bing/Unsplash │                   │
│                    └────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**Rendering Pipeline:**

```
Text Input → Scene Parser → [4 Scene Types]
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
  TTS Audio   Image Fetch  HTML/Canvas Animation
    │           │           │
    ▼           ▼           ▼
  MP3 Files   Cached JPG   Playwright Frames (PNG sequence)
    │                       │
    ▼                       ▼
  Subtitle Generator     FFmpeg → Scene MP4
    │                       │
    ▼                       ▼
  SRT File ────────────▶ FFmpeg Compositing
                            │
                            ▼
                       Final MP4
                      (1080p, H.264, AAC, with burned subs)
```

---

## 📂 Project Structure

```
karpathy-video/
├── app.py                     # Desktop shell entry point
├── project_paths.py           # Centralized path resolution (dev + frozen)
├── build.py                   # PyInstaller onefile build script
├── requirements.txt           # Python dependencies
│
├── server/                    # FastAPI Backend
│   ├── main.py                # Server entry, static file mount
│   ├── routes.py              # REST API endpoints
│   └── services/
│       ├── export_service.py  # Full render pipeline orchestrator
│       ├── scene_parser.py    # Markdown text → scene list
│       └── render_service.py  # Playwright render helpers
│
├── renderer/
│   └── playwright_renderer.py # Scene HTML compiler + Playwright capture
│
├── tts_engine.py              # Edge TTS voice generation w/ word timestamps
├── subtitle_generator.py      # Word-boundary → SRT subtitle file
├── video_utils.py             # FFmpeg concat, audio merge, subtitle burn
├── media_fetcher.py           # Bing/Unsplash image scraper w/ disk cache
│
├── web/                       # React + TypeScript Frontend
│   └── src/
│       ├── App.tsx            # Root layout (Editor | Preview | Export)
│       ├── components/        # Editor, PreviewPanel, ExportPanel, Timeline
│       ├── scenes/            # TitleScene, BulletsScene, ImageScene, OutroScene
│       ├── animation/         # anime.js primitives + timeline engine
│       └── api.ts             # Backend API client
│
├── docs/superpowers/          # Design specs & implementation plans
├── 启动.bat                   # One-click launcher (build + run + open)
└── README.md
```

---

## 🎨 Scene Types

| Scene | Visual | Best For |
|-------|--------|----------|
| **Title** | Gradient + scale-in title + floating lines | Opening hook, topic intro |
| **Bullets** | Staggered list items, left-slide title | Explaining concepts, listing points |
| **Image** | Fullscreen photo + dark overlay + caption | Visual demonstrations, examples |
| **Outro** | Centered text, decorative accent line | Closing credits, "Thanks for watching" |

**Planned:** Concept diagram, comparison table, flowchart, data chart, quote card, timeline

---

## 🎙️ Voice Options

| Voice | Style | Best For |
|-------|-------|----------|
| `xiaoxiao` | Warm, natural female | General narration |
| `yunxi` | Clear, professional male | Technical topics |
| `yunyang` | Deep, authoritative male | Serious/formal content |
| `xiaoyi` | Bright, energetic female | Lively topics |
| `yunjian` | Gentle, soothing male | Calm narrations |
| `yunxia` | Soft, friendly female | Casual content |
| `xiaobei` | Liaoning dialect | Regional flavor |
| `xiaoni` | Shaanxi dialect | Regional flavor |

Speed adjustable from `-20%` to `+30%`.

---

## 🖼️ Image Pipeline

The image fetcher works **without any API keys**:

1. **Bing Image Search** — scrapes image search results for relevant photos
2. **Unsplash** — scrapes Unsplash search as secondary source
3. **Disk Cache** — downloaded images cached by keyword hash for reuse
4. **Gradient Fallback** — if no image found, uses smooth gradient background

> 💡 **Want AI-generated images?** Add your API key in `config.json` and the pipeline will use DALL·E / Stable Diffusion as primary source.

---

## 📦 Build Your Own .exe

```bash
# Build frontend + package with PyInstaller
python build.py

# Output: dist/AI视频生成器.exe (~68MB)
```

```bash
# Skip frontend build if already done
python build.py --skip-frontend
```

The build script:
- Bundles React frontend, FastAPI server, TTS engine, renderer
- Excludes heavy dependencies (matplotlib, pandas, scipy, etc.)
- Includes FFmpeg and Playwright browser detection

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Areas where help is especially welcome:**
- 🎨 New scene types (flowchart, timeline, chart, quote, compare)
- 🌍 i18n / multi-language UI support
- 🎵 Background music integration
- 🎞️ Transition effects between scenes
- 🧪 Test coverage
- 📱 macOS / Linux packaging support

---

## 📄 License

MIT © 2026 [Your Name]

---

<p align="center">
  <b>⭐ If you find this useful, give it a star!</b><br>
  <sub>It helps more people discover the project 🚀</sub>
</p>

<p align="center">
  <sub>
    <a href="README_CN.md">🇨🇳 中文文档</a> ·
    <a href="#-quick-start">Quick Start</a> ·
    <a href="#-features">Features</a>
  </sub>
</p>
