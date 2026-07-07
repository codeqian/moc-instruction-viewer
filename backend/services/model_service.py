"""模型管理服务 —— 根据 ID 查找模型、返回元信息"""

import os
from pathlib import Path
from datetime import datetime


class ModelService:
    """模型源文件查找与元信息管理"""

    def __init__(self, source_dir: Path):
        self.source_dir = source_dir

    def check_model_exists(self, model_id: str) -> bool:
        """检查模型是否存在（查找 .ldr 或 .mpd 文件）"""
        return self._find_source_file(model_id) is not None

    def get_model_meta(self, model_id: str) -> dict:
        """获取模型元信息"""
        source_path = self._find_source_file(model_id)
        if source_path is None:
            raise FileNotFoundError(f"模型 {model_id} 不存在")

        suffix = source_path.suffix.lower()
        format_type = "mpd" if suffix == ".mpd" else "ldr"

        stat = source_path.stat()

        return {
            "id": model_id,
            "name": source_path.stem,
            "format": format_type,
            "version": 1,
            "fileSize": stat.st_size,
            "updatedAt": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    def get_source_path(self, model_id: str) -> Path:
        """获取模型源文件路径"""
        source_path = self._find_source_file(model_id)
        if source_path is None:
            raise FileNotFoundError(f"模型 {model_id} 不存在")
        return source_path

    def _find_source_file(self, model_id: str) -> Path | None:
        """在 source 目录中查找匹配的 .ldr 或 .mpd 文件"""
        for ext in (".ldr", ".mpd", ".LDR", ".MPD"):
            candidate = self.source_dir / f"{model_id}{ext}"
            if candidate.exists():
                return candidate
        return None
