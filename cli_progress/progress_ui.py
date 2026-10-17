"""The 2.x API (``ProgressUI(log, command, title, subtitle, regex).start()``), kept for scripts that import it."""

from __future__ import annotations

import sys

from .app import ProgressApp, terminal_usable
from .plain import run_plain


class ProgressUI:
    def __init__(self, logpath: str | None, command: list[str], title: str, subtitle: str, regex: str) -> None:
        self.args = (logpath, command, title, subtitle, regex)

    def start(self) -> None:
        logpath, command, title, subtitle, regex = self.args
        if not terminal_usable():
            sys.exit(run_plain(command, log_path=logpath, regex=regex))
        sys.exit(ProgressApp(command, title=title, subtitle=subtitle, log_path=logpath, regex=regex).run())
