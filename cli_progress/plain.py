"""Without a usable terminal (a pipe, cron, a web terminal with no tty): the command's output as it comes, a line for each
progress step, the same log file. The command runs once, whatever happens."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import IO

from .runner import Command, LineSplitter, ProgressParser


async def _run(command: Command, parser: ProgressParser, logfile: IO[str] | None) -> int:
    last: tuple[int, str, str] | None = None

    def on_line(text: str, final: bool, stderr: bool) -> None:
        nonlocal last
        if not final:
            return
        if logfile:
            logfile.write(text + "\n")
        progress = parser.parse(text)
        if progress is None:
            print(text, file=sys.stderr if stderr else sys.stdout, flush=True)
            return
        key = (progress.percent, progress.title, progress.subtitle)
        if key != last:
            last = key
            step = " · ".join(part for part in (progress.title, progress.subtitle) if part)
            print(f"[{progress.percent:3d}%] {step}", flush=True)

    try:
        await command.start()
    except OSError as e:
        print(f"cli_progress: can not run {' '.join(command.argv)}: {e}", file=sys.stderr)
        return 127
    assert command.proc is not None
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        try:
            loop.add_signal_handler(sig, lambda: loop.create_task(command.stop()))
        except (NotImplementedError, RuntimeError):
            pass
    out = LineSplitter(lambda t, f: on_line(t, f, False))
    err = LineSplitter(lambda t, f: on_line(t, f, True))
    await asyncio.gather(command.pump(command.proc.stdout, out), command.pump(command.proc.stderr, err))
    return await command.proc.wait()


def run_plain(argv: list[str], *, log_path: str | None = None, regex: str | None = None) -> int:
    command = Command(argv)
    if not command.argv:
        print("cli_progress: no command given", file=sys.stderr)
        return 2
    parser = ProgressParser(regex) if regex else ProgressParser()
    logfile: IO[str] | None = None
    if log_path:
        os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
        logfile = open(log_path, "w", encoding="utf-8", buffering=1)
    try:
        return asyncio.run(_run(command, parser, logfile))
    finally:
        if logfile:
            logfile.close()
