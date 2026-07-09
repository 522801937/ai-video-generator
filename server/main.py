"""FastAPI 后端入口 — 托管前端静态文件 + API 路由"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from project_paths import get_project_root, get_web_dist_dir

WEB_DIR = get_web_dist_dir()

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
