from aiws_cli.cli import ingest, init


def _default(cmd, name):
    for p in cmd.params:
        if p.name == name:
            return p.default
    raise KeyError(name)


def test_auto_is_default_headless_for_both_commands():
    # Headless/auto is the default; --interactive opts out.
    assert _default(init, "auto") is True
    assert _default(ingest, "auto") is True


def test_init_defaults_launch_agent_scaffold_is_opt_in():
    # By default aiws init launches the agent; --scaffold is explicit opt-in.
    assert _default(init, "do_launch") is None   # None -> auto-decide (launch)
    assert _default(init, "scaffold") is False


