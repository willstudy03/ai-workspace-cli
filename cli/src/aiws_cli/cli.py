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
from .agent_runner import build_ingest_prompt, ensure_authenticated, launch_agent
from .assets import AssetError, build_copy_plan, place_assets, resolve_asset_source
from .config import AiwsConfig, load_config, save_config
from .console import console, err, err_console, info, ok, step, warn
from .deps import detect_package_manager, ensure_markitdown, ensure_node, run_preflight
from .proc import run_cli
from .scaffold import scaffold_workspace
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
              help="Launch the AI tool headless (auto-approved) and run the init skill "
                   "to completion.")
@click.option("--scaffold/--no-scaffold", "scaffold", default=None,
              help="Create the full workspace folder tree directly in Python "
                   "(no agent, no per-action permission prompts).")
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
    scaffold: bool | None,
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

        # ── 6b. Native scaffold (deterministic, no agent, no permission prompts)
        if scaffold is None:
            scaffold = assume_yes or Confirm.ask(
                "    Create the full workspace structure now "
                "(directly, no agent or per-action confirmations)?",
                default=True,
                console=console,
            )
        if scaffold:
            step("Scaffolding", "workspace structure")
            for line in scaffold_workspace(target / tool.workspace_root, overwrite=overwrite):
                info(line)

    except AssetError as exc:
        err_console.print(f"Error: {exc}")
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        console.print("\n[yellow]init interrupted.[/yellow]")
        sys.exit(1)

    # ── 7. Summary ────────────────────────────────────────────────────────────
    _print_summary(tool, target, track_market, scaffolded=bool(scaffold))

    # ── 8. Launch the agent to run aiws-workspace-init ────────────────────────
    # --auto implies launching (headless) unless the user explicitly said --no-launch.
    if auto and do_launch is None:
        do_launch = True
    # Without the tool CLI ensured, don't offer to launch unless explicitly asked.
    if not check_tool_cli and do_launch is None and not auto:
        do_launch = False
    # If we already scaffolded natively, the agent isn't needed to build structure.
    if scaffold and do_launch is None and not auto:
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


@cli.command()
@click.option("--path", "target_str", default=".", help="Workspace directory (default: current).")
@click.option(
    "--tool",
    "tool_key",
    type=click.Choice(TOOL_ORDER, case_sensitive=False),
    default=None,
    help="AI tool to use (default: read from .aiws/config.toml, else prompt).",
)
@click.option("--auto", is_flag=True,
              help="Run headless (auto-approved) end-to-end without confirmations.")
@click.option(
    "--input", "--source", "inputs",
    multiple=True,
    type=click.Path(exists=True, dir_okay=True, file_okay=True),
    help="File(s) or folder(s) to copy into knowledge/source/raw/ before ingesting "
         "(repeatable).",
)
@click.option("--validate/--no-validate", "do_validate", default=True,
              help="Chain aiws-validate-knowledge after curation (default: on).")
@click.option("--tool-cli/--no-tool-cli", "check_tool_cli", default=True,
              help="Check for (and offer to install) the AI tool's CLI.")
@click.option("--no-markitdown", "install_markitdown", flag_value=False, default=True,
              help="Skip installing MarkItDown during preflight.")
