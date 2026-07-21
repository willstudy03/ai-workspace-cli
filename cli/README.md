# aiws CLI

`aiws` bootstraps a portable **AI-agent workspace** — the built-in `aiws-*` skills
and governance instructions — for **Claude Code**, **GitHub Copilot**, or
**OpenAI Codex**, in whatever directory you run it.

**Platform support:** Windows, macOS, and Linux. `aiws` is a pure-Python package
(`py3-none-any` wheel, dependencies `click` + `rich`) with per-OS handling for the
optional dependency installers:

| Step | Windows | macOS | Linux |
|------|---------|-------|-------|
| Install git | winget / choco | Homebrew / Xcode CLT | apt / dnf / yum / pacman / zypper |
| Install Node.js (npm) | winget / choco | Homebrew | apt / dnf / yum / pacman / zypper |
| Launch tool CLIs | `.cmd` shims via `cmd /c` | direct exec | direct exec |

## Install

**From PyPI (recommended for users):**

```bash
pip install aiws-cli        # or: uv tool install aiws-cli
```

This installs the `aiws` command with the built-in skills bundled inside the
package — no repo checkout or network access is needed to run `aiws init`.

**From source (this repo):**

```bash
cd cli
python install.py        # auto-detects uv, falls back to pip
```

`install.py` installs the `aiws` command, **configures your PATH automatically** if
the command isn't already discoverable (via `uv tool update-shell`, or by adding the
executable directory to your user PATH on Windows / your shell rc on macOS/Linux),
and verifies it works. If PATH was just updated, open a **new terminal** so the
change takes effect.

## `aiws init`

Run it inside the project you want to set up:

```bash
aiws init
```

What it does, in order:

1. **Preflight** — checks Python (3.11+) and your package manager (uv/pip), and
   installs **git** and **MarkItDown** (`markitdown[all]`). git is needed to fetch
   skill updates from an upstream repo; MarkItDown is used by the
   `aiws-raw-to-markdown` skill.
2. **Choose your AI tool** — Claude Code, GitHub Copilot, or OpenAI Codex. If that
   tool's CLI isn't installed, `aiws` offers to install it (via `npm`). If `npm`
   itself is missing, `aiws` first offers to install **Node.js LTS** (which includes
   npm) using your OS package manager (winget/choco on Windows, Homebrew on macOS,
   apt/dnf/yum/pacman/zypper on Linux), then installs the tool CLI.
3. **Track the skill market** — optionally records an upstream repo so
   `aiws-install-skill` can fetch built-in skill updates later. There is **no
   default upstream** — if you don't provide one it is left blank, and skill syncing
   is simply skipped until you set it.
4. **Place built-in skills** — copies the tool-native instruction file and the ten
   `aiws-*` skills into the target directory:

   | Tool           | Instruction file                  | Skills folder     |
   |----------------|-----------------------------------|-------------------|
   | Claude Code    | `CLAUDE.md`                       | `.claude/skills/` |
   | GitHub Copilot | `.github/copilot-instructions.md` | `.github/skills/` |
   | OpenAI Codex   | `AGENTS.md`                       | `.codex/skills/`  |

5. **Launch the agent (default)** — opens your AI tool and asks it to run the
   `aiws-workspace-init` skill to build the workspace. This is the default; pass
   `--scaffold` instead to build the tree natively in Python with **no agent**
   (see below). By default the launch is **headless with auto-approval**; pass
   `--interactive` to approve actions yourself:

   | Tool           | Headless (default)                                         | Interactive (`--interactive`) |
   |----------------|------------------------------------------------------------|-------------------------------|
   | Claude Code    | `claude -p "<prompt>" --permission-mode acceptEdits`       | `claude "<prompt>"`           |
   | GitHub Copilot | `copilot -p "<prompt>" --allow-all-tools --allow-all-paths`| `copilot -i "<prompt>"`       |
   | OpenAI Codex   | `codex exec --full-auto "<prompt>"`                        | `codex "<prompt>"`            |

   **First-time sign-in:** launching an unauthenticated CLI fails — e.g.
   `copilot -p` prints *"No authentication information found"* and exits instead of
   running the skill. So before launching, `aiws` runs an **authentication gate**:
   it checks whether you're signed in (an auth token env var
   `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` / `GITHUB_TOKEN` / `ANTHROPIC_API_KEY` /
   `OPENAI_API_KEY`, or a working `gh auth status` for Copilot). If sign-in can't be
   confirmed, it opens the tool's login flow, waits for you to finish, then continues
   to run `aiws-workspace-init`.

   | Tool           | Sign-in step                                                            |
   |----------------|-------------------------------------------------------------------------|
   | Claude Code    | opens `claude`; complete the browser OAuth, then `/exit` to continue    |
   | GitHub Copilot | opens `copilot`; run `/login` (or `gh auth login`), then `/exit`        |
   | OpenAI Codex   | runs `codex login` (ChatGPT account or API key)                         |

   In non-interactive mode (`-y`) the gate can't drive a login, so it warns and
   proceeds; authenticate first (or set a token env var) for unattended runs.

