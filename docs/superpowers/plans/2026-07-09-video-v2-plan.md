# AI 科普视频生成器 V2 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 karpathy-video 从"命令行 PPT 转视频工具"升级为"基于 HTML5 Canvas 动画引擎的桌面科普视频生成器"

**Architecture:** Python FastAPI 后端（复用 V1 的 TTS/字幕/爬图模块）+ React 前端编辑器（场景编排 + 实时预览）+ HTML5 Canvas 动画引擎（浏览器预览 + Playwright 逐帧导出）+ PyInstaller 打包为 exe

**Tech Stack:** Python 3.13+, FastAPI, React 18 + TypeScript + Vite, anime.js, Playwright, FFmpeg, PyInstaller

**Source spec:** `docs/superpowers/specs/2026-07-09-video-v2-design.md`

---

## 文件结构

```
karpathy-video/
├── server/                          # 新建: FastAPI 后端
│   ├── __init__.py
│   ├── main.py                      # FastAPI app + 静态文件托管
│   ├── routes.py                    # 所有 API 路由
│   └── services/
│       ├── __init__.py
│       ├── scene_parser.py          # 文案 → 场景JSON智能拆分
│       ├── render_service.py        # Playwright 渲染调度
│       └── export_service.py        # 视频导出编排
├── web/                             # 新建: React 前端
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api.ts                   # 后端 HTTP 通信
│       ├── types.ts                 # Scene/Slide 类型定义
│       ├── animation/
│       │   ├── primitives.ts        # 动画原语 (fadeIn, slideIn, scaleIn...)
│       │   └── timeline.ts          # 时间线引擎
│       ├── scenes/
│       │   ├── TitleScene.tsx       # 标题页
│       │   ├── BulletsScene.tsx     # 要点列举
│       │   ├── ImageScene.tsx       # 图片展示
│       │   └── OutroScene.tsx       # 片尾
│       ├── components/
│       │   ├── Editor.tsx           # 文案编辑器
│       │   ├── SceneConfigurator.tsx # 场景类型选择和参数编辑
│       │   ├── PreviewPanel.tsx     # 实时动画预览
│       │   ├── Timeline.tsx         # 时间线/场景排序
│       │   └── ExportPanel.tsx      # 导出控制
│       └── styles/
│           └── global.css
├── renderer/                        # 新建: 渲染引擎
│   ├── __init__.py
│   └── playwright_renderer.py       # 场景JSON → HTML页面 → 逐帧截图
├── app.py                           # 新建: 桌面壳入口 (打包入口)
├── build.py                         # 新建: PyInstaller 构建脚本
│
├── generate_video.py                # V1 保留
├── tts_engine.py                    # V1 复用
├── subtitle_generator.py            # V1 复用
├── media_fetcher.py                 # V1 复用
├── slide_generator.py               # V1 保留 (不再使用)
├── video_composer.py                # V1 保留 (不再使用)
└── requirements.txt                 # 更新依赖
```

---

## Phase 1: 项目骨架 (Task 1–4)

### Task 1: 后端 FastAPI 骨架

**Files:**
- Create: `server/__init__.py`
- Create: `server/main.py`
- Create: `server/routes.py`
- Create: `server/services/__init__.py`

- [ ] **Step 1: 创建 `server/__init__.py`**

```python
"""AI Video Generator V2 - Server"""
```

- [ ] **Step 2: 创建 `server/main.py` — FastAPI 应用入口**

```python
"""FastAPI 后端入口 — 托管前端静态文件 + API 路由"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

PROJECT_DIR = Path(__file__).parent.parent
WEB_DIR = PROJECT_DIR / "web" / "dist"

app = FastAPI(title="AI Video Generator V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
from server.routes import router
app.include_router(router, prefix="/api")

# 托管前端静态文件 (Vite build 产物)
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
```

- [ ] **Step 3: 创建 `server/routes.py` — API 路由骨架**

```python
"""API 路由定义"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# ---------- 类型定义 ----------

class SlideItem(BaseModel):
    type: str  # "title" | "bullets" | "image" | "outro"
    text: str = ""
    title: str = ""
    keywords: list[str] = []
    config: dict = {}  # 场景特定配置

class ParseRequest(BaseModel):
    content: str  # 用户输入的文案
    title: str = ""

class ParseResponse(BaseModel):
    title: str
    slides: list[SlideItem]

class RenderRequest(BaseModel):
    slides: list[SlideItem]
    title: str
    voice: str = "xiaoxiao"
    speed: str = "+10%"
    resolution: list[int] = [1920, 1080]
    fps: int = 30

class RenderResponse(BaseModel):
    task_id: str
    status: str  # "queued"

# ---------- 路由 ----------

@router.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}

@router.post("/parse", response_model=ParseResponse)
async def parse_script(req: ParseRequest):
    """将用户文案智能拆分为场景列表"""
    from server.services.scene_parser import parse_to_slides
    slides = parse_to_slides(req.content, req.title)
    return ParseResponse(title=req.title or "未命名视频", slides=slides)

@router.post("/render", response_model=RenderResponse)
async def start_render(req: RenderRequest):
    """启动视频渲染任务"""
    import uuid
    task_id = str(uuid.uuid4())[:8]
    from server.services.export_service import queue_render
    queue_render(task_id, req.model_dump())
    return RenderResponse(task_id=task_id, status="queued")

@router.get("/render/{task_id}/status")
async def render_status(task_id: str):
    """查询渲染进度"""
    from server.services.export_service import get_status
    return get_status(task_id)
```

- [ ] **Step 4: 创建 `server/services/__init__.py`**

```python
"""Backend services"""
```

- [ ] **Step 5: 安装依赖并测试启动**

Run:
```bash
pip install fastapi uvicorn
cd F:/claude-deepseek/karpathy-video
python -c "from server.main import app; print('FastAPI app created OK')"
```
Expected: `FastAPI app created OK`

- [ ] **Step 6: 启动服务器测试**

Run:
```bash
cd F:/claude-deepseek/karpathy-video
python -m server.main
```
Expected: Server starts on `http://127.0.0.1:8765`, `/api/health` returns `{"status":"ok","version":"2.0.0"}`

- [ ] **Step 7: Commit**

```bash
git add server/ requirements.txt
git commit -m "feat: FastAPI backend skeleton with /api/health, /api/parse, /api/render routes"
```

---

### Task 2: 前端 React 骨架

**Files:**
- Create: `web/package.json`
- Create: `web/vite.config.ts`
- Create: `web/tsconfig.json`
- Create: `web/index.html`
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/api.ts`
- Create: `web/src/types.ts`
- Create: `web/src/styles/global.css`

- [ ] **Step 1: 创建 `web/package.json`**

```json
{
  "name": "ai-video-generator",
  "private": true,
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "animejs": "^3.2.2"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "^5.6.3",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2: 创建 `web/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8765',
    },
  },
  build: {
    outDir: 'dist',
  },
})
```

- [ ] **Step 3: 创建 `web/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 4: 创建 `web/index.html`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI 视频生成器</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: 创建 `web/src/types.ts`**

```typescript
export interface SlideItem {
  type: 'title' | 'bullets' | 'image' | 'outro' | 'concept' | 'compare' | 'flow' | 'chart' | 'quote' | 'timeline'
  text: string
  title: string
  keywords: string[]
  config: Record<string, any>
}

export interface RenderStatus {
  task_id: string
  status: 'queued' | 'generating_audio' | 'rendering_frames' | 'compositing' | 'done' | 'error'
  progress: number  // 0-100
  output_path?: string
  error?: string
}
```

- [ ] **Step 6: 创建 `web/src/api.ts`**

```typescript
import type { SlideItem, RenderStatus } from './types'

const BASE = '/api'

export async function healthCheck(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/health`)
    return r.ok
  } catch {
    return false
  }
}

export async function parseScript(content: string, title: string): Promise<{ title: string; slides: SlideItem[] }> {
  const r = await fetch(`${BASE}/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content, title }),
  })
  if (!r.ok) throw new Error(`Parse failed: ${r.statusText}`)
  return r.json()
}

