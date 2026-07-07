"""MPD 写入器 —— 将主模型内容和依赖文件合并为单个 packed MPD 文件"""


class MPDWriter:
    """生成打包后的 MPD 文件"""

    def write(
        self,
        main_content: str,
        dependency_files: dict[str, str],
        config_files: dict[str, str] | None = None,
    ) -> str:
        """将主模型和依赖合并为一个 packed MPD 文本

        ⚠️ 关键：主模型内容必须放在最前面（不用 0 FILE 包裹），
        因为 LDrawLoader 会跳过第一行的 0 FILE 指令（lineIndex > 0 检查）。

        Args:
            main_content: 主模型 LDraw 内容
            dependency_files: {filename: content} 依赖文件字典
            config_files: 颜色配置文件 {filename: content}，如 LDConfig.ldr

        Returns:
            str: 完整的 packed MPD 文本
        """
        lines: list[str] = []

        # 1. 主模型内容放在最前面（不带 0 FILE 包裹）
        #    LDrawLoader 会将其解析为"主文件"
        lines.append(main_content.strip())
        lines.append("")

        # 2. 颜色配置文件（作为嵌入子文件）
        if config_files:
            for filename, content in config_files.items():
                lines.append(f"0 FILE {filename}")
                lines.append(content.strip())
                lines.append("")

        # 3. 依赖零件文件
        for filename, content in dependency_files.items():
            lines.append(f"0 FILE {filename}")
            lines.append(content.strip())
            lines.append("")

        # 标记结束
        lines.append("0 NOFILE")

        return "\n".join(lines)
