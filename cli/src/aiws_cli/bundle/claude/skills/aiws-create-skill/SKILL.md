---
name: "aiws-create-skill"
description: "Interactive skill authoring workflow that creates new, standards-compliant SKILL.md files for this workspace — it clarifies the requirement, asks about unclear implementation steps and which tools (MCP/CLI) will be invoked, and first searches the knowledge/ and skills/ folders for reusable context before writing the skill."
tags: ["meta", "authoring", "skills", "scaffold", "standards"]
applies-to: ["agent-skills repo", "aiws workspace"]
author: ""
last-updated: "2026-07-20"
---

# AIWS Create Skill

Guides the creation of a new, **standards-compliant** skill for this AI workspace
(AIWS). It does not blindly generate a file — it first **clarifies the requirement**,
**asks about any unclear implementation step**, **asks which tools (MCP servers or
CLI commands) the skill will invoke**, and **researches the existing `knowledge/`
and `skills/` folders** for reusable context. Only then does it author the
`SKILL.md`, validate it against the repo rules, and report back.

## When to Use

Trigger phrases: "create a skill", "author a new skill", "aiws create skill",
"make a new SKILL.md", "help me write a skill", "scaffold a skill that follows the standard",
"build a skill for <task>", "new built-in skill"

Use this whenever the user wants to add a new capability to the workspace as a
reusable skill and wants it to conform to the repo's naming, front-matter, and
section standards.

---

## Purpose

Skills are only useful if they are **discoverable, consistent, and grounded**. A
skill written from a vague one-line request tends to be incomplete, non-compliant,
or duplicative of something that already exists.

This skill enforces a disciplined authoring workflow:
1. **Clarify** the goal, scope, and triggers before writing anything.
2. **Resolve ambiguity** — for every task step whose implementation is unclear, ask.
3. **Pin down tooling** — know exactly which MCP tools / CLI commands the skill relies on.
4. **Research first** — search `knowledge/` and `skills/` so the new skill reuses
   existing patterns, references, and terminology instead of reinventing them.
5. **Author to standard** — produce a `SKILL.md` that passes `aiws-validate-skill`.

---

## Standards This Skill Enforces

Every skill authored here must satisfy the repo rules (same as `aiws-validate-skill`):

**Location & naming**
- Path: `skills/<skill-name>/SKILL.md` or `.claude/skills/<skill-name>/SKILL.md`
- `<skill-name>` is `kebab-case`; the folder name must equal the front-matter `name`
- Primary file is `SKILL.md` (all uppercase)

**Required front-matter**
```yaml
---
name: "<kebab-case-name>"
version: "1.0.0"          # SemVer, no "v" prefix
description: "One sentence: what it provides and when to use it."
tags: ["lowercase", "no-spaces"]
applies-to: ["..."]
author: "<name>"
last-updated: "YYYY-MM-DD"
---
```

**Required sections:** `## Purpose`, `## Instructions`
**Recommended sections:** `## Examples`, `## References`, plus a `## When to Use`
(trigger phrases) block near the top.

---

## Instructions

Follow these phases in order. **Do not skip the clarification and research phases** —
they are the reason this skill exists. Ask questions **one focused topic at a time**.

### Phase 1 — Clarify the Requirement

Establish what the skill is for before anything else. If the user has not already
provided each item, ask for it:

1. **Objective** — What single task should the skill help the agent perform?
   (Keep it to one bounded task; if it's several tasks, propose splitting into
   multiple skills.)
2. **Trigger conditions** — When should the agent load/use it? What phrases signal it?
3. **Inputs & outputs** — What does the agent receive, and what should it produce?
4. **Scope boundaries** — What is explicitly out of scope?
5. **Proposed name** — Confirm a `kebab-case` name (folder + front-matter `name`).
6. **Location** — `.claude/skills/` (built-in, auto-loaded) or `skills/` (repo library).

Summarize your understanding back to the user in 2–3 lines and get a quick confirmation.

### Phase 2 — Clarify Unclear Implementation Steps

Draft the intended step-by-step workflow the skill will instruct the agent to
follow. For **every step whose implementation is ambiguous**, ask a targeted
question rather than assuming. Examples of things to pin down:

- Decision points ("If X, do we do A or B?")
- Ordering and dependencies between steps
- Edge cases and failure handling
- Required confirmations before destructive actions
- Expected output format / report shape

> Do not proceed to authoring while any step's behavior is unclear. Collect answers,
> then restate the finalized step list for confirmation.

### Phase 3 — Identify the Tools (MCP / CLI)

Determine exactly what the skill will invoke to do its work. Ask the user:

> **"Which tools will this skill use to perform its task?**
> - **MCP tools/servers** (e.g., a database MCP, a Jira/ADO MCP, a browser MCP) — name each and the operations needed.
> - **CLI commands** (e.g., `git`, `docker`, `kubectl`, `az`, a project script) — list the exact commands.
> - **None** — the skill is pure guidance/knowledge with no external calls."

For each tool, capture:
- Name / command
- The specific operations or subcommands used
- Required inputs, auth, or preconditions
- Failure handling (what to do if the tool is missing or errors)

Record these so the authored `## Instructions` reference the exact tool invocations.

### Phase 4 — Research Existing Workspace Knowledge & Skills

**Before writing the skill**, search the workspace so the new skill reuses existing
patterns, references, terminology, and tooling rather than duplicating them.

#### 4.1 Search the `knowledge/` layer

Look for concepts, systems, policies, workflows, how-tos, or references relevant to
the task:

```bash
# Replace <TERMS> with a regex of the task's key nouns/synonyms
grep -rniE "<term1|term2|term3>" knowledge/ --include="*.md" -l
grep -rniE "^(title|tags|type):" knowledge/ --include="*.md"
```

