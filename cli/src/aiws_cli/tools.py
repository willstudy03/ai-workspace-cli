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

    @property
    def instruction_filename(self) -> str:
        """Bare filename of the instruction file (e.g. ``copilot-instructions.md``)."""
        return self.instruction_src.rsplit("/", 1)[-1]

    def launch_argv(self, prompt: str) -> list[str]:
        """Return the argv used to open the tool interactively with a starting prompt."""
        if self.key == "copilot":
            return [self.cli_command, "-p", prompt]
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
        # copilot: programmatic prompt mode, pre-approve tool use.
        return [self.cli_command, "-p", prompt, "--allow-all-tools"]


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
    ),
}

# Stable display order for the wizard menu.
TOOL_ORDER: list[str] = ["claude", "copilot", "codex"]


def get_tool(key: str) -> AiTool | None:
    return TOOLS.get(key.strip().lower())

