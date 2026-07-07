"""分步服务 —— 解析 0 STEP、生成步骤 manifest 和分步 packed MPD"""

import json
from pathlib import Path

from services.model_service import ModelService
from services.cache_service import CacheService
from services.pack_service import PackService
from ldraw.parser import LDrawParser
from ldraw.dependency_resolver import DependencyResolver
from ldraw.mpd_writer import MPDWriter
from config import LDRAW_LIB_DIR


class StepService:
    """分步浏览服务"""

    def __init__(
        self,
        model_service: ModelService,
        cache_service: CacheService,
        pack_service: PackService,
    ):
        self.model_service = model_service
        self.cache_service = cache_service
        self.pack_service = pack_service
        self.parser = LDrawParser()
        self.resolver = DependencyResolver(LDRAW_LIB_DIR)
        self.writer = MPDWriter()

    def ensure_steps(self, model_id: str) -> None:
        """确保步骤缓存存在，不存在则生成"""
        if not self.steps_cache_exists(model_id):
            self.build_step_packed_files(model_id)

    def get_total_steps(self, model_id: str) -> int:
        """获取模型总步骤数"""
        manifest = self.get_step_manifest(model_id)
        if manifest is None:
            return 0
        return manifest.get("totalSteps", 0)

    def get_step_manifest(self, model_id: str) -> dict | None:
        """获取步骤 manifest"""
        manifest_path = self.cache_service.get_manifest_path(model_id)
        if not manifest_path.exists():
            return None
        return json.loads(manifest_path.read_text(encoding="utf-8"))

    def get_step_file(self, model_id: str, step_no: int) -> Path | None:
        """获取某一步骤的 packed MPD 文件路径"""
        step_path = self.cache_service.get_step_path(model_id, step_no)
        if step_path.exists():
            return step_path
        return None

    def build_step_packed_files(self, model_id: str) -> None:
        """生成所有步骤的累计 packed MPD 文件"""
        source_path = self.model_service.get_source_path(model_id)
        source_content = source_path.read_text(encoding="utf-8")

        # 按 0 STEP 切分
        step_blocks = self.parser.split_by_step(source_content)

        step_dir = self.cache_service.ensure_step_dir(model_id)

        accumulated_lines: list[str] = []
        steps_info: list[dict] = []
        previous_parts: set[tuple[str, str]] = set()

        for index, block_lines in enumerate(step_blocks):
            step_no = index + 1
            accumulated_lines.extend(block_lines)

            # 收集当前步骤引用
            block_content = "\n".join(block_lines)
            block_refs = self.parser.collect_references(block_content)

            # 统计本步新增零件（与之前步骤比较）
            current_parts = {(r.filename, r.color) for r in block_refs}
            new_parts = current_parts - previous_parts
            previous_parts = current_parts

            # 聚合新增零件统计
            new_parts_agg: dict[str, dict] = {}
            for filename, color in new_parts:
                key = f"{filename}|{color}"
                if key not in new_parts_agg:
                    new_parts_agg[key] = {"partId": filename, "color": color, "count": 0}
                new_parts_agg[key]["count"] += 1

            steps_info.append({
                "step": step_no,
                "partCount": len(block_refs),
                "newParts": list(new_parts_agg.values()),
            })

            # 生成累计 packed MPD
            acc_content = "\n".join(accumulated_lines)
            refs = self.parser.collect_references(acc_content)
            deps = self.resolver.resolve_all(refs)
            packed = self.writer.write(main_content=acc_content, dependency_files=deps)

            step_path = self.cache_service.get_step_path(model_id, step_no)
            step_path.write_text(packed, encoding="utf-8")

        # 写入 manifest
        meta = self.model_service.get_model_meta(model_id)
        manifest = {
            "id": model_id,
            "name": meta["name"],
            "totalSteps": len(step_blocks),
            "steps": steps_info,
        }
        manifest_path = self.cache_service.get_manifest_path(model_id)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
