"""打包服务 —— 生成完整 Packed MPD"""

from pathlib import Path

from services.model_service import ModelService
from services.cache_service import CacheService
from ldraw.parser import LDrawParser
from ldraw.dependency_resolver import DependencyResolver
from ldraw.mpd_writer import MPDWriter
from config import LDRAW_LIB_DIR


class PackService:
    """完整模型 Packed MPD 生成服务"""

    def __init__(self, model_service: ModelService, cache_service: CacheService):
        self.model_service = model_service
        self.cache_service = cache_service
        self.parser = LDrawParser()
        self.resolver = DependencyResolver(LDRAW_LIB_DIR)
        self.writer = MPDWriter()

    def ensure_packed(self, model_id: str) -> Path:
        """确保 packed MPD 缓存存在，不存在则生成"""
        cache_path = self.cache_service.get_packed_path(model_id)

        if not cache_path.exists() or self.cache_service.is_expired(cache_path):
            self.build_packed_mpd(model_id, cache_path)

        return cache_path

    def build_packed_mpd(self, model_id: str, output_path: Path) -> None:
        """生成完整 packed MPD 文件"""
        source_path = self.model_service.get_source_path(model_id)
        source_content = source_path.read_text(encoding="utf-8")

        # 解析文件块
        mpd_blocks = self.parser.parse_mpd_blocks(source_content)

        # 收集所有依赖引用
        references = self.parser.collect_references(source_content)

        # 解析依赖文件
        dependencies = self.resolver.resolve_all(references)

        # 写入 packed MPD
        packed_content = self.writer.write(
            main_content=source_content,
            dependency_files=dependencies,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(packed_content, encoding="utf-8")
