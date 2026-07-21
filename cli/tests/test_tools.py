from aiws_cli.tools import TOOL_ORDER, TOOLS, get_tool


def test_registry_has_three_tools():
    assert set(TOOLS) == {"claude", "copilot", "codex"}
    assert TOOL_ORDER == ["claude", "copilot", "codex"]
    for key, tool in TOOLS.items():
        assert tool.key == key


def test_get_tool_case_insensitive():
    assert get_tool("Copilot").key == "copilot"
    assert get_tool("  CODEX ").key == "codex"
    assert get_tool("nope") is None


def test_workspace_root_and_instruction_filename():
    assert TOOLS["copilot"].workspace_root == ".github"
    assert TOOLS["claude"].workspace_root == ".claude"
    assert TOOLS["codex"].workspace_root == ".codex"
    assert TOOLS["copilot"].instruction_filename == "copilot-instructions.md"
    assert TOOLS["claude"].instruction_filename == "CLAUDE.md"


def test_launch_argv():
    assert TOOLS["copilot"].launch_argv("P") == ["copilot", "-i", "P"]
    assert TOOLS["claude"].launch_argv("P") == ["claude", "P"]
    assert TOOLS["codex"].launch_argv("P") == ["codex", "P"]


def test_headless_argv():
    assert TOOLS["copilot"].headless_argv("P") == [
        "copilot", "-p", "P", "--allow-all-tools", "--allow-all-paths",
    ]
    assert TOOLS["claude"].headless_argv("P") == [
        "claude", "-p", "P", "--permission-mode", "bypassPermissions",
    ]
    assert TOOLS["codex"].headless_argv("P") == ["codex", "exec", "--full-auto", "P"]


def test_login_argv():
    assert TOOLS["codex"].login_argv() == ["codex", "login"]
    assert TOOLS["copilot"].login_argv() == ["copilot"]
    assert TOOLS["claude"].login_argv() == ["claude"]


def test_copilot_auth_env_vars():
    assert "COPILOT_GITHUB_TOKEN" in TOOLS["copilot"].auth_env_vars
    assert "GH_TOKEN" in TOOLS["copilot"].auth_env_vars

