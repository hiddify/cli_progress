Changelog
=========


(unreleased)
------------

Fix
~~~
- Bypass urwid UI when stdout is not a TTY. [Cursor, Hossein]

  Without a terminal, cli_progress wraps install/apply in an urwid MainLoop
  that never exits after the subprocess finishes. This leaves apply_configs and
  apply_users stuck indefinitely and prevents sing-box configs from reloading.

  Run the wrapped command directly in non-interactive environments.

  Fixes hiddify/Hiddify-Manager#5479

Other
~~~~~
- Merge pull request #8 from mktwix/fix/non-tty-bypass-urwid. [Hiddify]

  fix: bypass urwid UI when stdout is not a TTY


2.2.0 (2026-09-19)
------------------
- Release: version 2.2.0 🚀 [Hiddify]


2.1.0 (2026-09-19)
------------------
- Release: version 2.1.0 🚀 [Hiddify]


2.0.0 (2024-04-05)
------------------
- Release: version 2.0.0 🚀 [Hiddify]
- Use asynio event loop. [Hiddify]


1.9.0 (2024-04-01)
------------------
- Release: version 1.9.0 🚀 [Hiddify]


1.8.0 (2024-04-01)
------------------
- Update dependencies. [Hiddify]


1.7.0 (2024-01-27)
------------------
- Release: version 1.7.0 🚀 [hiddify]


1.6.0 (2024-01-21)
------------------

Fix
~~~
- Bug in key. [Hiddify]

Other
~~~~~
- Release: version 1.6.0 🚀 [Hiddify]


1.5.0 (2024-01-21)
------------------

Fix
~~~
- Bug in ansi long text. [Hiddify]

Other
~~~~~
- Release: version 1.5.0 🚀 [Hiddify]


1.4.0 (2024-01-21)
------------------

Fix
~~~
- Long text. [Hiddify]

Other
~~~~~
- Release: version 1.4.0 🚀 [Hiddify]


1.3.0 (2024-01-21)
------------------

Fix
~~~
- Bug. [Hiddify]

Other
~~~~~
- Release: version 1.3.0 🚀 [Hiddify]


1.2.0 (2024-01-21)
------------------

New
~~~
- Add exit code. [Hiddify]

Other
~~~~~
- Release: version 1.2.0 🚀 [Hiddify]


1.1.0 (2024-01-21)
------------------

Fix
~~~
- Typo. [Hiddify]

Other
~~~~~
- Release: version 1.1.0 🚀 [Hiddify]
- Format the files. [Hiddify]


1.0.0 (2024-01-21)
------------------
- Release: version 1.0.0 🚀 [Hiddify]
- ✅ Ready to clone and code. [hiddify-com]
- Initial commit. [Hiddify]


