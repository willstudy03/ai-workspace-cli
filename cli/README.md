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

`install.py` installs the `aiws` command and verifies it is on your PATH.

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

5. **Launch the agent** — opens your AI tool and asks it to run the
   `aiws-workspace-init` skill to scaffold the full workspace folder tree. By
   default this is an interactive launch; pass `--auto` to run it **headless with
   auto-approval** so the skill completes end-to-end without prompts:

   | Tool           | Interactive launch      | `--auto` (headless)                                   |
   |----------------|-------------------------|-------------------------------------------------------|
   | Claude Code    | `claude "<prompt>"`     | `claude -p "<prompt>" --permission-mode acceptEdits`  |
   | GitHub Copilot | `copilot -p "<prompt>"` | `copilot -p "<prompt>" --allow-all-tools`             |
   | OpenAI Codex   | `codex "<prompt>"`      | `codex exec --full-auto "<prompt>"`                   |

   **First-time sign-in:** if `aiws` just installed the tool's CLI (or you run
   `--auto`), you likely aren't authenticated yet. Before launching the init prompt,
   `aiws` runs an **authentication gate**: if no auth token is detected
   (`ANTHROPIC_API_KEY` / `GH_TOKEN` / `GITHUB_TOKEN` / `OPENAI_API_KEY`), it opens
   the tool's sign-in flow and waits for you to complete login, then continues to run
   `aiws-workspace-init`.

   | Tool           | Sign-in step                                                            |
   |----------------|-------------------------------------------------------------------------|
   | Claude Code    | opens `claude`; complete the browser OAuth, then `/exit` to continue    |
   | GitHub Copilot | opens `copilot`; run `/login`, then `/exit` to continue                 |
   | OpenAI Codex   | runs `codex login` (ChatGPT account or API key)                         |

Your choices are saved to `<workspace>/.aiws/config.toml`.

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
aiws init --no-tool-cli           # pure-Python run: don't check/install the tool CLI (no npm)
aiws init --auto                  # launch the AI tool headless and run init to completion
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



