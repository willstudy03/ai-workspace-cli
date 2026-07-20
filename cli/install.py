#!/usr/bin/env python3
"""
install.py — Bootstrap installer for the aiws CLI.

Usage:
    python install.py           # auto-detect uv (preferred) or pip
    python install.py --pip     # force pip install -e .
    python install.py --uv      # force uv tool install .
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure Unicode glyphs (✓, ✗) never crash on Windows consoles that default to a
# legacy code page (cp1252) — e.g. when output is piped/redirected.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

# ── Color helpers (stdlib only) ───────────────────────────────────────────────


def _windows_ansi_enabled() -> bool:
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        stdout = kernel32.GetStdHandle(-11)
        return kernel32.SetConsoleMode(stdout, 7) != 0
    except Exception:
        return False


USE_COLOR = sys.stdout.isatty() and (os.name != "nt" or _windows_ansi_enabled())


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


def green(t: str) -> str:
    return _c(t, "32")


def yellow(t: str) -> str:
    return _c(t, "33")


def red(t: str) -> str:
    return _c(t, "31")


def bold(t: str) -> str:
    return _c(t, "1")


def info(msg: str) -> None:
    print(f"  {msg}")


def ok(msg: str) -> None:
    print(f"  {green('✓')} {msg}")


def warn(msg: str) -> None:
    print(f"  {yellow('!')} {msg}")


def die(msg: str, code: int = 1) -> None:
    print(f"  {red('✗')} {msg}", file=sys.stderr)
    sys.exit(code)


# ── Steps ─────────────────────────────────────────────────────────────────────


def check_python() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) < (3, 11):
        die(f"Python 3.11+ required. You have {major}.{minor}.")
    ok(f"Python {major}.{minor}")


def detect_repo_root() -> Path:
    here = Path(__file__).parent.resolve()
    if not (here / "pyproject.toml").exists():
        die(f"Run install.py from the cli/ directory (where pyproject.toml lives).\n  Got: {here}")
    return here


def detect_installer(force_uv: bool, force_pip: bool) -> str:
    if force_pip:
        return "pip"
    if force_uv:
        if not shutil.which("uv"):
            die("uv not found. Install from https://docs.astral.sh/uv/ or use --pip")
        return "uv"
    return "uv" if shutil.which("uv") else "pip"


def install_with_uv(repo_root: Path) -> None:
    info("Running: uv tool install . --force --reinstall")
    if subprocess.run(["uv", "tool", "install", ".", "--force", "--reinstall"], cwd=repo_root).returncode:
        die("uv install failed. Try: python install.py --pip")


def install_with_pip(repo_root: Path) -> None:
    info("Running: pip install -e .")
    if subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], cwd=repo_root).returncode:
        die("pip install failed. See errors above.")


def verify_install() -> bool:
    if not shutil.which("aiws"):
        return False
    return subprocess.run(["aiws", "--version"], capture_output=True, text=True).returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the aiws CLI")
    parser.add_argument("--pip", action="store_true", help="Force pip install")
    parser.add_argument("--uv", action="store_true", help="Force uv install")
    args = parser.parse_args()

    print()
    print(bold("aiws") + "  installer")
    print()

    check_python()
    repo_root = detect_repo_root()

    installer = detect_installer(force_uv=args.uv, force_pip=args.pip)
    info(f"Package manager: {bold(installer)}")
    print()

    if installer == "uv":
        install_with_uv(repo_root)
    else:
        install_with_pip(repo_root)

    print()
    if verify_install():
        ok(bold("aiws is on PATH and working"))
        print()
        info("Next: bootstrap a workspace in your project:")
        print(f"    {bold('aiws init')}")
        print()
    else:
        warn("aiws was installed but not found on PATH.")
        if os.name == "nt" and installer == "uv":
            warn("Add the uv tools dir to PATH:  uv tool dir")
        info("After updating PATH, run:  aiws init")
        sys.exit(1)


if __name__ == "__main__":
    main()

