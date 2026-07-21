from aiws_cli.scaffold import scaffold_workspace

EXPECTED = [
    "agents/example-agent/AGENT.md",
    "agents/example-agent/context/working-context.md",
    "skills/example-skill/SKILL.md",
    "references/example-reference/example-reference.md",
    "knowledge/concepts/example-concept.md",
    "knowledge/systems/example-system.md",
    "knowledge/workflows/example-workflow.md",
    "knowledge/policies/example-policy.md",
    "knowledge/how-to/example-how-to.md",
    "knowledge/references/example-reference-note.md",
    "knowledge/source/raw/README.md",
    "knowledge/source/processed/README.md",
    "codebases/example-codebase/OVERVIEW.md",
    "codebases/example-codebase/architecture/system-architecture.md",
    "codebases/example-codebase/architecture/data-flow.md",
    "codebases/example-codebase/architecture/component-diagram.md",
    "codebases/example-codebase/architecture/tech-stack.md",
    "codebases/example-codebase/modules/example-module/MODULE.md",
    "docs/example-guide.md",
    "scripts/example-script.sh",
]


def test_scaffold_creates_expected_tree(tmp_path):
    results = scaffold_workspace(tmp_path, today="2026-07-21")
    for rel in EXPECTED:
        assert (tmp_path / rel).is_file(), f"missing {rel}"
    # source/{raw,processed}, and NO legacy knowledge/raw
    assert (tmp_path / "knowledge/source/raw").is_dir()
    assert (tmp_path / "knowledge/source/processed").is_dir()
    assert not (tmp_path / "knowledge/raw").exists()
    assert any("Scaffold complete" in line for line in results)


def test_scaffold_is_idempotent(tmp_path):
    scaffold_workspace(tmp_path, today="2026-07-21")
    second = scaffold_workspace(tmp_path, today="2026-07-21")
    # Second run should skip everything (0 created).
    assert any("0 created" in line for line in second)
    assert all("↷ skipped" in line or "Scaffold complete" in line for line in second)


def test_scaffold_date_substitution(tmp_path):
    scaffold_workspace(tmp_path, today="2099-01-02")
    concept = (tmp_path / "knowledge/concepts/example-concept.md").read_text(encoding="utf-8")
    assert 'last_updated: "2099-01-02"' in concept


