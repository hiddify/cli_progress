#!/usr/bin/env python

from __future__ import annotations

import re
from typing import Any, Iterable, List, Optional, Tuple

import urwid


class ANSICanvas(urwid.canvas.Canvas):
    def __init__(self, size: Tuple[int, int], text_lines: List[str]) -> None:
        super().__init__()

        self.maxcols, self.maxrows = size

        self.text_lines = text_lines

    def cols(self) -> int:
        return self.maxcols

    def rows(self) -> int:
        return self.maxrows

    def content(
        self,
        trim_left: int = 0,
        trim_top: int = 0,
        cols: Optional[int] = None,
        rows: Optional[int] = None,
        attr_map: Optional[Any] = None,
    ) -> Iterable[List[Tuple[None, str, bytes]]]:
        assert cols is not None
        assert rows is not None

        for i in range(rows):
            if i < len(self.text_lines):
                text = self.text_lines[i]
            else:
                text = ""
            oversize = cols - len(escape_ansi(text))
            if oversize < 0:
                text = trancate_ansi(text,cols-1) +">\033[0m"
                oversize = 0

            padding = bytes().rjust(oversize)

            line = [(None, "U", text.encode("utf-8") + padding)]

            yield line


class ANSIWidget(urwid.Widget):
    _sizing = frozenset([urwid.widget.BOX])

    def __init__(self, text: str = "") -> None:
        self.lines = text.split("\n")

    def set_content(self, lines: List[str]) -> None:
        self.lines = lines
        self._invalidate()

    def render(self, size: Tuple[int, int], focus: bool = False) -> urwid.canvas.Canvas:
        canvas = ANSICanvas(size, self.lines)

        return canvas


def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def trancate_ansi(line,cols):
    
    while len(with_out_ansi:=escape_ansi(line))>cols:

        line=line[:-1]
    return line