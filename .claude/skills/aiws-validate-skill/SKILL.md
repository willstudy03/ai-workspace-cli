---
name: "aiws-validate-skill"
description: "Validates newly added Skills, Agents, Scripts, References, and Codebase docs against the repo's predefined directory structure and file format rules. Compares the current branch against remote master, identifies all new files, checks their placement and content format, then reports a clear pass/fail result with actionable fix instructions. No files are created or modified."
tags: ["validation", "ci", "standards", "repo-health"]
applies-to: ["agent-skills repo"]
author: "William Theo (IT RDI IM TD)"
last-updated: "2026-06-24"
---

# Validate Skill

Validates every newly added file in this repository against the standardized
directory layout and content format rules. Reports a pass/fail result with
exact remediation steps. **This skill is read-only — it never creates, edits,
or deletes any file.**

## When to Use

Trigger phrases: "validate my changes", "check my new files", "validate skill",
"validate agent", "run validation", "check if my file is correct",
"did I put it in the right place", "validate repo structure"

---

## Purpose

Contributors to this repo add Skills, Agents, Scripts, References, and Codebase
docs. Without automated validation it is easy to put files in the wrong folder,
use the wrong filename casing, or omit required front-matter fields — all of
which break the agent's ability to discover and load the content correctly.

This skill closes that gap: it compares the contributor's branch against remote
master, finds every newly added file, and checks each one against the repo's
standardized rules. The result is a clear, line-by-line report of what passed,
what failed, and exactly what to change — with no automated modifications made.

---

## Instructions

### Step 1 — Sync with Remote Master

Run the following command to fetch the latest state of the remote master branch
without modifying the working tree:

```bash
git fetch origin master
```

> If `git fetch` fails (e.g., no network, wrong remote name), report the error
> and ask the user to confirm the correct remote name (`git remote -v`) before
> proceeding.

---

### Step 2 — Identify Newly Added Files

Compare the current local branch against `origin/master` and collect **only
files that are new in the current branch** (status `A` = Added):

```bash
git diff --name-status origin/master...HEAD --diff-filter=A
```

Parse the output: each line is `A\t<relative-file-path>`.  
Collect all file paths into a **New Files List**.

Also capture the current branch name for the report:

```bash
git rev-parse --abbrev-ref HEAD
```

If the New Files List is **empty**, report:

```
✅ No new files detected between this branch and origin/master. Nothing to validate.
```

and stop.

---

### Step 3 — Classify Each New File

For every file in the New Files List, classify it into one of the following
types using its path:

| Type | Path Pattern |
|---|---|
| **Skill** | `skills/<any>/<any>.md` |
| **Claude Skill** | `.claude/skills/<any>/<any>.md` |
| **Agent** | `agents/<any>/AGENT.md` |
| **Agent Context** | `agents/<any>/context/<any>.md` |
| **Script** | `scripts/<any>.sh` |
| **Codebase Overview** | `codebases/<any>/OVERVIEW.md` |
| **Codebase Module** | `codebases/<any>/modules/<any>/MODULE.md` |
| **Codebase Module Doc** | `codebases/<any>/modules/<any>/<any>.md` (not MODULE.md) |
| **Codebase Architecture** | `codebases/<any>/architecture/<any>.md` |
| **Codebase Pattern** | `codebases/<any>/patterns/<any>.md` |
| **Codebase Standard** | `codebases/<any>/standards/<any>.md` |
| **Reference** | `references/<any>/<any>` |
| **Doc** | `docs/<any>.md` |
| **Unknown** | Anything else |

**Unknown** files are flagged as warnings — they may be misplaced.

---

### Step 4 — Validate Each File

Apply the validation rules for the file's type (defined in Step 5 below).
Read the file content using available tools. For each file collect:

- **Directory Check** — Is the file in the correct location?
- **Filename Check** — Does the filename follow the naming convention?
- **Content Check** — Does the file contain all required sections and front-matter?

---

### Step 5 — Validation Rules by File Type

#### 5.1 Skill (`skills/<skill-name>/SKILL.md`)

**Directory Rules**
- [ ] File must reside under `skills/` at exactly one level deep: `skills/<skill-name>/SKILL.md`
- [ ] `<skill-name>` must be `kebab-case` (lowercase letters and hyphens only; no underscores, no spaces, no uppercase)
- [ ] Primary file must be named `SKILL.md` (all uppercase)