Your choices are saved to `<workspace>/.aiws/config.toml`.

### Direct scaffolding (no agent, no permission prompts)

By default `aiws init` launches the AI agent to run `aiws-workspace-init`. As an
alternative, `--scaffold` builds the **entire workspace folder tree itself in
Python** — instantly, deterministically, and with no agent or per-action
confirmations:

```bash
aiws init --scaffold        # build the structure natively, no agent launch
```

This creates the full tree under the tool's workspace root (`.github/`, `.claude/`,
or `.codex/`) and seeds every folder with a standards-compliant `example-*` file
(agents, skills, references, knowledge/{concepts,systems,workflows,policies,how-to,
references, source/raw, source/processed}, codebases, docs, scripts). It's **additive
and idempotent** — existing files are skipped (use `--overwrite` to replace). When
`--scaffold` is used the agent is not launched (the structure already exists). The
generated files match the `aiws-workspace-init` skill and pass `aiws-validate-skill`
/ `aiws-validate-knowledge`.

### Using aiws without npm (pure Python)

`aiws` itself is a pure-Python package (installed via pip/uv) — **npm/Node is never
required to run it or to scaffold a workspace**. The instruction file, the ten
`aiws-*` skills, and `config.toml` are all placed by Python alone.

npm is only used for the optional convenience of installing/launching a vendor AI
CLI (`claude`, `copilot`, `codex`) — those CLIs are published on npm by their vendors
and are **not** available on PyPI, so they can't be installed with pip. If you'd
rather avoid npm entirely, run:

```bash
aiws init --no-tool-cli --no-launch
```

This does the full workspace setup with Python only. You can then use your AI tool
however you already have it — for example its **IDE extension**, or a CLI you
installed through a non-npm channel (Homebrew, a vendor install script, or a
prebuilt binary). Point that tool at the project and ask it to run
`aiws-workspace-init`.

### Useful flags

```bash
aiws init --tool copilot          # preselect the AI tool
aiws init --path ./my-project     # target a different directory
aiws init --upstream <git-url>    # track a specific upstream repo (blank by default)
aiws init --ref <branch>          # dedicated branch to pull skill updates from
aiws init --no-track              # don't track an upstream skill market
aiws init --no-launch             # set up files but don't open the AI tool
aiws init --scaffold              # build the full workspace tree directly (no agent)
aiws init --no-tool-cli           # pure-Python run: don't check/install the tool CLI (no npm)
aiws init --auto                  # headless launch (default) — run init to completion
aiws init --interactive           # launch the tool interactively (approve actions)
aiws init --no-git                # skip installing git during preflight
aiws init --no-markitdown         # skip installing MarkItDown during preflight
aiws init --overwrite             # overwrite existing instruction/skill files
aiws init -y                      # accept all defaults, no prompts
```

### Where assets come from

`aiws init` locates the built-in workspace content in this order:

1. `$AIWS_SOURCE_ROOT` — explicit override (a repo checkout).
2. A local ai-workspace checkout (auto-detected).
3. A shallow `git clone` of the tracked upstream repo (cached under
   `~/.aiws/cache/`) — what "track the skill market" enables.
4. **The bundle shipped inside the package** — a guaranteed offline fallback, so
   `aiws init` works standalone in any project with no checkout or network.

