"""Colors of the progress window.

Each entry: (name, 16-color fg, 16-color bg, mono, 256-color fg, 256-color bg). The 256-color part is used when the
terminal has it (almost every one does); the rest is the fallback.
"""

from __future__ import annotations

BG = "#001"  # deep navy
PANEL = "g11"

LOGO_DONE = "#0d6"
LOGO_FAIL = "#f44"

PALETTE: list[tuple[str, str, str, str, str, str]] = [
    ("bg", "default", "default", "", "default", BG),
    ("title", "white,bold", "default", "bold", "#fff,bold", BG),
    ("subtitle", "light blue", "default", "", "#69f", BG),
    ("muted", "dark gray", "default", "", "g50", BG),
    ("faint", "dark gray", "default", "", "g30", BG),
    ("step", "white", "default", "", "#def", BG),
    ("step_done", "dark green", "default", "", "#3c7", BG),
    ("step_desc", "light gray", "default", "", "g70", BG),
    ("spinner", "light cyan", "default", "", "#0df", BG),
    ("bar_done", "light cyan", "default", "", "#0cf", BG),
    ("bar_head", "white", "default", "", "#aff", BG),
    ("bar_todo", "dark gray", "default", "", "g23", BG),
    ("bar_ok", "light green", "default", "", "#0d6", BG),
    ("bar_fail", "light red", "default", "", "#f44", BG),
    ("percent", "white,bold", "default", "bold", "#fff,bold", BG),
    ("ok", "light green,bold", "default", "bold", "#0d6,bold", BG),
    ("fail", "light red,bold", "default", "bold", "#f55,bold", BG),
    ("warn", "yellow", "default", "", "#fc3", BG),
    ("err", "light red", "default", "", "#f66", BG),
    ("preview", "dark gray", "default", "", "g42", BG),
    ("key", "black", "light gray", "standout", "#001", "#9cf"),
    ("key_label", "light gray", "default", "", "g62", BG),
    ("badge_warn", "black", "yellow", "standout", "#001", "#fc3"),
    ("badge_err", "white", "dark red", "standout", "#fff", "#c22"),
    # log view
    ("log_bg", "default", "default", "", "g85", "g7"),
    ("log_head", "black", "light gray", "standout", "#001", "#8bf"),
    ("log_head_dim", "dark blue", "light gray", "", "#124", "#8bf"),
    ("log_num", "dark gray", "default", "", "g30", "g7"),
    ("log_focus", "white", "dark blue", "standout", "#fff", "g19"),
    ("log_match", "black", "yellow", "standout", "#001", "#fc3"),
    # dialog
    ("dialog", "white", "dark blue", "", "#fff", "g15"),
    ("dialog_title", "white,bold", "dark blue", "bold", "#fc3,bold", "g15"),
    ("dialog_border", "light blue", "dark blue", "", "#58f", "g15"),
    ("button", "white", "dark blue", "", "g85", "g23"),
    ("button_focus", "black", "light cyan", "standout", "#001", "#0df"),
    ("failure_box", "light red", "default", "", "#f99", "#200"),
    ("failure_title", "light red,bold", "default", "bold", "#f66,bold", "#200"),
]

PALETTE += [
    # The logo fills like a glass as the progress grows: light blue on top, dark blue rising from the bottom
    ("logo_light", "light cyan", "default", "", "#bdf", BG),
    ("logo_fill", "light blue", "default", "", "#06e", BG),
    ("logo_fill_deep", "dark blue", "default", "", "#04c", BG),
    ("logo_surface", "light blue", "default", "", "#4af", BG),
    ("logo_shine", "white", "default", "", "#eff,bold", BG),
    ("logo_ok", "light green", "default", "", LOGO_DONE, BG),
    ("logo_fail", "light red", "default", "", LOGO_FAIL, BG),
]

# The 16 ANSI colors a command prints (SGR 30-37 / 90-97), in the log
ANSI_NAMES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
_ANSI_256 = {
    "black": "g35",
    "red": "#f66",
    "green": "#3c7",
    "yellow": "#fc3",
    "blue": "#69f",
    "magenta": "#d7f",
    "cyan": "#0cf",
    "white": "g85",
}
_ANSI_16 = {
    "black": "dark gray",
    "red": "light red",
    "green": "light green",
    "yellow": "yellow",
    "blue": "light blue",
    "magenta": "light magenta",
    "cyan": "light cyan",
    "white": "light gray",
}
for _name in ANSI_NAMES:
    PALETTE.append((f"ansi_{_name}", _ANSI_16[_name], "default", "", _ANSI_256[_name], "g7"))
    PALETTE.append((f"ansi_{_name}_bold", _ANSI_16[_name] + ",bold", "default", "bold", _ANSI_256[_name] + ",bold", "g7"))
PALETTE.append(("ansi_bold", "white,bold", "default", "bold", "#fff,bold", "g7"))
