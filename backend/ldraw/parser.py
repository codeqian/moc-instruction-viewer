"""LDraw 文件解析器 —— 解析 MPD 文件块、零件引用、步骤标记"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class PartReference:
    """零件引用"""
    filename: str
    color: str = "16"


class LDrawParser:
    """LDraw / MPD 文件解析"""

    # 匹配零件引用行：1 <color> <x> <y> <z> <a> <b> <c> <d> <e> <f> <g> <h> <i> <file>
    _PART_LINE = re.compile(
        r"^\s*1\s+(\S+)\s+(?:\S+\s+){12}(\S+\.dat|\S+\.ldr|\S+\.mpd)",
        re.IGNORECASE,
    )

    # 匹配 0 FILE 块头
    _FILE_HEADER = re.compile(r"^\s*0\s+FILE\s+(.+)$", re.IGNORECASE)

    # 匹配 0 STEP 标记
    _STEP_MARKER = re.compile(r"^\s*0\s+STEP\s*$", re.IGNORECASE)

    def parse_mpd_blocks(self, content: str) -> dict[str, str]:
        """将 MPD 内容按 0 FILE 切分为块

        Returns:
            dict[str, str]: {filename: content}
        """
        blocks: dict[str, str] = {}
        current_file = "main.ldr"
        current_lines: list[str] = []

        for line in content.splitlines():
            m = self._FILE_HEADER.match(line)
            if m:
                if current_lines:
                    blocks[current_file] = "\n".join(current_lines)
                current_file = m.group(1).strip()
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            blocks[current_file] = "\n".join(current_lines)

        return blocks

    def collect_references(self, content: str) -> list[PartReference]:
        """收集 LDraw 内容中的零件引用"""
        refs: list[PartReference] = []
        for line in content.splitlines():
            m = self._PART_LINE.match(line)
            if m:
                refs.append(PartReference(
                    filename=m.group(2),
                    color=m.group(1),
                ))
        return refs

    def split_by_step(self, content: str) -> list[list[str]]:
        """按 0 STEP 切分 LDraw 内容

        Returns:
            list[list[str]]: 每一步对应的行列表
        """
        steps: list[list[str]] = []
        current_block: list[str] = []

        for line in content.splitlines():
            if self._STEP_MARKER.match(line):
                if current_block:
                    steps.append(current_block)
                current_block = [line]
            else:
                current_block.append(line)

        if current_block:
            steps.append(current_block)

        # 如果一步都不存在，整个文件算一步
        if not steps:
            return [content.splitlines()]

        return steps
