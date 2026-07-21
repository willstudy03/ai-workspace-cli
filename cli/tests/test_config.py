from aiws_cli.config import AiwsConfig, config_path, load_config, save_config


def test_save_load_round_trip(tmp_path):
    cfg = AiwsConfig(
        tool="copilot",
        track_skill_market=True,
        upstream_repo="git@example.com:me/repo.git",
        upstream_ref="main",
    )
    cfg.stamp_now()
    path = save_config(tmp_path, cfg)
    assert path == config_path(tmp_path)
    assert path.exists()

    loaded = load_config(tmp_path)
    assert loaded is not None
    assert loaded.tool == "copilot"
    assert loaded.track_skill_market is True
    assert loaded.upstream_repo == "git@example.com:me/repo.git"
    assert loaded.upstream_ref == "main"
    assert loaded.initialized_at is not None


def test_load_missing_returns_none(tmp_path):
    assert load_config(tmp_path) is None


def test_blank_upstream_is_omitted(tmp_path):
    cfg = AiwsConfig(tool="claude", track_skill_market=True, upstream_repo=None)
    path = save_config(tmp_path, cfg)
    text = path.read_text(encoding="utf-8")
    assert "upstream_repo" not in text
    assert "track_skill_market = true" in text


def test_stamp_now_is_iso(tmp_path):
    cfg = AiwsConfig()
    cfg.stamp_now()
    assert "T" in cfg.initialized_at and cfg.initialized_at.endswith("+00:00")

