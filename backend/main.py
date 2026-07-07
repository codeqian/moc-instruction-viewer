"""MOC Instruction Viewer — FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.model_api import router as model_router
from config import LDRAW_LIB_DIR

app = FastAPI(
    title="MOC Instruction Viewer",
    description="在线 LDR/MPD 拼搭图纸浏览服务",
    version="0.1.0",
)

# CORS 配置（开发阶段允许前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(model_router)

# 挂载 LDraw 零件库目录，作为 LDrawLoader 的兜底加载路径
if LDRAW_LIB_DIR.exists():
    app.mount("/api/ldraw", StaticFiles(directory=str(LDRAW_LIB_DIR)), name="ldraw")


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "version": "0.1.0"}
