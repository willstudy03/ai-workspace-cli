"""Registry of the AI coding tools that aiws can bootstrap a workspace for.

Each tool has its own native instruction file, workspace root, and CLI binary:

| Tool           | Instruction file                | Workspace root | Skills folder     |
|----------------|---------------------------------|----------------|-------------------|
| Claude Code    | CLAUDE.md                       | .claude/       | .claude/skills/   |
| GitHub Copilot | .github/copilot-instructions.md | .github/       | .github/skills/   |
| OpenAI Codex   | AGENTS.md                       | .codex/        | .codex/skills/    |
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AiTool:
    """Describes one supported AI coding tool and how to bootstrap it."""

    key: str
    display_name: str
    cli_command: str  # binary looked up on PATH (shutil.which)
    install_hint: str  # command a user can run to install the CLI
    docs_url: str
    instruction_src: str  # path (relative to source root) of the instruction file
    instruction_dest: str  # path (relative to target dir) where it should land
    skills_src: str  # skills dir relative to source root
    skills_dest: str  # skills dir relative to target dir
    auth_env_vars: tuple[str, ...] = ()  # if any is set, the tool is likely authenticated
    login_hint: str = ""  # human guidance for completing first-time authentication

    @property
    def instruction_filename(self) -> str:
        """Bare filename of the instruction file (e.g. ``copilot-instructions.md``)."""
        return self.instruction_src.rsplit("/", 1)[-1]

    def login_argv(self) -> list[str]:
        """Return the argv that starts the tool's interactive authentication flow.

        Codex exposes a dedicated ``login`` subcommand. Claude Code and GitHub
        Copilot authenticate on first interactive run (browser/device or a
        ``/login`` slash command), so we open the interactive session and let the
        user complete sign-in, then exit to return to aiws.
        """
        if self.key == "codex":
            return [self.cli_command, "login"]
        return [self.cli_command]

    def launch_argv(self, prompt: str) -> list[str]:
        """Return the argv used to open the tool interactively with a starting prompt."""
        if self.key == "copilot":
            # `-i/--interactive` starts an interactive session AND runs the prompt, so
            # Copilot can request tool/file permissions from the user (unlike `-p`,
            # which is non-interactive and denies tools without --allow-all-tools).
            return [self.cli_command, "-i", prompt]
        # claude and codex both accept a positional prompt argument.
        return [self.cli_command, prompt]

    def headless_argv(self, prompt: str) -> list[str]:
        """Return the argv to run the tool non-interactively with auto-approval.

        Used by ``aiws init --auto`` so the agent runs ``aiws-workspace-init`` to
        completion without interactive prompts. Approval/permission flags are the
        tool's documented "let it act" modes.
        """
        if self.key == "claude":
            # Print mode + auto-accept file edits (scaffolding writes files).
            return [self.cli_command, "-p", prompt, "--permission-mode", "acceptEdits"]
        if self.key == "codex":
            # Non-interactive exec subcommand with workspace-write auto approvals.
            return [self.cli_command, "exec", "--full-auto", prompt]
        # copilot: non-interactive requires pre-approving BOTH tools and file paths,
        # otherwise scaffolding writes fail with "could not request permission".
        return [self.cli_command, "-p", prompt, "--allow-all-tools", "--allow-all-paths"]


TOOLS: dict[str, AiTool] = {
    "claude": AiTool(
        key="claude",
        display_name="Claude Code",
        cli_command="claude",
        install_hint="npm install -g @anthropic-ai/claude-code",
        docs_url="https://docs.anthropic.com/en/docs/claude-code",
        instruction_src="CLAUDE.md",
        instruction_dest="CLAUDE.md",
        skills_src=".claude/skills",
        skills_dest=".claude/skills",
        auth_env_vars=("ANTHROPIC_API_KEY",),
        login_hint=(
            "On first run Claude Code prompts you to sign in (browser OAuth). "
            "Complete sign-in, then type /exit (or press Ctrl-D) to return to aiws."
        ),
    ),
    "copilot": AiTool(
        key="copilot",
        display_name="GitHub Copilot",
        cli_command="copilot",
        install_hint="npm install -g @github/copilot",
        docs_url="https://docs.github.com/en/copilot",
        instruction_src=".github/copilot-instructions.md",
        instruction_dest=".github/copilot-instructions.md",
        skills_src=".github/skills",
        skills_dest=".github/skills",
        auth_env_vars=("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"),
        login_hint=(
            "In the Copilot session, run /login to authenticate with your GitHub "
            "account, then run /exit (or press Ctrl-D) to return to aiws. "
            "(Alternatively: run `gh auth login`, or set GH_TOKEN / GITHUB_TOKEN.)"
        ),
    ),
    "codex": AiTool(
        key="codex",
        display_name="OpenAI Codex",
        cli_command="codex",
        install_hint="npm install -g @openai/codex",
        docs_url="https://developers.openai.com/codex/cli",
        instruction_src="AGENTS.md",
        instruction_dest="AGENTS.md",
        skills_src=".codex/skills",
        skills_dest=".codex/skills",
        auth_env_vars=("OPENAI_API_KEY",),
        login_hint=(
            "Codex opens a sign-in flow (ChatGPT account or API key). Complete it "
            "to finish authentication; aiws continues automatically afterwards."
        ),
    ),
}

# Stable display order for the wizard menu.
TOOL_ORDER: list[str] = ["claude", "copilot", "codex"]


def get_tool(key: str) -> AiTool | None:
    return TOOLS.get(key.strip().lower())

