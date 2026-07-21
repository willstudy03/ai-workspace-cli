"""Robust subprocess launching, especially for Windows ``.cmd``/``.bat`` shims.

npm-installed CLIs (``claude``, ``codex``, ``copilot``, ``npm`` itself) are exposed
on Windows as ``*.cmd`` shims. ``subprocess.run(["copilot", ...])`` fails because:

* a bare name isn't resolved through ``PATHEXT`` by ``CreateProcess`` (``WinError 2``),
* and a ``.cmd``/``.bat`` file can't be executed directly (``WinError 193``).

``run_cli`` resolves the executable with :func:`shutil.which` and, on Windows, runs
``.cmd``/``.bat`` shims through ``cmd /s /c "<command>"``. The ``/s`` + single
wrapping-quotes form is required so that paths/arguments containing spaces (e.g. a
shim under ``C:\\Users\\End User\\...`` or a prompt with spaces) are not split by
``cmd``'s quote-stripping rules.
"""

from __future__ import annotations

import os
import shutil
import subprocess


def run_cli(argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run ``argv`` after resolving argv[0] on PATH. Raises FileNotFoundError if absent."""
    exe = shutil.which(argv[0])
    if exe is None:
        raise FileNotFoundError(argv[0])
    rest = argv[1:]
    if os.name == "nt" and exe.lower().endswith((".cmd", ".bat")):
        # A .cmd/.bat shim must run via cmd.exe. Build a properly quoted command,
        # then wrap it for `cmd /s /c "<command>"`: with /s, cmd strips only the
        # outer wrapping quotes and runs the rest verbatim — so the shim path and
        # any arguments that contain spaces keep their own quoting intact.
        inner = subprocess.list2cmdline([exe, *rest])
        return subprocess.run(f'cmd /s /c "{inner}"', **kwargs)
    return subprocess.run([exe, *rest], **kwargs)

