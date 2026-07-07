"""缓存管理服务 —— 管理 packed MPD 缓存文件的读写与失效判断"""

import time
from pathlib import Path

from config import CACHE_TTL


class CacheService:
    """Packed MPD 缓存管理"""

    def __init__(self, packed_cache_dir: Path, steps_cache_dir: Path):
        self.packed_cache_dir = packed_cache_dir
        self.steps_cache_dir = steps_cache_dir

    # ---- 完整模型缓存 ----

    def get_packed_path(self, model_id: str, version: int = 1) -> Path:
        """获取完整 packed MPD 缓存路径"""
        return self.packed_cache_dir / f"{model_id}.v{version}.packed.mpd"

    def packed_cache_exists(self, model_id: str, version: int = 1) -> bool:
        """检查完整模型缓存是否存在且有效"""
        cache_path = self.get_packed_path(model_id, version)
        return cache_path.exists() and not self.is_expired(cache_path)

    def is_expired(self, cache_path: Path) -> bool:
        """检查缓存是否过期"""
        if not cache_path.exists():
            return True
        age = time.time() - cache_path.stat().st_mtime
        return age > CACHE_TTL

    # ---- 步骤缓存 ----

    def get_step_dir(self, model_id: str) -> Path:
        """获取步骤缓存目录"""
        return self.steps_cache_dir / model_id

    def get_step_path(self, model_id: str, step_no: int) -> Path:
        """获取某一步骤的 packed MPD 缓存路径"""
        return self.get_step_dir(model_id) / f"step_{step_no:03d}.packed.mpd"

    def get_manifest_path(self, model_id: str) -> Path:
        """获取步骤 manifest 路径"""
        return self.get_step_dir(model_id) / "manifest.json"

    def steps_cache_exists(self, model_id: str) -> bool:
        """检查步骤缓存是否存在"""
        manifest_path = self.get_manifest_path(model_id)
        return manifest_path.exists()

    def ensure_step_dir(self, model_id: str) -> Path:
        """确保步骤缓存目录存在"""
        step_dir = self.get_step_dir(model_id)
        step_dir.mkdir(parents=True, exist_ok=True)
        return step_dir
