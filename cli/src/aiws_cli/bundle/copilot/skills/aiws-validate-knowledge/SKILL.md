---
name: "aiws-validate-knowledge"
version: "1.0.0"
description: "Validates newly added knowledge entries against the knowledge/ layer taxonomy and YAML front-matter schema. Compares the current branch against the base branch, finds every new knowledge file, checks folder placement, filename casing, required front-matter fields, and body structure, then reports a clear pass/fail result with actionable fixes. No files are created or modified."
tags: ["validation", "knowledge", "standards", "repo-health"]
applies-to: ["agent-skills repo"]
author: "William Theo (IT RDI IM TD)"
last-updated: "2026-07-20"
---

# Validate Knowledge

Validates every newly added file under `knowledge/` against the taxonomy folder
layout and the front-matter schema. Reports a pass/fail result with exact
remediation steps. **This skill is read-only — it never creates, edits, or
deletes any file.**

## When to Use

Trigger phrases: "validate knowledge", "check my knowledge entry", "validate my new note",
"is this knowledge entry correct", "did I file this in the right folder",
"validate knowledge structure", "check knowledge front-matter"

---

## Purpose

Contributors add knowledge entries (concepts, systems, workflows, policies,
how-tos, references). Without validation it is easy to file an entry in the wrong
type folder, mismatch the `type` field to its folder, use the wrong filename
casing, or omit required front-matter fields — all of which break the agent's
ability to discover and cross-link the knowledge correctly.

This skill compares the contributor's branch against the base branch, finds every
newly added `knowledge/` file, and checks each one against the taxonomy and
front-matter rules. The result is a clear, line-by-line report of what passed,
what failed, and exactly what to change — with no automated modifications made.

---

## Instructions

### Step 1 — Resolve the Base Branch and Sync

Determine the branch to compare against — there is **no hardcoded `master`/`main`**.
Resolve the base branch in this order:

1. **Tracked dedicated branch** — if `<workspace>/.aiws/config.toml` sets
   `upstream_ref`, use that branch.
2. **Repository default branch** — otherwise detect it from the remote.
3. **Fallback** — if neither resolves, ask the user for the base branch name.

```bash
# 1) Prefer the dedicated branch tracked by `aiws init`
BASE="$(sed -n 's/^upstream_ref[[:space:]]*=[[:space:]]*"\(.*\)"/\1/p' .aiws/config.toml 2>/dev/null)"
# 2) Fall back to the remote's default branch
[ -z "$BASE" ] && BASE="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##')"
[ -z "$BASE" ] && BASE="$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p')"
echo "Base branch: ${BASE:-<unset>}"
```

If `BASE` is still empty, ask the user for the correct base branch before continuing.
Then fetch it without modifying the working tree:

```bash
git fetch origin "$BASE"
```

> If `git fetch` fails (e.g., no network, wrong remote name), report the error
> and ask the user to confirm the correct remote name (`git remote -v`) before
> proceeding.

---

### Step 2 — Identify Newly Added Knowledge Files

Compare the current local branch against `origin/$BASE` and collect **only new
files under `knowledge/`** (status `A` = Added):

```bash
git diff --name-status origin/$BASE...HEAD --diff-filter=A -- knowledge/
```

Parse the output: each line is `A\t<relative-file-path>`.
Collect all file paths into a **New Knowledge Files List**.

Also capture the current branch name for the report:

```bash
git rev-parse --abbrev-ref HEAD
```

If the list is **empty**, report:

```
✅ No new knowledge files detected between this branch and origin/$BASE. Nothing to validate.
```

and stop.

---

### Step 3 — Classify Each New File by Type Folder

For every file, determine its taxonomy `type` from the folder it sits in:

| Folder | Expected `type` |
|---|---|
| `knowledge/concepts/` | `concept` |
| `knowledge/systems/` | `system` |
| `knowledge/workflows/` | `workflow` |
| `knowledge/policies/` | `policy` |
| `knowledge/how-to/` | `how-to` |
| `knowledge/references/` | `reference` |
| `knowledge/source/raw/` | (staging — relaxed rules, see 5.4) |
| anything else under `knowledge/` | **Unknown** |

