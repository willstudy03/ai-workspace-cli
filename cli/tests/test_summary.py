from aiws_cli.cli import _print_summary
from aiws_cli.console import console
from aiws_cli.tools import TOOLS


def _summary(**kw):
    with console.capture() as cap:
        _print_summary(TOOLS["copilot"], __import__("pathlib").Path("/tmp/x"), False, **kw)
    return cap.get()


def test_summary_shows_launch_hint_when_launching():
    out = _summary(scaffolded=False, launching=True, headless=True)
    assert "Launching" in out
    assert "--scaffold" in out          # discoverable no-agent alternative
    assert "headless" in out


def test_summary_interactive_label():
    out = _summary(scaffolded=False, launching=True, headless=False)
    assert "interactive" in out


def test_summary_scaffolded():
    out = _summary(scaffolded=True, launching=False, headless=True)
    assert "structure is ready" in out
    assert "Structure" in out


def test_summary_no_launch_manual_message():
    out = _summary(scaffolded=False, launching=False, headless=True)
    assert "ask it to run" in out

