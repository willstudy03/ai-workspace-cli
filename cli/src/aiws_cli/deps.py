"""Preflight checks and dependency installation for ``aiws init``.

Before scaffolding a workspace we make sure the toolchain the built-in skills rely
on is present: a supported Python, a package manager (uv or pip), and MarkItDown
(used by the ``aiws-raw-to-markdown`` skill).
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys

from .console import err, info, ok, warn

MIN_PYTHON = (3, 11)


def check_python() -> bool:
    """Verify the interpreter running aiws meets the minimum version."""
    major, minor = sys.version_info[:2]
    if (major, minor) < MIN_PYTHON:
        err(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required. You have {major}.{minor}. "
            "Install a newer Python from https://python.org/downloads/"
        )
        return False
    ok(f"Python {major}.{minor}")
    return True


def detect_package_manager() -> str | None:
    """Return 'uv' if available, else 'pip' if importable, else None."""
    if shutil.which("uv"):
        return "uv"
    if _pip_available():
        return "pip"
    return None


def _pip_available() -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "--version"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def check_core_dependencies() -> bool:
    """Confirm the CLI's own runtime dependencies import correctly."""
    missing: list[str] = []
    for module in ("click", "rich"):
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    if missing:
        err(f"Missing Python packages: {', '.join(missing)}. Reinstall aiws (see install.py).")
        return False
    ok("Core dependencies (click, rich)")
    return True


def ensure_markitdown(manager: str | None, *, auto_install: bool) -> bool:
    """Ensure the MarkItDown CLI is installed; install it when requested.

    Returns True if MarkItDown is available afterwards.
    """
    if shutil.which("markitdown"):
        ok("MarkItDown found")
        return True

    if not auto_install:
        warn("MarkItDown not found — the aiws-raw-to-markdown skill needs it.")
        info(r"Install later with: pip install 'markitdown\[all]'")
        return False

    if manager is None:
        warn("No package manager available to install MarkItDown.")
        info(r"Install manually with: pip install 'markitdown\[all]'")
        return False

    info("Installing MarkItDown (markitdown[all]) ...")
    if manager == "uv":
        cmd = ["uv", "tool", "install", "markitdown[all]"]
    else:
        cmd = [sys.executable, "-m", "pip", "install", "markitdown[all]"]

    result = subprocess.run(cmd)
    if result.returncode == 0 and shutil.which("markitdown"):
        ok("MarkItDown installed")
        return True

    warn("MarkItDown install did not complete — you can install it later.")
    info(r"Retry with: pip install 'markitdown\[all]'")
    return False


def run_preflight(*, install_markitdown: bool, install_git: bool) -> str | None:
    """Run all preflight checks. Returns the detected package manager (or None)."""
    check_python()
    check_core_dependencies()
    manager = detect_package_manager()
    if manager:
        ok(f"Package manager: {manager}")
    else:
        warn("Neither uv nor pip found — some steps may need manual installation.")
    ensure_git(auto_install=install_git)
    ensure_markitdown(manager, auto_install=install_markitdown)
    return manager


# ── git ────────────────────────────────────────────────────────────────────────


def ensure_git(*, auto_install: bool) -> bool:
    """Ensure git is installed; install it when requested. Returns availability.

    git is required to fetch built-in skill updates from a tracked upstream repo.
    """
    if shutil.which("git"):
        ok("git found")
        return True

    if not auto_install:
        warn("git not found — required to fetch skill updates from an upstream repo.")
        info("Install from https://git-scm.com/downloads")
        return False

    if _install_git() and shutil.which("git"):
        ok("git installed")
        return True

    warn("git could not be installed automatically.")
    info("Install manually from https://git-scm.com/downloads")
    return False


def _install_git() -> bool:
    """Best-effort git installation using the platform's package manager."""
    system = platform.system()
    info("Installing git ...")
    try:
        if system == "Windows":
            if shutil.which("winget"):
                return subprocess.run(
                    [
                        "winget", "install", "--id", "Git.Git", "-e",
                        "--source", "winget",
                        "--accept-package-agreements", "--accept-source-agreements",
                    ]
                ).returncode == 0
            if shutil.which("choco"):
                return subprocess.run(["choco", "install", "git", "-y"]).returncode == 0
            warn("No winget/choco found to install git automatically.")
            return False
        if system == "Darwin":
            if shutil.which("brew"):
                return subprocess.run(["brew", "install", "git"]).returncode == 0
            info("Trigger the Xcode command line tools: xcode-select --install")
            return subprocess.run(["xcode-select", "--install"]).returncode == 0
        # Linux / other
        if shutil.which("apt-get"):
            subprocess.run(["sudo", "apt-get", "update"])
            return subprocess.run(["sudo", "apt-get", "install", "-y", "git"]).returncode == 0
        if shutil.which("dnf"):
            return subprocess.run(["sudo", "dnf", "install", "-y", "git"]).returncode == 0
        if shutil.which("yum"):
            return subprocess.run(["sudo", "yum", "install", "-y", "git"]).returncode == 0
        if shutil.which("pacman"):
            return subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "git"]).returncode == 0
        if shutil.which("zypper"):
            return subprocess.run(["sudo", "zypper", "install", "-y", "git"]).returncode == 0
        warn("No supported package manager found to install git automatically.")
        return False
    except Exception as exc:  # pragma: no cover - platform dependent
        warn(f"git install error: {exc}")
        return False



