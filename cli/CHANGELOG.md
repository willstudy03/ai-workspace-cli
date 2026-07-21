# Changelog

All notable changes to the `aiws` CLI are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and this project adheres to
[Semantic Versioning](https://semver.org/).

## [0.3.1] — 2026-07-21

### Fixed
- Windows: launching an npm `.cmd`/`.bat` shim (claude/copilot/codex/npm) failed with
  `'C:\Users\<name>' is not recognized …` when the path or an argument contained a
  space (e.g. a `C:\Users\End User\…` profile). `run_cli` now invokes shims via
  `cmd /s /c "<command>"` with proper quoting so spaces are preserved.

## [0.3.0] — 2026-07-21

### Added
- **`aiws ingest`** — knowledge-ingestion pipeline that runs `aiws-raw-to-markdown`
  then `aiws-create-knowledge` (and `aiws-validate-knowledge` unless `--no-validate`)
  by launching the AI tool with a chained prompt.
  - `--input` / `--source` (repeatable) stages file(s) or folder(s) into
    `knowledge/source/raw/` before ingesting (non-destructive; skips existing).
  - `--auto` runs headless/hands-free.
- **`--scaffold`** on `aiws init` — builds the full workspace tree natively in Python
  (no agent, no per-action permission prompts); additive and idempotent.
- **`--no-tool-cli`** — pure-Python, npm-free run of `aiws init`.
- **First-time authentication gate** — detects sign-in (token env vars or
  `gh auth status` for Copilot) and runs the tool's login flow before launching.
- **Node.js/npm auto-install** during preflight when missing (winget/choco/brew/apt/
  dnf/yum/pacman/zypper), so a missing tool CLI can be installed end-to-end.
- **PATH auto-configuration** in `install.py` (uv `update-shell`, user PATH on
  Windows, shell rc on POSIX).
- **Offline bundle** — built-in assets shipped inside the package so `aiws` works with
  no checkout or network; per-tool fallback if a source folder is missing.
- Release tooling: `scripts/release.sh` (build + verify bundle-in-wheel + publish) and
  `scripts/sync_bundle.sh`.

### Changed
- **`aiws init` launches the agent by default** to run `aiws-workspace-init`;
  `--scaffold` is an explicit opt-in that builds the tree natively in Python (no
  agent). Previously native scaffolding was offered by default.
- **Headless is the default** launch mode for both `aiws init` and `aiws ingest`
  (`--auto` is the default; pass `--interactive` to approve actions per-step).
- **Knowledge staging restructured**: `knowledge/raw/` → `knowledge/source/` with
  `source/raw/` (incoming) and `source/processed/` (curated). `aiws-create-knowledge`
  now **moves** processed sources to `source/processed/` instead of deleting them.
- `aiws-raw-to-markdown` writes converted Markdown **directly into `source/raw/`**
  (removed the `source/raw/converted/` subfolder that curation didn't read).
- Copilot launch fixed: interactive uses `copilot -i`; headless uses
  `copilot -p --allow-all-tools --allow-all-paths` (previously failed with
  "No authentication information found" / permission-denied).
- Cross-platform process launching via `run_cli` (handles Windows `.cmd`/`.bat`
  shims); UTF-8 console safety.

### Notes
- No default upstream repo — skill-market tracking is blank unless provided.

## [0.1.0] — 2026-07-20

### Added
- Initial `aiws init` command: preflight, tool selection, skill-market tracking,
  places instruction file + built-in `aiws-*` skills, optional agent launch.

