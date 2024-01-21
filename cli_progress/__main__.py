"""Entry point for cli_progress."""


import argparse

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

    ui = ProgressUI(args.log, args.command, args.title, args.subtitle, args.regex)
    ui.start()


if __name__ == "__main__":
    main()
