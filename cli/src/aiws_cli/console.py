"""Shared Rich console objects and small print helpers for the aiws CLI."""

from __future__ import annotations

import sys

from rich.console import Console

# Ensure Unicode glyphs (✓, ↷, box-drawing) never crash on Windows consoles that
# default to a legacy code page (cp1252) — e.g. when output is piped/redirected.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except Exception:
        pass

console = Console()
err_console = Console(stderr=True, style="bold red")


def info(msg: str) -> None:
    console.print(f"  {msg}")


def ok(msg: str) -> None:
    console.print(f"  [green]✓[/green] {msg}")


def warn(msg: str) -> None:
    console.print(f"  [yellow]![/yellow] {msg}")


def err(msg: str) -> None:
    err_console.print(f"  ✗ {msg}")


def step(label: str, title: str) -> None:
    """Print a wizard step header, e.g. `Step 1  Choose your AI tool`."""
    console.print()
    console.print(f"  [bold]{label}[/bold]  {title}")


