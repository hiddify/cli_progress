"""The pieces of the progress window."""

from __future__ import annotations

import time
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field
from enum import Enum

import urwid

from .ansi import Line, Markup, Severity

SPINNER = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class Phase(Enum):
    running = "running"
    stopping = "stopping"
    done = "done"
    failed = "failed"


def duration(seconds: float) -> str:
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {seconds:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


# ---------------------------------------------------------------------------------------------- logo


class Logo(urwid.WidgetWrap):
    """The logo fills with blue as the progress grows: light blue at the start, dark blue rising from the bottom to
    the top, with a light that sweeps across it now and then; green when it succeeded, red when it failed."""

    SWEEP_EVERY = 4.0  # seconds between two sweeps
    SWEEP_TIME = 1.2

    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.width = max((len(line) for line in lines), default=0)
        self.phase = Phase.running
        self.level = 0.0  # 0..100: how far up the dark blue has risen
        self._text = urwid.Text("", wrap="clip")
        super().__init__(urwid.Padding(self._text, align="center", width=self.width))
        self.tick(0.0)

    def tick(self, now: float, level: float | None = None) -> None:
        if level is not None:
            self.level = max(0.0, min(100.0, level))
        self._text.set_text(self._markup(now))

    def _row_attr(self, r: int, rows: int) -> str:
        """Light blue above the level, dark blue below it (deeper at the bottom), a brighter surface row between."""
        filled = self.level / 100 * rows  # rows filled, counted from the bottom
        from_bottom = rows - r  # this row's top edge, counted from the bottom
        if from_bottom <= filled:
            return "logo_fill_deep" if from_bottom <= filled / 2 else "logo_fill"
        if from_bottom - 1 < filled:  # the row the level is in
            return "logo_surface"
        return "logo_light"

    def _markup(self, now: float) -> Markup:
        rows = len(self.lines)
        if self.phase in (Phase.done, Phase.failed):
            attr = "logo_ok" if self.phase is Phase.done else "logo_fail"
            return [(attr, "\n".join(self.lines))] if self.lines else [(None, "")]
        t = now % self.SWEEP_EVERY
        # The light moves diagonally (column + 2×row) across the logo, then rests
        span = self.width + 2 * rows + 8
        center = (t / self.SWEEP_TIME) * span - 4 if t < self.SWEEP_TIME else None
        out: Markup = []
        for r, line in enumerate(self.lines):
            base = self._row_attr(r, rows)
            run_attr: str | None = None
            run = ""
            for c, ch in enumerate(line):
                lit = center is not None and ch.strip() and abs((c + 2 * r) - center) < 2.5
                attr = "logo_shine" if lit else base
                if attr != run_attr and run:
                    out.append((run_attr, run))
                    run = ""
                run_attr = attr
                run += ch
            if run:
                out.append((run_attr, run))
            if r < rows - 1:
                out.append((None, "\n"))
        return out or [(None, "")]


# ---------------------------------------------------------------------------------------------- progress bar


class Bar(urwid.Widget):
    """A thin bar that glides to its value (it never jumps), with the percentage after it."""

    _sizing = frozenset([urwid.FLOW])
    _selectable = False

    def __init__(self) -> None:
        super().__init__()
        self.target = 0.0
        self.shown = 0.0
        self.phase = Phase.running

    def set(self, percent: float) -> None:
        self.target = max(0.0, min(100.0, percent))

    def tick(self) -> bool:
        """Move a step toward the target; True when it moved."""
        if abs(self.target - self.shown) < 0.05:
            if self.shown != self.target:
                self.shown = self.target
                self._invalidate()
                return True
            return False
        self.shown += (self.target - self.shown) * 0.18 + (0.05 if self.target > self.shown else -0.05)
        self._invalidate()
        return True

    def rows(self, size: tuple[int], focus: bool = False) -> int:
        return 1

    def render(self, size: tuple[()] | tuple[int] | tuple[int, int], focus: bool = False) -> urwid.Canvas:
        maxcol = size[0] if size else 80
        label = f" {self.shown:5.1f}%" if self.shown < 100 else "  100%"
        width = max(1, maxcol - len(label))
        cells = self.shown / 100 * width
        full = int(cells)
        done_attr = {Phase.done: "bar_ok", Phase.failed: "bar_fail"}.get(self.phase, "bar_done")
        markup: Markup = []
        if full:
            markup.append((done_attr, "━" * full))
        rest = width - full
        if rest > 0:
            if cells - full >= 0.5:
                markup.append(("bar_head" if self.phase is Phase.running else done_attr, "╸"))
                rest -= 1
            markup.append(("bar_todo", "━" * rest))
        markup.append(("percent", label))
        return urwid.Text(markup, wrap="clip").render((maxcol,))


# ---------------------------------------------------------------------------------------------- steps


@dataclass
class Step:
    name: str
    started: float = field(default_factory=time.monotonic)
    finished: float | None = None
    failed: bool = False


class Steps(urwid.WidgetWrap):
    """The current step (with a spinner) under the last few finished ones."""

    def __init__(self) -> None:
        self.steps: list[Step] = []
        self.visible = 4
        self._holder: urwid.WidgetPlaceholder[urwid.Widget] = urwid.WidgetPlaceholder(urwid.Pile([]))
        super().__init__(self._holder)

    def advance(self, name: str) -> None:
        name = name.strip()
        if not name or (self.steps and self.steps[-1].name == name and self.steps[-1].finished is None):
            return
        now = time.monotonic()
        if self.steps and self.steps[-1].finished is None:
            self.steps[-1].finished = now
        self.steps.append(Step(name, now))

    def finish(self, failed: bool = False) -> None:
        """The run ended: the current step is done, or the one that failed."""
        if self.steps and self.steps[-1].finished is None:
            self.steps[-1].finished = time.monotonic()
            self.steps[-1].failed = failed

    def tick(self, now: float, phase: Phase) -> None:
        shown = self.steps[-self.visible :] if self.visible > 0 else []
        rows = []
        spin = SPINNER[int(now * 12) % len(SPINNER)]
        for step in shown:
            if step.finished is None and phase in (Phase.running, Phase.stopping):
                icon, attr, took = (("spinner", spin), "step", duration(now - step.started))
            elif step.failed:
                icon, attr, took = (("fail", "✗"), "err", duration((step.finished or now) - step.started))
            else:
                icon, attr, took = (("step_done", "✓"), "step_desc", duration((step.finished or now) - step.started))
            rows.append(
                urwid.Columns(
                    [
                        (2, urwid.Text(icon)),
                        urwid.Text((attr, step.name), wrap="ellipsis"),
                        (8, urwid.Text(("faint", took), align="right")),
                    ]
                )
            )
        self._holder.original_widget = urwid.Pile(rows)


# ---------------------------------------------------------------------------------------------- key hints


def keys(*pairs: tuple[str, str]) -> urwid.Text:
    markup: Markup = []
    for i, (key, label) in enumerate(pairs):
        if i:
            markup.append((None, "   "))
        markup += [("key", f" {key} "), ("key_label", f" {label}")]
    return urwid.Text(markup, align="center")


# ---------------------------------------------------------------------------------------------- log view


class LogView(urwid.WidgetWrap):
    """The whole output, scrollable. It follows new lines while you are at the bottom; scrolling up holds it still.
    ``e`` / ``E`` jump to the next / previous error or warning."""

    MAX_LINES = 20000

    def __init__(self, path: str | None, on_close: Callable[[], None]) -> None:
        self.path = path
        self.on_close = on_close
        self.follow = True
        self.lines: list[Line] = []
        self.walker: urwid.SimpleFocusListWalker[urwid.AttrMap[urwid.Text]] = urwid.SimpleFocusListWalker([])
        self.listbox = urwid.ListBox(self.walker)
        self.header_left = urwid.Text("", wrap="ellipsis")
        self.header_right = urwid.Text("", align="right", wrap="clip")
        self.header = urwid.Columns([self.header_left, ("pack", self.header_right)], dividechars=2)
        self.counter = 0  # line numbers keep counting when old lines are dropped
        frame = urwid.Frame(
            urwid.AttrMap(self.listbox, "log_bg"),
            header=urwid.AttrMap(self.header, "log_head"),
            footer=urwid.AttrMap(
                keys(("Esc", "back"), ("↑↓", "scroll"), ("End", "follow"), ("e", "next problem"), ("E", "previous")),
                "bg",
            ),
        )
        super().__init__(frame)
        self._update_header()

    def add(self, line: Line, replace: bool = False) -> None:
        if replace and self.walker:
            self.walker[-1] = self._row(self.counter, line)
            self.lines[-1] = line
        else:
            self.counter += 1
            self.lines.append(line)
            self.walker.append(self._row(self.counter, line))
            if len(self.walker) > self.MAX_LINES:
                drop = len(self.walker) - self.MAX_LINES
                del self.walker[:drop]
                del self.lines[:drop]
        if self.follow and self.walker:
            self.walker.set_focus(len(self.walker) - 1)

    def _row(self, number: int, line: Line) -> urwid.AttrMap[urwid.Text]:
        mark = {Severity.error: ("err", "▌"), Severity.warning: ("warn", "▌")}.get(line.severity, ("log_num", " "))
        text = urwid.Text([("log_num", f"{number:>6} "), mark, " ", *line.markup])
        focus_map: dict[Hashable, Hashable] = {None: "log_focus", "log_num": "log_focus"}
        return urwid.AttrMap(text, None, focus_map=focus_map)

    def _update_header(self) -> None:
        state = "following" if self.follow else "paused · End to follow"
        problems = sum(1 for line in self.lines if line.severity)
        self.header_left.set_text([("log_head", " ▤ Log "), ("log_head_dim", f" {self.path or ''}")])
        self.header_right.set_text(("log_head", f"{len(self.lines)} lines · {problems} problems · {state} "))

    def tick(self) -> None:
        self._update_header()

    def _jump(self, step: int) -> None:
        if not self.walker:
            return
        pos = self.walker.focus or 0
        n = len(self.lines)
        for k in range(1, n + 1):
            i = (pos + step * k) % n
            if self.lines[i].severity:
                self.follow = False
                self.walker.set_focus(i)
                self.listbox.set_focus_valign("middle")
                return

    def keypress(self, size: tuple[int, int], key: str) -> str | None:
        if key in ("esc", "l", "L", "q", "Q", "tab", "backspace"):
            self.on_close()
            return None
        if key in ("end", "G"):
            self.follow = True
            self.walker.set_focus(max(0, len(self.walker) - 1))
            return None
        if key in ("home", "g"):
            self.follow = False
            self.walker.set_focus(0)
            return None
        if key in ("f", "F"):
            self.follow = not self.follow
            if self.follow:
                self.walker.set_focus(max(0, len(self.walker) - 1))
            return None
        if key == "e":
            self._jump(1)
            return None
        if key == "E":
            self._jump(-1)
            return None
        result = super().keypress(size, key)
        if key in ("up", "page up", "k"):
            self.follow = False
        elif key in ("down", "page down", "j") and self.walker:
            pos = self.walker.focus
            self.follow = pos is not None and pos >= len(self.walker) - 1
        return result


# ---------------------------------------------------------------------------------------------- dialog


class Confirm(urwid.WidgetWrap):
    """A question with two buttons; the safe one has the focus."""

    def __init__(self, title: str, text: str, yes: str, no: str, on_answer: Callable[[bool], None]) -> None:
        self.on_answer = on_answer
        yes_btn = urwid.AttrMap(urwid.Button(yes, lambda _b: on_answer(True)), "button", "button_focus")
        no_btn = urwid.AttrMap(urwid.Button(no, lambda _b: on_answer(False)), "button", "button_focus")
        buttons = urwid.Columns([(len(no) + 4, no_btn), (len(yes) + 4, yes_btn)], dividechars=3)
        buttons.focus_position = 0
        body = urwid.Pile(
            [
                urwid.Text(("dialog_title", title), align="center"),
                urwid.Divider(),
                urwid.Text(("dialog", text), align="center"),
                urwid.Divider(),
                urwid.Padding(buttons, align="center", width=len(yes) + len(no) + 11),
            ]
        )
        box = urwid.LineBox(urwid.Padding(body, left=2, right=2), tlcorner="╭", trcorner="╮", blcorner="╰", brcorner="╯")
        super().__init__(urwid.AttrMap(box, "dialog_border"))

    def keypress(self, size: tuple[int, ...], key: str) -> str | None:
        if key in ("y", "Y"):
            self.on_answer(True)
            return None
        if key in ("n", "N", "esc"):
            self.on_answer(False)
            return None
        return super().keypress(size, key)