export async function startRender(slides: SlideItem[], title: string, voice: string = 'xiaoxiao'): Promise<{ task_id: string; status: string }> {
  const r = await fetch(`${BASE}/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slides, title, voice }),
  })
  if (!r.ok) throw new Error(`Render failed: ${r.statusText}`)
  return r.json()
}

export async function getRenderStatus(taskId: string): Promise<RenderStatus> {
  const r = await fetch(`${BASE}/render/${taskId}/status`)
  if (!r.ok) throw new Error(`Status check failed: ${r.statusText}`)
  return r.json()
}
```

- [ ] **Step 7: 创建 `web/src/App.tsx`**

```tsx
import { useState } from 'react'
import Editor from './components/Editor'
import PreviewPanel from './components/PreviewPanel'
import ExportPanel from './components/ExportPanel'
import type { SlideItem } from './types'
import './styles/global.css'

export default function App() {
  const [slides, setSlides] = useState<SlideItem[]>([])
  const [title, setTitle] = useState('')
  const [currentSlide, setCurrentSlide] = useState(0)

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🎬 AI 科普视频生成器</h1>
      </header>
      <main className="app-main">
        <div className="panel panel-left">
          <Editor
            onSlidesChange={(s, t) => { setSlides(s); setTitle(t) }}
            onSlideSelect={setCurrentSlide}
            currentSlide={currentSlide}
          />
        </div>
        <div className="panel panel-center">
          <PreviewPanel slides={slides} title={title} currentSlide={currentSlide} />
        </div>
        <div className="panel panel-right">
          <ExportPanel slides={slides} title={title} />
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 8: 创建 `web/src/main.tsx`**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 9: 创建 `web/src/styles/global.css`**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; background: #0d1117; color: #e6edf3; }
.app-container { display: flex; flex-direction: column; height: 100vh; }
.app-header { padding: 12px 24px; background: #161b22; border-bottom: 1px solid #30363d; }
.app-header h1 { font-size: 18px; font-weight: 600; }
.app-main { display: flex; flex: 1; overflow: hidden; }
.panel { padding: 16px; overflow-y: auto; }
.panel-left { width: 320px; border-right: 1px solid #30363d; }
.panel-center { flex: 1; display: flex; align-items: center; justify-content: center; background: #010409; }
.panel-right { width: 280px; border-left: 1px solid #30363d; }
```

- [ ] **Step 10: 安装依赖并验证构建**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web
npm install
npm run build
```
Expected: Build succeeds, `web/dist/` directory created

- [ ] **Step 11: Commit**

```bash
git add web/
git commit -m "feat: React frontend scaffold with editor/preview/export panel layout"
```

---

### Task 3: 文案解析服务 (scene_parser)

**Files:**
- Create: `server/services/scene_parser.py`
- Test via curl

- [ ] **Step 1: 创建 `server/services/scene_parser.py`**

```python
"""文案智能解析 — 将用户输入拆分为场景列表"""
import re


def parse_to_slides(content: str, title: str = "") -> list[dict]:
    """
    将文案按段落拆分为场景

    规则:
    1. `# 标题` → title 场景
    2. `## 小标题` → 带标题的 bullets 场景
    3. `![keyword]` → image 场景
    4. 普通段落 → bullets 场景
    5. 空行 → 场景分隔
    """
    slides = []
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    for para in paragraphs:
        lines = para.split("\n")
        first_line = lines[0]
        body = " ".join(lines[1:]).strip() if len(lines) > 1 else ""

        if first_line.startswith("# "):
            # 一级标题 → title 场景
            t = first_line[2:].strip()
            slides.append({
                "type": "title",
                "title": t,
                "text": body or t,
                "keywords": _extract_keywords(t + " " + body),
                "config": {},
            })

        elif first_line.startswith("## "):
            # 二级标题 → 带标题的 bullets
            subt = first_line[3:].strip()
            slides.append({
                "type": "bullets",
                "title": subt,
                "text": body or subt,
                "keywords": _extract_keywords(subt + " " + body),
                "config": {},
            })

        elif first_line.startswith("!["):
            # 图片场景: ![搜索关键词]
            m = re.match(r"!\[(.+)\]", first_line)
            kw = m.group(1) if m else ""
            slides.append({
                "type": "image",
                "title": "",
                "text": body,
                "keywords": [kw] if kw else [],
                "config": {"imageQuery": kw},
            })

        else:
            # 普通段落 → bullets
            t = para[:50].replace("\n", " ")
            slides.append({
                "type": "bullets",
                "title": "",
                "text": para,
                "keywords": _extract_keywords(para),
                "config": {},
            })

    # 如果没有 title 场景，自动添加一个
    has_title = any(s["type"] == "title" for s in slides)
    if not has_title and title:
        slides.insert(0, {
            "type": "title",
            "title": title,
            "text": "",
            "keywords": _extract_keywords(title),
            "config": {},
        })

    # 最后添加片尾
    slides.append({
        "type": "outro",
        "title": "感谢观看",
        "text": "",
        "keywords": [],
        "config": {},
    })

    return slides


def _extract_keywords(text: str, max_kw: int = 5) -> list[str]:
    """提取关键词 (中文2-4字 / 英文3+字母)"""
    words = re.findall(r"[一-鿿]{2,4}|[a-zA-Z]{3,}", text)
    seen = set()
    keywords = []
    for w in sorted(words, key=len, reverse=True):
        if w.lower() not in seen:
            keywords.append(w)
            seen.add(w.lower())
        if len(keywords) >= max_kw:
            break
    return keywords if keywords else ["科技"]
```

- [ ] **Step 2: 测试解析逻辑**

Run:
```bash
cd F:/claude-deepseek/karpathy-video
python -c "
from server.services.scene_parser import parse_to_slides
content = '''# AI Agent 是什么
## 从工具到智能体
传统的AI工具只能执行单一任务，而AI Agent能够自主感知环境、制定计划并完成复杂目标。

## 核心架构
Agent = LLM + 记忆 + 规划 + 工具调用

![robot artificial intelligence]
现代AI Agent可以像人类一样使用各种数字工具。'''
slides = parse_to_slides(content, 'AI Agent 科普')
for i, s in enumerate(slides):
    print(f'{i}: [{s[\"type\"]}] {s[\"title\"][:40]} | {s[\"keywords\"]}')
"
```
Expected: 5 scenes output (title → bullets →
bullets → image → outro)

- [ ] **Step 3: Commit**

```bash
git add server/services/scene_parser.py
git commit -m "feat: scene_parser - rule-based text to slide scene list"
```

---

### Task 4: 前端编辑器组件

**Files:**
- Create: `web/src/components/Editor.tsx`
- Create: `web/src/components/SceneConfigurator.tsx`
- Create: `web/src/components/Timeline.tsx`

- [ ] **Step 1: 创建 `web/src/components/Editor.tsx`**

```tsx
import { useState } from 'react'
import { parseScript } from '../api'
import type { SlideItem } from '../types'
import Timeline from './Timeline'

interface Props {
  onSlidesChange: (slides: SlideItem[], title: string) => void
  onSlideSelect: (index: number) => void
  currentSlide: number
}

export default function Editor({ onSlidesChange, onSlideSelect, currentSlide }: Props) {
  const [content, setContent] = useState('')
  const [title, setTitleLocal] = useState('')
  const [loading, setLoading] = useState(false)

  const handleParse = async () => {
    if (!content.trim()) return
    setLoading(true)
    try {
      const result = await parseScript(content, title)
      onSlidesChange(result.slides, result.title)
    } catch (err) {
      console.error('解析失败:', err)
      alert('解析失败，请检查后端是否已启动')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="editor">
      <h3>📝 文案编辑</h3>
      <div className="field">
        <label>视频标题</label>
        <input
          type="text"
          value={title}
          onChange={e => setTitleLocal(e.target.value)}
          placeholder="输入视频标题"
          className="input"
        />
      </div>
      <div className="field">
        <label>文案内容</label>
        <p className="hint">用 # 开头标记标题，## 开头标记小标题，空行分隔场景</p>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder={`# AI Agent 是什么\n\n## 从工具到智能体\n传统的AI工具只能执行单一任务，而AI Agent能够自主感知环境...\n\n## 核心架构\nAgent = LLM + 记忆 + 规划 + 工具调用`}
          rows={16}
          className="textarea"
        />
      </div>
      <button
        onClick={handleParse}
        disabled={loading || !content.trim()}
        className="btn btn-primary"
      >
        {loading ? '解析中...' : '🔍 解析生成场景'}
      </button>

      <Timeline onSlideSelect={onSlideSelect} currentSlide={currentSlide} />
    </div>
  )
}
```

- [ ] **Step 2: 创建 `web/src/components/Timeline.tsx`**

```tsx
import { useContext } from 'react'

interface Props {
  onSlideSelect: (index: number) => void
  currentSlide: number
}

export default function Timeline({ onSlideSelect, currentSlide }: Props) {
  return (
    <div className="timeline" style={{ marginTop: 16 }}>
      <h4>📋 场景列表</h4>
      <p style={{ color: '#8b949e', fontSize: 12, marginTop: 4 }}>
        选择场景查看预览，拖拽排序 (即将支持)
      </p>
    </div>
  )
}
```

- [ ] **Step 3: 创建 `web/src/components/SceneConfigurator.tsx`**

```tsx
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem | null
  onChange: (updated: SlideItem) => void
}

const SCENE_LABELS: Record<string, string> = {
  title: '📌 标题页',
  bullets: '📝 要点列举',
  image: '🖼️ 图片展示',
  outro: '👋 片尾',
}

export default function SceneConfigurator({ slide, onChange }: Props) {
  if (!slide) {
    return <div style={{ color: '#8b949e' }}>选择一个场景来编辑参数</div>
  }

  const sceneTypes = ['title', 'bullets', 'image', 'outro']

  return (
    <div className="scene-config">
      <h4>⚙️ 场景配置</h4>
      <div className="field">
        <label>场景类型</label>
        <select
          value={slide.type}
          onChange={e => onChange({ ...slide, type: e.target.value as any })}
          className="select"
        >
          {sceneTypes.map(t => (
            <option key={t} value={t}>{SCENE_LABELS[t] || t}</option>
          ))}
        </select>
      </div>
      <div className="field">
        <label>文本内容</label>
        <textarea
          value={slide.text}
          onChange={e => onChange({ ...slide, text: e.target.value })}
          rows={4}
          className="textarea"
        />
      </div>
    </div>
  )
}
```

- [ ] **Step 4: 验证前端构建**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web
npm run build
```
Expected: Build succeeds without errors

- [ ] **Step 5: Commit**

```bash
git add web/src/components/Editor.tsx web/src/components/Timeline.tsx web/src/components/SceneConfigurator.tsx
git commit -m "feat: editor components - text input, timeline, scene configurator"
```

---

## Phase 2: 动画引擎 (Task 5–8)

### Task 5: 动画原语库

**Files:**
- Create: `web/src/animation/primitives.ts`
- Create: `web/src/animation/timeline.ts`

- [ ] **Step 1: 创建 `web/src/animation/primitives.ts`**

```typescript
/**
 * 动画原语 — 基于 anime.js 封装的常用动画效果
 * 所有函数操作 DOM 元素，返回 anime.js 实例
 */
import anime from 'animejs'

export type AnimationTarget = string | HTMLElement | NodeList

export function fadeIn(target: AnimationTarget, duration: number = 800, delay: number = 0) {
  return anime({ targets: target, opacity: [0, 1], duration, delay, easing: 'easeOutCubic' })
}

export function fadeOut(target: AnimationTarget, duration: number = 600, delay: number = 0) {
  return anime({ targets: target, opacity: [1, 0], duration, delay, easing: 'easeInCubic' })
}

export function slideIn(target: AnimationTarget, from: 'left' | 'right' | 'bottom' = 'bottom', duration: number = 700, delay: number = 0) {
  const translateMap = { left: [-60, 0], right: [60, 0], bottom: [40, 0] }
  const [fromVal, toVal] = translateMap[from]
  return anime({
    targets: target,
    translateY: from === 'bottom' ? [fromVal, toVal] : undefined,
    translateX: from !== 'bottom' ? [fromVal, toVal] : undefined,
    opacity: [0, 1],
    duration,
    delay,
    easing: 'easeOutCubic',
  })
}

export function scaleIn(target: AnimationTarget, duration: number = 800, delay: number = 0) {
  return anime({
    targets: target,
    scale: [0.3, 1],
    opacity: [0, 1],
    duration,
    delay,
    easing: 'easeOutElastic(1, .6)',
  })
}

export function typewriter(target: HTMLElement, text: string, duration: number = 2000, delay: number = 0) {
  const chars = text.length
  const perChar = duration / chars
  let i = 0
  target.textContent = ''
  return anime({
    targets: { count: 0 },
    count: [0, chars],
    duration,
    delay,
    easing: 'linear',
    update(anim) {
      const c = Math.floor(anim.animations[0].currentValue as number)
      while (i < c) { target.textContent += text[i]; i++ }
    },
  })
}

export function staggerList(targets: AnimationTarget, duration: number = 500, staggerDelay: number = 200, delay: number = 0) {
  return anime({
    targets,
    translateY: [30, 0],
    opacity: [0, 1],
    duration,
    delay: anime.stagger(staggerDelay, { start: delay }),
    easing: 'easeOutCubic',
  })
}

export function counterUp(target: HTMLElement, from: number, to: number, duration: number = 1500, delay: number = 0) {
  return anime({
    targets: { val: from },
    val: [from, to],
    duration,
    delay,
    easing: 'easeOutCubic',
    round: 1,
    update(anim) {
      target.textContent = String(Math.round(anim.animations[0].currentValue as number))
    },
  })
}
```

- [ ] **Step 2: 创建 `web/src/animation/timeline.ts`**

```typescript
/**
 * 场景时间线引擎 — 管理一个场景内多个动画的编排
 */
import anime from 'animejs'

export interface AnimationStep {
  name: string
  fn: () => anime.AnimeInstance
  at: number  // 开始时间(秒)
}

export class SceneTimeline {
  private steps: AnimationStep[] = []
  private instances: anime.AnimeInstance[] = []

  add(name: string, fn: () => anime.AnimeInstance, at: number) {
    this.steps.push({ name, fn, at })
    return this
  }

  play(onComplete?: () => void) {
    this.stop()
    this.instances = []
    // 按 at 排序
    this.steps.sort((a, b) => a.at - b.at)

    const maxEnd = this.steps.reduce((max, step) => {
      const inst = step.fn()
      this.instances.push(inst)
      const end = step.at * 1000 + (inst.duration || 0) + (inst.delay || 0)
      return Math.max(max, end)
    }, 0)

    if (onComplete) {
      setTimeout(onComplete, maxEnd)
    }
    return this
  }

  stop() {
    this.instances.forEach(inst => {
      try { inst.pause() } catch {}
    })
    this.instances = []
  }

  get totalDuration(): number {
    return this.steps.reduce((max, step) => {
      // 估算每个动画的结束时间
      return Math.max(max, step.at + 1.5)  // 保守估计每个动画约1.5秒
    }, 0)
  }
}
```

- [ ] **Step 3: 验证 TypeScript 编译**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web
npx tsc --noEmit
```
Expected: No type errors

- [ ] **Step 4: Commit**

```bash
git add web/src/animation/
git commit -m "feat: animation primitives (fadeIn, slideIn, scaleIn, typewriter, staggerList) + SceneTimeline engine"
```

---

### Task 6: 标题场景组件 (TitleScene)

**Files:**
- Create: `web/src/scenes/TitleScene.tsx`

- [ ] **Step 1: 创建 `web/src/scenes/TitleScene.tsx`**

```tsx
import { useEffect, useRef } from 'react'
import { fadeIn, scaleIn, slideIn } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function TitleScene({ slide, width = 1920, height = 1080 }: Props) {
  const titleRef = useRef<HTMLHeadingElement>(null)
  const subtitleRef = useRef<HTMLParagraphElement>(null)
  const decorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()

    // 0.0s: 装饰线淡入
    if (decorRef.current) {
      tl.add('decor', () => fadeIn(decorRef.current!, 600), 0)
    }

    // 0.3s: 标题弹性放大
    if (titleRef.current) {
      tl.add('title', () => scaleIn(titleRef.current!, 800), 0.3)
    }

    // 1.2s: 副标题滑入
    if (subtitleRef.current && slide.text) {
      tl.add('subtitle', () => slideIn(subtitleRef.current!, 'bottom', 600), 1.2)
    }

    tl.play()

    return () => tl.stop()
  }, [slide])

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d1b2a 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
    }}>
      {/* 背景浮动装饰圆 */}
      <div style={{
        position: 'absolute', top: '15%', right: '10%',
        width: 300, height: 300, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(0,200,255,0.08), transparent)',
      }} />
      <div style={{
        position: 'absolute', bottom: '20%', left: '8%',
        width: 200, height: 200, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(120,80,255,0.06), transparent)',
      }} />

      {/* 装饰线 */}
      <div ref={decorRef} style={{
        width: 160, height: 3,
        background: 'linear-gradient(90deg, transparent, #00c8ff, transparent)',
        marginBottom: 40, opacity: 0,
      }} />

      {/* 标题 */}
      <h1 ref={titleRef} style={{
        fontSize: 72, fontWeight: 700, color: '#ffffff',
        textAlign: 'center', maxWidth: '80%',
        textShadow: '0 2px 20px rgba(0,200,255,0.3)',
        opacity: 0,
      }}>
        {slide.title || slide.text}
      </h1>

      {/* 副标题 */}
      {slide.text && slide.title && (
        <p ref={subtitleRef} style={{
          fontSize: 28, color: 'rgba(255,255,255,0.7)',
          marginTop: 24, textAlign: 'center', maxWidth: '60%',
          opacity: 0,
        }}>
          {slide.text}
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: 验证构建**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web && npx tsc --noEmit
```
Expected: No type errors

- [ ] **Step 3: Commit**

```bash
git add web/src/scenes/TitleScene.tsx
git commit -m "feat: TitleScene component with gradient bg, scale-in title, slide-in subtitle"
```

---

### Task 7: 要点列举 + 图片展示 + 片尾场景

**Files:**
- Create: `web/src/scenes/BulletsScene.tsx`
- Create: `web/src/scenes/ImageScene.tsx`
- Create: `web/src/scenes/OutroScene.tsx`

- [ ] **Step 1: 创建 `web/src/scenes/BulletsScene.tsx`**

```tsx
import { useEffect, useRef } from 'react'
import { slideIn, staggerList } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function BulletsScene({ slide, width = 1920, height = 1080 }: Props) {
  const titleRef = useRef<HTMLHeadingElement>(null)
  const itemsRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()

    if (titleRef.current && slide.title) {
      tl.add('title', () => slideIn(titleRef.current!, 'left', 600), 0)
    }

    if (itemsRef.current) {
      const items = itemsRef.current.querySelectorAll('li')
      tl.add('items', () => staggerList(items, 500, 250), 0.5)
    }

    tl.play()
    return () => tl.stop()
  }, [slide])

  // 将文本按换行或分号拆分为列表项
  const items = slide.text
    .split(/[\n；;]/)
    .map(s => s.trim())
    .filter(Boolean)

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(160deg, #0d1117 0%, #161b22 100%)',
      display: 'flex', flexDirection: 'column', justifyContent: 'center',
      padding: '100px 140px',
    }}>
      {slide.title && (
        <h2 ref={titleRef} style={{
          fontSize: 48, fontWeight: 700, color: '#00c8ff',
          marginBottom: 40, opacity: 0,
        }}>
          {slide.title}
        </h2>
      )}
      <ul ref={itemsRef} style={{ listStyle: 'none', padding: 0 }}>
        {items.map((item, i) => (
          <li key={i} style={{
            fontSize: 32, color: '#e6edf3', marginBottom: 20,
            paddingLeft: 40, position: 'relative', opacity: 0,
          }}>
            <span style={{
              position: 'absolute', left: 0, color: '#00c8ff',
              fontSize: 24, top: 4,
            }}>
              ●
            </span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 2: 创建 `web/src/scenes/ImageScene.tsx`**

```tsx
import { useEffect, useRef } from 'react'
import { fadeIn, slideIn } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function ImageScene({ slide, width = 1920, height = 1080 }: Props) {
  const imgRef = useRef<HTMLDivElement>(null)
  const captionRef = useRef<HTMLParagraphElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()
    if (imgRef.current) tl.add('img', () => fadeIn(imgRef.current!, 1000), 0)
    if (captionRef.current && slide.text) {
      tl.add('caption', () => slideIn(captionRef.current!, 'bottom', 600), 1.0)
    }
    tl.play()
    return () => tl.stop()
  }, [slide])

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(180deg, #0d1117 0%, #010409 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      position: 'relative',
    }}>
      <div ref={imgRef} style={{
        width: '80%', height: '60%',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        borderRadius: 16, border: '1px solid rgba(255,255,255,0.08)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        opacity: 0,
      }}>
        <span style={{ color: '#8b949e', fontSize: 24 }}>
          🖼️ {slide.keywords?.[0] || '图片区域'}
        </span>
      </div>
      {slide.text && (
        <p ref={captionRef} style={{
          fontSize: 28, color: 'rgba(255,255,255,0.7)',
          marginTop: 32, textAlign: 'center', maxWidth: '70%',
          opacity: 0,
        }}>
          {slide.text}
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 3: 创建 `web/src/scenes/OutroScene.tsx`**

```tsx
import { useEffect, useRef } from 'react'
import { fadeIn, scaleIn } from '../animation/primitives'
import { SceneTimeline } from '../animation/timeline'
import type { SlideItem } from '../types'

interface Props {
  slide: SlideItem
  width?: number
  height?: number
}

export default function OutroScene({ slide, width = 1920, height = 1080 }: Props) {
  const textRef = useRef<HTMLHeadingElement>(null)
  const lineRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const tl = new SceneTimeline()
    if (lineRef.current) tl.add('line', () => fadeIn(lineRef.current!, 600), 0)
    if (textRef.current) tl.add('text', () => scaleIn(textRef.current!, 1000), 0.5)
    tl.play()
    return () => tl.stop()
  }, [slide])

  return (
    <div style={{
      width, height,
      background: 'linear-gradient(135deg, #0a0a2e 0%, #0d1b2a 100%)',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
    }}>
      <div ref={lineRef} style={{
        width: 120, height: 3,
        background: 'linear-gradient(90deg, transparent, #00c8ff, transparent)',
        marginBottom: 32, opacity: 0,
      }} />
      <h1 ref={textRef} style={{
        fontSize: 56, fontWeight: 700, color: '#ffffff',
        textAlign: 'center', opacity: 0,
      }}>
        {slide.title || slide.text || '感谢观看'}
      </h1>
    </div>
  )
}
```

- [ ] **Step 4: 验证构建**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web && npx tsc --noEmit
```
Expected: No type errors

- [ ] **Step 5: Commit**

```bash
git add web/src/scenes/BulletsScene.tsx web/src/scenes/ImageScene.tsx web/src/scenes/OutroScene.tsx
git commit -m "feat: BulletsScene, ImageScene, OutroScene components"
```

---

### Task 8: 预览面板 — 连接场景渲染

**Files:**
- Create: `web/src/components/PreviewPanel.tsx`

- [ ] **Step 1: 创建 `web/src/components/PreviewPanel.tsx`**

```tsx
import TitleScene from '../scenes/TitleScene'
import BulletsScene from '../scenes/BulletsScene'
import ImageScene from '../scenes/ImageScene'
import OutroScene from '../scenes/OutroScene'
import type { SlideItem } from '../types'

interface Props {
  slides: SlideItem[]
  title: string
  currentSlide: number
}

export default function PreviewPanel({ slides, title, currentSlide }: Props) {
  if (slides.length === 0) {
    return (
      <div style={{ textAlign: 'center', color: '#8b949e' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🎬</div>
        <p>在左侧输入文案并点击"解析"</p>
        <p>即可在此预览视频动画效果</p>
      </div>
    )
  }

  const slide = slides[currentSlide]
  if (!slide) return null

  // 预览缩放: 1920x1080 → 容器内自适应
  const scale = 0.45

  const sceneComponent = (() => {
    switch (slide.type) {
      case 'title': return <TitleScene slide={slide} />
      case 'bullets': return <BulletsScene slide={slide} />
      case 'image': return <ImageScene slide={slide} />
      case 'outro': return <OutroScene slide={slide} />
      default: return <div style={{ color: '#8b949e' }}>未知场景类型: {slide.type}</div>
    }
  })()

  return (
    <div style={{
      transform: `scale(${scale})`,
      transformOrigin: 'center center',
      borderRadius: 8,
      overflow: 'hidden',
      boxShadow: '0 4px 40px rgba(0,0,0,0.5)',
    }}>
      {sceneComponent}
    </div>
  )
}
```

- [ ] **Step 2: 验证构建**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web && npx tsc --noEmit && npm run build
```
Expected: No type errors, build succeeds

- [ ] **Step 3: Commit**

```bash
git add web/src/components/PreviewPanel.tsx
git commit -m "feat: PreviewPanel connects scene components with scale transform"
```

---

## Phase 3: 渲染管线 (Task 9–11)

### Task 9: Playwright 渲染引擎

**Files:**
- Create: `renderer/__init__.py`
- Create: `renderer/playwright_renderer.py`

- [ ] **Step 1: 创建 `renderer/__init__.py`**

```python
"""V2 Renderer — HTML5 Canvas to Video via Playwright + FFmpeg"""
```

- [ ] **Step 2: 创建 `renderer/playwright_renderer.py`**

```python
"""
Playwright 渲染引擎
将场景列表编译为 HTML 页面 → 无头浏览器逐帧截图 → 输出 PNG 序列
"""
import json
import os
import subprocess
import time
from pathlib import Path

# 场景 HTML 模板
SCENE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Microsoft YaHei','PingFang SC',sans-serif;overflow:hidden}}
.scene{{width:{W}px;height:{H}px;position:relative;overflow:hidden}}
</style>
</head>
<body>
<div id="scene" class="scene"></div>
<script>
// 场景数据
const SCENE = {scene_json};
const W = {W}, H = {H};

// ===== 动画原语 (精简版, 用于渲染) =====
function fadeIn(el, duration, delay) {{
  el.style.transition = `opacity ${{duration}}ms ease-out`;
  el.style.transitionDelay = `${{delay}}ms`;
  el.style.opacity = '1';
}}
function scaleIn(el, duration, delay) {{
  el.style.transition = `transform ${{duration}}ms cubic-bezier(0.34,1.56,0.64,1), opacity ${{duration}}ms ease-out`;
  el.style.transitionDelay = `${{delay}}ms`;
  el.style.transform = 'scale(1)';
  el.style.opacity = '1';
}}
function slideIn(el, from, duration, delay) {{
  el.style.transition = `transform ${{duration}}ms ease-out, opacity ${{duration}}ms ease-out`;
  el.style.transitionDelay = `${{delay}}ms`;
  el.style.transform = 'translate(0, 0)';
  el.style.opacity = '1';
}}

// ===== 场景渲染 =====
function renderScene() {{
  const container = document.getElementById('scene');
  const s = SCENE;

  if (s.type === 'title') {{
    container.style.background = 'linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #0d1b2a 100%)';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';

    const title = document.createElement('h1');
    title.textContent = s.title || s.text;
    title.style.cssText = 'font-size:72px;color:#fff;text-align:center;max-width:80%;opacity:0;transform:scale(0.3)';
    container.appendChild(title);
    scaleIn(title, 800, 300);

    if (s.text && s.title) {{
      const sub = document.createElement('p');
      sub.textContent = s.text;
      sub.style.cssText = 'font-size:28px;color:rgba(255,255,255,0.7);margin-top:24px;opacity:0;transform:translateY(40px)';
      container.appendChild(sub);
      slideIn(sub, 'bottom', 600, 1200);
    }}
  }}

  else if (s.type === 'bullets') {{
    container.style.background = 'linear-gradient(160deg, #0d1117 0%, #161b22 100%)';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.justifyContent = 'center';
    container.style.padding = '100px 140px';

    if (s.title) {{
      const h2 = document.createElement('h2');
      h2.textContent = s.title;
      h2.style.cssText = 'font-size:48px;color:#00c8ff;margin-bottom:40px;opacity:0;transform:translateX(-60px)';
      container.appendChild(h2);
      slideIn(h2, 'left', 600, 0);
    }}

    const items = s.text.split(/[\\n；;]/).map(x => x.trim()).filter(Boolean);
    const ul = document.createElement('ul');
    ul.style.cssText = 'list-style:none;padding:0';
    items.forEach((item, i) => {{
      const li = document.createElement('li');
      li.textContent = item;
      li.style.cssText = 'font-size:32px;color:#e6edf3;margin-bottom:20px;padding-left:40px;opacity:0;transform:translateY(30px)';
      ul.appendChild(li);
      slideIn(li, 'bottom', 500, 500 + i * 250);
    }});
    container.appendChild(ul);
  }}

  else if (s.type === 'image') {{
    container.style.background = 'linear-gradient(180deg, #0d1117 0%, #010409 100%)';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';

    const imgDiv = document.createElement('div');
    imgDiv.style.cssText = 'width:80%;height:60%;background:linear-gradient(135deg,#1a1a2e,#16213e);border-radius:16px;opacity:0';
    container.appendChild(imgDiv);
    fadeIn(imgDiv, 1000, 0);

    if (s.text) {{
      const cap = document.createElement('p');
      cap.textContent = s.text;
      cap.style.cssText = 'font-size:28px;color:rgba(255,255,255,0.7);margin-top:32px;text-align:center;opacity:0;transform:translateY(40px)';
      container.appendChild(cap);
      slideIn(cap, 'bottom', 600, 1000);
    }}
  }}

  else if (s.type === 'outro') {{
    container.style.background = 'linear-gradient(135deg, #0a0a2e 0%, #0d1b2a 100%)';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';

    const text = document.createElement('h1');
    text.textContent = s.title || s.text || '感谢观看';
    text.style.cssText = 'font-size:56px;color:#fff;opacity:0;transform:scale(0.3)';
    container.appendChild(text);
    scaleIn(text, 1000, 500);
  }}
}}

window.addEventListener('DOMContentLoaded', renderScene);
</script>
</body>
</html>"""


def build_scene_html(slide: dict, width: int = 1920, height: int = 1080) -> str:
    """将单个场景 JSON 编译为自包含 HTML 页面"""
    return SCENE_HTML_TEMPLATE.format(
        W=width, H=height,
        scene_json=json.dumps(slide, ensure_ascii=False),
    )


def render_scene_frames(
    slide: dict,
    output_dir: str,
    duration: float = 4.0,
    resolution: tuple = (1920, 1080),
    fps: int = 30,
) -> list[str]:
    """
    用 Playwright 渲染一个场景的每一帧

    返回: [frame_0001.png, frame_0002.png, ...]
    """
    from playwright.sync_api import sync_playwright

    W, H = resolution
    html = build_scene_html(slide, W, H)
    html_path = os.path.join(output_dir, f"scene_{slide.get('type', 'unknown')}.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    os.makedirs(output_dir, exist_ok=True)
    frame_paths = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": W, "height": H})
        page.goto(f"file:///{html_path.replace(chr(92), '/')}")

        # 等待渲染完成
        page.wait_for_timeout(500)

        total_frames = int(duration * fps)
        for frame_idx in range(total_frames):
            elapsed = frame_idx / fps
            # 更新页面时间 (用于 CSS 动画进度)
            page.evaluate(f"document.documentElement.style.setProperty('--time', '{elapsed}s')")

            # 截图
            frame_path = os.path.join(output_dir, f"frame_{frame_idx:04d}.png")
            page.screenshot(path=frame_path)
            frame_paths.append(frame_path)

            # 等待到下一帧
            page.wait_for_timeout(int(1000 / fps))

        browser.close()

    return frame_paths


def frames_to_video(
    frame_dir: str,
    output_path: str,
    fps: int = 30,
    crf: int = 18,
) -> str:
    """用 FFmpeg 将 PNG 帧序列合成为 MP4"""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", os.path.join(frame_dir, "frame_%04d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", str(crf),
        "-pix_fmt", "yuv420p",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg frame-to-video failed: {result.stderr[-500:]}")
    return output_path
```

- [ ] **Step 2: 安装 Playwright**

Run:
```bash
pip install playwright
python -m playwright install chromium
```
Expected: Chromium installed successfully

- [ ] **Step 3: 验证导入**

Run:
```bash
cd F:/claude-deepseek/karpathy-video
python -c "from renderer.playwright_renderer import build_scene_html, render_scene_frames; print('Import OK')"
```
Expected: `Import OK`

- [ ] **Step 4: Commit**

```bash
git add renderer/
git commit -m "feat: Playwright renderer - scene JSON → HTML → frames → MP4"
```

---

### Task 10: 后端导出服务 (TTS + 渲染 + 合成)

**Files:**
- Create: `server/services/export_service.py`
- Create: `server/services/render_service.py`

- [ ] **Step 1: 创建 `server/services/render_service.py`**

```python
"""渲染服务 — 复用 V1 的 TTS 和字幕模块"""
import asyncio
import os
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent.parent


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
```

- [ ] **Step 2: 创建 `server/services/export_service.py`**

```python
"""视频导出编排服务"""
import asyncio
import os
import threading
from pathlib import Path
import uuid

PROJECT_DIR = Path(__file__).parent.parent.parent
OUTPUT_ROOT = PROJECT_DIR / "output"

# 内存中的任务状态 (简化版，后续可换 Redis)
_tasks: dict[str, dict] = {}


def queue_render(task_id: str, params: dict):
    """将渲染任务入队 (异步执行)"""
    _tasks[task_id] = {"status": "queued", "progress": 0}
    thread = threading.Thread(target=_run_render, args=(task_id, params), daemon=True)
    thread.start()


def get_status(task_id: str) -> dict:
    """查询渲染任务状态"""
    if task_id not in _tasks:
        return {"task_id": task_id, "status": "not_found", "progress": 0}
    return {"task_id": task_id, **_tasks[task_id]}


def _run_render(task_id: str, params: dict):
    """同步渲染流程"""
    try:
        slides = params["slides"]
        title = params["title"]
        voice = params.get("voice", "xiaoxiao")
        speed = params.get("speed", "+10%")
        resolution = tuple(params.get("resolution", [1920, 1080]))
        fps = params.get("fps", 30)

        safe_title = "".join(c if c.isalnum() or c in "._- " else "_" for c in title)[:50]
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

        # Step 2: 渲染每个场景为帧序列
        _tasks[task_id] = {"status": "rendering_frames", "progress": 30}
        from renderer.playwright_renderer import render_scene_frames, frames_to_video

        scene_videos = []
        for i, (slide, result) in enumerate(zip(slides, slide_results)):
            duration = result["meta"]["duration"]
            scene_frame_dir = str(out_dir / f"scene_{i:02d}")
            os.makedirs(scene_frame_dir, exist_ok=True)

            render_scene_frames(slide, scene_frame_dir, duration, resolution, fps)

            scene_video = str(out_dir / f"scene_{i:02d}.mp4")
            frames_to_video(scene_frame_dir, scene_video, fps)
            scene_videos.append(scene_video)

            _tasks[task_id]["progress"] = 30 + int(40 * (i + 1) / len(slides))

        # Step 3: 拼接所有场景 + 音频
        _tasks[task_id] = {"status": "compositing", "progress": 75}
        final_video = str(out_dir / f"{safe_title}.mp4")

        # 用 FFmpeg concat 拼接所有场景视频
        concat_list = str(out_dir / "concat.txt")
        with open(concat_list, "w") as f:
            for v in scene_videos:
                f.write(f"file '{v.replace(chr(92), '/')}'\n")

        import subprocess
        # 先合视频
        temp_video = str(out_dir / "temp_merged.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list, "-c:v", "libx264", "-preset", "medium",
            "-crf", "18", temp_video,
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

        # 合并音频
        from video_composer import concat_audio_files
        audio_paths = [r["audio_path"] for r in slide_results]
        silence_paths = [r["silence_path"] for r in slide_results]
        combined_audio = str(out_dir / "combined_audio.mp3")
        concat_audio_files(audio_paths, silence_paths, combined_audio)

        # 视频 + 音频合成
        subprocess.run([
            "ffmpeg", "-y", "-i", temp_video, "-i", combined_audio,
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-shortest",
            final_video,
        ], capture_output=True, text=True, encoding='utf-8', errors='replace')

        # Step 4: 字幕烧录
        _tasks[task_id] = {"status": "compositing", "progress": 90}
        from subtitle_generator import generate_srt
        srt_path = str(out_dir / "subtitles.srt")
        generate_srt(slide_results, srt_path)

        from video_composer import burn_subtitles
        subtitled_video = str(out_dir / f"{safe_title}_subtitled.mp4")
        burn_subtitles(final_video, srt_path, subtitled_video)

        # 清理
        for v in scene_videos:
            try: os.remove(v)
            except: pass
        try: os.remove(temp_video)
        except: pass
        try: os.remove(concat_list)
        except: pass

        _tasks[task_id] = {
            "status": "done",
            "progress": 100,
            "output_path": subtitled_video,
        }

    except Exception as e:
        _tasks[task_id] = {"status": "error", "progress": 0, "error": str(e)}
```

- [ ] **Step 3: 验证导入**

Run:
```bash
cd F:/claude-deepseek/karpathy-video
python -c "from server.services.export_service import queue_render, get_status; print('Import OK')"
```
Expected: `Import OK`

- [ ] **Step 4: Commit**

```bash
git add server/services/export_service.py server/services/render_service.py
git commit -m "feat: export_service orchestrator + render_service for TTS/subtitle integration"
```

---

### Task 11: 前端导出面板

**Files:**
- Create: `web/src/components/ExportPanel.tsx`

- [ ] **Step 1: 创建 `web/src/components/ExportPanel.tsx`**

```tsx
import { useState, useEffect, useRef } from 'react'
import { startRender, getRenderStatus } from '../api'
import type { SlideItem, RenderStatus } from '../types'

interface Props {
  slides: SlideItem[]
  title: string
}

export default function ExportPanel({ slides, title }: Props) {
  const [voice, setVoice] = useState('xiaoxiao')
  const [taskId, setTaskId] = useState('')
  const [status, setStatus] = useState<RenderStatus | null>(null)
  const [exporting, setExporting] = useState(false)
  const intervalRef = useRef<number>(0)

  const VOICES = [
    { id: 'xiaoxiao', name: '晓晓 (女) — 温暖自然' },
    { id: 'yunyang', name: '云扬 (男) — 专业可靠' },
    { id: 'yunxi', name: '云希 (男) — 阳光活泼' },
  ]

  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [])

  const pollStatus = (id: string) => {
    intervalRef.current = window.setInterval(async () => {
      try {
        const s = await getRenderStatus(id)
        setStatus(s)
        if (s.status === 'done' || s.status === 'error') {
          clearInterval(intervalRef.current)
          setExporting(false)
        }
      } catch {
        clearInterval(intervalRef.current)
        setExporting(false)
      }
    }, 2000)
  }

  const handleExport = async () => {
    if (slides.length === 0) return
    setExporting(true)
    try {
      const result = await startRender(slides, title, voice)
      setTaskId(result.task_id)
      pollStatus(result.task_id)
    } catch (err) {
      console.error('导出失败:', err)
      alert('导出失败，请确认后端已启动')
      setExporting(false)
    }
  }

  return (
    <div className="export-panel">
      <h3>🎬 导出视频</h3>

      <div className="field">
        <label>配音音色</label>
        <select value={voice} onChange={e => setVoice(e.target.value)} className="select">
          {VOICES.map(v => (
            <option key={v.id} value={v.id}>{v.name}</option>
          ))}
        </select>
      </div>

      <div style={{ marginTop: 16 }}>
        <p style={{ fontSize: 12, color: '#8b949e', marginBottom: 8 }}>
          场景数: {slides.length} | 标题: {title || '未设置'}
        </p>
      </div>

      <button
        onClick={handleExport}
        disabled={exporting || slides.length === 0}
        className="btn btn-primary"
        style={{ width: '100%', marginTop: 12 }}
      >
        {exporting ? '⏳ 生成中...' : '🚀 生成视频'}
      </button>

      {status && (
        <div style={{ marginTop: 16, padding: 12, background: '#161b22', borderRadius: 8 }}>
          <StatusBar status={status} />
        </div>
      )}
    </div>
  )
}

function StatusBar({ status }: { status: RenderStatus }) {
  const labels: Record<string, string> = {
    queued: '排队中...',
    generating_audio: '🎤 生成配音...',
    rendering_frames: '🎨 渲染动画帧...',
    compositing: '🎬 合成视频...',
    done: '✅ 完成!',
    error: '❌ 出错',
  }

  return (
    <div>
      <p style={{ fontSize: 14, fontWeight: 600 }}>{labels[status.status] || status.status}</p>
      <div style={{ background: '#30363d', borderRadius: 4, height: 6, marginTop: 8 }}>
        <div style={{
          width: `${status.progress}%`, height: 6,
          background: 'linear-gradient(90deg, #00c8ff, #6366f1)',
          borderRadius: 4, transition: 'width 1s ease',
        }} />
      </div>
      {status.output_path && (
        <p style={{ fontSize: 12, color: '#8b949e', marginTop: 8 }}>
          文件: {status.output_path}
        </p>
      )}
      {status.error && (
        <p style={{ fontSize: 12, color: '#f85149', marginTop: 8 }}>
          {status.error}
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: 验证构建**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web && npx tsc --noEmit && npm run build
```
Expected: No type errors, build succeeds

- [ ] **Step 3: Commit**

```bash
git add web/src/components/ExportPanel.tsx
git commit -m "feat: ExportPanel with voice selection, progress bar, status polling"
```

---

## Phase 4: 桌面打包 (Task 12–13)

### Task 12: 桌面壳入口 + PyInstaller 构建

**Files:**
- Create: `app.py`
- Create: `build.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 更新 `requirements.txt`**

```
edge-tts>=7.2.0
pillow>=11.0.0
moviepy>=2.0.0
requests>=2.32.0
beautifulsoup4>=4.12.0
numpy>=2.0.0
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
playwright>=1.48.0
```

- [ ] **Step 2: 创建 `app.py`**

```python
"""
桌面壳入口 — PyInstaller 打包入口
启动后端 → 打开浏览器 → 保持运行
"""
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path


def find_chromium() -> str | None:
    """查找系统中可用的 Chromium/Chrome"""
    candidates = []
    if sys.platform == 'win32':
        candidates = [
            os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright\chromium-*"),
            os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES(x86)%\Microsoft\Edge\Application\msedge.exe"),
        ]
    for c in candidates:
        import glob
        matches = glob.glob(c)
        if matches:
            # 优先取 playwright 的 chromium
            for m in sorted(matches, reverse=True):
                chrome_path = os.path.join(m, "chrome.exe") if os.path.isdir(m) else m
                if os.path.exists(chrome_path):
                    return chrome_path
    return None


def main():
    print("=" * 50)
    print("  AI 科普视频生成器 V2")
    print("=" * 50)
    print()

    # 查找浏览器
    browser_path = find_chromium()
    if browser_path:
        print(f"[Browser] {browser_path}")

    # 设置 Playwright 使用已有 Chromium
    if browser_path:
        os.environ["PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"] = browser_path

    # 启动 FastAPI 服务器 (在后台线程)
    def run_server():
        import uvicorn
        from server.main import app
        uvicorn.run(app, host="127.0.0.1", port=8765, log_level="warning")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 等待服务器就绪
    time.sleep(2)

    # 打开浏览器
    url = "http://127.0.0.1:8765"
    print(f"[App] 打开浏览器: {url}")
    webbrowser.open(url)

    print("[App] 服务器运行中，关闭此窗口即可退出")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[App] 正在退出...")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 创建 `build.py`**

```python
"""
PyInstaller 打包脚本
用法: python build.py
输出: dist/AI视频生成器.exe
"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent


def build_frontend():
    """构建前端静态文件"""
    web_dir = PROJECT_DIR / "web"
    if not (web_dir / "node_modules").exists():
        print("[Build] 安装前端依赖...")
        subprocess.run(["npm", "install"], cwd=str(web_dir), check=True)

    print("[Build] 构建前端...")
    subprocess.run(["npm", "run", "build"], cwd=str(web_dir), check=True)

    dist_dir = web_dir / "dist"
    if dist_dir.exists():
        print(f"[Build] 前端构建完成: {dist_dir}")
    else:
        raise RuntimeError("前端构建失败: dist 目录不存在")


def build_exe():
    """PyInstaller 打包"""
    print("[Build] PyInstaller 打包...")

    # 确保 playwright 浏览器已安装
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                   check=True)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AI视频生成器",
        "--onefile",
        "--console",
        "--add-data", f"web/dist{';'}web/dist",
        "--add-data", f"renderer{';'}renderer",
        "--add-data", f"server{';'}server",
        "--add-data", f"tts_engine.py{';'}.",  
        "--add-data", f"subtitle_generator.py{';'}.",
        "--add-data", f"media_fetcher.py{';'}.",
        "--add-data", f"video_composer.py{';'}.",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "fastapi",
        "--hidden-import", "playwright",
        "--hidden-import", "edge_tts",
        "--hidden-import", "PIL",
        "--hidden-import", "moviepy",
        "--hidden-import", "bs4",
        "app.py",
    ]

    subprocess.run(cmd, cwd=str(PROJECT_DIR), check=True)
    print(f"[Build] 打包完成: {PROJECT_DIR}/dist/AI视频生成器.exe")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-frontend", action="store_true",
                        help="跳过前端构建 (如果已手动构建)")
    args = parser.parse_args()

    if not args.skip_frontend:
        build_frontend()
    build_exe()