### Refreshing the bundled assets

The offline bundle lives at `src/aiws_cli/bundle/<tool>/` and is generated from the
repository's canonical tool folders. Regenerate it whenever the built-in skills or
instruction files change (and before publishing a release):

```bash
bash cli/scripts/sync_bundle.sh
```

## `aiws ingest` — knowledge ingestion pipeline

Once a workspace is set up, drop source files (PDF, Word, PowerPoint, Excel,
Markdown, images, HTML, …) into `<root>/knowledge/source/raw/` and run:

```bash
aiws ingest
```

Or point `aiws ingest` straight at a file or folder and it stages them into
`knowledge/source/raw/` for you first (repeatable; `--source` is an alias):

```bash
aiws ingest --input ./report.pdf
aiws ingest --input ./a.docx --input ./b.xlsx
aiws ingest --source ./docs-to-ingest/     # copies the folder's files in
```

This launches your AI tool and runs the **knowledge ingestion pipeline** as a
two-skill chain (optionally validating afterwards):

1. **`aiws-raw-to-markdown`** — converts every non-Markdown file in `knowledge/source/raw/`
   to Markdown (using MarkItDown).
2. **`aiws-create-knowledge`** — curates each Markdown file into a standards-compliant
   knowledge entry, one at a time, filed into the correct taxonomy folder, then moves
   the original source from `source/raw/` into `source/processed/`.
3. **`aiws-validate-knowledge`** *(unless `--no-validate`)* — validates the new
   entries and reports pass/fail.

Before launching, `aiws ingest` preflights: ensures **MarkItDown** is installed,
confirms `knowledge/source/raw/` exists and has files to process, and checks the required
skills are installed. The AI tool is resolved from `--tool`, else `.aiws/config.toml`,
else a prompt.

```bash
aiws ingest                       # headless, hands-free (default)
aiws ingest --input ./report.pdf  # stage a file into source/raw/, then ingest
aiws ingest --interactive         # approve each step yourself
aiws ingest --no-validate         # skip the validate-knowledge step
aiws ingest --tool claude -y      # preselect tool, accept defaults
```

> Note: curation is performed by the AI agent (it classifies and rewrites each
> file), so results depend on the model — unlike `--scaffold`, it isn't
> deterministic. The chained `aiws-validate-knowledge` step is the automated quality
> gate. Ingestion is additive; source files are moved to `source/processed/` (never deleted).

## Development

Run the test suite and linter from the `cli/` directory:

```bash
pip install pytest ruff          # or: uv sync
python -m pytest -q               # unit tests (tests/)
ruff check src tests             # lint
```

CI (`.gitlab-ci.yml`) runs lint + tests, a **bundle-drift check** (fails if the
committed bundle is out of sync with the canonical skills — run
`bash cli/scripts/sync_bundle.sh` and commit), and `release.sh` to build and verify
the wheel. Tagging `vX.Y.Z` enables a manual publish job.

## Releasing / Publishing to PyPI

End users install `aiws` from PyPI (`pip install aiws-cli`). The published **wheel
ships the offline bundle**, so the dot folders (`.claude/`, `.codex/`, `.github/`)
in this repo are never distributed — they are only the maintainer's source of truth
for regenerating the bundle.

Use the release script, which regenerates the bundle, builds the wheel + sdist,
**verifies the bundle is actually inside the wheel**, and optionally uploads:

```bash
# Build + verify only (artifacts land in cli/dist/):
bash cli/scripts/release.sh

# Build, verify, then upload to TestPyPI (dry run of the real thing):
bash cli/scripts/release.sh --publish-test

# Build, verify, then upload to PyPI:
bash cli/scripts/release.sh --publish
```

Requirements: `pip install build twine` (the script auto-detects `python3`/`python`/`py`).

Typical release checklist:

1. Bump `version` in `pyproject.toml`.
2. Ensure the built-in skills/instructions are final (they drive the bundle).
3. `bash cli/scripts/release.sh --publish-test` → install from TestPyPI and smoke-test.
4. `bash cli/scripts/release.sh --publish` → live on PyPI.
5. Tag the release in git.