**Unknown** locations are flagged as warnings — the entry may be misfiled.

---

### Step 4 — Validate Each File

Read each file with available tools. For each entry collect:

- **Directory Check** — Is the file in a valid taxonomy folder?
- **Filename Check** — Does the filename follow `kebab-case.md`?
- **Content Check** — Does the front-matter contain all required fields, and does
  `type` match the folder? Does the body open with `## Summary`?

---

### Step 5 — Validation Rules

#### 5.1 Directory Rules

- [ ] File must reside directly inside one of the taxonomy folders in Step 3
      (e.g., `knowledge/concepts/<entry>.md`), not nested deeper.
- [ ] The folder must be one of the six curated types (or `source/raw/`).

#### 5.2 Filename Rules

- [ ] Filename must be `kebab-case` with a `.md` extension
      (lowercase letters, digits, and hyphens only; no underscores, spaces, or uppercase).
- [ ] `README.md` files are exempt (skipped, not validated as entries).

#### 5.3 Front-Matter Rules

YAML block between `---` delimiters at the very top of the file. All fields below
are **required** unless marked optional:

| Field | Rule |
|---|---|
| `title` | Non-empty string; Title Case recommended (e.g., `"Incident Response"`) |
| `type` | Must exactly match the folder's expected `type` (see Step 3 table) |
| `owner` | Non-empty string |
| `status` | One of: `active`, `draft`, `deprecated` |
| `last_updated` | Date string in `YYYY-MM-DD` format |
| `tags` | Non-empty YAML list; each tag lowercase with no spaces |
| `related` | Optional YAML list of relative paths from the `knowledge/` root |
| `sources` | Optional YAML list (provenance) |

> **Key cross-check:** the `type` field **must** match the folder. An entry in
> `knowledge/policies/` with `type: "concept"` is a **failure**.

**`related` link integrity (when present):**
- [ ] Each `related` path should resolve to an existing file under `knowledge/`.
      Flag broken links as a warning (do not fail — the target may be added later
      in the same branch).

#### 5.4 Content / Body Rules

- [ ] The body must open with a `## Summary` section that is non-empty.
- [ ] File must not be an empty placeholder or contain unmodified template TODOs.

#### 5.5 Raw Staging Files (`knowledge/source/raw/`)

Files under `knowledge/source/raw/` are uncurated staging material:

- [ ] Only require: `kebab-case.md` filename and a non-empty body.
- [ ] Front-matter and `## Summary` are **recommended**, not required — warn if missing.

#### 5.6 Unknown Location

Any file under `knowledge/` not inside a recognized folder:

- [ ] Flag as ⚠️ **Warning — Unrecognized knowledge folder**
- [ ] Suggest the correct folder based on the entry's `type` field or apparent
      content using the taxonomy table.

---

### Step 6 — Generate Validation Report

After validating all new files, produce a report using this exact format:

````markdown
## Knowledge Validation Report

### Branch vs. Base Comparison
- **Current branch:** `<branch-name>`
- **Compared against:** `origin/$BASE`
- **New knowledge files detected:** <count>

---

### File Results

| # | File | Type | Directory ✔ | Filename ✔ | Front-Matter ✔ | Body ✔ | Result |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|
| 1 | `knowledge/concepts/rate-limiting.md` | concept | ✅ | ✅ | ✅ | ✅ | ✅ PASS |
| 2 | `knowledge/policies/data_retention.md` | policy | ✅ | ❌ | ✅ | ✅ | ❌ FAIL |
| 3 | `knowledge/workflows/onboarding.md` | workflow | ✅ | ✅ | ❌ | ✅ | ❌ FAIL |

---

### Failures & Required Changes

#### ❌ `knowledge/policies/data_retention.md`
- **Filename — Convention violation:**
  Filename uses underscore. Rename to `kebab-case`: `data-retention.md`.

#### ❌ `knowledge/workflows/onboarding.md`
- **Front-Matter — `type` mismatch:**
  `type` is `"concept"` but the file lives in `knowledge/workflows/`. Change
  `type` to `"workflow"` (or move the file to `knowledge/concepts/`).

