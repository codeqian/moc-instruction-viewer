"""依赖解析器 —— 根据零件引用在 LDraw 零件库中查找依赖文件并递归解析"""

from pathlib import Path

from ldraw.parser import PartReference


class DependencyResolver:
    """解析 LDraw 零件引用，在零件库中查找依赖文件"""

    # 查找目录优先级
    _SEARCH_DIRS = ["parts", "p", "models"]

    def __init__(self, ldraw_lib_dir: Path):
        self.lib_dir = ldraw_lib_dir

    def resolve_all(self, references: list[PartReference]) -> dict[str, str]:
        """解析所有引用，返回依赖文件字典

        Returns:
            dict[str, str]: {filename: file_content}
        """
        resolved: dict[str, str] = {}
        visited: set[str] = set()

        for ref in references:
            self._resolve_recursive(ref.filename, resolved, visited)

        return resolved

    def _resolve_recursive(
        self, filename: str, resolved: dict[str, str], visited: set[str]
    ) -> None:
        """递归解析单个文件及其依赖"""
        if filename in visited or filename in resolved:
            return

        visited.add(filename)

        file_path = self.find_ldraw_file(filename)
        if file_path is None:
            return  # 零件缺失，记录日志但不中断

        content = file_path.read_text(encoding="utf-8", errors="ignore")
        resolved[filename] = content

        # 递归查找该文件的依赖
        from ldraw.parser import LDrawParser
        parser = LDrawParser()
        sub_refs = parser.collect_references(content)
        for sub_ref in sub_refs:
            self._resolve_recursive(sub_ref.filename, resolved, visited)

    def find_ldraw_file(self, filename: str) -> Path | None:
        """在 LDraw 零件库中查找文件"""
        # 直接路径查找
        direct = self.lib_dir / filename
        if direct.exists():
            return direct

        # 在子目录中查找
        for subdir in self._SEARCH_DIRS:
            candidate = self.lib_dir / subdir / filename
            if candidate.exists():
                return candidate

        # 递归查找（处理 p/48/ 等深层目录）
        for subdir in self._SEARCH_DIRS:
            base = self.lib_dir / subdir
            if base.exists():
                for found in base.rglob(filename):
                    return found

        return None
