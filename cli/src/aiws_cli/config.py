"""Per-workspace aiws configuration, stored at ``<workspace>/.aiws/config.toml``.

This records which AI tool the workspace was initialised for, whether the skill
market (upstream repo) should be tracked, and where to fetch built-in skills from
so ``aiws-install-skill`` can pull updates later.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIRNAME = ".aiws"
CONFIG_FILENAME = "config.toml"


@dataclass
class AiwsConfig:
    tool: str | None = None
    track_skill_market: bool = True
    upstream_repo: str | None = None
    upstream_ref: str = "master"
    initialized_at: str | None = None

    def stamp_now(self) -> None:
        self.initialized_at = datetime.now(timezone.utc).isoformat(timespec="seconds")


def config_path(workspace: Path) -> Path:
    return workspace / CONFIG_DIRNAME / CONFIG_FILENAME


def load_config(workspace: Path) -> AiwsConfig | None:
    """Load the workspace config. Returns None if missing or malformed."""
    path = config_path(workspace)
    if not path.exists():
        return None
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return AiwsConfig(
            tool=data.get("tool"),
            track_skill_market=bool(data.get("track_skill_market", True)),
            upstream_repo=data.get("upstream_repo"),
            upstream_ref=data.get("upstream_ref", "master"),
            initialized_at=data.get("initialized_at"),
        )
    except Exception:
        return None


def save_config(workspace: Path, cfg: AiwsConfig) -> Path:
    """Write the workspace config to disk, creating ``.aiws/`` if needed."""
    path = config_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    if cfg.tool is not None:
        lines.append(f"tool = {_toml_str(cfg.tool)}")
    lines.append(f"track_skill_market = {'true' if cfg.track_skill_market else 'false'}")
    if cfg.upstream_repo is not None:
        lines.append(f"upstream_repo = {_toml_str(cfg.upstream_repo)}")
    lines.append(f"upstream_ref = {_toml_str(cfg.upstream_ref)}")
    if cfg.initialized_at is not None:
        lines.append(f"initialized_at = {_toml_str(cfg.initialized_at)}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _toml_str(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'

