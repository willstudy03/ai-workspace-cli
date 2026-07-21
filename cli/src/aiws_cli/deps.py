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
from .proc import run_cli

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
    try:
        if manager == "uv":
            result = run_cli(["uv", "tool", "install", "markitdown[all]"])
        else:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "markitdown[all]"])
    except OSError as exc:
        warn(f"MarkItDown install could not start ({exc}).")
        info(r"Install manually with: pip install 'markitdown\[all]'")
        return False
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
                return run_cli(
                    [
                        "winget", "install", "--id", "Git.Git", "-e",
                        "--source", "winget",
                        "--accept-package-agreements", "--accept-source-agreements",
                    ]
                ).returncode == 0
            if shutil.which("choco"):
                return run_cli(["choco", "install", "git", "-y"]).returncode == 0
            warn("No winget/choco found to install git automatically.")
            return False
        if system == "Darwin":
            if shutil.which("brew"):
                return run_cli(["brew", "install", "git"]).returncode == 0
            info("Trigger the Xcode command line tools: xcode-select --install")
            return run_cli(["xcode-select", "--install"]).returncode == 0
        # Linux / other
        if shutil.which("apt-get"):
            run_cli(["sudo", "apt-get", "update"])
            return run_cli(["sudo", "apt-get", "install", "-y", "git"]).returncode == 0
        if shutil.which("dnf"):
            return run_cli(["sudo", "dnf", "install", "-y", "git"]).returncode == 0
        if shutil.which("yum"):
            return run_cli(["sudo", "yum", "install", "-y", "git"]).returncode == 0
        if shutil.which("pacman"):
            return run_cli(["sudo", "pacman", "-S", "--noconfirm", "git"]).returncode == 0
        if shutil.which("zypper"):
            return run_cli(["sudo", "zypper", "install", "-y", "git"]).returncode == 0
        warn("No supported package manager found to install git automatically.")
        return False
    except Exception as exc:  # pragma: no cover - platform dependent
        warn(f"git install error: {exc}")
        return False


# ── Node.js / npm ────────────────────────────────────────────────────────────


def ensure_node(*, auto_install: bool) -> bool:
    """Ensure Node.js/npm is installed; install it when requested.

    npm is how the AI tool CLIs (Claude Code, GitHub Copilot, OpenAI Codex) are
    installed, so ``aiws init`` needs it to offer to install a missing tool CLI.
    Returns True if npm is available afterwards.
    """
    if shutil.which("npm"):
        ok("Node.js/npm found")
        return True

    if not auto_install:
        warn("npm not found — needed to install AI tool CLIs (claude/copilot/codex).")
        info("Install Node.js (includes npm) from https://nodejs.org/en/download")
        return False

    if _install_node() and shutil.which("npm"):
        ok("Node.js/npm installed")
        return True

    # On Windows a freshly installed npm often isn't on the current shell's PATH.
    if shutil.which("npm"):
        ok("Node.js/npm installed")
        return True
    warn("Node.js/npm could not be installed (or isn't on PATH in this shell yet).")
    info("Install manually from https://nodejs.org/en/download, then re-run aiws init.")
    return False


def _install_node() -> bool:
    """Best-effort Node.js (LTS) installation using the platform's package manager."""
    system = platform.system()
    info("Installing Node.js LTS (includes npm) ...")
    try:
        if system == "Windows":
            if shutil.which("winget"):
                return run_cli(
                    [
                        "winget", "install", "--id", "OpenJS.NodeJS.LTS", "-e",
                        "--source", "winget",
                        "--accept-package-agreements", "--accept-source-agreements",
                    ]
                ).returncode == 0
            if shutil.which("choco"):
                return run_cli(["choco", "install", "nodejs-lts", "-y"]).returncode == 0
            warn("No winget/choco found to install Node.js automatically.")
            return False
        if system == "Darwin":
            if shutil.which("brew"):
                return run_cli(["brew", "install", "node"]).returncode == 0
            warn("Homebrew not found. Install Node.js from https://nodejs.org/en/download")
            return False
        # Linux / other
        if shutil.which("apt-get"):
            run_cli(["sudo", "apt-get", "update"])
            return run_cli(["sudo", "apt-get", "install", "-y", "nodejs", "npm"]).returncode == 0
        if shutil.which("dnf"):
            return run_cli(["sudo", "dnf", "install", "-y", "nodejs", "npm"]).returncode == 0
        if shutil.which("yum"):
            return run_cli(["sudo", "yum", "install", "-y", "nodejs", "npm"]).returncode == 0
        if shutil.which("pacman"):
            return run_cli(["sudo", "pacman", "-S", "--noconfirm", "nodejs", "npm"]).returncode == 0
        if shutil.which("zypper"):
            return run_cli(["sudo", "zypper", "install", "-y", "nodejs", "npm"]).returncode == 0
        warn("No supported package manager found to install Node.js automatically.")
        return False
    except Exception as exc:  # pragma: no cover - platform dependent
        warn(f"Node.js install error: {exc}")
        return False



