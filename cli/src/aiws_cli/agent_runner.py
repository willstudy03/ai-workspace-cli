"""Launch the chosen AI coding tool and hand it the aiws-workspace-init prompt."""

from __future__ import annotations

import os
import shutil

from rich.prompt import Confirm

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


def ensure_authenticated(tool: AiTool, *, assume_yes: bool, force: bool = False) -> bool:
    """Make sure the tool is signed in before we hand it the init prompt.

    A first-time user whose CLI aiws just installed is not authenticated yet, so
    launching (especially headless) would fail. If no auth env var/token is
    detected, we run the tool's interactive login flow and wait for the user to
    complete sign-in, then continue.

    Returns True if we should proceed to launch, False if the user aborted.
    """
    # Already authenticated via an environment token — nothing to do.
    env_var = next((v for v in tool.auth_env_vars if os.environ.get(v)), None)
    if env_var and not force:
        ok(f"{tool.display_name} appears authenticated (${env_var} is set).")
        return True

    if not shutil.which(tool.cli_command):
        # Can't log in to a CLI that isn't installed; caller handles the manual path.
        return True

    console.print()
    console.print(f"  [bold]Authentication[/bold]  {tool.display_name} may require sign-in")
    if tool.login_hint:
        info(tool.login_hint)

    do_login = assume_yes or Confirm.ask(
        f"    Open {tool.display_name} to sign in now?", default=True, console=console
    )
    if not do_login:
        warn("Skipping sign-in. If the tool isn't authenticated, the init step may fail.")
        info(f"You can authenticate later and re-run: aiws init --tool {tool.key}")
        # Let the caller decide whether to still attempt the launch.
        return True

    login_argv = tool.login_argv()
    info(f"Starting sign-in: {login_argv[0]} {' '.join(login_argv[1:])}".rstrip())
    console.print(f"  [dim]Complete authentication in {tool.display_name}, then return here.[/dim]")
    console.print()
    try:
        run_cli(login_argv)
    except KeyboardInterrupt:
        warn(f"{tool.display_name} sign-in interrupted.")
    except OSError as exc:
        warn(f"Could not start {tool.display_name} sign-in: {exc}")
        info(f"Authenticate manually, then re-run: aiws init --tool {tool.key}")
        return True

    # Give the user a chance to confirm before we launch the init prompt.
    if assume_yes:
        return True
    return Confirm.ask(
        f"    Finished signing in to {tool.display_name}? Continue to run aiws-workspace-init?",
        default=True,
        console=console,
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