**Front-Matter Rules** — YAML block between `---` delimiters at the very top of the file.

All fields below are **required**:

| Field | Rule |
|---|---|
| `name` | Non-empty string; Title Case recommended (e.g., `"Java Coding Standard"`) |
| `version` | SemVer format: `"MAJOR.MINOR.PATCH"` (e.g., `"1.0.0"`); no `v` prefix |
| `description` | Non-empty string; one-sentence description of the skill |
| `tags` | Non-empty YAML list; each tag lowercase with no spaces (e.g., `["java", "testing"]`) |
| `applies-to` | Non-empty YAML list (e.g., `["Java", "Spring Boot"]`) |
| `author` | Non-empty string |
| `last-updated` | Date string in `"YYYY-MM-DD"` format |

**Content Section Rules**

| Section | Required | Rule |
|---|---|---|
| `## Purpose` | ✅ Required | Must be present and non-empty; no unmodified TODO placeholder |
| `## Instructions` | ✅ Required | Must be present and non-empty; no unmodified TODO placeholder |
| `## Examples` | ⚠️ Recommended | Warn if missing but do not fail |
| `## References` | ℹ️ Optional | No penalty if absent |

---

#### 5.2 Claude Skill (`.claude/skills/<skill-name>/SKILL.md`)

Apply the **same rules as 5.1** with the following directory adjustment:

- [ ] File must reside under `.claude/skills/` at exactly one level deep: `.claude/skills/<skill-name>/SKILL.md`
- [ ] `<skill-name>` must be `kebab-case`
- [ ] Primary file must be named `SKILL.md` (all uppercase)

> Claude Skills in `.claude/skills/` are automatically loaded by Claude Code when
> users clone this repo. They follow the identical schema as `skills/`.

---

#### 5.3 Agent (`agents/<role>/AGENT.md`)

**Directory Rules**
- [ ] File must reside at exactly: `agents/<role>/AGENT.md`
- [ ] `<role>` must be `kebab-case`
- [ ] Primary file must be named `AGENT.md` (all uppercase)

**Front-Matter Rules** — YAML block between `---` delimiters.

| Field | Rule |
|---|---|
| `name` | Non-empty string |
| `description` | Non-empty string; describes persona, objective, and when to use |

**Content Section Rules**

| Section | Required | Rule |
|---|---|---|
| `## Persona` | ✅ Required | Must be present and non-empty |
| `## Goals` | ✅ Required | Must be present and non-empty |
| `## Skills` | ✅ Required | Must list at least one skill with its path |
| `## Constraints` | ✅ Required | Must be present and non-empty |
| `## Core Principles` | ⚠️ Recommended | Warn if missing |
| `## Workflow` | ⚠️ Recommended | Warn if missing |

---

#### 5.4 Agent Context (`agents/<role>/context/<file>.md`)

**Directory Rules**
- [ ] Must reside under `agents/<role>/context/`
- [ ] Filename must be `kebab-case` with `.md` extension

**Content Rules**
- [ ] File must be non-empty (no blank placeholder files)

---

#### 5.5 Script (`scripts/<script-name>.sh`)

**Directory Rules**
- [ ] Must reside directly under `scripts/` (no subdirectories)
- [ ] Filename must be `kebab-case` with `.sh` extension (no underscores, no uppercase)

**Content Rules**
- [ ] First line must be a shebang: `#!/usr/bin/env bash`
- [ ] Must contain at least one comment line (`#`) describing what the script does
- [ ] File must not be empty beyond the shebang line

---

#### 5.6 Codebase Overview (`codebases/<codebase-slug>/OVERVIEW.md`)

**Directory Rules**
- [ ] Must be at exactly: `codebases/<codebase-slug>/OVERVIEW.md`
- [ ] `<codebase-slug>` must be `kebab-case`
- [ ] Filename must be `OVERVIEW.md` (all uppercase)

**Content Rules**
- [ ] File must be non-empty
- [ ] Should describe: the project's purpose, tech stack, and high-level architecture

---

#### 5.7 Codebase Module (`codebases/<codebase-slug>/modules/<module-name>/MODULE.md`)

**Directory Rules**
- [ ] Must be at exactly: `codebases/<codebase-slug>/modules/<module-name>/MODULE.md`
- [ ] Both `<codebase-slug>` and `<module-name>` must be `kebab-case`
- [ ] Filename must be `MODULE.md` (all uppercase)

