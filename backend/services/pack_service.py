"""打包服务 —— 生成 MPD 文件（模型 + 颜色配置，零件由前端按需加载）"""

from __future__ import annotations

from pathlib import Path

from services.model_service import ModelService
from services.cache_service import CacheService
from ldraw.mpd_writer import MPDWriter
from config import LDRAW_LIB_DIR


class PackService:
    """MPD 生成服务"""

    def __init__(self, model_service: ModelService, cache_service: CacheService):
        self.model_service = model_service
        self.cache_service = cache_service
        self.writer = MPDWriter()

    def ensure_packed(self, model_id: str) -> Path:
        """确保 MPD 缓存存在，不存在则生成"""
        cache_path = self.cache_service.get_packed_path(model_id)

        if not cache_path.exists() or self.cache_service.is_expired(cache_path):
            self.build_mpd(model_id, cache_path)

        return cache_path

    def build_mpd(self, model_id: str, output_path: Path) -> None:
        """生成 MPD 文件"""
        source_path = self.model_service.get_source_path(model_id)
        source_content = source_path.read_text(encoding="utf-8")

        config_files = self._load_config_files()

        packed_content = self.writer.write(
            main_content=source_content,
            config_files=config_files,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(packed_content, encoding="utf-8")

    def _load_config_files(self) -> dict[str, str]:
        """加载 LDraw 颜色配置文件"""
        configs = {}
        for cfg_name in ("LDConfig.ldr", "LDCfgalt.ldr"):
            cfg_path = LDRAW_LIB_DIR / cfg_name
            if cfg_path.exists():
                configs[cfg_name] = cfg_path.read_text(encoding="utf-8", errors="ignore")
        return configs
