from aiws_cli.cli import _stage_inputs


def test_stage_single_file(tmp_path):
    src = tmp_path / "note.md"
    src.write_text("# hi", encoding="utf-8")
    raw = tmp_path / "raw"
    raw.mkdir()
    n = _stage_inputs((str(src),), raw)
    assert n == 1
    assert (raw / "note.md").is_file()


def test_stage_folder_copies_top_level_files(tmp_path):
    folder = tmp_path / "docs"
    folder.mkdir()
    (folder / "a.md").write_text("a", encoding="utf-8")
    (folder / "b.csv").write_text("b", encoding="utf-8")
    (folder / "sub").mkdir()
    (folder / "sub" / "deep.md").write_text("d", encoding="utf-8")  # not copied
    raw = tmp_path / "raw"
    raw.mkdir()
    n = _stage_inputs((str(folder),), raw)
    assert n == 2
    assert (raw / "a.md").is_file() and (raw / "b.csv").is_file()
    assert not (raw / "deep.md").exists()


def test_stage_skips_existing(tmp_path):
    src = tmp_path / "note.md"
    src.write_text("# hi", encoding="utf-8")
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "note.md").write_text("existing", encoding="utf-8")
    n = _stage_inputs((str(src),), raw)
    assert n == 0
    assert (raw / "note.md").read_text(encoding="utf-8") == "existing"