---

### Warnings

#### ⚠️ `knowledge/concepts/rate-limiting.md`
- `related` link `policies/nonexistent.md` does not resolve to an existing file.

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
## Knowledge Validation Report

### Branch vs. Base Comparison
- **Current branch:** `<branch-name>`
- **Compared against:** `origin/$BASE`
- **New knowledge files detected:** <count>

### Result
✅ All <count> new knowledge file(s) passed validation.

### Highlights
- [Note any particularly well-structured entries or good cross-linking observed]
````

---

### Step 7 — Remediation Guidance

After the report, for **each failed file**, provide specific guidance:

1. **Exact issue** — state which rule was violated (e.g., "Directory Rule",
   "Front-Matter: `type` mismatch", "Filename convention").
2. **Expected value** — show exactly what the correct value should be.
3. **Example snippet** — provide the corrected path, front-matter block, or heading.

Do **not** make any changes to any file. Only report and guide.

---

## Validation Quick Reference

### Naming Conventions

| Thing | Convention | Valid Example | Invalid Example |
|---|---|---|---|
| Entry filename | `kebab-case.md` | `incident-response.md` | `incident_response.md`, `IncidentResponse.md` |
| `title` front-matter | Title Case | `"Incident Response"` | `"incident response"` |
| `tags` | lowercase, no spaces | `["security", "on-call"]` | `["Security", "On Call"]` |
| `last_updated` | ISO date `YYYY-MM-DD` | `"2026-07-20"` | `"20/07/2026"` |

### Type ↔ Folder Matrix

| Folder | Required `type` |
|---|---|
| `knowledge/concepts/` | `concept` |
| `knowledge/systems/` | `system` |
| `knowledge/workflows/` | `workflow` |
| `knowledge/policies/` | `policy` |
| `knowledge/how-to/` | `how-to` |
| `knowledge/references/` | `reference` |

### Required Front-Matter Fields

`title`, `type`, `owner`, `status`, `last_updated`, `tags`
(Optional: `related`, `sources`)

### Status Values

`status` must be one of: `active`, `draft`, `deprecated`.

---

## Examples

### ✅ Correct Knowledge Front-Matter

```yaml
---
title: "Rate Limiting"
type: "concept"
owner: "William Theo"
status: "active"
last_updated: "2026-07-20"
tags:
  - "resilience"
  - "api"
related:
  - "policies/example-secret-management.md"
---
```

### ❌ Incorrect Front-Matter → Fix

**Before (broken):**
```yaml
---
title: rate limiting
type: idea
owner:
status: live
last_updated: 20/07/2026
tags: resilience, api
---
```

**Issues:**
- `title` — should be Title Case: `"Rate Limiting"`
- `type` — `idea` is not a valid type; a file in `concepts/` must be `"concept"`
- `owner` — empty
- `status` — `live` is invalid; use `active` / `draft` / `deprecated`
- `last_updated` — must be `YYYY-MM-DD`
- `tags` — must be a YAML list, not a comma-separated string

**After (fixed):**
```yaml
---
title: "Rate Limiting"
type: "concept"
owner: "William Theo"
status: "active"
last_updated: "2026-07-20"
tags:
  - "resilience"
  - "api"
---
```

---

### ❌ Wrong Folder / Type → Fix

| Wrong | Correct | Issue |
|---|---|---|
| `knowledge/policy/retention.md` | `knowledge/policies/retention.md` | Folder `policy` should be `policies` |
| `knowledge/concepts/RateLimiting.md` | `knowledge/concepts/rate-limiting.md` | Filename must be `kebab-case` |
| `knowledge/workflows/x.md` with `type: "concept"` | `type: "workflow"` | `type` must match its folder |

---

## References
- The knowledge taxonomy and front-matter schema this skill validates against are
  defined inline in this skill.
- [Validate Skill](../aiws-validate-skill/SKILL.md)
- [Install Knowledge](../aiws-install-knowledge/SKILL.md)
