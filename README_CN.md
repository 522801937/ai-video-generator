<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/python-3.10+-steelblue?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/react-18-61DAFB?style=for-the-badge&logo=react" alt="React">
  <img src="https://img.shields.io/badge/desktop-exe-orange?style=for-the-badge" alt="Desktop">
</p>

<h1 align="center">🎬 AI 视频生成器</h1>
<h3 align="center">输入文字 → 一键生成精美科普视频</h3>
<p align="center"><em>写一篇文章，自动生成带配音、字幕、动画和配图的专业视频——全程自动化。</em></p>

<p align="center">
  <a href="#-快速开始">快速开始</a> ·
  <a href="#-核心功能">核心功能</a> ·
  <a href="#-技术架构">技术架构</a> ·
  <a href="#-使用指南">使用指南</a> ·
  <a href="README.md">English Docs</a>
</p>

---

## ✨ 这是什么？

**AI 视频生成器**是一款桌面应用，能将你写的文字一键转化为精美的科普动画视频。无论是解释 AI 原理、生物知识还是物理概念——只需写好文案，几分钟后你就能得到一段 1080p 高清视频，包含：

- 🎨 **动画视觉场景** — Ken Burns 缩放效果、流畅过渡动画、动态排版
- 🎙️ **AI 神经网络配音** — 微软 Edge TTS，8+ 音色可选，完全免费
- 📝 **自动字幕** — 基于 TTS 词级时间戳逐词对齐，SRT 格式内嵌
- 🖼️ **智能配图** — 自动从必应/Unsplash 搜索相关图片作为场景背景
- 📦 **一键打包 .exe** — 双击即用，无需安装 Python 环境

**🎯 适合谁用：** 科普博主、教育工作者、知识付费创作者、学生——任何想用视频讲清楚复杂概念的人，无需打开任何剪辑软件。

<p align="center">
  <sup><a href="README.md">🇺🇸 Click here for English documentation</a></sup>
</p>

---

## 🎯 核心功能

| 功能 | 说明 |
|------|------|
| 📝 **文案智能解析** | 自动将文章拆分为标题页、要点列表、配图页、结尾页等场景 |
| 🎨 **4 种场景类型** | 标题页、要点列表、全屏大图、片尾致谢（还有 6 种开发中） |
| 🎙️ **Edge TTS 配音** | 微软神经网络语音——晓晓、云希、云扬等，支持方言 |
| 📝 **词级字幕** | 从 TTS 词边界精准生成 SRT 字幕，毫秒级同步 |
| 🖼️ **自动搜图** | 每页场景自动爬取必应/Unsplash 相关图片作为背景 |
| 🎬 **Ken Burns 动效** | 所有场景自动慢速缩放，告别静态幻灯片 |
| 📦 **桌面 .exe** | PyInstaller 单文件打包，约 68MB，最终用户零依赖 |
| ⚡ **本地 Web 界面** | React + TypeScript 前端，本地 FastAPI 后端，无需联网 |

---

## 🚀 快速开始

### 方式一：直接使用打包好的 .exe（Windows）

