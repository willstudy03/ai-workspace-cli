---
name: "aiws-workspace-init"
description: "Scaffolds the complete agent-skills workspace file structure (agents, codebases, docs, knowledge, references, scripts, skills) into a project's .codex/ folder or the user's global ~/.codex/ folder, seeding every folder with a standards-compliant example file so users get a well-organized, ready-to-use layout."
tags: ["init", "scaffold", "setup", "workspace", "bootstrap"]
applies-to: ["agent-skills repo", "any project"]
author: ""
last-updated: "2026-07-20"
---

# Workspace Init

Initializes a well-organized agent workspace by scaffolding the full folder
structure — `agents/`, `codebases/`, `docs/`, `knowledge/`, `references/`,
`scripts/`, and `skills/` — into either a project's `.codex/` folder or the
user's global `~/.codex/` folder. Every folder is seeded with a
**standards-compliant example** so the user immediately has a correct, copyable
starting point.

## When to Use

Trigger phrases: "initialize workspace", "init workspace", "scaffold workspace",
"set up agent workspace", "bootstrap .codex structure", "create the folder structure",
"set up Codex folders", "workspace init", "start a new agent workspace"

---

## Purpose

New users of the agent-skills system need the canonical folder layout in place
before they can add their own agents, skills, references, and codebase docs.
Creating this by hand is error-prone: folders get misnamed, primary files use the
wrong casing, and front-matter is omitted — all of which break agent discovery.

This skill automates the bootstrap. It creates the entire directory tree in the
chosen target (`.codex/` for a single project, or `~/.codex/` globally) and
drops a valid `example-*` file into each folder that follows the repo's naming,
front-matter, and section rules. The result passes `aiws-validate-skill` and
`aiws-validate-knowledge` out of the box.

---

## Target Structure Reference

The skill scaffolds this tree under the chosen `<target-root>`
(`<project>/.codex/` or `~/.codex/`):

```
<target-root>/
├── agents/
│   └── example-agent/
│       ├── AGENT.md
│       └── context/
│           └── working-context.md
├── skills/
│   └── example-skill/
│       └── SKILL.md
├── references/
│   └── example-reference/
│       └── example-reference.md
├── knowledge/
│   ├── concepts/    example-concept.md
│   ├── systems/     example-system.md
│   ├── workflows/   example-workflow.md
│   ├── policies/    example-policy.md
│   ├── how-to/      example-how-to.md
│   ├── references/  example-reference-note.md
│   └── source/
│       ├── raw/         README.md
│       └── processed/   README.md
├── codebases/
│   └── example-codebase/
│       ├── OVERVIEW.md
│       ├── architecture/
│       │   ├── system-architecture.md
│       │   ├── data-flow.md
│       │   ├── component-diagram.md
│       │   └── tech-stack.md
│       └── modules/
│           └── example-module/
│               └── MODULE.md
├── docs/
│   └── example-guide.md
└── scripts/
    └── example-script.sh
```

---

## Instructions

### Step 1 — Clarify the Target Location

Ask the user where to initialize the workspace:

> **"Where would you like to initialize the workspace?**
>
> - **[G] Global** — Available across all projects. Files go into `~/.codex/`.
> - **[P] Project** — Scoped to one project. Files go into `<project>/.codex/`.
>
> Reply with **G** for global or **P** for project."

Wait for the answer before continuing.

---

### Step 2 — Resolve the Target Root

#### 2A — Global

```bash
echo "$HOME"
mkdir -p "$HOME/.codex"
```

Target root = `$HOME/.codex`. Confirm:
> ✅ Global target root ready: `~/.codex/`

#### 2B — Project

1. Ask for the absolute project path:
> **"Please provide the absolute path to your project directory."**

2. Verify and prepare:

```bash
ls "<project-dir>" 2>/dev/null || echo "NOT_FOUND"
mkdir -p "<project-dir>/.codex"
```

If `NOT_FOUND`, report and re-ask. Target root = `<project-dir>/.codex`. Confirm:
> ✅ Project target root ready: `<project-dir>/.codex/`

---

### Step 3 — Detect Existing Structure (Non-Destructive)

Before creating anything, check what already exists so the skill never overwrites
user content:

```bash
for d in agents skills references knowledge codebases docs scripts; do
  if [ -e "<target-root>/${d}" ]; then echo "EXISTS: ${d}"; else echo "MISSING: ${d}"; fi
done
```

