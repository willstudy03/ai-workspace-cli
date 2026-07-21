import aiws_cli.proc as proc


def test_run_cli_raises_when_missing(monkeypatch):
    monkeypatch.setattr(proc.shutil, "which", lambda c: None)
    try:
        proc.run_cli(["nope-xyz"])
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("expected FileNotFoundError")


def test_run_cli_runs_binary_directly_on_posix(monkeypatch):
    captured = {}

    def fake_run(argv, **kw):
        captured["argv"] = argv
        class R:
            returncode = 0
        return R()

    monkeypatch.setattr(proc.shutil, "which", lambda c: "/usr/local/bin/tool")
    monkeypatch.setattr(proc.os, "name", "posix")
    monkeypatch.setattr(proc.subprocess, "run", fake_run)
    proc.run_cli(["tool", "-x"])
    assert captured["argv"] == ["/usr/local/bin/tool", "-x"]


def test_run_cli_wraps_cmd_shim_on_windows(monkeypatch):
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        class R:
            returncode = 0
        return R()

    # Shim path AND an argument both contain spaces (the reported "End User" case).
    monkeypatch.setattr(proc.shutil, "which", lambda c: r"C:\Users\End User\npm\tool.CMD")
    monkeypatch.setattr(proc.os, "name", "nt")
    monkeypatch.setattr(proc.subprocess, "run", fake_run)
    proc.run_cli(["tool", "-p", "a b c"])

    cmd = captured["cmd"]
    assert isinstance(cmd, str)
    assert cmd.startswith("cmd /s /c ")
    # The shim path (with its space) stays quoted, as does the spaced argument.
    assert '"C:\\Users\\End User\\npm\\tool.CMD"' in cmd
    assert '"a b c"' in cmd

