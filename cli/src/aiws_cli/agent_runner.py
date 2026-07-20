"""Launch the chosen AI coding tool and hand it the aiws-workspace-init prompt."""

from __future__ import annotations

import shutil

from .console import console, info, ok, warn
from .proc import run_cli
from .tools import AiTool

INIT_PROMPT = (
    "Use the aiws-workspace-init skill to scaffold the full agent workspace folder "
    "structure (agents, codebases, docs, knowledge, references, scripts, skills) in "
    "this project. The built-in aiws-* skills are already installed."
)

# Stronger phrasing for non-interactive runs so the agent completes without pausing.
AUTO_INIT_PROMPT = (
    INIT_PROMPT + " Run it now, end to end, without asking for confirmation."
)


def launch_agent(tool: AiTool, *, prompt: str | None = None, headless: bool = False) -> bool:
    """Open the tool's CLI with the init prompt. Returns True if it was launched.

    When ``headless`` is True the tool is run non-interactively with auto-approval
    so it executes ``aiws-workspace-init`` to completion without prompting.
    """
    if prompt is None:
        prompt = AUTO_INIT_PROMPT if headless else INIT_PROMPT

    if not shutil.which(tool.cli_command):
        warn(f"{tool.display_name} CLI ('{tool.cli_command}') is not on PATH — cannot launch.")
        _print_manual_prompt(tool, prompt)
        return False

    argv = tool.headless_argv(prompt) if headless else tool.launch_argv(prompt)
    mode = "headless" if headless else "interactive"
    info(f"Launching {tool.display_name} ({mode}): {argv[0]} ...")
    console.print(f"  [dim]It will be asked to run:[/dim] {prompt}")
    console.print()
    try:
        run_cli(argv)
    except KeyboardInterrupt:
        warn(f"{tool.display_name} session interrupted.")
        return True
    except OSError as exc:
        warn(f"Could not launch {tool.display_name}: {exc}")
        _print_manual_prompt(tool, prompt)
        return False
    ok(f"{tool.display_name} session finished.")
    return True


def _print_manual_prompt(tool: AiTool, prompt: str) -> None:
    console.print()
    console.print("  [bold]To finish manually:[/bold]")
    console.print(f"    1. Install {tool.display_name}: [bold]{tool.install_hint}[/bold]")
    console.print(f"    2. Open it here and ask:  [italic]{prompt}[/italic]")

