"""Running the command: its output as lines, progress markers, and stopping it gently."""

from __future__ import annotations

import asyncio
import codecs
import os
import re
import signal
from collections.abc import Callable
from dataclasses import dataclass

DEFAULT_REGEX = r"####(?P<progress>\d+)####(?P<title>.*?)####(?P<subtitle>.*?)####"


@dataclass(frozen=True, slots=True)
class Progress:
    percent: int
    title: str
    subtitle: str


class ProgressParser:
    """``####42####Installing...####Hiddify Panel####`` (or the caller's regex) → Progress."""

    def __init__(self, regex: str = DEFAULT_REGEX) -> None:
        self.regex = re.compile(regex)

    def parse(self, line: str) -> Progress | None:
        m = self.regex.search(line)
        if not m:
            return None
        groups = m.groupdict()
        try:
            percent = max(0, min(100, int(groups.get("progress") or 0)))
        except ValueError:
            return None
        return Progress(percent, (groups.get("title") or "").strip(), (groups.get("subtitle") or "").strip())


class LineSplitter:
    """Bytes → lines. UTF-8 split across reads is kept whole; ``\\r\\n`` is one line end; a lone ``\\r`` (a progress
    bar redrawing itself) replaces the line being written instead of adding one."""

    def __init__(self, on_line: Callable[[str, bool], None]) -> None:
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._buf = ""
        self._cr = False
        self._on_line = on_line  # (text, final): final False = a \r redraw of the current line

    def feed(self, data: bytes) -> None:
        self._take(self._decoder.decode(data))

    def close(self) -> None:
        self._take(self._decoder.decode(b"", final=True))
        if self._buf:
            self._on_line(self._buf, True)
            self._buf = ""

    def _take(self, text: str) -> None:
        for ch in text:
            if ch == "\n":
                self._on_line(self._buf, True)
                self._buf, self._cr = "", False
            elif ch == "\r":
                self._cr = True
            else:
                if self._cr:  # \r then text: the line is redrawn
                    if self._buf:
                        self._on_line(self._buf, False)
                    self._buf, self._cr = "", False
                self._buf += ch


class Command:
    """The wrapped command, in its own session: the terminal's Ctrl+C reaches this window (which asks first), not it."""

    def __init__(self, argv: list[str]) -> None:
        self.argv = argv[1:] if argv and argv[0] == "--" else argv
        self.proc: asyncio.subprocess.Process | None = None

    async def start(self) -> None:
        self.proc = await asyncio.create_subprocess_exec(
            *self.argv,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )

    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    async def pump(self, stream: asyncio.StreamReader | None, splitter: LineSplitter) -> None:
        if stream is None:
            return
        while chunk := await stream.read(65536):
            splitter.feed(chunk)
        splitter.close()

    def signal(self, sig: int) -> None:
        if not self.running or self.proc is None:
            return
        try:
            os.killpg(self.proc.pid, sig)  # the whole session: the script and what it started
        except (ProcessLookupError, PermissionError):
            try:
                self.proc.send_signal(sig)
            except ProcessLookupError:
                pass

    async def stop(self, grace: float = 8.0) -> None:
        """SIGINT (the command can clean up), then SIGTERM, then SIGKILL."""
        for sig, wait in ((signal.SIGINT, grace), (signal.SIGTERM, 4.0), (signal.SIGKILL, 2.0)):
            if not self.running or self.proc is None:
                return
            self.signal(sig)
            try:
                await asyncio.wait_for(self.proc.wait(), wait)
                return
            except asyncio.TimeoutError:
                continue
