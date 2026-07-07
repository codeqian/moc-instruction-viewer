"""MPD 写入器 —— 将主模型内容和依赖文件合并为单个 packed MPD 文件"""


class MPDWriter:
    """生成打包后的 MPD 文件"""

    def write(self, main_content: str, dependency_files: dict[str, str]) -> str:
        """将主模型和依赖合并为一个 packed MPD 文本

        Args:
            main_content: 主模型 LDraw 内容
            dependency_files: {filename: content} 依赖文件字典

        Returns:
            str: 完整的 packed MPD 文本
        """
        lines: list[str] = []

        # 写入主模型内容
        lines.append("0 FILE main.ldr")
        lines.append(main_content.strip())

        # 写入依赖文件
        for filename, content in dependency_files.items():
            lines.append("")
            lines.append(f"0 FILE {filename}")
            lines.append(content.strip())

        # 标记结束
        lines.append("")
        lines.append("0 NOFILE")

        return "\n".join(lines)
