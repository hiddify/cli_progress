# cli_progress

Run a long command (an installer, an update) behind a calm full-screen progress window.

While it runs you see only your logo, the current step and a smooth progress bar, with the time it has taken and
roughly how long is left. The output is one key away, and it is always written to the log file.

```
                    ▓▓▓
                  ▓▓▓▓▓
             ▓▓▓
           ▓▓▓▓▓  ▓▓▓▓▓
      ▓▓▓  ▓▓▓▓▓  ▓▓▓▓▓
   ▓▓▓▓▓▓  ▓▓▓▓▓  ▓▓▓▓▓
   ▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓
   ▓▓▓▓▓▓  ▓▓▓▓▓  ▓▓▓▓▓

        Hiddify Manager   v14.0.0

 Installing...

 ━━━━━━━━━━━━━━━━━━━━━━━━━╸━━━━━━━━━━━━━  62.1%
 ⏱ 2m 10s   ≈ 1m 20s left    ⚠ 1

 ✓ MySQL                                 12s
 ✓ Hiddify Panel                         48s
 ⠦ Xray                                   6s

   Setting up xray-core (25.10.15) ...

            L  show log    Q  quit
```

## Usage

```bash
python -m cli_progress --title "Hiddify Manager" --subtitle v14 \
    --logo logo.ico --log /var/log/install.log -- ./install.sh --no-gui
```

| Option | |
|---|---|
| `--title`, `--subtitle` | shown under the logo |
| `--logo FILE` | a text file with the logo (block characters); a built-in one by default |
| `--log FILE` | the command's whole output (with its colors) goes there |
| `--regex` | the progress line; default `####<percent>####<title>####<step>####` |
| `--auto-exit SECONDS` | close this long after a success (default 5; `0` waits for a key) |
| `--no-counts` | hide the ⚠ warnings / ✗ errors counts next to the timer |
| `--plain` | no window: print the output and a line for each step |

The command reports progress by printing lines such as:

```bash
echo "####42####Installing...####Hiddify Panel####"
```

Those lines are not shown or logged as output; they move the bar and add a step.

### Keys

| | Running | Finished |
|---|---|---|
| `L` | show the log | show the log |
| `Q`, `Esc`, Ctrl+C | ask before stopping (Ctrl+C twice stops) | close |
| `Enter` | | close |

In the log (it opens under the logo and the progress bar, which stay on top): `↑` `↓` `PgUp` `PgDn` scroll (it holds still while you read), `End` follows new lines again, `e` / `E` jump
to the next / previous error or warning, `Esc` goes back.

### What happens when

- **Success**: the logo turns green and the window closes after a few seconds (any key keeps it open).
- **Failure**: the logo turns red, the step that failed is marked, the last errors and warnings are shown, and the
  window stays until you close it. A short summary with the log's path is printed after it closes.
- **Stop**: the command gets SIGINT (to clean up), then SIGTERM, then SIGKILL. The exit code is 130.
- **No usable terminal** (a pipe, cron, `ssh` without `-t`, `TERM=dumb`): plain output, same log, same exit code. The
  command never runs twice.

The command runs in its own session with no stdin: the terminal's Ctrl+C reaches the window (which asks first), not
the command.

## Development

```bash
pip install -e .[test]
pytest
```
