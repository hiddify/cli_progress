#!/usr/bin/env python

from __future__ import annotations
from typing import Tuple, List, Optional, Any, Iterable
import threading
from .BackgroundWidget import BackgroundView
import os
import subprocess
import sys
import signal
import urwid
import re
from twisted.internet import reactor, threads

from .LogListWidget import LogListBox


main_event_loop = urwid.TwistedEventLoop()

palette = [
    ("screen edge", "light blue", "dark blue"),
    ("main shadow", "dark gray", "black"),
    ("body", "default", "default"),
    ("foot", "dark cyan", "dark blue", "bold"),
    ("key", "light cyan", "dark blue", "underline"),
    ("footer_foot", "light gray", "black"),
    ("footer_key", "light cyan", "black", "underline"),
    ("footer_title", "white", "black"),
    ("header_title", "black", "white"),
    ("header_version", "dark red", "white"),
    ("header_back", "black", "white"),
    ("progressbar_header", "black", "light gray"),
    ("progress_header_title", "white", "black", "bold"),
    ("progress_header_descr", "dark blue", "light gray"),
    ("progressbar_normal", "light gray", "black"),
    ("progressbar_complete", "white", "dark green"),
    ("progressbar_error","dark red","dark red")
]

footer_info = [
    ("footer_title", "KEY"),
    "    ",
    ("footer_key", "Q"),
    ", ",
    ("footer_key", "CTRL+C"),
    " exits      ",
    ("footer_key", "UP"),
    ", ",
    ("footer_key", "DOWN"),
    ", ",
    ("footer_key", "PAGE+UP"),
    ", ",
    ("footer_key", "PAGE DOWN"),
    " move",
]


def exit_on_enter(key):
    if key in ("q", "Q"):
        raise urwid.ExitMainLoop()


class ProgressUI:
    def __init__(
        self, logpath: str, command: str, title: str, subtitle: str, regex: str
    ):
        self.logpath = logpath or "/dev/null"
        self.cmds = command
        self.regex = re.compile(regex)
        header_text = [
            ("header_title", title),
            "    ",
            ("header_version", subtitle),
        ]

        header_widget = urwid.AttrMap(urwid.Text(header_text), "header_back")
        self.progressbar = urwid.ProgressBar(
            "progressbar_normal", "progressbar_complete", 0, 100
        )
        self.listbox = LogListBox()
        self.progressbar_header = urwid.Text("")
        footer_footer = urwid.AttrMap(urwid.Text(footer_info), "footer_foot")

        footer = urwid.Pile(
            [
                urwid.AttrMap(self.progressbar_header, "progressbar_header"),
                self.progressbar,
                footer_footer,
            ]
        )

        self.loop = urwid.MainLoop(
            BackgroundView(urwid.AttrMap(self.listbox, "body"), header_widget, footer),
            palette,
            unhandled_input=exit_on_enter,
            handle_mouse=False,
            event_loop=main_event_loop,
        )
        self.write_fd = self.loop.watch_pipe(self.received_output)
        self.write_fd_err = self.loop.watch_pipe(self.received_err)

        self.std_err_line = ["", ""]

    def received_output(self, data):
        self.handle_in(data, False)

    def received_err(self, data):
        self.handle_in(data, True)

    def handle_in(self, data, err):
        indx = 1 if err else 0
        last_char = ""
        # print(self.std_err_line[indx],data)
        for c in data.decode():
            if c in ["\r", "\n"]:
                self.handle_line(self.std_err_line[indx], err)
                self.std_err_line[indx] = ""
            # elif '\r' == c:
            #     listbox.add_log_line(std_err_line[indx], err, replace=True)
            #     std_err_line[indx] = ''
            else:
                self.std_err_line[indx] += c

    def handle_line(self, data, err):
        self.logfile.writelines([data])
        # data = escape_ansi(data)
        progress_match = self.regex.match(data)
        if progress_match:
            p = int(progress_match.group("progress"))
            title = f'{progress_match.group("title")} '
            desc = f'{progress_match.group("subtitle")}'
            self.handle_progress(p, title, desc)

        else:
            self.listbox.add_log_line(data, err)

    def handle_progress(self, progress: int, title: str, subtitle: str):
        self.progressbar.set_completion(progress)
        self.progressbar_header.set_text(
            [
                ("progress_header_title", title),
                (" "),
                ("progress_header_descr", subtitle),
            ]
        )

    def start(self):
        with open(self.logpath, "w") as self.logfile:
            proc = subprocess.Popen(
                self.cmds,
                stdout=self.write_fd,
                stderr=self.write_fd_err,
                close_fds=True,
            )
            d = threads.deferToThread(proc.wait)
            d.addCallback(self.exit_loop)
            # try:
            self.loop.run()
            # except:
            #     pass
            try:
                proc.send_signal(signal.SIGTERM)
            except:
                pass
            sys.exit(0)

    def exit_loop_finish_proceess(self, exit_code):
        # self.handle_line("Process Finished... To Exit Press Q",False)
        if exit_code:
            self.progressbar.normal="progressbar_error"
            self.handle_progress(self.progressbar.current, "An Error Occured...", f"Code {exit_code}")
        else:
            self.handle_progress(100, "Process Finished...", "To Exit Press Q")
            if self.listbox.is_focus_end():
                main_event_loop.alarm(1, self.exit_loop_exception)

    def exit_loop_exception(self):
        if self.listbox.is_focus_end():
            raise urwid.ExitMainLoop

    @main_event_loop.handle_exit
    def exit_loop(self, exit_code):
        main_event_loop.alarm(0, lambda: self.exit_loop_finish_proceess(exit_code))