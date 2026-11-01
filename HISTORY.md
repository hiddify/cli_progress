Changelog
=========


(unreleased)
------------
- Merge remote-tracking branch 'pr/12' [hiddify-com]
- Build(deps-dev): bump pytest from 9.1.1 to 9.2.0. [dependabot[bot]]

  Bumps [pytest](https://github.com/pytest-dev/pytest) from 9.1.1 to 9.2.0.
  - [Release notes](https://github.com/pytest-dev/pytest/releases)
  - [Changelog](https://github.com/pytest-dev/pytest/blob/main/CHANGELOG.rst)
  - [Commits](https://github.com/pytest-dev/pytest/compare/9.1.1...9.2.0)

  ---
  updated-dependencies:
  - dependency-name: pytest
    dependency-version: 9.2.0
    dependency-type: direct:development
    update-type: version-update:semver-minor
  ...
- Merge remote-tracking branch 'pr/11' [hiddify-com]
- Build(deps-dev): bump mypy from 2.4.0 to 2.4.1. [dependabot[bot]]

  Bumps [mypy](https://github.com/python/mypy) from 2.4.0 to 2.4.1.
  - [Changelog](https://github.com/python/mypy/blob/master/CHANGELOG.md)
  - [Commits](https://github.com/python/mypy/compare/v2.4.0...v2.4.1)

  ---
  updated-dependencies:
  - dependency-name: mypy
    dependency-version: 2.4.1
    dependency-type: direct:development
    update-type: version-update:semver-patch
  ...
- Merge remote-tracking branch 'pr/10' [hiddify-com]
- Build(deps): bump urwid from 3.0.5 to 4.2.5. [dependabot[bot]]

  Bumps [urwid](https://github.com/urwid/urwid) from 3.0.5 to 4.2.5.
  - [Release notes](https://github.com/urwid/urwid/releases)
  - [Changelog](https://github.com/urwid/urwid/blob/master/docs/changelog.rst)
  - [Commits](https://github.com/urwid/urwid/compare/3.0.5...4.2.5)

  ---
  updated-dependencies:
  - dependency-name: urwid
    dependency-version: 4.2.5
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...
- Merge remote-tracking branch 'pr/9' [hiddify-com]
- Build(deps): bump actions/checkout from 4 to 7. [dependabot[bot]]

  Bumps [actions/checkout](https://github.com/actions/checkout) from 4 to 7.
  - [Release notes](https://github.com/actions/checkout/releases)
  - [Changelog](https://github.com/actions/checkout/blob/main/CHANGELOG.md)
  - [Commits](https://github.com/actions/checkout/compare/v4...v7)

  ---
  updated-dependencies:
  - dependency-name: actions/checkout
    dependency-version: '7'
    dependency-type: direct:production
    update-type: version-update:semver-major
  ...


3.0.5 (2026-11-01)
------------------

Fix
~~~
- Exit when the terminal is gone instead of spinning at full CPU.
  [hiddify-com]

  urwid reads its input in 'while ready: read'; a hung-up terminal is always ready with nothing to read, so that one
  callback never returned (no frame, no signal handler, no exit) and the process stayed at ~60% CPU for good.
  - a hung-up terminal (EOF / EIO on stdin) ends the window; a running command is stopped as on SIGHUP
  - SIGTERM / SIGHUP after the command ended close the window (they only stopped a running command)
  - each second: the parent gone or the terminal unusable stops it; after the end, no key for 30 min closes it

Other
~~~~~
- Release: version 3.0.5 🚀 [hiddify-com]


3.0.4 (2026-10-17)
------------------
- Release: version 3.0.4 🚀 [hiddify-com]
- Make it fantastic. [hiddify-com]


3.0.2 (2026-10-17)
------------------
- Release: version 3.0.2 🚀 [hiddify-com]
- Make it fantastic. [hiddify-com]


3.0.1 (2026-10-17)
------------------
- Release: version 3.0.1 🚀 [hiddify-com]
- Make it fantastic. [hiddify-com]
- Make it fantastic. [hiddify-com]


3.0.0 (2026-10-17)
------------------
- Release: version 3.0.0 🚀 [hiddify-com]
- Make it fantastic. [hiddify-com]
- Make it fantastic. [hiddify-com]


2.2.2 (2026-09-19)
------------------
- Release: version 2.2.2 🚀 [Hiddify]


2.2.1 (2026-09-19)
------------------

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
- Release: version 2.2.1 🚀 [Hiddify]
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


