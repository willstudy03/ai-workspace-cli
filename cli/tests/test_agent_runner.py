
import aiws_cli.agent_runner as ar
from aiws_cli.tools import TOOLS


def test_build_ingest_prompt_variants():
    p = ar.build_ingest_prompt(validate=True, auto=True)
    assert "aiws-raw-to-markdown" in p
    assert "aiws-create-knowledge" in p
    assert "aiws-validate-knowledge" in p
    assert "source/raw" in p and "source/processed" in p
    assert "without asking for confirmation" in p

    p2 = ar.build_ingest_prompt(validate=False, auto=False)
    assert "aiws-validate-knowledge" not in p2
    assert "without asking for confirmation" not in p2


def test_init_prompts_reference_skill():
    assert "aiws-workspace-init" in ar.INIT_PROMPT
    assert "aiws-workspace-init" in ar.AUTO_INIT_PROMPT
    assert "without asking for confirmation" in ar.AUTO_INIT_PROMPT


def test_detect_auth_env_token(monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "x")
    authed, how = ar._detect_auth(TOOLS["copilot"])
    assert authed is True
    assert "GH_TOKEN" in how


def test_detect_auth_none_when_no_token(monkeypatch):
    for v in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(v, raising=False)
    # No gh on PATH -> cannot confirm
    monkeypatch.setattr(ar.shutil, "which", lambda c: None)
    authed, how = ar._detect_auth(TOOLS["copilot"])
    assert authed is False
    assert how == ""


def test_detect_auth_gh_status(monkeypatch):
    for v in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setattr(ar.shutil, "which", lambda c: "/usr/bin/" + c)

    class R:
        returncode = 0

    monkeypatch.setattr(ar, "run_cli", lambda argv, **k: R())
    authed, how = ar._detect_auth(TOOLS["copilot"])
    assert authed is True
    assert how == "gh auth"

