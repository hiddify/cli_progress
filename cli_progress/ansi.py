"""A command's colored output → urwid markup, its plain text and how serious it looks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum

from .theme import ANSI_NAMES

# CSI sequences (colors, cursor moves, erase), OSC (titles, links) and other two-byte escapes
_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
_SGR = re.compile(r"\x1b\[([0-9;]*)m")
_ERROR_TEXT = re.compile(r"^(E:|ERROR\b|Error:|error:|FATAL|Fatal|Traceback \(most recent call last\))")
_WARN_TEXT = re.compile(r"^(W:|WARNING\b|Warning:|warning:)")

Markup = list[tuple[str | None, str]]


class Severity(IntEnum):
    normal = 0
    warning = 1
    error = 2


@dataclass(frozen=True, slots=True)
class Line:
    markup: Markup
    text: str
    severity: Severity


def strip(text: str) -> str:
    return _ESCAPE.sub("", text)


def parse(raw: str, *, stderr: bool = False) -> Line:
    """Colors become attributes (``ansi_red``, ``ansi_yellow_bold``, ...); everything else is dropped. Red text, or a
    line that starts like an error, is an error; yellow (or a warning prefix) a warning."""
    markup: Markup = []
    fg: str | None = None
    bold = False
    reds = yellows = 0
    pos = 0
    for m in _SGR.finditer(raw):
        chunk = strip(raw[pos : m.start()])
        if chunk:
            markup.append((_attr(fg, bold), chunk))
            reds += fg == "red" and bool(chunk.strip())
            yellows += fg == "yellow" and bool(chunk.strip())
        fg, bold = _apply_sgr(m.group(1), fg, bold)
        pos = m.end()
    tail = strip(raw[pos:])
    if tail:
        markup.append((_attr(fg, bold), tail))
        reds += fg == "red" and bool(tail.strip())
        yellows += fg == "yellow" and bool(tail.strip())
    text = "".join(chunk for _, chunk in markup)
    stripped = text.lstrip()
    if reds or _ERROR_TEXT.match(stripped):
        severity = Severity.error
    elif yellows or _WARN_TEXT.match(stripped):
        severity = Severity.warning
    else:
        severity = Severity.normal
    if stderr and severity == Severity.normal and not markup:
        markup = [(None, text)]
    return Line(markup or [(None, "")], text, severity)


def _attr(fg: str | None, bold: bool) -> str | None:
    if fg is None:
        return "ansi_bold" if bold else None
    return f"ansi_{fg}_bold" if bold else f"ansi_{fg}"


def _apply_sgr(params: str, fg: str | None, bold: bool) -> tuple[str | None, bool]:
    codes = [int(c) for c in params.split(";") if c.isdigit()] or [0]
    i = 0
    while i < len(codes):
        code = codes[i]
        if code == 0:
            fg, bold = None, False
        elif code == 1:
            bold = True
        elif code == 22:
            bold = False
        elif 30 <= code <= 37:
            fg = ANSI_NAMES[code - 30]
        elif 90 <= code <= 97:
            fg = ANSI_NAMES[code - 90]
        elif code == 39:
            fg = None
        elif code in (38, 48):  # 256 / true color: skip its arguments, keep the current color
            i += 2 if i + 1 < len(codes) and codes[i + 1] == 5 else 4
        i += 1
    return fg, bold
