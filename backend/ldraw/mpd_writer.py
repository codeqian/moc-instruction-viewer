"""MPD 写入器 —— 将主模型和颜色配置合并为单个 MPD 文件

注意：不嵌入零件依赖。零件由前端 LDrawLoader 通过 /api/ldraw/ 按需加载。
因为 LDrawLoader 内部解析 0 FILE 行时 getRemainingString() 不带 trim，
导致嵌入文件名带前导空格，缓存键与查找键不匹配，零件全部被误判为缺失。
"""

from __future__ import annotations


class MPDWriter:
    """生成 MPD 文件（模型 + 颜色配置，零件走网络按需加载）"""

    def write(
        self,
        main_content: str,
        config_files: dict[str, str] | None = None,
    ) -> str:
        """合并主模型和颜色配置

        Args:
            main_content: 主模型 LDraw 内容
            config_files: 颜色配置文件 {filename: content}，如 LDConfig.ldr

        Returns:
            str: MPD 文本
        """
        lines: list[str] = []

        # 1. 主模型内容（不带 0 FILE 包裹）
        lines.append(main_content.strip())
        lines.append("")

        # 2. 颜色配置文件（嵌入，绕过 LDrawLoader 对 /ldraw/LDConfig.ldr 的额外请求）
        if config_files:
            for filename, content in config_files.items():
                lines.append(f"0 FILE {filename}")
                lines.append(content.strip())
                lines.append("")

        lines.append("0 NOFILE")

        return "\n".join(lines)
