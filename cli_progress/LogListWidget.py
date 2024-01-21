import urwid

from .ANSIWidget import ANSIWidget


class LogListBox(urwid.ListBox):
    def __init__(self):
        body = urwid.SimpleFocusListWalker([get_line("")])
        super().__init__(body)

    def add_log_line(self, data, err, replace=False):
        txt = f"\033[91m{data}\033[0m" if err else data
        if replace:
            self.body[-1].set_content(txt)
        else:
            self.body.append(get_line(txt))
        if self.is_focus_end():
            self.focus_position = len(self.body) - 1

    def is_focus_end(self):
        return self.focus_position >= len(self.body) - 2


def get_line(text):
    return urwid.BoxAdapter(ANSIWidget(text), 1)
