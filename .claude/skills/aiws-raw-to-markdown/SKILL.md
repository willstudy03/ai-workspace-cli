---
name: "aiws-raw-to-markdown"
description: "Converts non-Markdown source files dropped in knowledge/raw/ (PDF, Word, PowerPoint, Excel, images, audio, HTML, CSV/JSON/XML, EPub, ZIP, and more) into Markdown using Microsoft's open-source MarkItDown tool, writing the output back under knowledge/raw/ so aiws-create-knowledge can curate it into proper knowledge entries."
tags: ["knowledge", "conversion", "markitdown", "raw", "ingestion"]
applies-to: ["agent-skills repo", "aiws workspace"]
author: "William Theo (IT RDI IM TD)"
last-updated: "2026-07-20"
---

# AIWS Raw to Markdown

Converts raw, non-Markdown source files placed under `knowledge/raw/` into
Markdown using **MarkItDown** (Microsoft's open-source file-to-Markdown utility).
The converted `.md` files are written **back under `knowledge/raw/`** — they remain
staging material, ready to be curated into proper knowledge entries by the
`aiws-create-knowledge` skill. This skill only converts; it does **not** classify,
reshape, or file entries.

## When to Use

Trigger phrases: "convert raw to markdown", "markitdown the raw files", "raw to markdown",
"turn my PDF/Word/PPT into markdown", "convert knowledge/raw", "ingest raw documents",
"prepare raw files for knowledge", "aiws raw to markdown"

Use this as the **first stage** of knowledge ingestion: whenever binary or
non-Markdown documents (PDFs, Office files, images, audio, HTML, spreadsheets,
etc.) land in `knowledge/raw/` and need to become Markdown before curation.

---

## Purpose

The knowledge pipeline expects Markdown. But source material often arrives as PDFs,
Word/PowerPoint/Excel files, images, or exports — formats the curation skill cannot
process directly.

This skill bridges that gap. It runs MarkItDown over each non-Markdown file in
`knowledge/raw/`, producing structure-preserving Markdown (headings, lists, tables,
links) that stays in the raw staging area. The result is a clean handoff:
`aiws-raw-to-markdown` (convert) → `aiws-create-knowledge` (classify + curate + file).

---

## Pipeline Position

```
knowledge/raw/  ──[aiws-raw-to-markdown]──▶  knowledge/raw/  (now Markdown)
                                                   │
                                                   ▼
                                          [aiws-create-knowledge]
                                                   │
                                                   ▼
             concepts/ | systems/ | workflows/ | policies/ | how-to/ | references/
```

---

## Core Principles

1. **Convert only — never curate.** This skill produces Markdown; it does not
   classify content, rewrite it into a type format, or move it out of `raw/`. That
   is `aiws-create-knowledge`'s job.
2. **Non-destructive.** Never delete or overwrite the original source file. Leave it
   in place; only add the converted `.md`.
3. **Stay in `raw/`.** All output remains under `knowledge/raw/` (staging). Nothing
   authoritative is produced here.
4. **Preserve structure & content.** Use MarkItDown so headings, lists, tables, and
   links survive the conversion. Do not hand-summarize.
5. **Skip what's already Markdown.** Do not re-convert existing `.md` files or
   `README.md`.
6. **Sanitize inputs.** Only convert local files the user placed in `raw/`. Do not
   pass untrusted URLs/paths; prefer `convert_local()` in the Python API.

---

## Prerequisites — MarkItDown

MarkItDown requires **Python 3.10+**. A virtual environment is recommended.

### Check whether MarkItDown is installed

```bash
markitdown --version 2>/dev/null || echo "MARKITDOWN_NOT_FOUND"
```

### Install if missing

```bash
# (Recommended) create/activate a virtual environment first
python -m venv .venv && source .venv/bin/activate   # Windows Git Bash: source .venv/Scripts/activate

# Install all optional format dependencies (PDF, DOCX, PPTX, XLSX, audio, etc.)
pip install 'markitdown[all]'
```

> If you only need specific formats, install narrower extras, e.g.
> `pip install 'markitdown[pdf, docx, pptx]'`. If a conversion later fails with a
> missing-dependency error, install the matching extra and retry.

---

## Supported Source Formats (via MarkItDown)

| Category | Examples | Notes |
|---|---|---|
| Documents | PDF, Word (`.docx`) | `[pdf]`, `[docx]` extras |
| Presentations | PowerPoint (`.pptx`) | `[pptx]`; LLM image descriptions optional |
| Spreadsheets | Excel (`.xlsx`, `.xls`) | `[xlsx]`, `[xls]` |
| Images | `.jpg`, `.png` | EXIF metadata + OCR; LLM captioning optional |
| Audio | `.wav`, `.mp3` | EXIF + speech transcription (`[audio-transcription]`) |
| Web/Markup | HTML, XML | — |
| Text data | CSV, JSON | — |
| Archives | ZIP | Iterates over contents |
| Books | EPub | — |
| URLs | YouTube | Fetches transcript (`[youtube-transcription]`) |

> For scanned PDFs, complex tables, audio/video, or structured field extraction,
> MarkItDown can use Azure Document Intelligence (`-d -e <endpoint>`) or Azure
> Content Understanding (`--use-cu --cu-endpoint <endpoint>`). Offer these only if
> the user has the endpoints; otherwise use the offline built-in converters.

---

## Instructions

### Step 1 — Locate the Raw Folder and Inventory Source Files

Find the knowledge root and list **non-Markdown** files in `raw/`:

```bash
for r in "knowledge" ".claude/knowledge" "$HOME/.claude/knowledge"; do
  [ -d "$r/raw" ] && echo "ROOT: $r/raw" && \
    find "$r/raw" -maxdepth 1 -type f ! -iname "*.md" ! -iname "README.md" | sort
done
```

Build a **Conversion Queue** of the non-Markdown files found. If the queue is empty,
report:
> ✅ No non-Markdown files found in `knowledge/raw/`. Nothing to convert.

and stop. (Files that are already `.md` are left for `aiws-create-knowledge`.)

### Step 2 — Ensure MarkItDown Is Available

Run the check from **Prerequisites**. If `MARKITDOWN_NOT_FOUND`, guide the user
through installation (venv + `pip install 'markitdown[all]'`). Confirm it works
before converting.

### Step 3 — Prepare the Output Location (Stays in `raw/`)

Keep converted Markdown inside the raw staging area. Default output folder:

```bash
mkdir -p "knowledge/raw/converted"
```

> Rationale: output stays under `raw/` so it is still treated as unprocessed
> staging material and gets curated by `aiws-create-knowledge`. Confirm the output
> folder with the user if they prefer a different location under `raw/`.

### Step 4 — Convert Each File

For every file in the Conversion Queue, run MarkItDown and write a `.md` with the
same base name into the output folder:

```bash
# CLI form
markitdown "knowledge/raw/<source-file>" -o "knowledge/raw/converted/<source-stem>.md"
```

Or the Python API for finer control / local-only safety:

```python
from markitdown import MarkItDown
md = MarkItDown(enable_plugins=False)
result = md.convert_local("knowledge/raw/<source-file>")   # convert_local avoids remote fetches
open("knowledge/raw/converted/<source-stem>.md", "w", encoding="utf-8").write(result.text_content)
```

Rules for each conversion:
- **Do not overwrite** an existing output `.md` — if it exists, append a suffix
  (e.g., `-2`) or ask the user.
- **Verify** the output file exists and is non-empty after conversion.
- **On a missing-dependency error**, install the matching extra
  (e.g., `pip install 'markitdown[pdf]'`) and retry once.
- **On an unsupported/failed file**, skip it, keep the original, and record the
  failure with its exact error for the report.
- **Never delete** the source file.

### Step 5 — Verify and Report

List the produced Markdown and summarize:

```bash
ls -la "knowledge/raw/converted/"
```

```
✅ Raw → Markdown Conversion Complete
─────────────────────────────────────────────
Tool     : MarkItDown
Output   : knowledge/raw/converted/   (still in raw/ staging)

Converted:
  ✅ knowledge/raw/converted/q3-report.md        (from q3-report.pdf)
  ✅ knowledge/raw/converted/runbook.md          (from runbook.docx)
  ✅ knowledge/raw/converted/metrics.md          (from metrics.xlsx)

Skipped / failed:
  ❌ diagram.heic — unsupported format (kept original)

Originals: kept (non-destructive)
─────────────────────────────────────────────
```

### Step 6 — Hand Off to Curation

Tell the user the next stage:
> The Markdown is staged under `knowledge/raw/converted/`. Run the
> **`aiws-create-knowledge`** skill to classify each file, reshape it to its type's
> format, and file it into the correct `knowledge/` folder.

Do **not** curate or move files yourself — that is out of scope for this skill.

---

## Examples

### ✅ Good — Convert a Mixed Batch, Then Hand Off

**Raw folder:** `report.pdf`, `notes.docx`, `data.xlsx`, `already.md`

1. Inventory → queue = `report.pdf`, `notes.docx`, `data.xlsx` (`already.md` skipped).
2. MarkItDown present (`markitdown --version` OK).
3. `mkdir -p knowledge/raw/converted`.
4. Convert each → `converted/report.md`, `converted/notes.md`, `converted/data.md`;
   verify non-empty; originals kept.
5. Report ✅ → tell user to run `aiws-create-knowledge`.

### ✅ Good — Missing Optional Dependency

- `markitdown report.pdf ...` fails: "missing pdf dependencies".
- Run `pip install 'markitdown[pdf]'`, retry once → success.

### ❌ Bad — What This Skill Must NOT Do

> ❌ Classifying the converted file as a `concept` and moving it to `knowledge/concepts/`.

Forbidden — this skill only converts and keeps output in `raw/`. Classification and
filing belong to `aiws-create-knowledge`.

> ❌ Deleting or overwriting the original source file after conversion.

Forbidden — conversion is non-destructive; originals stay in `raw/`.

> ❌ Hand-writing Markdown from the source instead of using MarkItDown.

Forbidden — always use MarkItDown so structure (tables, headings, lists) is preserved.

---

## Quick Reference

| Step | Action | Guardrail |
|---|---|---|
| 1 | Inventory non-`.md` files in `raw/` | Skip `.md` and `README.md` |
| 2 | Ensure MarkItDown installed | Python 3.10+, `markitdown[all]` |
| 3 | Prepare `raw/converted/` | Output stays in `raw/` |
| 4 | `markitdown <src> -o <out>.md` | Non-destructive; retry on missing extra |
| 5 | Verify + report | Note skipped/failed files |
| 6 | Hand off | Next: `aiws-create-knowledge` |

### Common MarkItDown Commands

```bash
markitdown file.pdf -o out.md            # convert to a file
markitdown file.pdf > out.md             # via stdout
cat file.pdf | markitdown                # via stdin
markitdown --list-plugins                # list installed plugins
markitdown --use-plugins file.pdf        # enable 3rd-party plugins
markitdown file.pdf -d -e "<endpoint>"   # Azure Document Intelligence
markitdown file.pdf --use-cu --cu-endpoint "<endpoint>"  # Azure Content Understanding
```

---

## References
- [MarkItDown (Microsoft, GitHub)](https://github.com/microsoft/markitdown) — the conversion tool this skill wraps
- [AIWS Create Knowledge](../aiws-create-knowledge/SKILL.md) — the curation stage that consumes this skill's output
- [Validate Knowledge](../aiws-validate-knowledge/SKILL.md)