```

- [ ] **Step 4: 验证 `app.py` 导入**

Run:
```bash
cd F:/claude-deepseek/karpathy-video
python -c "from app import find_chromium; print('app.py OK')"
```
Expected: `app.py OK`

- [ ] **Step 5: Commit**

```bash
git add app.py build.py requirements.txt
git commit -m "feat: desktop shell entry (app.py) + PyInstaller build script"
```

---

### Task 13: 端到端验证

- [ ] **Step 1: 构建前端**

Run:
```bash
cd F:/claude-deepseek/karpathy-video/web
npm run build
```
Expected: Build succeeds

- [ ] **Step 2: 启动后端，验证前端可访问**

Run (in background or separate terminal):
```bash
cd F:/claude-deepseek/karpathy-video
python -m server.main
```
Open browser to `http://127.0.0.1:8765` — should see the React app

- [ ] **Step 3: 测试 API 解析**

Run:
```bash
curl -X POST http://127.0.0.1:8765/api/parse \
  -H "Content-Type: application/json" \
  -d '{"content": "# 测试\n## 第一页\n这是第一页内容\n\n## 第二页\n这是第二页内容", "title": "测试视频"}'
```
Expected: Returns JSON with `slides` array of 4 items (title + 2 bullets + outro)

- [ ] **Step 4: 测试完整渲染 (小型)**

