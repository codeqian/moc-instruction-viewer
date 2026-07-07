"""模型相关 API 路由"""

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse

from config import SOURCE_DIR, PACKED_CACHE_DIR, STEPS_CACHE_DIR
from services.model_service import ModelService
from services.pack_service import PackService
from services.step_service import StepService
from services.cache_service import CacheService

router = APIRouter(prefix="/api/models", tags=["models"])

model_service = ModelService(SOURCE_DIR)
cache_service = CacheService(PACKED_CACHE_DIR, STEPS_CACHE_DIR)
pack_service = PackService(model_service, cache_service)
step_service = StepService(model_service, cache_service, pack_service)

# 只允许数字和字母、下划线组成的 ID
_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def validate_model_id(model_id: str) -> None:
    """校验模型 ID 格式，防止路径遍历"""
    if not _ID_PATTERN.match(model_id):
        raise HTTPException(status_code=400, detail="无效的模型 ID")
    if ".." in model_id:
        raise HTTPException(status_code=400, detail="无效的模型 ID")


@router.get("/{model_id}/meta")
async def get_model_meta(model_id: str):
    """获取模型基础信息"""
    validate_model_id(model_id)

    if not model_service.check_model_exists(model_id):
        raise HTTPException(status_code=404, detail="模型不存在")

    meta = model_service.get_model_meta(model_id)
    meta["hasPackedCache"] = cache_service.packed_cache_exists(model_id)
    meta["hasSteps"] = step_service.source_has_steps(model_id)
    if meta["hasSteps"]:
        # 触发步骤缓存生成（如未生成）
        step_service.ensure_steps(model_id)
        meta["totalSteps"] = step_service.get_total_steps(model_id)
    else:
        meta["totalSteps"] = 0

    return meta


@router.get("/{model_id}/packed")
async def get_packed_model(model_id: str):
    """获取完整 Packed MPD 文件"""
    validate_model_id(model_id)

    if not model_service.check_model_exists(model_id):
        raise HTTPException(status_code=404, detail="模型不存在")

    cache_path = pack_service.ensure_packed(model_id)
    return FileResponse(
        cache_path,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "private, max-age=3600"},
    )


@router.get("/{model_id}/steps")
async def get_steps_manifest(model_id: str):
    """获取步骤清单"""
    validate_model_id(model_id)

    if not model_service.check_model_exists(model_id):
        raise HTTPException(status_code=404, detail="模型不存在")

    manifest = step_service.get_step_manifest(model_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="该模型无步骤信息")

    return manifest


@router.get("/{model_id}/steps/{step_no}")
async def get_step_model(model_id: str, step_no: int):
    """获取某一步的累计 Packed MPD"""
    validate_model_id(model_id)

    if not model_service.check_model_exists(model_id):
        raise HTTPException(status_code=404, detail="模型不存在")

    if not step_service.steps_cache_exists(model_id):
        raise HTTPException(status_code=404, detail="该模型无步骤信息")

    step_path = step_service.get_step_file(model_id, step_no)
    if step_path is None:
        raise HTTPException(status_code=404, detail="步骤不存在")

    return FileResponse(
        step_path,
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "private, max-age=3600"},
    )
