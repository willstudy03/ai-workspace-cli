"""aiws CLI — bootstrap an AI-agent workspace.

Commands:
  init  — preflight deps, place built-in skills for a chosen AI tool, and launch it.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from . import __version__
from .agent_runner import ensure_authenticated, launch_agent
from .assets import AssetError, build_copy_plan, place_assets, resolve_asset_source
from .config import AiwsConfig, save_config
from .console import console, err_console, info, ok, step, warn
from .deps import ensure_node, run_preflight
from .proc import run_cli
from .tools import TOOL_ORDER, TOOLS, AiTool, get_tool

# Upstream repo used when "track the skill market" is enabled and no local checkout
# is available. There is no built-in default — it must be provided explicitly via
# --upstream or the AIWS_UPSTREAM_REPO env var, otherwise it is left blank.
DEFAULT_UPSTREAM_REF = "master"


@click.group()
@click.version_option(__version__, prog_name="aiws")
def cli() -> None:
    """aiws — bootstrap an AI-agent workspace (skills + knowledge) for your AI tool."""


@cli.command()
@click.option("--path", "target_str", default=".", help="Workspace directory (default: current).")
@click.option(
    "--tool",
    "tool_key",
    type=click.Choice(TOOL_ORDER, case_sensitive=False),
    default=None,
    help="Preselect the AI tool (skips the prompt).",
)
@click.option(
    "--track/--no-track",
    "track_market",
    default=None,
    help="Track the upstream skill market so install-skill can fetch updates.",
)
@click.option("--upstream", "upstream_repo", default=None, help="Upstream repo URL to track.")
@click.option("--ref", "upstream_ref", default=DEFAULT_UPSTREAM_REF, help="Upstream branch/tag.")
@click.option("--overwrite", is_flag=True, help="Overwrite existing instruction/skill files.")
@click.option("--no-markitdown", "install_markitdown", flag_value=False, default=True,
              help="Skip installing MarkItDown during preflight.")
@click.option("--no-git", "install_git", flag_value=False, default=True,
              help="Skip installing git during preflight.")
@click.option("--tool-cli/--no-tool-cli", "check_tool_cli", default=True,
              help="Check for (and offer to install via npm) the AI tool's CLI. "
                   "Use --no-tool-cli for a pure-Python, npm-free run.")
@click.option("--launch/--no-launch", "do_launch", default=None,
              help="Launch the AI tool to run aiws-workspace-init when done.")
@click.option("--auto", is_flag=True,
              help="Launch the AI tool headless (auto-approved) and run the init skill to completion.")
@click.option("-y", "--yes", "assume_yes", is_flag=True, help="Accept defaults; no prompts.")
def init(
    target_str: str,
    tool_key: str | None,
    track_market: bool | None,
    upstream_repo: str | None,
    upstream_ref: str,
    overwrite: bool,
    install_markitdown: bool,
    install_git: bool,
    check_tool_cli: bool,
    do_launch: bool | None,
    auto: bool,
    assume_yes: bool,
) -> None:
    """Set up an AI-agent workspace in the current (or given) directory."""
    import os

    target = Path(target_str).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    _print_header(target)

    # ── 1. Preflight: dependencies + MarkItDown ───────────────────────────────
    console.print()
    console.print("  [bold]Preflight[/bold]  installing dependencies")
    run_preflight(install_markitdown=install_markitdown, install_git=install_git)

    try:
        # ── 2. Choose the AI tool ─────────────────────────────────────────────
        tool = _select_tool(tool_key, assume_yes)
        if check_tool_cli:
            _ensure_tool_cli(tool, assume_yes)
        else:
            info("Skipping AI tool CLI check (--no-tool-cli); no npm/Node required.")

        # ── 3. Skill-market tracking ──────────────────────────────────────────
        if track_market is None:
            track_market = assume_yes or Confirm.ask(
                "    Track the skill market (fetch built-in skill updates from upstream)?",
                default=True,
                console=console,
            )
        resolved_upstream = upstream_repo or os.environ.get("AIWS_UPSTREAM_REPO") or None
        if track_market and not assume_yes and upstream_repo is None:
            entered = Prompt.ask(
                "    Upstream repo URL [dim](leave blank to skip)[/dim]",
                default=resolved_upstream or "",
                console=console,
            ).strip()
            resolved_upstream = entered or resolved_upstream

        # ── 4. Confirm the plan ───────────────────────────────────────────────
        if not _confirm_plan(tool, target, track_market, resolved_upstream, assume_yes):
            console.print("  [yellow]Aborted.[/yellow]")
            return

        # ── 5. Resolve source & place built-in skills ─────────────────────────
        step("Placing", "built-in skills & instructions")
        source = resolve_asset_source(
            upstream_repo=resolved_upstream,
            upstream_ref=upstream_ref,
            allow_clone=bool(track_market),
        )
        plan = build_copy_plan(source, tool, target)
        for line in place_assets(plan, overwrite=overwrite):
            info(line)

        # ── 6. Persist workspace config ───────────────────────────────────────
        cfg = AiwsConfig(
            tool=tool.key,
            track_skill_market=bool(track_market),
            upstream_repo=resolved_upstream,
            upstream_ref=upstream_ref,
        )
        cfg.stamp_now()
        cfg_path = save_config(target, cfg)
        ok(f"Wrote {cfg_path.relative_to(target)}")

    except AssetError as exc:
        err_console.print(f"Error: {exc}")
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]init interrupted.[/yellow]")
        sys.exit(1)

    # ── 7. Summary ────────────────────────────────────────────────────────────
    _print_summary(tool, target, track_market)

    # ── 8. Launch the agent to run aiws-workspace-init ────────────────────────
    # --auto implies launching (headless) unless the user explicitly said --no-launch.
    if auto and do_launch is None:
        do_launch = True
    # Without the tool CLI ensured, don't offer to launch unless explicitly asked.
    if not check_tool_cli and do_launch is None and not auto:
        do_launch = False
    if do_launch is None:
        do_launch = assume_yes or Confirm.ask(
            f"    Launch {tool.display_name} now to run aiws-workspace-init?",
            default=True,
            console=console,
        )
    if do_launch:
        # Ensure the tool is authenticated before launching — an unauthenticated
        # CLI (e.g. `copilot -p`) errors out with "No authentication information
        # found" instead of running the init skill. Fires for every launch; a
        # confirmed sign-in (token/gh) short-circuits without prompting.
        if check_tool_cli:
            if not ensure_authenticated(tool, assume_yes=assume_yes):
                console.print("  [yellow]Launch skipped until authentication is complete.[/yellow]")
                do_launch = False
    if do_launch:
        console.print()
        launch_agent(tool, headless=auto)


# ── Wizard helpers ────────────────────────────────────────────────────────────


def _print_header(target: Path) -> None:
    console.print()
    console.print(
        Panel(
            f"[bold]aiws[/bold] v{__version__}  ·  init\n[dim]{target}[/dim]",
            expand=False,
            border_style="blue",
            padding=(0, 4),
        )
    )


def _select_tool(tool_key: str | None, assume_yes: bool) -> AiTool:
    if tool_key:
        tool = get_tool(tool_key)
        if tool:
            return tool

    step("Step 1", "Which AI tool are you using?")
    for i, key in enumerate(TOOL_ORDER, 1):
        t = TOOLS[key]
        console.print(f"      {i}. {t.display_name:<16} [dim]({t.cli_command})[/dim]")
    console.print()

    if assume_yes:
        return TOOLS[TOOL_ORDER[0]]

    raw = Prompt.ask("    Select (number or name)", default="1", console=console).strip().lower()
    if raw.isdigit() and 1 <= int(raw) <= len(TOOL_ORDER):
        return TOOLS[TOOL_ORDER[int(raw) - 1]]
    tool = get_tool(raw)
    if tool:
        return tool
    warn(f"Unknown '{raw}', defaulting to {TOOLS[TOOL_ORDER[0]].display_name}.")
    return TOOLS[TOOL_ORDER[0]]


def _ensure_tool_cli(tool: AiTool, assume_yes: bool) -> bool:
    """Verify the tool CLI is on PATH; offer to install it (and Node/npm) if missing.

    Returns True if the CLI was *newly installed* during this call (so the caller
    knows the user likely still needs to authenticate).
    """
    if shutil.which(tool.cli_command):
        ok(f"{tool.display_name} CLI found ('{tool.cli_command}')")
        return False

    warn(f"{tool.display_name} CLI ('{tool.cli_command}') is not installed.")
    info(f"Install command: {tool.install_hint}")

    npm = shutil.which("npm")
    if not npm:
        # npm is required to install the tool CLI — offer to install Node.js first.
        warn("npm not found — it is required to install the tool CLI.")
        install_node = assume_yes or Confirm.ask(
            "    Install Node.js (includes npm) now?", default=True, console=console
        )
        if install_node and ensure_node(auto_install=True):
            npm = shutil.which("npm")
        if not npm:
            warn("Skipping tool CLI install — install Node.js/npm, then re-run aiws init.")
            return False

    do_install = assume_yes or Confirm.ask(
        f"    Install {tool.display_name} now with npm?", default=True, console=console
    )
    if not do_install:
        return False

    info(f"Running: {tool.install_hint}")
    try:
        result = run_cli(tool.install_hint.split())
    except OSError as exc:
        warn(f"Could not run the installer ({exc}). Install manually: {tool.install_hint}")
        return False
    if result.returncode == 0 and shutil.which(tool.cli_command):
        ok(f"{tool.display_name} installed.")
        return True
    warn(f"Could not install {tool.display_name} automatically — install it manually later.")
    return False


def _confirm_plan(
    tool: AiTool,
    target: Path,
    track_market: bool,
    upstream: str | None,
    assume_yes: bool,
) -> bool:
    step("Plan", "review before applying")
    console.print(f"      Tool         : [bold]{tool.display_name}[/bold]")
    console.print(f"      Target       : {target}")
    console.print(f"      Instructions : {tool.instruction_dest}")
    console.print(f"      Skills       : {tool.skills_dest}/")
    console.print(f"      Track market : {'yes' if track_market else 'no'}")
    if track_market:
        console.print(f"      Upstream     : {upstream or '[dim]not set[/dim]'}")
    console.print()
    if assume_yes:
        return True
    return Confirm.ask("    Proceed?", default=True, console=console)


def _print_summary(tool: AiTool, target: Path, track_market: bool) -> None:
    lines = [
        "[green]✓[/green]  Workspace initialised\n",
        f"  Tool     : [bold]{tool.display_name}[/bold]",
        f"  Target   : {target}",
        f"  Skills   : {tool.skills_dest}/  [dim](10 built-in aiws-* skills)[/dim]",
        f"  Config   : .aiws/config.toml  [dim](track_market={'on' if track_market else 'off'})[/dim]",
        "",
        "  Next: open your AI tool here and ask it to run [bold]aiws-workspace-init[/bold].",
    ]
    console.print()
    console.print(Panel("\n".join(lines), border_style="green", expand=False, padding=(0, 2)))


if __name__ == "__main__":
    cli()

