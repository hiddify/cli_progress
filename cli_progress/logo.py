"""The logo shown while the command runs: a text file of block characters (``--logo PATH``)."""

from __future__ import annotations

from pathlib import Path

DEFAULT_LOGO = """\
                 ▓▓▓
               ▓▓▓▓▓
          ▓▓▓
        ▓▓▓▓▓  ▓▓▓▓▓
   ▓▓▓  ▓▓▓▓▓  ▓▓▓▓▓
▓▓▓▓▓▓  ▓▓▓▓▓  ▓▓▓▓▓
▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓
▓▓▓▓▓▓  ▓▓▓▓▓  ▓▓▓▓▓"""

MAX_ROWS = 24
MAX_COLS = 80


def load(path: str | None) -> list[str]:
    """The logo's lines: the file as it is (trailing spaces, empty first / last lines and ANSI codes dropped), the
    built-in one when there is no path or it can not be read."""
    text = DEFAULT_LOGO
    if path:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            text = DEFAULT_LOGO
    from .ansi import strip

    if "<< END\n" in text and "\nEND" in text:  # an old bash logo script (text=$(cat << END ... END))
        text = text.split("<< END\n", 1)[1].split("\nEND", 1)[0]
    lines = [strip(line).rstrip() for line in text.expandtabs().splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    lines = [line[:MAX_COLS] for line in lines[:MAX_ROWS]]
    if not lines:
        return DEFAULT_LOGO.splitlines()
    # Drop the indentation every line shares, keep the shape
    indent = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    return [line[indent:] for line in lines]
