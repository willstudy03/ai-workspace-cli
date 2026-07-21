"""Locate the built-in workspace assets and place them into a target directory.

The "assets" are the tool-native instruction file (e.g. ``CLAUDE.md``) and the
built-in ``aiws-*`` skills folder. They are sourced, in priority order, from:

1. ``$AIWS_SOURCE_ROOT`` — an explicit override (a repo checkout).
2. A detected ai-workspace checkout (walking up from the CWD and the installed
   package location, looking for the three instruction files).
3. A shallow ``git clone`` of the upstream repo into a local cache — this is what
   makes "track the skill market" work when aiws is installed globally.
4. The **bundle** shipped inside the ``aiws_cli`` package — a guaranteed offline
   fallback so ``aiws init`` works standalone anywhere, with no checkout or clone.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .console import info, ok, warn
from .tools import AiTool

# Markers that identify a valid ai-workspace source root (a repo checkout).
SOURCE_MARKERS = ("CLAUDE.md", "AGENTS.md", ".github/copilot-instructions.md")

CACHE_DIR = Path.home() / ".aiws" / "cache" / "ai-workspace"

# Assets bundled inside the installed package: bundle/<tool-key>/<files>.
BUNDLE_DIR = Path(__file__).resolve().parent / "bundle"


class AssetError(Exception):
    """Raised when built-in workspace assets cannot be located or copied."""


@dataclass
class AssetSource:
    """A resolved place to copy built-in assets from.

    ``kind`` is ``"repo"`` (mirror of the repository layout) or ``"bundle"``
    (packaged layout ``bundle/<tool-key>/{<instruction>,skills/}``).
    """

    kind: str
    base: Path


@dataclass
class CopyPlan:
    instruction: tuple[Path, Path]  # (src, dest)
    skills: tuple[Path, Path]  # (src_dir, dest_dir)


# ── Source resolution ─────────────────────────────────────────────────────────


def _is_source_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in SOURCE_MARKERS)


def _walk_up_for_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if _is_source_root(candidate):
            return candidate
    return None


def _bundle_available() -> bool:
    return BUNDLE_DIR.is_dir() and any(BUNDLE_DIR.iterdir())


def resolve_asset_source(
    *, upstream_repo: str | None, upstream_ref: str, allow_clone: bool
) -> AssetSource:
    """Resolve where to copy built-in assets from. Never fails if the bundle exists."""
    env_root = os.environ.get("AIWS_SOURCE_ROOT")
    if env_root:
        root = Path(env_root).expanduser().resolve()
        if _is_source_root(root):
            ok(f"Using AIWS_SOURCE_ROOT: {root}")
            return AssetSource("repo", root)
        warn(f"AIWS_SOURCE_ROOT set but not a valid workspace root: {root}")

    # Detect a local checkout (developer / cloned-repo scenario).
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        found = _walk_up_for_root(start)
        if found:
            ok(f"Using local workspace source: {found}")
            return AssetSource("repo", found)

    # Fetch the upstream repo if the user asked to track it and gave a URL.
    if allow_clone and upstream_repo:
        try:
            return AssetSource("repo", _clone_or_update_cache(upstream_repo, upstream_ref))
        except AssetError as exc:
            warn(f"{exc}")
            info("Falling back to the assets bundled with aiws.")

    # Guaranteed offline fallback: the packaged bundle.
    if _bundle_available():
        ok("Using built-in assets bundled with aiws")
        return AssetSource("bundle", BUNDLE_DIR)

    raise AssetError(
        "Could not locate built-in workspace assets and no bundle is packaged. "
        "Run inside an ai-workspace checkout, set AIWS_SOURCE_ROOT, or provide a "
        "reachable upstream repository."
    )


def _clone_or_update_cache(upstream_repo: str, ref: str) -> Path:
    if not shutil.which("git"):
        raise AssetError("git is required to fetch upstream assets but was not found on PATH.")

    if (CACHE_DIR / ".git").exists():
        info(f"Updating cached workspace from {upstream_repo} ...")
        subprocess.run(["git", "fetch", "--depth", "1", "origin", ref], cwd=CACHE_DIR)
        subprocess.run(["git", "checkout", ref], cwd=CACHE_DIR)
        subprocess.run(["git", "reset", "--hard", f"origin/{ref}"], cwd=CACHE_DIR)
    else:
        CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        info(f"Cloning workspace assets from {upstream_repo} (ref: {ref}) ...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", ref, upstream_repo, str(CACHE_DIR)],
        )
        if result.returncode != 0:
            raise AssetError(f"git clone of {upstream_repo} failed.")

    if not _is_source_root(CACHE_DIR):
        raise AssetError(
            f"Cloned repo at {CACHE_DIR} does not contain the expected workspace assets."
        )
    ok(f"Fetched workspace assets into {CACHE_DIR}")
    return CACHE_DIR


# ── Copy planning & execution ─────────────────────────────────────────────────


def _tool_paths(source: AssetSource, tool: AiTool) -> tuple[Path, Path]:
    """Return (instruction_src, skills_src) for a tool within a given source."""
    if source.kind == "bundle":
        return (
            source.base / tool.key / tool.instruction_filename,
            source.base / tool.key / "skills",
        )
    return source.base / tool.instruction_src, source.base / tool.skills_src


def build_copy_plan(source: AssetSource, tool: AiTool, target: Path) -> CopyPlan:
    inst_src, skills_src = _tool_paths(source, tool)

    # If a repo source is missing this tool's assets (e.g. its .claude/ folder was
    # deleted), fall back to the packaged bundle so init still works.
    if (
        not (inst_src.exists() and skills_src.is_dir())
        and source.kind != "bundle"
        and _bundle_available()
    ):
        warn(f"Source is missing assets for {tool.display_name}; using the bundled copy.")
        inst_src, skills_src = _tool_paths(AssetSource("bundle", BUNDLE_DIR), tool)

    if not inst_src.exists():
        raise AssetError(f"Instruction file missing in source: {inst_src}")
    if not skills_src.is_dir():
        raise AssetError(f"Skills folder missing in source: {skills_src}")
    return CopyPlan(
        instruction=(inst_src, target / tool.instruction_dest),
        skills=(skills_src, target / tool.skills_dest),
    )


def place_assets(plan: CopyPlan, *, overwrite: bool) -> list[str]:
    """Copy the planned assets into the target. Returns human-readable results."""
    results: list[str] = []

    inst_src, inst_dest = plan.instruction
    inst_dest.parent.mkdir(parents=True, exist_ok=True)
    if inst_dest.exists() and not overwrite:
        results.append(f"↷ skipped {inst_dest.name} (already exists)")
    else:
        shutil.copy2(inst_src, inst_dest)
        results.append(f"✓ {inst_dest}")

    skills_src, skills_dest = plan.skills
    skills_dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    for skill_dir in sorted(p for p in skills_src.iterdir() if p.is_dir()):
        dest_dir = skills_dest / skill_dir.name
        if dest_dir.exists() and not overwrite:
            results.append(f"↷ skipped skills/{skill_dir.name}/ (already exists)")
            continue
        shutil.copytree(skill_dir, dest_dir, dirs_exist_ok=True)
        copied += 1
    results.append(f"✓ {copied} built-in skill(s) → {skills_dest}")
    return results

