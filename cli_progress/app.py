"""The full-screen progress window.

While the command runs only the logo, the step and the progress show. The output is behind ``L`` (and still goes to
the log file). Ctrl+C or ``Q`` ask before stopping anything. When it ends: a success closes by itself after a few
seconds; a failure stays, with the last problems on the screen and a summary printed after the window closes.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import time
from collections import deque
from typing import IO, Literal

import urwid

from . import logo as logo_mod
from .ansi import Line, Severity, parse, strip
from .runner import Command, LineSplitter, ProgressParser
from .theme import PALETTE
from .widgets import Bar, Confirm, Logo, LogView, Phase, Steps, duration, keys

FPS = 12
STOPPED_BY_USER = 130


class ProgressApp:
    def __init__(
        self,
        command: list[str],
        *,
        title: str = "",
        subtitle: str = "",
        log_path: str | None = None,
        logo_path: str | None = None,
        regex: str | None = None,
        auto_exit: float = 5.0,
        show_counts: bool = True,
    ) -> None:
        self.command = Command(command)
        self.title = title
        self.subtitle = subtitle
        self.log_path = log_path
        self.auto_exit = auto_exit
        self.show_counts = show_counts  # the ⚠ / ✗ badges next to the timer
        self.parser = ProgressParser(regex) if regex else ProgressParser()
        self.phase = Phase.running
        self.exit_code = 0
        self.started = time.monotonic()
        self.finished_at: float | None = None
        self.close_at: float | None = None
        self.percent = 0
        self.headline = "Starting…"
        self.warnings = 0
        self.errors = 0
        self.problems: deque[Line] = deque(maxlen=8)
        self.last_line = ""
        self._logfile: IO[str] | None = None
        self._layout_key: tuple[object, ...] | None = None
        self._footer_key: tuple[object, ...] | None = None
        self._redrawing = False  # the last log line is being redrawn (\r)
        self._problems_shown: tuple[int, int, int] | None = None

        self.logo = Logo(logo_mod.load(logo_path))
        self.bar = Bar()
        self.steps = Steps()
        self.headline_text = urwid.Text("", wrap="ellipsis")
        self.info_text = urwid.Text("", wrap="ellipsis")
        self.preview_text = urwid.Text("", wrap="ellipsis")
        self.problem_pile: urwid.WidgetPlaceholder[urwid.Widget] = urwid.WidgetPlaceholder(urwid.Pile([]))
        self.log_view = LogView(log_path, self.close_log)
        self.main: urwid.WidgetPlaceholder[urwid.Widget] = urwid.WidgetPlaceholder(urwid.SolidFill(" "))
        self.footer: urwid.WidgetPlaceholder[urwid.Widget] = urwid.WidgetPlaceholder(urwid.Text(""))
        self.frame: urwid.Frame = urwid.Frame(self.main, footer=urwid.Padding(self.footer, left=1, right=1))
        self.root: urwid.WidgetPlaceholder[urwid.Widget] = urwid.WidgetPlaceholder(urwid.AttrMap(self.frame, "bg"))
        self.screen = urwid.raw_display.Screen()
        self.screen.set_terminal_properties(colors=_colors())
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.loop = urwid.MainLoop(
            self.root,
            PALETTE,
            screen=self.screen,
            unhandled_input=self.on_key,
            handle_mouse=False,
            event_loop=urwid.AsyncioEventLoop(loop=self.event_loop),
        )
        self._showing_log = False
        self._dialog: urwid.Widget | None = None
        self._under_dialog: urwid.Widget = self.root.original_widget

    # ------------------------------------------------------------------------------------------ layout

    def _layout(self) -> None:
        cols, rows = self.screen.get_cols_rows()
        key: tuple[object, ...]
        if self._showing_log:
            # The logo (when it leaves the log at least 10 rows) and the progress stay on top; the log fills the rest
            # The logo on the left with the progress beside it (when that leaves the log 10 rows and the bar 40 columns)
            with_logo = rows - (len(self.logo.lines) + 3) >= 10 and cols >= self.logo.width + 46
            key = ("log", with_logo)
            if key != self._layout_key:
                self._layout_key = key
                self.main.original_widget = self._log_layout(cols, with_logo)
            return
        compact = rows < len(self.logo.lines) + 16 or cols < self.logo.width + 4
        steps = max(1, min(5, rows - (12 if compact else len(self.logo.lines) + 15)))
        key = ("main", compact, steps)
        if key == self._layout_key:
            return
        self._layout_key = key
        self.steps.visible = steps
        column = urwid.Pile(
            [
                ("pack", self.headline_text),
                ("pack", urwid.Divider()),
                ("pack", self.bar),
                ("pack", self.info_text),
                ("pack", urwid.Divider()),
                ("pack", self.steps),
                ("pack", urwid.Divider()),
                ("pack", self.preview_text),
                ("pack", self.problem_pile),
            ]
        )
        body: list[urwid.Widget] = []
        if not compact:
            body += [self.logo, urwid.Divider()]
        body += [self._title(), urwid.Divider(), self._centered(column, cols)]
        self.main.original_widget = urwid.Filler(urwid.Pile(body), valign="middle")

    def _log_layout(self, cols: int, with_logo: bool) -> urwid.Widget:
        progress = urwid.Pile(
            [("pack", self._title(align="left")), ("pack", urwid.Divider()), ("pack", self.headline_text), ("pack", self.bar), ("pack", self.info_text)]
        )
        if with_logo:
            # Logo left, the title / step / bar / timer vertically centered beside it
            beside = urwid.BoxAdapter(urwid.Filler(progress, valign="middle"), len(self.logo.lines))
            top: urwid.Widget = urwid.Padding(urwid.Columns([(self.logo.width, self.logo), beside], dividechars=4), left=2, right=2)
        else:
            top = self._centered(progress, cols)
        layout = urwid.Pile([("pack", urwid.Divider()), ("pack", top), ("pack", urwid.Divider()), ("weight", 1, self.log_view)])
        layout.focus_position = 3  # the log gets the keys
        return layout

    def _title(self, align: Literal["left", "center", "right"] = "center") -> urwid.Widget:
        return urwid.Text([("title", self.title), ("subtitle", f"   {self.subtitle}" if self.subtitle else "")], align=align)

    @staticmethod
    def _centered(widget: urwid.Widget, cols: int) -> urwid.Widget:
        return urwid.Padding(widget, align="center", width=("relative", 86), min_width=min(40, cols - 2))

    # ------------------------------------------------------------------------------------------ output

    def on_line(self, raw: str, final: bool, stderr: bool) -> None:
        if final and self._logfile:
            self._logfile.write(raw + "\n")
        progress = self.parser.parse(raw)
        if progress is not None:
            if final:
                self.set_progress(progress.percent, progress.title, progress.subtitle)
            return
        line = parse(raw, stderr=stderr)
        self.log_view.add(line, replace=self._redrawing)
        self._redrawing = not final
        if final and line.severity:
            self.problems.append(line)
            if line.severity is Severity.error:
                self.errors += 1
            else:
                self.warnings += 1
        if line.text.strip():
            self.last_line = line.text.strip()

    def set_progress(self, percent: int, title: str, subtitle: str) -> None:
        self.percent = percent
        self.bar.set(percent)
        if title:
            self.headline = title
        self.steps.advance(subtitle or title)

    # ------------------------------------------------------------------------------------------ the run

    async def run_command(self) -> None:
        try:
            await self.command.start()
        except OSError as e:
            self.on_line(f"\x1b[31mcli_progress: can not run {' '.join(self.command.argv)}: {e}\x1b[0m", True, True)
            self.finish(127)
            return
        assert self.command.proc is not None
        out = LineSplitter(lambda text, final: self.on_line(text, final, False))
        err = LineSplitter(lambda text, final: self.on_line(text, final, True))
        await asyncio.gather(self.command.pump(self.command.proc.stdout, out), self.command.pump(self.command.proc.stderr, err))
        code = await self.command.proc.wait()
        self.finish(STOPPED_BY_USER if self.phase is Phase.stopping else code)

    def finish(self, code: int) -> None:
        self.exit_code = code
        self.finished_at = time.monotonic()
        self.steps.finish(failed=code != 0)
        if code == 0:
            self.phase = Phase.done
            self.bar.set(100)
            self.headline = "Completed"
            if self.auto_exit > 0 and not self._showing_log and self._dialog is None:
                self.close_at = self.finished_at + self.auto_exit
        else:
            self.phase = Phase.failed
            self.headline = "Stopped" if code == STOPPED_BY_USER else f"Failed (exit code {code})"
        self.logo.phase = self.bar.phase = self.phase
        self.close_dialog()

    def stop(self) -> None:
        if self.command.running and self.phase is Phase.running:
            self.phase = Phase.stopping
            self.headline = "Stopping… (the command is cleaning up)"
            self.event_loop.create_task(self.command.stop())

    # ------------------------------------------------------------------------------------------ every frame

    def tick(self, _loop: urwid.MainLoop | None = None, _data: object = None) -> None:
        now = time.monotonic()
        self._layout()
        self.bar.tick()
        self.logo.tick(now, self.bar.shown)
        self.steps.tick(now, self.phase)
        self.headline_text.set_text(self._headline())
        self.info_text.set_text(self._info(now))
        self.preview_text.set_text(("preview", f"  {self.last_line}") if self.phase in (Phase.running, Phase.stopping) else "")
        self._update_problems()
        self._update_footer(now)
        if self._showing_log:
            self.log_view.tick()
        if self.close_at is not None and now >= self.close_at:
            raise urwid.ExitMainLoop()
        self.loop.set_alarm_in(1 / FPS, self.tick)

    def _headline(self) -> list[tuple[str, str]]:
        attr = {Phase.done: "ok", Phase.failed: "fail"}.get(self.phase, "title")
        icon = {Phase.done: "✓ ", Phase.failed: "✗ "}.get(self.phase, "")
        return [(attr, icon + self.headline)]

    def _info(self, now: float) -> list[tuple[str, str]]:
        end = self.finished_at or now
        parts: list[tuple[str, str]] = [("muted", f"⏱ {duration(end - self.started)}")]
        if self.phase is Phase.running and 3 <= self.percent < 100:
            elapsed = now - self.started
            left = elapsed / self.percent * (100 - self.percent)
            if left >= 5:
                parts.append(("muted", f"   ≈ {duration(left)} left"))
        if self.show_counts and self.warnings:
            parts += [("muted", "   "), ("badge_warn", f" ⚠ {self.warnings} ")]
        if self.show_counts and self.errors:
            parts += [("muted", "  "), ("badge_err", f" ✗ {self.errors} ")]
        return parts

    def _update_problems(self) -> None:
        if self.phase is not Phase.failed:
            if self._problems_shown is not None:
                self.problem_pile.original_widget = urwid.Pile([])
                self._problems_shown = None
            return
        if self._problems_shown == (len(self.problems), self.errors, self.warnings):
            return
        self._problems_shown = (len(self.problems), self.errors, self.warnings)
        shown = list(self.problems) or [parse(line) for line in self._tail(6)]
        rows: list[urwid.Widget] = [urwid.Text(("failure_title", " Last problems "))]
        rows += [urwid.Text([("failure_box", " "), *line.markup], wrap="ellipsis") for line in shown]
        box = urwid.AttrMap(urwid.Pile(rows), "failure_box")
        self.problem_pile.original_widget = urwid.Pile([urwid.Divider(), box])

    def _tail(self, n: int) -> list[str]:
        return [line.text for line in self.log_view.lines[-n:]]

    def _update_footer(self, now: float) -> None:
        left = max(0, int(self.close_at - now + 0.99)) if self.close_at is not None else None
        key = (self.phase, self._showing_log, left)
        if key != self._footer_key:
            self._footer_key = key
            self.footer.original_widget = self._footer(left)

    def _footer(self, left: int | None) -> urwid.Widget:
        if self._showing_log:
            return urwid.Text("")
        if self.phase is Phase.done:
            if left is not None:
                return urwid.Pile([urwid.Text(("muted", f"Closing in {left}s · any key to stay"), align="center"), keys(("Enter", "close now"), ("L", "log"))])
            return keys(("Enter", "close"), ("L", "log"))
        if self.phase is Phase.failed:
            return keys(("L", "full log"), ("Enter", "close"))
        return keys(("L", "show log"), ("Q", "quit"))

    # ------------------------------------------------------------------------------------------ keys and dialogs

    def on_key(self, key: str | tuple) -> None:
        if not isinstance(key, str):
            return
        finished = self.phase in (Phase.done, Phase.failed)
        if key in ("l", "L", "tab"):
            self.close_at = None
            self.open_log()
        elif finished and key in ("enter", "q", "Q", "esc", " "):
            raise urwid.ExitMainLoop()
        elif finished:
            self.close_at = None  # any other key: stay
        elif key in ("q", "Q", "esc"):
            self.ask_stop()

    def open_log(self) -> None:
        self._showing_log = True
        if self.log_view.follow and self.log_view.walker:
            self.log_view.walker.set_focus(len(self.log_view.walker) - 1)
        self._layout()

    def close_log(self) -> None:
        self._showing_log = False
        self._layout()

    def ask_stop(self) -> None:
        if self._dialog is not None:
            return
        if self.phase is Phase.stopping:
            return

        def answer(stop: bool) -> None:
            self.close_dialog()
            if stop:
                self.stop()

        dialog = Confirm(
            "Stop now?",
            "It is still running. Stopping it in the middle\ncan leave things half done.",
            "Stop it",
            "Keep running",
            answer,
        )
        self._dialog = dialog
        base = self.root.original_widget
        self._under_dialog = base
        self.root.original_widget = urwid.Overlay(dialog, base, "center", 56, "middle", "pack")

    def close_dialog(self) -> None:
        if self._dialog is None:
            return
        self._dialog = None
        self.root.original_widget = self._under_dialog

    def on_sigint(self) -> None:
        if self.phase in (Phase.done, Phase.failed):
            self.close_at = time.monotonic()  # the next frame closes the window
            return
        if self._dialog is not None:  # Ctrl+C twice: yes, stop
            self.close_dialog()
            self.stop()
        else:
            self.ask_stop()

    # ------------------------------------------------------------------------------------------ start

    def run(self) -> int:
        if self.log_path:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_path)), exist_ok=True)
            self._logfile = open(self.log_path, "w", encoding="utf-8", buffering=1)
        try:
            self.event_loop.add_signal_handler(signal.SIGINT, self.on_sigint)
            self.event_loop.add_signal_handler(signal.SIGTERM, self.stop)
            self.event_loop.add_signal_handler(signal.SIGHUP, self.stop)
            # The command starts only once the screen is up: a terminal that can not be set up never runs it twice
            self.loop.set_alarm_in(0, lambda *_: self.event_loop.create_task(self.run_command()))
            self.loop.set_alarm_in(0, self.tick)
            self.loop.run()
        finally:
            if self.command.running:  # the window closed while it runs (a crash, a lost terminal)
                self.event_loop.run_until_complete(self.command.stop())
            if self._logfile:
                self._logfile.close()
            self.event_loop.close()
        self.print_summary()
        return self.exit_code

    def print_summary(self) -> None:
        """After the window: one line of what happened (and the last problems of a failure), so it stays visible."""
        took = duration((self.finished_at or time.monotonic()) - self.started)
        green, red, dim, reset = "\033[32m", "\033[31m", "\033[2m", "\033[0m"
        if self.phase is Phase.done:
            print(f"{green}✓ {self.title or 'Done'}: completed in {took}{reset}")
            return
        print(f"{red}✗ {self.title or 'Command'}: {self.headline.lower()} after {took}{reset}")
        for line in list(self.problems)[-5:]:
            print(f"  {dim}│{reset} {strip(line.text)}")
        if self.log_path:
            print(f"  {dim}Full log: {self.log_path}{reset}")


def _colors() -> int:
    term = os.environ.get("TERM", "")
    if os.environ.get("COLORTERM") or "256" in term or "direct" in term or term in ("xterm-kitty", "alacritty", "wezterm"):
        return 256
    return 16


DEFAULT_SIZE = (80, 24)
MIN_SIZE = (30, 10)


def terminal_problem() -> str | None:
    """Why the window can not be shown (None: it can). Browser SSH clients often send no TERM and a 0x0 size: TERM
    then defaults to xterm-256color, and the terminal is given 80x24 (urwid needs a size)."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return "not a terminal (a pipe or a file)"
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return "TERM=dumb"
    if not term:
        os.environ["TERM"] = "xterm-256color"
    try:
        import fcntl
        import struct
        import termios

        fd = sys.stdout.fileno()
        _settable(sys.stdin.fileno())
        rows, cols = struct.unpack("hh", fcntl.ioctl(fd, termios.TIOCGWINSZ, b"\0" * 4))
        if rows <= 0 or cols <= 0:
            cols, rows = DEFAULT_SIZE
            fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
    except Exception as e:  # termios.error, OSError, no termios at all
        return f"the terminal can not be set up ({e})"
    if cols < MIN_SIZE[0] or rows < MIN_SIZE[1]:
        return f"the terminal is too small ({cols}x{rows}, needs {MIN_SIZE[0]}x{MIN_SIZE[1]})"
    return None


def _settable(fd: int) -> None:
    """Make sure the terminal's modes can be set (urwid sets them). A custom line speed (Linux BOTHER, which some web
    SSH bridges use) reads back as a value tcsetattr refuses with EINVAL: give it a standard one, meaningless on a
    pseudo-terminal."""
    import errno
    import termios

    attrs = termios.tcgetattr(fd)
    try:
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
    except termios.error as e:
        if e.args[0] != errno.EINVAL:
            raise
        attrs[4] = attrs[5] = termios.B38400
        termios.tcsetattr(fd, termios.TCSANOW, attrs)


def terminal_usable() -> bool:
    return terminal_problem() is None