从 [Releases](https://github.com/522801937/ai-video-generator/releases) 下载 `AI视频生成器.exe`，双击运行即可。

> **系统要求：** Windows 10/11，已安装 Chrome 或 Edge 浏览器

### 方式二：从源码运行

```bash
# 1. 克隆项目
git clone https://github.com/522801937/ai-video-generator.git
cd ai-video-generator

# 2. 安装 Python 依赖
pip install -r requirements.txt

# 3. 安装 Playwright 浏览器
python -m playwright install chromium

# 4. 下载 FFmpeg（视频合成必需）
#    将 ffmpeg.exe 放在项目根目录，或确保系统 PATH 中已有
#    https://ffmpeg.org/download.html

# 5. 启动应用
python app.py
```

服务器启动在 `http://127.0.0.1:8765`，自动打开浏览器。

### 方式三：开发模式

```bash
# 终端 1：启动后端
cd server
uvicorn main:app --host 127.0.0.1 --port 8765 --reload

# 终端 2：启动前端
cd web
npm install
npm run dev
```

打开 `http://localhost:5173`，前后端均支持热重载。

---

## 🏗 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    桌面应用 (.exe)                        │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐     ┌──────────────────┐              │
│  │  React + TS   │────▶│  FastAPI 后端    │              │
│  │  (前端界面)    │◀────│  :8765           │              │
│  └──────────────┘     └──────┬───────────┘              │
│                              │                           │
│         ┌────────────────────┼─────────────────────┐     │
│         │                    │                     │     │
│         ▼                    ▼                     ▼     │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │  Edge TTS    │  │   Playwright   │  │    FFmpeg    │ │
│  │  语音合成     │  │   帧截图渲染    │  │   视频合成    │ │
│  └──────────────┘  └────────────────┘  └──────────────┘ │
│                              │                           │
│                              ▼                           │
│                    ┌────────────────┐                   │
│                    │   图片爬取引擎  │                   │
│                    │  Bing/Unsplash │                   │
│                    └────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**渲染流水线：**

```
用户文案 → 场景解析器 → [4 种场景类型]
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
  TTS 音频    图片搜索    HTML/CSS 动画
    │           │           │
    ▼           ▼           ▼
  MP3 文件    缓存图片    Playwright 截图 (PNG 序列)
    │                       │
    ▼                       ▼
  字幕生成器             FFmpeg → 场景 MP4
    │                       │
    ▼                       ▼
  SRT 文件 ────────────▶ FFmpeg 合成
                            │
                            ▼
                       最终 MP4 视频
                  (1080p, H.264, AAC, 内嵌字幕)
```

---

## 📂 项目结构

```
karpathy-video/
├── app.py                     # 桌面壳入口
├── project_paths.py           # 统一路径解析（开发 + 打包）
├── build.py                   # PyInstaller 单文件打包脚本
├── requirements.txt           # Python 依赖
│
├── server/                    # FastAPI 后端
│   ├── main.py                # 服务入口，托管前端静态文件
│   ├── routes.py              # REST API 路由
│   └── services/
│       ├── export_service.py  # 视频导出完整流水线
│       ├── scene_parser.py    # Markdown 文案 → 场景列表
│       └── render_service.py  # Playwright 渲染辅助
│
├── renderer/
│   └── playwright_renderer.py # 场景 HTML 编译 + 浏览器帧截图
│
├── tts_engine.py              # Edge TTS 语音合成（含词时间戳）
├── subtitle_generator.py      # 词边界 → SRT 字幕文件
├── video_utils.py             # FFmpeg 拼接/混音/字幕烧录
├── media_fetcher.py           # Bing/Unsplash 图片爬取 + 磁盘缓存
│
├── web/                       # React + TypeScript 前端
│   └── src/
│       ├── App.tsx            # 根布局（编辑器 | 预览 | 导出）
│       ├── components/        # 编辑器、预览面板、导出面板、时间线
│       ├── scenes/            # 标题/要点/图片/结尾场景组件
│       ├── animation/         # anime.js 动画基础 + 时间线引擎
│       └── api.ts             # 后端 API 客户端
│
├── docs/superpowers/          # 设计文档与实现计划
├── 启动.bat                   # 一键启动脚本
└── README.md
```

---

## 🎨 场景类型

| 场景 | 视觉效果 | 适用场景 |
|------|---------|----------|
| **标题页** | 渐变背景 + 标题缩放进入 + 装饰线条 | 视频开场、主题引入 |
| **要点列表** | 列表项依次滑入、标题左侧进入 | 概念解释、要点罗列 |
| **大图页** | 全屏图片 + 暗色遮罩 + 文字说明 | 视觉展示、案例演示 |
| **结尾页** | 居中致谢文字 + 装饰线 | 片尾、感谢观看 |

**规划中：** 概念图解、对比表格、流程图、数据图表、引用卡片、时间线

---

## 🎙️ 配音音色

| 音色 | 风格 | 适用场景 |
|------|------|----------|
| `xiaoxiao` | 温暖自然女声 | 通用解说 |
| `yunxi` | 清晰专业男声 | 技术科普 |
| `yunyang` | 深沉磁性男声 | 严肃/正式内容 |
| `xiaoyi` | 活泼元气女声 | 轻松话题 |
| `yunjian` | 温和舒缓男声 | 平静叙述 |
| `yunxia` | 柔和亲切女声 | 日常内容 |
| `xiaobei` | 辽宁方言 | 地域特色 |
| `xiaoni` | 陕西方言 | 地域特色 |

语速可在 `-20%` 到 `+30%` 之间调节。

---

## 🖼️ 图片获取机制

图片引擎**无需任何 API Key**即可工作：

1. **必应图片搜索** — 抓取图片搜索结果
2. **Unsplash** — 作为备用图片来源
3. **磁盘缓存** — 按关键词哈希缓存，避免重复下载
4. **渐变回退** — 搜索失败时使用纯色渐变背景

> 💡 **想用 AI 生成图片？** 在 `config.json` 中配置 API Key，流水线即可使用 DALL·E / Stable Diffusion 作为主图源。

---

## 📦 打包为 .exe

```bash
# 构建前端 + PyInstaller 打包
python build.py

# 输出: dist/AI视频生成器.exe (~68MB)
```

```bash
# 跳过前端构建（已手动构建时）
python build.py --skip-frontend
```

---

## 🤝 参与贡献

欢迎贡献代码！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

**优先需要帮助的方向：**
- 🎨 新场景类型（流程图、时间线、图表、引用、对比）
- 🌍 国际化 / 多语言 UI 支持
- 🎵 背景音乐集成
- 🎞️ 场景过渡特效
- 🧪 测试覆盖
- 📱 macOS / Linux 打包支持

---

## 📄 开源协议

MIT © 2026 [Your Name]

---

<p align="center">
  <b>⭐ 如果觉得有用，请给个 Star！</b><br>
  <sub>让更多人发现这个项目 🚀</sub>
</p>

<p align="center">
  <sub>
    <a href="README.md">🇺🇸 English Docs</a> ·
    <a href="#-快速开始">快速开始</a> ·
    <a href="#-核心功能">核心功能</a>
  </sub>
</p>