Run:
```bash
cd F:/claude-deepseek/karpathy-video
python -c "
import asyncio, json
from server.services.export_service import _run_render

params = {
    'title': '测试', 'voice': 'xiaoxiao', 'speed': '+10%',
    'resolution': [1920, 1080], 'fps': 30,
    'slides': [
        {'type': 'title', 'title': '测试标题', 'text': '副标题测试', 'keywords': ['test']},
        {'type': 'outro', 'title': '谢谢', 'text': '', 'keywords': []},
    ]
}
_run_render('test123', params)
from server.services.export_service import get_status
print(json.dumps(get_status('test123'), ensure_ascii=False, indent=2))
"
```
Expected: Status returns `done` with `output_path`

- [ ] **Step 5: Commit (if any changes)**

```bash
git status
```

---

## Phase 5: 后续迭代 (规划中,不在本计划)

以下功能在 MVP 完成后作为第二阶段：

1. **剩余 6 种场景类型** — Concept, Compare, Flow, Chart, Quote, Timeline
2. **图片管道集成** — 前端调用后端爬图/API 生图，图片在场景中显示
3. **场景拖拽排序** — Timeline 组件支持拖拽重排
4. **自定义动画参数** — 每个场景可调时间、缓动、风格
5. **API Key 管理页面** — 设置中配置 DALL·E/通义 API Key
6. **PyInstaller 实际打包** — 生成可分发的 .exe 文件
7. **动画引擎升级** — CSS 动画 → Canvas 逐帧精确控制，支持更复杂动画
```

- [ ] **Step 6: Commit**

(handled above)

---

## 计划自检

**1. Spec 覆盖:**
- [x] 整体架构 → Task 1 (后端) + Task 2 (前端)
- [x] 场景/动画系统 → Task 5-8 (动画原语 + 4种场景组件)
- [x] 图片流水线 → 后续迭代 (本阶段先用占位符，爬虫复用 V1)
- [x] 桌面打包 → Task 12 (app.py + build.py)
- [x] 数据流 → Task 9-11 (渲染管线 + 导出服务)

**2. 占位符扫描:** 无 TBD/TODO

**3. 类型一致性:** 
- `SlideItem` 类型在 `web/src/types.ts` (Task 2) 和 `server/routes.py` (Task 1) 中一致
- `SceneTimeline` API 在 Task 5 定义，Task 6-7 使用
- `server/services/export_service.py` 导入的 `render_scene_frames` 在 Task 9 定义

**4. 复用 V1 模块确认:**
- `tts_engine.py` → Task 10 复用 ✅
- `subtitle_generator.py` → Task 10 复用 ✅
- `media_fetcher.py` → 后续集成 ✅
- `video_composer.py` (burn_subtitles, concat_audio_files) → Task 10 复用 ✅
