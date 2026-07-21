from aiws_cli.assets import (
    BUNDLE_DIR,
    AssetSource,
    _bundle_available,
    build_copy_plan,
    place_assets,
)
from aiws_cli.tools import TOOLS


def test_bundle_is_available_and_has_three_tools():
    assert _bundle_available()
    for key in ("claude", "copilot", "codex"):
        assert (BUNDLE_DIR / key / "skills").is_dir()


def test_build_copy_plan_from_bundle(tmp_path):
    src = AssetSource("bundle", BUNDLE_DIR)
    plan = build_copy_plan(src, TOOLS["copilot"], tmp_path)
    inst_src, inst_dest = plan.instruction
    assert inst_src.exists()
    assert inst_dest == tmp_path / ".github" / "copilot-instructions.md"
    assert plan.skills[0].is_dir()


def test_place_assets_copies_instruction_and_skills(tmp_path):
    src = AssetSource("bundle", BUNDLE_DIR)
    plan = build_copy_plan(src, TOOLS["claude"], tmp_path)
    results = place_assets(plan, overwrite=False)

    assert (tmp_path / "CLAUDE.md").is_file()
    skills = list((tmp_path / ".claude" / "skills").iterdir())
    assert len([p for p in skills if p.is_dir()]) == 10
    assert any("built-in skill" in line for line in results)


def test_place_assets_is_non_destructive(tmp_path):
    src = AssetSource("bundle", BUNDLE_DIR)
    plan = build_copy_plan(src, TOOLS["codex"], tmp_path)
    place_assets(plan, overwrite=False)
    results = place_assets(plan, overwrite=False)  # second run
    assert any("skipped" in line for line in results)

