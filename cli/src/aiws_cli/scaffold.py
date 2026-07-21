"""Native, deterministic workspace scaffolding — the Python implementation of the
``aiws-workspace-init`` skill.

Creating the folder tree directly (instead of asking the launched AI agent to do
it) means the user never has to approve dozens of individual file-write actions.
It is **additive and idempotent**: existing files are never overwritten unless
``overwrite=True``; missing files are created.

The structure and templates mirror ``aiws-workspace-init/SKILL.md`` exactly, so the
result passes ``aiws-validate-skill`` and ``aiws-validate-knowledge``.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

# ── Templates (mirror aiws-workspace-init/SKILL.md; {date} is substituted) ─────

_SKILL = """\
---
name: "example-skill"
version: "1.0.0"
description: "Example skill demonstrating the required structure — replace with your own task instructions."
tags: ["example", "template"]
applies-to: ["any"]
author: "Your Name"
last-updated: "{date}"
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
"""

_AGENT = """\
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
"""

_WORKING_CONTEXT = """\
# Working Context — Example Agent

_Current focus areas, active sprint, and short-lived notes for this agent._

- **Current focus:** (replace me)
- **Active tasks:** (replace me)
"""

_REFERENCE = """\
# Example Reference

External standard, spec, or guide excerpt that skills can cite.
Replace with the actual reference content or a link summary.
"""

_CONCEPT = """\
---
title: "Example Concept"
type: "concept"
owner: "Your Name"
status: "active"
last_updated: "{date}"
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
"""

_SYSTEM = """\
---
title: "Example System"
type: "system"
owner: "Your Name"
status: "active"
last_updated: "{date}"
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
"""

_WORKFLOW = """\
---
title: "Example Workflow"
type: "workflow"
owner: "Your Name"
status: "active"
last_updated: "{date}"
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
Trigger --> Decision? --Yes--> Path A
                       --No--> Path B
```

## Exit Criteria

- How you know the process is complete.
"""

_POLICY = """\
---
title: "Example Policy"
type: "policy"
owner: "Your Name"
status: "active"
last_updated: "{date}"
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
"""

_HOWTO = """\
---
title: "Example How-To"
type: "how-to"
owner: "Your Name"
status: "active"
last_updated: "{date}"
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
"""

_REFERENCE_NOTE = """\
---
title: "Example Reference"
type: "reference"
owner: "Your Name"
status: "active"
last_updated: "{date}"
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
"""

_RAW_README = """\
# Raw (Staging)

Uncurated staging area. Drop draft or unprocessed notes here, then promote them
into the correct taxonomy folder once cleaned up. Files here are **not** authoritative.
"""

_OVERVIEW = """\
# Example Codebase — Overview

- **Purpose:** What this project does.
- **Tech stack:** Languages, frameworks, datastores.
- **High-level architecture:** One-paragraph summary; see `architecture/`.

Replace with your real project details.
"""

_ARCH_SYSTEM = """\
# System Architecture

Describe the system's major components and how they interact. Replace me.
"""

_ARCH_DATAFLOW = """\
# Data Flow

Describe how data moves through the system end to end. Replace me.
"""

_ARCH_COMPONENT = """\
# Component Diagram

Describe the components and their relationships. Replace me.
"""

_ARCH_TECHSTACK = """\
# Tech Stack

List the languages, frameworks, datastores, and key libraries. Replace me.
"""

_MODULE = """\
# Example Module

- **Responsibility:** What this module owns.
- **Key files / entrypoints:** (replace me)
- **Dependencies:** (replace me)
"""

_GUIDE = """\
# Example Guide

A how-to guide for contributors. Replace with real meta-documentation
(contributing steps, conventions, versioning, etc.).
"""

_SCRIPT = """\
#!/usr/bin/env bash
# example-script.sh
# Usage: bash scripts/example-script.sh
#
# Describe what this script does. Replace with your own automation.

echo "example-script.sh: completed successfully"
exit 0
"""


def _file_map(today: str) -> dict[str, str]:
    """Return {relative_path: content} for every seeded example file."""
    return {
        "agents/example-agent/AGENT.md": _AGENT,
        "agents/example-agent/context/working-context.md": _WORKING_CONTEXT,
        "skills/example-skill/SKILL.md": _SKILL.format(date=today),
        "references/example-reference/example-reference.md": _REFERENCE,
        "knowledge/concepts/example-concept.md": _CONCEPT.format(date=today),
        "knowledge/systems/example-system.md": _SYSTEM.format(date=today),
        "knowledge/workflows/example-workflow.md": _WORKFLOW.format(date=today),
        "knowledge/policies/example-policy.md": _POLICY.format(date=today),
        "knowledge/how-to/example-how-to.md": _HOWTO.format(date=today),
        "knowledge/references/example-reference-note.md": _REFERENCE_NOTE.format(date=today),
        "knowledge/raw/README.md": _RAW_README,
        "codebases/example-codebase/OVERVIEW.md": _OVERVIEW,
        "codebases/example-codebase/architecture/system-architecture.md": _ARCH_SYSTEM,
        "codebases/example-codebase/architecture/data-flow.md": _ARCH_DATAFLOW,
        "codebases/example-codebase/architecture/component-diagram.md": _ARCH_COMPONENT,
        "codebases/example-codebase/architecture/tech-stack.md": _ARCH_TECHSTACK,
        "codebases/example-codebase/modules/example-module/MODULE.md": _MODULE,
        "docs/example-guide.md": _GUIDE,
        "scripts/example-script.sh": _SCRIPT,
    }


def scaffold_workspace(
    root: Path, *, overwrite: bool = False, today: str | None = None
) -> list[str]:
    """Create the full workspace tree under ``root`` (e.g. ``<project>/.github``).

    Additive and idempotent: existing files are skipped unless ``overwrite``.
    Returns human-readable result lines.
    """
    today = today or date.today().isoformat()
    results: list[str] = []
    created = skipped = 0

    for rel, content in _file_map(today).items():
        dest = root / rel
        if dest.exists() and not overwrite:
            results.append(f"↷ skipped {rel} (already exists)")
            skipped += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        results.append(f"✓ {rel}")
        created += 1

    results.append(f"✓ Scaffold complete — {created} created, {skipped} skipped → {root}")
    return results