**Content Rules**
- [ ] File must be non-empty

---

#### 5.8 Codebase Module Supporting Docs

Recognized filenames: `api-contracts.md`, `data-models.md`, `dependencies.md`, `conventions.md`

**Directory Rules**
- [ ] Must reside under `codebases/<codebase-slug>/modules/<module-name>/`
- [ ] Filename must be one of the recognized names above, or any `kebab-case` name with `.md` extension

**Content Rules**
- [ ] File must be non-empty

---

#### 5.9 Codebase Architecture (`codebases/<codebase-slug>/architecture/<file>.md`)

**Directory Rules**
- [ ] Must reside under `codebases/<codebase-slug>/architecture/`
- [ ] Recognized standard filenames: `system-architecture.md`, `data-flow.md`, `component-diagram.md`, `tech-stack.md`
- [ ] Custom names are accepted if `kebab-case` with `.md` extension

**Content Rules**
- [ ] File must be non-empty

---

#### 5.10 Codebase Pattern / Standard

**Directory Rules**
- [ ] Pattern files: `codebases/<codebase-slug>/patterns/<pattern-name>.md`
- [ ] Standard files: `codebases/<codebase-slug>/standards/<standard-name>.md`
- [ ] Filenames must be `kebab-case` with `.md` extension

**Content Rules**
- [ ] File must be non-empty

---

#### 5.11 Reference (`references/<reference-name>/`)

**Directory Rules**
- [ ] Must reside under `references/<reference-name>/` (exactly one level of grouping folder)
- [ ] `<reference-name>` folder must be `kebab-case`

**Content Rules**
- [ ] File must be non-empty

---

#### 5.12 Doc (`docs/<doc-name>.md`)

**Directory Rules**
- [ ] Must reside directly under `docs/`
- [ ] Filename must be `kebab-case` with `.md` extension

**Content Rules**
- [ ] File must be non-empty

---

#### 5.13 Unknown File Type

Any file that does not match the patterns above:

- [ ] Flag as ⚠️ **Warning — Unrecognized path**
- [ ] Suggest the correct location based on the file's apparent purpose using the
  "Where to Put Your File" table in `README.md`

---

### Step 6 — Generate Validation Report

After validating all new files, produce a report using this exact format:

````markdown
## Validation Report

### Branch vs. Master Comparison
- **Current branch:** `<branch-name>`
- **Compared against:** `origin/master`
- **New files detected:** <count>

---

### File Results

| # | File | Type | Directory ✔ | Filename ✔ | Content ✔ | Result |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 1 | `skills/my-skill/SKILL.md` | Skill | ✅ | ✅ | ✅ | ✅ PASS |
| 2 | `agents/reviewer/AGENT.md` | Agent | ✅ | ✅ | ❌ | ❌ FAIL |
| 3 | `scripts/my_script.sh` | Script | ✅ | ❌ | ✅ | ❌ FAIL |

---

### Failures & Required Changes

#### ❌ `agents/reviewer/AGENT.md`
- **Content — Missing required section `## Skills`:**
  Add a `## Skills` section listing at least one skill with its path under `skills/`.
- **Content — Missing required section `## Constraints`:**
  Add a `## Constraints` section listing the agent's hard rules.

#### ❌ `scripts/my_script.sh`
- **Filename — Convention violation:**
  Filename uses underscore (`my_script.sh`). Rename to `kebab-case`: `my-script.sh`.

---

### Warnings

#### ⚠️ `skills/my-skill/SKILL.md`
- `## Examples` section is missing. This is recommended — consider adding good vs. bad examples.

---

### Summary

| Status | Count |
|---|---|
| ✅ PASS | 1 |
| ❌ FAIL | 2 |
| ⚠️ WARNING | 1 |

**Overall Result: ❌ FAILED — 2 file(s) require changes before this branch is ready to merge.**
````

#### When all files pass:

````markdown
## Validation Report

### Branch vs. Master Comparison
- **Current branch:** `<branch-name>`
- **Compared against:** `origin/master`
- **New files detected:** <count>

### Result
✅ All <count> new file(s) passed validation.

### Highlights
- [Note any particularly well-structured files or good practices observed]
````

---

### Step 7 — Remediation Guidance

After the report, for **each failed file**, provide specific guidance:

