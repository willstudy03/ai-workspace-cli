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


def build_ingest_prompt(*, validate: bool, auto: bool) -> str:
    """Prompt for the knowledge-ingestion pipeline (raw-to-markdown -> create-knowledge).

    Optionally chains aiws-validate-knowledge, and (for ``auto``) adds explicit
    "run without confirmation" phrasing.
    """
    steps = [
        "Run the knowledge ingestion pipeline for this workspace.",
        "1) Use the aiws-raw-to-markdown skill to convert EVERY non-Markdown file under "
        "knowledge/source/raw/ into Markdown, written back into knowledge/source/raw/.",
        "2) Then use the aiws-create-knowledge skill to curate each Markdown file in "
        "knowledge/source/raw/ into a standards-compliant knowledge entry — process ONE "
        "FILE AT A TIME and file each into the correct taxonomy folder (concepts, systems, "
        "workflows, policies, how-to, references). After filing each entry, MOVE its source "
        "file from knowledge/source/raw/ to knowledge/source/processed/. Skip files already "
        "in processed/.",
    ]
    if validate:
        steps.append(
            "3) Then use the aiws-validate-knowledge skill to validate the new entries and "
            "report pass/fail with any fixes."
        )
    if auto:
        steps.append("Do all of this now, end to end, without asking for confirmation.")
    return " ".join(steps)


def _detect_auth(tool: AiTool) -> tuple[bool, str]:
    """Best-effort check whether the tool is already authenticated.

    Returns (True, how) if we can positively confirm sign-in, else (False, "").
    We never return a false positive: an unconfirmed result is treated as "not
    authenticated" so the user is guided to sign in.
    """
    env_var = next((v for v in tool.auth_env_vars if os.environ.get(v)), None)
    if env_var:
        return True, f"${env_var}"

    # GitHub Copilot can also use the GitHub CLI's stored token.
    if tool.key == "copilot" and shutil.which("gh"):
        try:
            r = run_cli(["gh", "auth", "status"], capture_output=True, text=True)
            if r.returncode == 0:
                return True, "gh auth"
        except (OSError, FileNotFoundError):
            pass
    return False, ""


def ensure_authenticated(tool: AiTool, *, assume_yes: bool) -> bool:
    """Make sure the tool is signed in before we hand it the init prompt.

    Launching an unauthenticated CLI (e.g. ``copilot -p`` prints
    "No authentication information found" and exits). If sign-in can't be
    confirmed, we run the tool's login flow and wait for the user to complete it.

    Returns True if we should proceed to launch, False if the user aborted.
    """
    authed, how = _detect_auth(tool)
    if authed:
        ok(f"{tool.display_name} authentication detected ({how}).")
        return True

    if not shutil.which(tool.cli_command):
        # Can't log in to a CLI that isn't installed; caller handles the manual path.
        return True

    console.print()
    console.print(f"  [bold]Authentication[/bold]  {tool.display_name} needs you to be signed in")
    if tool.login_hint:
        info(tool.login_hint)

    # Non-interactive mode: we can't drive an interactive login, so warn and proceed.
    if assume_yes:
        warn("Non-interactive mode (-y): skipping sign-in.")
        info(f"If the tool isn't authenticated, sign in and re-run: aiws init --tool {tool.key}")
        return True

    do_login = Confirm.ask(
        f"    Sign in to {tool.display_name} now?", default=True, console=console
    )
    if not do_login:
        warn("Continuing without sign-in — the tool may report an authentication error.")
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

    # Re-check: if we can now confirm auth, say so; either way let the user continue.
    authed, how = _detect_auth(tool)
    if authed:
        ok(f"{tool.display_name} authentication detected ({how}).")
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

