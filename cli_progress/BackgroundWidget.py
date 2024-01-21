import urwid


class BackgroundView(urwid.WidgetWrap):
    def __init__(self, forground, header, footer):
        self.forground = forground
        self.header_widget = header
        self.footer_widget = footer
        super().__init__(self.main_window())

    def main_shadow(self, w):
        """Wrap a shadow and background around widget w."""
        bg = urwid.AttrMap(urwid.SolidFill("\u2592"), "screen edge")
        shadow = urwid.AttrMap(urwid.SolidFill(" "), "main shadow")

        bg = urwid.Overlay(
            shadow,
            bg,
            ("fixed left", 2),
            ("fixed right", 1),
            ("fixed top", 2),
            ("fixed bottom", 1),
        )
        w = urwid.Overlay(
            w,
            bg,
            ("fixed left", 1),
            ("fixed right", 2),
            ("fixed top", 1),
            ("fixed bottom", 2),
        )
        # bg = urwid.Overlay(shadow, bg, ("fixed left", 0), ("fixed right", 0), ("fixed top", 0), ("fixed bottom", 0))
        # w = urwid.Overlay(w, bg, ("fixed left", 0), ("fixed right", 0), ("fixed top", 0), ("fixed bottom", 0))
        return w

    def main_window(self):
        self.forground_wrap = urwid.WidgetWrap(self.forground)
        w = urwid.Padding(self.forground_wrap, ("fixed left", 1), ("fixed right", 0))
        w = urwid.AttrMap(w, "body")
        w = urwid.LineBox(w)
        w = urwid.AttrMap(w, "line")
        w = self.main_shadow(w)
        return urwid.Frame(body=w, header=self.header_widget, footer=self.footer_widget)