1. **Exact issue** — state which rule was violated and its rule ID (e.g., "Directory Rule", "Front-Matter: `version`")
2. **Expected value** — show exactly what the correct value should be
3. **Example snippet** — provide the corrected path, front-matter block, or section heading

Do **not** make any changes to any file. Only report and guide.

---

## Validation Quick Reference

### Naming Conventions

| Thing | Convention | Valid Example | Invalid Example |
|---|---|---|---|
| Skill folder | `kebab-case` | `unit-test` | `unit_test`, `UnitTest` |
| Claude Skill folder | `kebab-case` | `aiws-validate-skill` | `validate_skill` |
| Agent role folder | `kebab-case` | `senior-dev` | `seniorDev`, `senior dev` |
| Codebase slug | `kebab-case` | `my-ecommerce-app` | `myEcommerceApp` |
| Module folder | `kebab-case` | `payment-service` | `PaymentService` |
| Primary concept file | `UPPERCASE.md` | `SKILL.md`, `AGENT.md`, `OVERVIEW.md`, `MODULE.md` | `skill.md`, `Skill.md` |
| Script file | `kebab-case.sh` | `validate-skill.sh` | `validate_skill.sh`, `ValidateSkill.sh` |
| Script file | `kebab-case.sh` / `kebab-case.py` | `validate-skill.sh`, `extract-pdf.py` | `validate_skill.sh`, `ValidateSkill.sh` |

### Required Front-Matter by Type

| Type | Required Fields |
|---|---|
| Skill / Claude Skill | `name`, `version`, `description`, `tags`, `applies-to`, `author`, `last-updated` |
| Agent | `name`, `description` |

### SemVer Validation

`version` must match: `X.Y.Z` where X, Y, Z are non-negative integers.

| Valid | Invalid |
|---|---|
| `"1.0.0"` | `"v1.0"` |
| `"2.3.11"` | `"1.0"` |
| `"0.1.0"` | `"latest"` |

### Date Format Validation

`last-updated` must match `YYYY-MM-DD`.

| Valid | Invalid |
|---|---|
| `"2026-06-24"` | `"24/06/2026"` |
| `"2025-01-01"` | `"June 24 2026"` |

---

## Examples

### ✅ Correct Skill Front-Matter

```yaml
---
name: "rest-api-error-handling"
version: "1.0.0"
description: "Enforce consistent error response shapes across REST endpoints."
tags: ["rest", "error-handling", "java"]
applies-to: ["Java", "Spring Boot"]
author: "williamtheo"
last-updated: "2026-06-24"
---
```

### ❌ Incorrect Skill Front-Matter → Fix

**Before (broken):**
```yaml
---
name: REST API Error Handling
version: v1.0
description:
tags: rest, error-handling
applies-to: Java
last-updated: 24/06/2026
---
```

**Issues:**
- `name` — unquoted; not `kebab-case` (must match folder name `rest-api-error-handling`)
- `version` — `v1.0` is not valid SemVer (missing patch; has `v` prefix)
- `description` — empty
- `tags` — must be a YAML list, not a comma-separated string
- `applies-to` — must be a YAML list
- `last-updated` — must be `YYYY-MM-DD`; `author` field is entirely missing

**After (fixed):**
```yaml
---
name: "rest-api-error-handling"
version: "1.0.0"
description: "Enforce consistent error response shapes across REST endpoints."
tags: ["rest", "error-handling", "java"]
applies-to: ["Java", "Spring Boot"]
author: "williamtheo"
last-updated: "2026-06-24"
---
```

---

### ❌ Wrong Directory → Fix

| Wrong | Correct | Issue |
|---|---|---|
| `skill/my-skill/SKILL.md` | `skills/my-skill/SKILL.md` | Folder `skill` should be `skills` |
| `skills/MySkill/SKILL.md` | `skills/my-skill/SKILL.md` | Folder not `kebab-case` |
| `skills/my-skill/skill.md` | `skills/my-skill/SKILL.md` | Filename must be all-uppercase |
| `agent/reviewer/AGENT.md` | `agents/reviewer/AGENT.md` | Folder `agent` should be `agents` |
| `scripts/validate_skill.sh` | `scripts/validate-skill.sh` | Underscore not allowed; use hyphens |

---

## References
- The directory-structure and file-format rules this skill checks are defined
  inline in this skill's Instructions.
- [Validate Knowledge](../aiws-validate-knowledge/SKILL.md)
