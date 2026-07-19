"""Entry point for cli_progress."""


import argparse
import subprocess
import sys

from .progress_ui import ProgressUI


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process log file with a command")

    # Add a title to the command-line arguments
    title_group = parser.add_argument_group("Arguments")
    title_group.add_argument("--log", help="Path to the log file", required=False)
    title_group.add_argument("--title", default="Title", help="Title for the script", required=False)
    title_group.add_argument(
        "--subtitle",
        default="SubTitle",
        help="SubTitle for the script. e.x. version",
        required=False,
    )
    title_group.add_argument(
        "--regex",
        default=r"####(?P<progress>\d+)####(?P<title>.*?)####(?P<subtitle>.*?)####",
        help="Regex for capturing the progress",
        required=False,
    )
    title_group.add_argument("command", nargs=argparse.REMAINDER, help="Command and its arguments")

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Without a TTY, urwid's MainLoop never exits after the subprocess finishes
    # (see hiddify/Hiddify-Manager#5479). Run the wrapped command directly.
    if not sys.stdout.isatty():
        cmd = args.command
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            print("cli_progress: no command provided", file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(subprocess.call(cmd))

    ui = ProgressUI(args.log, args.command, args.title, args.subtitle, args.regex)
    ui.start()


if __name__ == "__main__":
    main()