Read the promising entries. Note any that the new skill should **cite** in its
`## References`, or whose rules/definitions it must respect (e.g., a policy).

> If the `aiws-ask-knowledge` skill is available, prefer using it to pull grounded,
> cited context. Never fabricate domain facts — ground them in `knowledge/`.

#### 4.2 Search the `skills/` folders

Look for existing skills that solve a similar problem, share steps, or already wrap
the same tools:

```bash
grep -rniE "<term1|term2|tool-name>" skills/ .claude/skills/ --include="*.md" -l
ls skills/ .claude/skills/
```

For each relevant hit, decide:
- **Reuse** — reference the existing skill instead of duplicating it.
- **Pattern-match** — mirror its structure, phrasing, and report formats for consistency.
- **Extend/avoid overlap** — if it already covers the task, tell the user and ask
  whether to extend that skill instead of creating a new one.

#### 4.3 Consolidate Findings

Briefly report to the user what you found:
```
🔎 Research Summary
- Knowledge reused: knowledge/concepts/<x>.md (cited), knowledge/policies/<y>.md (must comply)
- Similar skills: skills/<z>/SKILL.md (mirroring its report format)
- Tools confirmed: <MCP/CLI list>
- No blocking duplication found.
```

### Phase 5 — Confirm the Authoring Plan

Present a concise plan before writing:

```
📋 Skill Authoring Plan
─────────────────────────────────────────────
Name       : <kebab-case-name>
Location   : .claude/skills/<name>/SKILL.md   (or skills/<name>/SKILL.md)
Objective  : <one line>
Triggers   : <phrases>
Tools       : <MCP/CLI or none>
Steps      : 1) ... 2) ... 3) ...
Reuses     : <knowledge/skill references>
─────────────────────────────────────────────
```

Ask:
> **"Shall I create the skill with this plan? Reply YES to author, or tell me what to adjust."**

### Phase 6 — Author the SKILL.md

On confirmation, create `<location>/<name>/SKILL.md` with:

- Front-matter per the **Standards** section (set `version` to `1.0.0`,
  `last-updated` to today's ISO date, `name` = folder name).
- `# Title`, then a `## When to Use` block with trigger phrases.
- `## Purpose` — why the skill exists and the problem it solves.
- `## Instructions` — the finalized, unambiguous steps from Phases 2–3, including
  the **exact MCP/CLI invocations** and their failure handling.
- `## Examples` — at least one good example (and a bad/anti-pattern where useful).
- `## References` — link the `knowledge/` entries and related skills found in Phase 4.

Write imperative, specific instructions ("Always…", "Never…", "If X then Y"). Use
comments/placeholders only where the user must fill in project-specific values.

### Phase 7 — Validate and Report

1. Self-check against the **Standards** section (folder/file casing, all required
   front-matter fields, required sections present, no unmodified TODO placeholders).
2. If the `aiws-validate-skill` skill is available, run its checks (or advise the user to).
3. Open the new file and give a short summary: what it does, its triggers, tools,
   and which knowledge/skills it reused. Suggest next steps (test it, or install it
   via `aiws-install-skill`).

---

## Examples

### ✅ Good — Full Authoring Flow

**User:** "Create a skill that opens merge requests in our GitLab via CLI."

1. **Clarify** — objective (open an MR from the current branch), triggers
   ("open an MR", "create merge request"), inputs (target branch, title),
   name `gitlab-open-mr`, location `.claude/skills/`.
2. **Steps** — ask: "Should it push the branch first if unpushed? What target
   branch is the default?" → user: "push if needed; default `main`."
3. **Tools** — CLI `glab` (`glab mr create`); handle `glab` not installed → instruct install.
4. **Research** — `grep` knowledge/ (no MR policy found), `skills/` (no existing
   GitLab skill) → no duplication.
5. **Plan → YES**.
6. Author `.claude/skills/gitlab-open-mr/SKILL.md` with exact `glab` commands.
7. Validate → open → summarize.

### ✅ Good — Detecting Duplication

**User:** "Make a skill to review Java code."

- Phase 4 finds `skills/code-review/SKILL.md` already covers this.
- Response: "A `code-review` skill already exists and handles Java. Do you want to
  extend it, or create a narrower skill (e.g., `java-null-safety-review`)?"

### ❌ Bad — What This Skill Must NOT Do

> ❌ Immediately writing a `SKILL.md` from a one-line request without clarifying
> steps, tools, or checking for existing knowledge/skills.

Forbidden. Always run Phases 1–4 first; skipping them produces incomplete,
non-compliant, or duplicate skills.

> ❌ Inventing domain facts in the skill body.

Ground any domain claims in `knowledge/`; if undocumented, ask the user or leave a
clearly marked placeholder — never fabricate.

---

## Quick Reference

| Phase | Goal | Key Question |
|---|---|---|
| 1 Clarify | Bound the task | "What single task, and when is it triggered?" |
| 2 Steps | Remove ambiguity | "For step N, do we do A or B?" |
| 3 Tools | Pin invocations | "Which MCP tools / CLI commands does it use?" |
| 4 Research | Reuse, avoid dupes | "What in knowledge/ and skills/ already helps?" |
| 5 Plan | Get sign-off | "Author with this plan? YES/adjust" |
| 6 Author | Write to standard | — |
| 7 Validate | Ensure compliance | "Does it pass aiws-validate-skill?" |

---

## References
- The skill naming, front-matter, and required-section standards are defined
  inline in this skill (see **Standards This Skill Enforces**).
- [Validate Skill](../aiws-validate-skill/SKILL.md)
- [Ask Knowledge](../aiws-ask-knowledge/SKILL.md)
- [Workspace Init](../aiws-workspace-init/SKILL.md)
