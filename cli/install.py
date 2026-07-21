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


# ── PATH setup ────────────────────────────────────────────────────────────────


def _candidate_bin_dirs(installer: str) -> list[Path]:
    """Directories where the ``aiws`` executable may have been installed."""
    import sysconfig

    dirs: list[Path] = []
    if installer == "uv" and shutil.which("uv"):
        # Newer uv exposes the executable dir directly.
        r = subprocess.run(["uv", "tool", "dir", "--bin"], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            dirs.append(Path(r.stdout.strip()))
    # pip user/base scripts dirs across schemes.
    schemes = {sysconfig.get_default_scheme(), "nt_user", "posix_user", "nt", "posix_prefix"}
    for scheme in schemes:
        try:
            p = sysconfig.get_path("scripts", scheme)
            if p:
                dirs.append(Path(p))
        except Exception:
            pass
    # Common fallbacks.
    dirs.append(Path.home() / ".local" / "bin")
    if os.name == "nt":
        dirs.append(Path.home() / ".local" / "bin")

    seen: set[str] = set()
    unique: list[Path] = []
    for d in dirs:
        key = str(d)
        if d and key not in seen:
            seen.add(key)
            unique.append(d)
    return unique


def _find_aiws_bin(installer: str) -> Path | None:
    """Return the directory that actually contains the installed aiws executable."""
    for d in _candidate_bin_dirs(installer):
        for name in ("aiws", "aiws.exe", "aiws.cmd"):
            if (d / name).exists():
                return d
    return None


def _persist_path_windows(bin_dir: Path) -> bool:
    """Append bin_dir to the *user* PATH persistently via PowerShell."""
    target = str(bin_dir)
    ps = (
        "$d=[Environment]::GetEnvironmentVariable('Path','User');"
        "if($null -eq $d){$d=''};"
        "if(-not (($d -split ';') -contains $env:AIWS_BIN)){"
        "$nd=($d.TrimEnd(';') + ';' + $env:AIWS_BIN).TrimStart(';');"
        "[Environment]::SetEnvironmentVariable('Path',$nd,'User')}"
    )
    env = {**os.environ, "AIWS_BIN": target}
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        env=env,
    )
    return r.returncode == 0


def _persist_path_posix(bin_dir: Path) -> bool:
    """Append an export line for bin_dir to the user's shell rc files."""
    line = f'\n# Added by aiws installer\nexport PATH="$PATH:{bin_dir}"\n'
    changed = False
    candidates = [Path.home() / ".profile"]
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        candidates.append(Path.home() / ".zshrc")
    else:
        candidates.append(Path.home() / ".bashrc")
    for rc in candidates:
        try:
            existing = rc.read_text(encoding="utf-8") if rc.exists() else ""
            if str(bin_dir) not in existing:
                with open(rc, "a", encoding="utf-8") as f:
                    f.write(line)
                changed = True
        except Exception:
            pass
    return changed


def ensure_on_path(installer: str) -> bool:
    """Make ``aiws`` runnable now and in future shells. Returns True if usable now."""
    # Preferred path for uv: it configures the shell for us.
    if installer == "uv" and shutil.which("uv"):
        info("Configuring your shell PATH: uv tool update-shell")
        subprocess.run(["uv", "tool", "update-shell"])

    bin_dir = _find_aiws_bin(installer)
    if bin_dir is None:
        warn("Could not locate the installed aiws executable to configure PATH.")
        return verify_install()

    # Persist to future shells.
    persisted = _persist_path_windows(bin_dir) if os.name == "nt" else _persist_path_posix(bin_dir)
    if persisted:
        ok(f"Added to PATH (new shells): {bin_dir}")

    # Make it work in *this* process so we can verify immediately.
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    return verify_install()


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
        _print_next_steps()
        return

    # Not on PATH yet — actively configure it.
    warn("aiws was installed but not yet on PATH — configuring it now ...")
    if ensure_on_path(installer):
        ok(bold("aiws is installed and configured"))
        warn("Open a NEW terminal (or restart your shell) so PATH takes effect.")
        _print_next_steps()
        return

    # Still not usable — give precise manual guidance.
    bin_dir = _find_aiws_bin(installer)
    warn("aiws was installed but is still not on PATH.")
    if bin_dir:
        if os.name == "nt":
            info(f"Add this folder to PATH, then restart your terminal:\n      {bin_dir}")
        else:
            info(f'Add to your shell rc:  export PATH="$PATH:{bin_dir}"')
    elif installer == "uv":
        info("Run:  uv tool update-shell   then restart your terminal.")
    info("After updating PATH, run:  aiws init")
    sys.exit(1)


def _print_next_steps() -> None:
    print()
    info("Next: bootstrap a workspace in your project:")
    print(f"    {bold('aiws init')}")
    print()


if __name__ == "__main__":
    main()

