"""The parts without a terminal: line splitting, progress lines, ANSI colors, the logo, and plain mode."""

from __future__ import annotations

import sys
import textwrap

from cli_progress import logo
from cli_progress.ansi import Severity, parse, strip
from cli_progress.plain import run_plain
from cli_progress.runner import LineSplitter, ProgressParser


def split(*chunks: bytes) -> list[tuple[str, bool]]:
    out: list[tuple[str, bool]] = []
    splitter = LineSplitter(lambda text, final: out.append((text, final)))
    for chunk in chunks:
        splitter.feed(chunk)
    splitter.close()
    return out


def test_lines_crlf_and_utf8_split_across_reads():
    assert split(b"a\r\nb\n") == [("a", True), ("b", True)]
    assert split("سلام\n".encode()[:3], "سلام\n".encode()[3:]) == [("سلام", True)]
    assert split(b"no newline at end") == [("no newline at end", True)]


def test_carriage_return_redraws_the_line():
    assert split(b"10%\r50%\r100%\n") == [("10%", False), ("50%", False), ("100%", True)]


def test_progress_parser():
    p = ProgressParser().parse("####42####Installing...####Hiddify Panel####")
    assert p and (p.percent, p.title, p.subtitle) == (42, "Installing...", "Hiddify Panel")
    assert ProgressParser().parse("####250####x####y####").percent == 100
    assert ProgressParser().parse("plain output") is None


def test_ansi_colors_and_severity():
    line = parse("\x1b[31mError: bad\x1b[0m done")
    assert line.text == "Error: bad done" and line.severity is Severity.error
    assert ("ansi_red", "Error: bad") in line.markup
    assert parse("\x1b[1;33mwarning\x1b[0m").severity is Severity.warning
    assert parse("E: Unable to locate package").severity is Severity.error
    assert parse("all good").severity is Severity.normal
    assert strip("\x1b]0;title\x07\x1b[2Kok") == "ok"


def test_logo_file_and_old_script(tmp_path):
    art = tmp_path / "logo.txt"
    art.write_text("\n   ▓▓\n   ▓▓▓▓\n\n")
    assert logo.load(str(art)) == ["▓▓", "▓▓▓▓"]
    script = tmp_path / "logo.ico"
    script.write_text(textwrap.dedent("""\
        text=$(cat << END
          ▓
         ▓▓▓
        END
        )
        center_text "$text"
        """))
    assert logo.load(str(script)) == [" ▓", "▓▓▓"]
    assert logo.load(str(tmp_path / "missing")) == logo.load(None)


def test_plain_mode_runs_once_and_keeps_exit_code(tmp_path, capsys):
    counter = tmp_path / "runs"
    log = tmp_path / "out.log"
    code = run_plain(
        [sys.executable, "-c", f"open({str(counter)!r}, 'a').write('x'); print('####50####Half####way####'); print('hi'); raise SystemExit(3)"],
        log_path=str(log),
    )
    assert code == 3
    assert counter.read_text() == "x"
    assert log.read_text().splitlines() == ["####50####Half####way####", "hi"]
    assert "[ 50%] Half · way" in capsys.readouterr().out