@click.option("-y", "--yes", "assume_yes", is_flag=True, help="Accept defaults; no prompts.")
def ingest(
    target_str: str,
    tool_key: str | None,
    auto: bool,
    inputs: tuple[str, ...],
    do_validate: bool,
    check_tool_cli: bool,
    install_markitdown: bool,
    assume_yes: bool,
) -> None:
    """Run the knowledge-ingestion pipeline: raw-to-markdown -> create-knowledge.

    Converts everything in ``knowledge/source/raw/`` to Markdown and curates it into
    proper knowledge entries by launching your AI tool with a two-skill pipeline
    prompt (optionally validating afterwards).

    Pass ``--input <path>`` (repeatable; files or folders) to copy sources into
    ``knowledge/source/raw/`` first.
    """
    target = Path(target_str).expanduser().resolve()
    _print_header(target, "ingest")

    # ── Resolve the AI tool (flag > config > prompt) ──────────────────────────
    tool = _resolve_tool_for_ingest(tool_key, target, assume_yes)

    raw_dir = target / tool.workspace_root / "knowledge" / "source" / "raw"

    # ── Stage any provided inputs into source/raw/ ────────────────────────────
    if inputs:
        console.print()
        console.print("  [bold]Staging[/bold]  copying inputs into knowledge/source/raw/")
        raw_dir.mkdir(parents=True, exist_ok=True)
        _stage_inputs(inputs, raw_dir)

    # ── Preflight: MarkItDown, raw content, required skills ───────────────────
    console.print()
    console.print("  [bold]Preflight[/bold]  checking ingestion prerequisites")
    manager = detect_package_manager()
    ensure_markitdown(manager, auto_install=install_markitdown)

    if not raw_dir.is_dir():
        err(f"No knowledge/source/raw/ folder at {raw_dir}.")
        info(f"Run 'aiws init --tool {tool.key}' first, then add files to ingest.")
        sys.exit(1)

    raw_files = [
        p for p in raw_dir.iterdir() if p.is_file() and p.name.lower() != "readme.md"
    ]
    if not raw_files:
        warn(f"Nothing to ingest — {raw_dir} has no files (besides README).")
        info("Drop PDF/Word/PPT/Excel/Markdown/etc. into knowledge/source/raw/, then re-run.")
        sys.exit(0)
    ok(f"Found {len(raw_files)} file(s) to ingest in knowledge/source/raw/")

    skills_dir = target / tool.skills_dest
    missing = [
        s for s in ("aiws-raw-to-markdown", "aiws-create-knowledge")
        if not (skills_dir / s).is_dir()
    ]
    if do_validate and not (skills_dir / "aiws-validate-knowledge").is_dir():
        missing.append("aiws-validate-knowledge")
    if missing:
        err(f"Required skill(s) not installed in {skills_dir}: {', '.join(missing)}")
        info(f"Run 'aiws init --tool {tool.key}' to install the built-in skills first.")
        sys.exit(1)

    # ── Tool CLI + authentication ─────────────────────────────────────────────
    if check_tool_cli:
        _ensure_tool_cli(tool, assume_yes)

    # ── Plan + confirm ────────────────────────────────────────────────────────
    step("Plan", "knowledge ingestion")
    console.print(f"      Tool     : [bold]{tool.display_name}[/bold]")
    console.print(
        f"      Source   : {tool.workspace_root}/knowledge/source/raw/  "
        f"[dim]({len(raw_files)} file(s))[/dim]"
    )
    console.print("      Pipeline : aiws-raw-to-markdown → aiws-create-knowledge"
                  + (" → aiws-validate-knowledge" if do_validate else ""))
    console.print(f"      Mode     : {'headless (--auto)' if auto else 'interactive'}")
    console.print()
    if not assume_yes and not Confirm.ask("    Proceed?", default=True, console=console):
        console.print("  [yellow]Aborted.[/yellow]")
        return

    if check_tool_cli and not ensure_authenticated(tool, assume_yes=assume_yes):
        console.print("  [yellow]Ingestion skipped until authentication is complete.[/yellow]")
        return

    # ── Launch the agent with the pipeline prompt ─────────────────────────────
    console.print()
    prompt = build_ingest_prompt(validate=do_validate, auto=auto)
    launch_agent(tool, prompt=prompt, headless=auto)


# ── Wizard helpers ────────────────────────────────────────────────────────────


def _print_header(target: Path, action: str = "init") -> None:
    console.print()
    console.print(
        Panel(
            f"[bold]aiws[/bold] v{__version__}  ·  {action}\n[dim]{target}[/dim]",
            expand=False,
            border_style="blue",
            padding=(0, 4),
        )
    )


def _resolve_tool_for_ingest(tool_key: str | None, target: Path, assume_yes: bool) -> AiTool:
    """Resolve the AI tool for ingest: --tool flag > .aiws/config.toml > prompt."""
    if tool_key:
        tool = get_tool(tool_key)
        if tool:
            return tool
    cfg = load_config(target)
    if cfg and cfg.tool:
        tool = get_tool(cfg.tool)
        if tool:
            ok(f"Using tool from .aiws/config.toml: {tool.display_name}")
            return tool
    return _select_tool(None, assume_yes)


def _stage_inputs(inputs: tuple[str, ...], raw_dir: Path) -> int:
    """Copy each input file (or the files inside an input folder) into raw_dir.

    Non-destructive: existing same-named files are skipped. Returns the count staged.
    """
    staged = 0
    for item in inputs:
        src_path = Path(item).expanduser().resolve()
        if src_path.is_dir():
            files = sorted(p for p in src_path.iterdir() if p.is_file())
            if not files:
                warn(f"No files in folder: {src_path}")
        elif src_path.is_file():
            files = [src_path]
        else:
            warn(f"Skipping (not a file or folder): {src_path}")
            continue

        for src in files:
            dest = raw_dir / src.name
            if dest.exists():
                warn(f"Already in source/raw: {src.name} (skipped)")
                continue
            try:
                shutil.copy2(src, dest)
            except OSError as exc:
                warn(f"Could not copy {src.name}: {exc}")
                continue
            ok(f"Staged {src.name}")
            staged += 1

    if staged:
        ok(f"Staged {staged} file(s) into knowledge/source/raw/")
    else:
        warn("No new files staged.")
    return staged


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


def _print_summary(tool: AiTool, target: Path, track_market: bool, *, scaffolded: bool) -> None:
    next_line = (
        "  Next: your workspace structure is ready — add your own agents, skills & knowledge."
        if scaffolded
        else "  Next: open your AI tool here and ask it to run [bold]aiws-workspace-init[/bold]."
    )
    lines = [
        "[green]✓[/green]  Workspace initialised\n",
        f"  Tool     : [bold]{tool.display_name}[/bold]",
        f"  Target   : {target}",
        f"  Skills   : {tool.skills_dest}/  [dim](10 built-in aiws-* skills)[/dim]",
        f"  Config   : .aiws/config.toml  "
        f"[dim](track_market={'on' if track_market else 'off'})[/dim]",
    ]
    if scaffolded:
        lines.append(
            f"  Structure: {tool.workspace_root}/  "
            "[dim](agents, codebases, docs, knowledge, references, scripts)[/dim]"
        )
    lines += ["", next_line]
    console.print()
    console.print(Panel("\n".join(lines), border_style="green", expand=False, padding=(0, 2)))


if __name__ == "__main__":
    cli()

