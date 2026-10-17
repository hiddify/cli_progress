"""cli_progress: run a command behind a calm full-screen progress window.

    python -m cli_progress --title "Hiddify Manager" --subtitle v14 --logo logo.txt --log install.log -- ./install.sh

The command reports progress with lines like ``####42####Installing...####Hiddify Panel####`` (see ``--regex``).
"""

from __future__ import annotations

import argparse
import sys

from .runner import DEFAULT_REGEX


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="cli_progress", description="Run a command behind a full-screen progress window.")
    parser.add_argument("--log", help="write the command's output to this file")
    parser.add_argument("--title", default="", help="shown under the logo")
    parser.add_argument("--subtitle", default="", help="shown next to the title, e.g. a version")
    parser.add_argument("--logo", help="a text file with the logo (block characters); a built-in one by default")
    parser.add_argument("--regex", default=DEFAULT_REGEX, help="the progress line, with the groups progress, title, subtitle")
    parser.add_argument("--auto-exit", type=float, default=5.0, help="seconds before closing after a success (0: wait for a key)")
    parser.add_argument("--no-counts", action="store_true", help="do not show the warning / error counts next to the timer")
    parser.add_argument("--plain", action="store_true", help="no window: print the output and the progress as lines")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="the command and its arguments")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_arguments(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        print("cli_progress: no command given", file=sys.stderr)
        raise SystemExit(2)

    from .app import terminal_problem

    problem = None if args.plain else terminal_problem()
    if args.plain or problem:
        from .plain import run_plain

        if problem:
            print(f"cli_progress: no progress window: {problem}", file=sys.stderr)

        raise SystemExit(run_plain(command, log_path=args.log, regex=args.regex))

    from .app import ProgressApp

    app = ProgressApp(
        command,
        title=args.title,
        subtitle=args.subtitle,
        log_path=args.log,
        logo_path=args.logo,
        regex=args.regex,
        auto_exit=args.auto_exit,
        show_counts=not args.no_counts,
    )
    raise SystemExit(app.run())


if __name__ == "__main__":
    main()
