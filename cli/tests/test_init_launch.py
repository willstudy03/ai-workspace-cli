from unittest import mock

from click.testing import CliRunner

from aiws_cli import cli as climod


def _run(extra_args, tmp):
    runner = CliRunner()
    with (
        mock.patch.object(climod, "run_preflight", lambda **k: None),
        mock.patch.object(climod, "_ensure_tool_cli", lambda tool, ay: False),
        mock.patch.object(climod, "ensure_authenticated", lambda tool, assume_yes: True),
        mock.patch.object(climod, "launch_agent") as launch,
    ):
        result = runner.invoke(
            climod.cli,
            [
                "init", "--path", str(tmp), "--tool", "copilot",
                "--no-git", "--no-markitdown", "--no-track", "-y", *extra_args,
            ],
        )
    return result, launch


def test_default_init_launches_the_agent(tmp_path):
    result, launch = _run([], tmp_path)
    assert result.exit_code == 0, result.output
    assert launch.called  # by default we launch the agent to run aiws-workspace-init


def test_scaffold_flag_skips_the_agent(tmp_path):
    result, launch = _run(["--scaffold"], tmp_path)
    assert result.exit_code == 0, result.output
    assert not launch.called  # --scaffold builds natively, no agent
    assert (tmp_path / ".github" / "knowledge" / "source" / "raw" / "README.md").is_file()


def test_no_launch_suppresses_agent(tmp_path):
    result, launch = _run(["--no-launch"], tmp_path)
    assert result.exit_code == 0, result.output
    assert not launch.called

