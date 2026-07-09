"""API 路由定义"""
from fastapi import APIRouter
from pydantic import BaseModel

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
    # ── 可选工作流开关 ──
    subtitles: bool = True       # 是否生成字幕
    voiceover: bool = True       # 是否生成配音 (False=纯画面)
    bgTheme: str = "deep"        # 背景主题: deep/cosmic/ocean/sunset/forest/aurora/slate/violet

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
    task_id = str(uuid.uuid4())[:12]
    from server.services.export_service import queue_render
    queue_render(task_id, req.model_dump())
    return RenderResponse(task_id=task_id, status="queued")

@router.get("/render/{task_id}/status")
async def render_status(task_id: str):
    """查询渲染进度"""
    from server.services.export_service import get_status
    return get_status(task_id)
