# aiws CLI

`aiws` bootstraps a portable **AI-agent workspace** — the built-in `aiws-*` skills
and governance instructions — for **Claude Code**, **GitHub Copilot**, or
**OpenAI Codex**, in whatever directory you run it.

## Install

From source (this repo):

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
   tool's CLI isn't installed, `aiws` offers to install it (via `npm`).
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

Your choices are saved to `<workspace>/.aiws/config.toml`.

### Useful flags

```bash
aiws init --tool copilot          # preselect the AI tool
aiws init --path ./my-project     # target a different directory
aiws init --upstream <git-url>    # track a specific upstream repo (blank by default)
aiws init --ref <branch>          # dedicated branch to pull skill updates from
aiws init --no-track              # don't track an upstream skill market
aiws init --no-launch             # set up files but don't open the AI tool
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