**Rule:** This skill is **additive and idempotent**. Never overwrite or delete an
existing file. If an example file already exists, skip it and mark it `↷ skipped`
in the report. Only create what is missing.

---

### Step 4 — Present the Scaffold Plan and Confirm

Show the user exactly what will be created vs. skipped:

```
📋 Workspace Init Plan
─────────────────────────────────────────────
Target : ~/.codex/   (Global)

Folders to create:
  agents/  skills/  references/  knowledge/{concepts,systems,workflows,policies,how-to,references}/  knowledge/source/{raw,processed}/
  codebases/  docs/  scripts/

Example files to seed:
  ✅ agents/example-agent/AGENT.md
  ✅ agents/example-agent/context/working-context.md
  ✅ skills/example-skill/SKILL.md
  ✅ references/example-reference/example-reference.md
  ✅ knowledge/concepts/example-concept.md
  ✅ knowledge/systems/example-system.md
  ✅ knowledge/workflows/example-workflow.md
  ✅ knowledge/policies/example-policy.md
  ✅ knowledge/how-to/example-how-to.md
  ✅ knowledge/references/example-reference-note.md
  ✅ knowledge/source/raw/README.md
  ✅ knowledge/source/processed/README.md
  ✅ codebases/example-codebase/OVERVIEW.md
  ✅ codebases/example-codebase/architecture/{system-architecture,data-flow,component-diagram,tech-stack}.md
  ✅ codebases/example-codebase/modules/example-module/MODULE.md
  ✅ docs/example-guide.md
  ↷ scripts/example-script.sh  (already exists — will skip)
─────────────────────────────────────────────
```

Ask:
> **"Proceed with initialization? Reply YES to create, or NO to adjust."**

If **NO**, ask what to change and return to the relevant step.

---

### Step 5 — Create Directories

```bash
mkdir -p "<target-root>"/{agents,skills,references,docs,scripts}
mkdir -p "<target-root>"/agents/example-agent/context
mkdir -p "<target-root>"/skills/example-skill
mkdir -p "<target-root>"/references/example-reference
mkdir -p "<target-root>"/knowledge/{concepts,systems,workflows,policies,how-to,references}
mkdir -p "<target-root>"/knowledge/source/{raw,processed}
mkdir -p "<target-root>"/codebases/example-codebase/architecture
mkdir -p "<target-root>"/codebases/example-codebase/modules/example-module
```

---

### Step 6 — Seed Example Files

For each file that does **not** already exist, create it using the exact templates
in the **Example File Templates** section below. Set `last-updated` / `last_updated`
to today's date. After writing all files, run Step 7.

> Use the today's date in ISO format (`YYYY-MM-DD`) for every date field.

---

### Step 7 — Verify and Report

Verify every intended file exists:

```bash
find "<target-root>" -type f | sort
```

Then produce a summary:

```
✅ Workspace Initialized
─────────────────────────────────────────────
Target : ~/.codex/
Created: 20 file(s)   Skipped: 1 (already existed)

Next steps:
  • Copy skills/example-skill/ as a starting point for your own skill.
  • Run the aiws-validate-skill / aiws-validate-knowledge skills to confirm compliance.
  • Add real content and delete the example-* files you don't need.
─────────────────────────────────────────────
```

If any creation failed (permission denied, etc.), list the failure and the exact
manual command to fix it.

---

## Example File Templates

Use these verbatim (substituting today's date). Every template already satisfies
the repo's validation rules.

### `skills/example-skill/SKILL.md`

````markdown
---
name: "example-skill"
version: "1.0.0"
description: "Example skill demonstrating the required structure — replace with your own task instructions."
tags: ["example", "template"]
applies-to: ["any"]
author: "Your Name"
last-updated: "YYYY-MM-DD"
---

# Example Skill

## Purpose

Explain why this skill exists and what single task it helps the agent perform.
Replace this with your own purpose statement.

## Instructions

Write the concrete, imperative rules the agent must follow. Use "Always...",
"Never...", "Prefer...". Keep the skill focused on one task.

## Examples

Show a good example and a bad example so the agent can tell them apart.

## References

- Link to any supporting docs under `references/`.
````

### `agents/example-agent/AGENT.md`

````markdown
---
name: "Example Agent"
description: >
  Example agent persona demonstrating the required structure. Replace with your
  agent's personality, objective, and the rules and standards it follows.
---

# Example Agent

## Persona

Describe who this agent is and how it should behave.

## Goals

- List the primary goals of this agent.

## Skills

- `skills/example-skill/SKILL.md`

## Constraints

- List the hard rules this agent must always follow.
````

### `agents/example-agent/context/working-context.md`

````markdown
# Working Context — Example Agent

_Current focus areas, active sprint, and short-lived notes for this agent._

- **Current focus:** (replace me)
- **Active tasks:** (replace me)
````

### `references/example-reference/example-reference.md`

````markdown
# Example Reference

External standard, spec, or guide excerpt that skills can cite.
Replace with the actual reference content or a link summary.
````

### Knowledge Example Templates (per type)

Each knowledge folder is seeded with **one example that uses its type's specialized
body structure** — not a generic `## Summary` stub. The canonical body shape for
every type is defined authoritatively in
[`aiws-create-knowledge` → **Per-Type Body Templates**](../aiws-create-knowledge/SKILL.md);
the templates below mirror it. Keep the same front-matter schema across all types;
only the body sections change.

#### `knowledge/concepts/example-concept.md` — `type: concept`

````markdown
---
title: "Example Concept"
type: "concept"
owner: "Your Name"
status: "active"
last_updated: "YYYY-MM-DD"
tags:
  - "concept"
  - "example"
---

## Summary

One-paragraph definition of the concept. Replace with your own.

## Why It Matters

- Why the concept is important.

## Key Ideas

| Term | Meaning |
|---|---|
| ... | ... |

## Common Pitfalls

- Mistakes to avoid.

## See Also

- `<folder>/<related-entry>.md`
````

#### `knowledge/systems/example-system.md` — `type: system`

````markdown
---
title: "Example System"
type: "system"
owner: "Your Name"
status: "active"
last_updated: "YYYY-MM-DD"
tags:
  - "system"
  - "example"
---

## Summary

What the system/service is and does, in one paragraph.

## At a Glance

| Attribute | Value |
|---|---|
| Owner team | ... |
| Language / framework | ... |
| Datastore | ... |

## Responsibilities

- What this system owns and guarantees.

## Non-Responsibilities

- What it explicitly does **not** do.

## Key Endpoints

| Method | Path | Purpose |
|---|---|---|
| ... | ... | ... |

## Operational Notes

- Retries, secrets, runbooks, cross-links.
````

#### `knowledge/workflows/example-workflow.md` — `type: workflow`

````markdown
---
title: "Example Workflow"
type: "workflow"
owner: "Your Name"
status: "active"
last_updated: "YYYY-MM-DD"
tags:
  - "workflow"
  - "example"
---

## Summary

The process/decision flow this entry describes, in one paragraph.

## Roles

| Role | Responsibility |
|---|---|
| ... | ... |

## Process

1. **Step** — what happens.
2. **Step** — what happens next.

## Decision Flow

```
Trigger ──▶ Decision? ──Yes──▶ Path A
                       └─No───▶ Path B
```

## Exit Criteria

- How you know the process is complete.
````

#### `knowledge/policies/example-policy.md` — `type: policy`

````markdown
---
title: "Example Policy"
type: "policy"
owner: "Your Name"
status: "active"
last_updated: "YYYY-MM-DD"
tags:
  - "policy"
  - "example"
---

## Summary

What the policy governs and enforces, in one paragraph.

## Scope

Who/what this policy applies to.

## Rules

| # | Rule | Rationale |
|---|---|---|
| P1 | Something **must** / **must not** ... | Why |

## Enforcement

- How the rules are enforced.

## Exceptions

- How exceptions are requested, approved, and expired.
````

#### `knowledge/how-to/example-how-to.md` — `type: how-to`

````markdown
---
title: "Example How-To"
type: "how-to"
owner: "Your Name"
status: "active"
last_updated: "YYYY-MM-DD"
tags:
  - "how-to"
  - "example"
---

## Summary

The task this guide accomplishes, in one paragraph.

## Prerequisites

- Access, tools, or preconditions needed.

## Steps

1. **Do this** — with the exact command:
   ```bash
   command --example
   ```
2. **Then this** — next action.

## Verification

- How to confirm the task succeeded.

## Rollback

- How to undo the change if something goes wrong.
````

#### `knowledge/references/example-reference-note.md` — `type: reference`

````markdown
---
title: "Example Reference"
type: "reference"
owner: "Your Name"
status: "active"
last_updated: "YYYY-MM-DD"
tags:
  - "reference"
  - "example"
---

## Summary

What this lookup material covers and how to scan it, in one paragraph.

## Lookup Table

| Key | Name | When to Use |
|---|---|---|
| ... | ... | ... |

## Quick Rules

- Short, scannable rules of thumb.
````


### `knowledge/source/raw/README.md`

````markdown
# Source · Raw (Staging)

Drop unprocessed source files here (PDF, Word, PPT, Excel, Markdown, …). The
`aiws-raw-to-markdown` skill converts them to Markdown; `aiws-create-knowledge`
curates each into the correct taxonomy folder and moves the original into
`../processed/`. Files here are **not** authoritative.
````

### `knowledge/source/processed/README.md`

````markdown
# Source · Processed

Source files already curated into knowledge entries are moved here from `../raw/`,
so `raw/` only ever holds items still awaiting processing. Files here are **not**
authoritative — kept for provenance.
````

### `codebases/example-codebase/OVERVIEW.md`

````markdown
# Example Codebase — Overview

- **Purpose:** What this project does.
- **Tech stack:** Languages, frameworks, datastores.
- **High-level architecture:** One-paragraph summary; see `architecture/`.

Replace with your real project details.
````

### `codebases/example-codebase/architecture/*.md`

Create four files — `system-architecture.md`, `data-flow.md`,
`component-diagram.md`, `tech-stack.md` — each with a heading and a one-line
placeholder, e.g.:

````markdown
# System Architecture

Describe the system's major components and how they interact. Replace me.
````

### `codebases/example-codebase/modules/example-module/MODULE.md`

````markdown
# Example Module

- **Responsibility:** What this module owns.
- **Key files / entrypoints:** (replace me)
- **Dependencies:** (replace me)
````

### `docs/example-guide.md`

````markdown
# Example Guide

A how-to guide for contributors. Replace with real meta-documentation
(contributing steps, conventions, versioning, etc.).
````

### `scripts/example-script.sh`

````bash
#!/usr/bin/env bash
# example-script.sh
# Usage: bash scripts/example-script.sh
#
# Describe what this script does. Replace with your own automation.

echo "example-script.sh: completed successfully"
exit 0
````

---

## Standards Enforced by This Skill

| Item | Rule Applied |
|---|---|
| Folder names | `kebab-case` (e.g., `example-skill`, `example-agent`) |
| Primary files | `UPPERCASE.md` (`SKILL.md`, `AGENT.md`, `OVERVIEW.md`, `MODULE.md`) |
| Skill front-matter | `name`, `version`, `description`, `tags`, `applies-to`, `author`, `last-updated` |
| Knowledge front-matter | `title`, `type`, `owner`, `status`, `last_updated`, `tags` — `type` matches its folder |
| Knowledge body | Matches its type's **Per-Type Body Template** (defined in `aiws-create-knowledge`) |
| Skill sections | `## Purpose`, `## Instructions` (required); `## Examples`, `## References` |
| Agent sections | `## Persona`, `## Goals`, `## Skills`, `## Constraints` |
| Scripts | `#!/usr/bin/env bash` shebang + descriptive comment; `kebab-case.sh` |
| Dates | ISO `YYYY-MM-DD` |

---

## Examples

### Example 1 — Initialize a New Project Workspace

**User:** "Initialize the agent workspace in my project at `/home/alice/projects/api`."

1. Target → Project → `/home/alice/projects/api/.codex/`
2. Detect existing structure (all missing)
3. Show plan → user confirms **YES**
4. Create all folders + seed every `example-*` file
5. Verify with `find` → report ✅ (20 files created)

---

### Example 2 — Initialize Global Workspace (Partial)

**User:** "Set up the Codex folders globally."

1. Target → Global → `~/.codex/`
2. Detect existing structure → `skills/` already exists
3. Plan shows `skills/example-skill/SKILL.md` as `↷ skipped`; everything else created
4. Confirm → create missing folders/files → verify → report ✅ (with skip noted)

---

### Example 3 — Re-run Is Safe

**User:** "Run workspace init again."

1. Detect structure → all example files already exist
2. Plan shows every file as `↷ skipped`
3. Confirm → nothing overwritten → report `✅ Already initialized — 0 files changed.`

---

## References
- Every folder, file, and template this skill scaffolds is defined inline in the
  **Target Structure Reference** and **Example File Templates** sections above.
- [Validate Skill](../aiws-validate-skill/SKILL.md)
- [Validate Knowledge](../aiws-validate-knowledge/SKILL.md)
