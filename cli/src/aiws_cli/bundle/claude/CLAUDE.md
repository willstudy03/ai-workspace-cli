# CLAUDE.md

Project memory for **ai-workspace** — a centralized workspace for AI agent
definitions, reusable **skills**, and curated **knowledge**. This file tells Claude
Code how to behave in this repo: which built-in skills exist, **when** and **how**
to use them, and the rules for managing skills and knowledge.

> Everything Claude Code loads lives under **`.claude/`**. Built-in skills are in
> [`.claude/skills/`](./.claude/skills/) and are named with the `aiws-` prefix.
> Claude Code auto-discovers them; this file governs how they are routed and combined.
>
> (For GitHub Copilot the same layout lives under `.github/` instead of `.claude/`.)

---

## 🥇 Golden Rule — Knowledge & Skills First

**Before answering any question or starting any task, ALWAYS consult local
knowledge and skills before falling back to general/training knowledge.**

On every user request, follow this order:

1. **Check `.claude/knowledge/` first.** If the question is about an internal concept,
   system, policy, workflow, how-to, or reference, use **`aiws-ask-knowledge`** to
   retrieve a grounded, cited answer. Never answer internal/project questions from
   memory when a curated entry may exist.
2. **Check `.claude/codebases/` for project context.** If the question is about a specific
   project's architecture, modules, or conventions, read the relevant
   `.claude/codebases/<slug>/` docs before reasoning.
3. **Route to a built-in skill.** Match the intent to a skill in the catalog below
   and use it. Do not hand-roll a workflow that a skill already defines.
4. **Only then use general knowledge** — and when you do, **say so explicitly** and
   label it as not sourced from the knowledge base.
5. **If knowledge is missing, say so.** Never fabricate. Offer to capture the answer
   as a new knowledge entry (see the ingestion pipeline).

> Precedence when sources conflict: `.claude/knowledge/` (curated) →
> `.claude/codebases/` docs → general knowledge. `.claude/knowledge/raw/` is
> **staging only** — never authoritative, never cited.

---

## 🧩 Built-in Skills Catalog

All skills are in `.claude/skills/<name>/SKILL.md`. Invoke by matching intent to the
"Use when" column.

| Skill | Use when… | Produces | Safety |
|---|---|---|---|
| **`aiws-ask-knowledge`** | User asks a question that should be answered from documented `.claude/knowledge/` ("what do we know about…", "check the knowledge base", "grounded answer") | A cited answer + explicit gaps | Read-only |
| **`aiws-codebase-analyst`** | An unfamiliar/undocumented codebase needs structured docs ("analyse this codebase", "document this repo") | `.claude/codebases/<slug>/` architecture, modules, patterns, `metadata.json` | **Docs only — never code** |
| **`aiws-raw-to-markdown`** | Non-Markdown files (PDF/Word/PPT/Excel/image/audio/HTML) are dropped in `.claude/knowledge/raw/` and need converting | Markdown written back into `.claude/knowledge/raw/` | Writes to `raw/` only |
| **`aiws-create-knowledge`** | Raw Markdown in `.claude/knowledge/raw/` must be curated into proper entries ("curate knowledge", "process the raw notes") | Standards-compliant entries filed into the taxonomy | Writes entries; non-destructive to raw |
| **`aiws-validate-knowledge`** | New/changed `.claude/knowledge/` files need checking ("validate knowledge", "is this entry correct") | Pass/fail report + fixes | Read-only |
| **`aiws-create-skill`** | User wants to author a new reusable skill ("create a skill", "new SKILL.md") | A standards-compliant `SKILL.md` | Writes one skill |
| **`aiws-validate-skill`** | New/changed skills, agents, scripts, references, or codebase docs need checking ("validate my changes", "check my new files") | Pass/fail report + fixes | Read-only |
| **`aiws-install-skill`** | User wants to install a skill/agent/script/reference into `~/.claude/` (global) or a project `.claude/` | Copied files + dependencies | Writes to target |
| **`aiws-install-knowledge`** | User wants to install knowledge entries into `~/.claude/knowledge/` (global) or a project `.claude/knowledge/` | Copied entries + `related` links | Writes to target |
| **`aiws-workspace-init`** | A new workspace needs the canonical folder structure ("init workspace", "scaffold workspace") | Full folder tree under `.claude/` (or `~/.claude/`) + example files | Creates folders/examples |

---

## 🔀 Intent → Skill Routing

- "What is X / how does our X work / what's our policy on Y?" → **`aiws-ask-knowledge`**
- "Understand / document this codebase" → **`aiws-codebase-analyst`**
- "I dropped a PDF/Doc in raw" → **`aiws-raw-to-markdown`** → then **`aiws-create-knowledge`**
- "Turn these raw notes into knowledge" → **`aiws-create-knowledge`** → then **`aiws-validate-knowledge`**
- "Make a new skill" → **`aiws-create-skill`** → then **`aiws-validate-skill`**
- "Install this skill/knowledge somewhere" → **`aiws-install-skill`** / **`aiws-install-knowledge`**
- "Set up a fresh workspace" → **`aiws-workspace-init`**

### Standard pipelines (chain skills in order)

```
Knowledge ingestion:
  .claude/knowledge/raw/ (binary)
     └─(aiws-raw-to-markdown)─▶ .claude/knowledge/raw/ (markdown)
            └─(aiws-create-knowledge)─▶ .claude/knowledge/{concepts|systems|workflows|policies|how-to|references}
                   └─(aiws-validate-knowledge)─▶ pass/fail

Skill authoring:
  aiws-create-skill ─▶ aiws-validate-skill ─▶ (optional) aiws-install-skill

Knowledge consumption:
  any question ─▶ aiws-ask-knowledge (grounded + cited)
```

---

## 📚 Knowledge Management Rules

The `.claude/knowledge/` layer is the single source of truth for durable, curated notes.

**Taxonomy (a file's folder MUST match its `type`):**

| Folder | `type` | Holds |
|---|---|---|
| `.claude/knowledge/concepts/` | `concept` | Definitions, "what is / how does X work" |
| `.claude/knowledge/systems/` | `system` | Internal services/systems |
| `.claude/knowledge/workflows/` | `workflow` | Multi-step processes |
| `.claude/knowledge/policies/` | `policy` | Rules, standards, must/should |
| `.claude/knowledge/how-to/` | `how-to` | Task-oriented guides |
| `.claude/knowledge/references/` | `reference` | Lookup tables, specs, cheat-sheets |
| `.claude/knowledge/raw/` | — | **Staging only.** Unprocessed, never cited |

**Rules:**

1. **Answer from knowledge, cite the source.** Use `aiws-ask-knowledge`; every
   factual claim must trace to a specific entry, listed by file path.
2. **No fabrication.** If the knowledge base is silent, say so — don't invent.
3. **`raw/` is never authoritative.** Treat it as unverified staging; convert
   (`aiws-raw-to-markdown`) and curate (`aiws-create-knowledge`) before use.
4. **Curate one file at a time.** Never batch-curate raw notes; preserve full
   content and context.
5. **Respect `status`.** Prefer `active`; flag `deprecated`; mark `draft` as
   provisional.
6. **Keep `related` links consistent.** When installing/moving entries, carry over
   cross-linked `related` entries.
7. **Validate before considering it done.** Run `aiws-validate-knowledge` on any new
   or changed entry (correct folder, `type`↔folder match, filename casing,
   front-matter, body structure).
8. **Filing to the wrong folder or mismatching `type` is a defect** — fix, don't ship.

---

## 🛠️ Skill Management Rules

Skills are reusable instruction files. All skills live under `.claude/skills/`;
built-in workspace skills use the `aiws-` prefix.

1. **Author with the skill, not by hand.** Use `aiws-create-skill` so new skills are
   clarified, researched against existing `.claude/knowledge/` + `.claude/skills/`,
   and standards-compliant.
2. **Search before creating.** Check `.claude/skills/` for an existing skill (or a
   reusable pattern) before authoring a new one — avoid duplicates.
3. **Naming & location.**
   - Folder is `kebab-case`; built-in workspace skills use the `aiws-` prefix.
   - The folder name MUST equal the front-matter `name`.
   - Primary file is `SKILL.md` (all uppercase).
   - Path: `.claude/skills/<name>/SKILL.md`.
4. **Front-matter standard (Claude Code).** Required: `name`, `description`.
   Retained metadata (optional, safely ignored by Claude Code but kept for the repo):
   `tags`, `applies-to`, `author`, `last-updated`.
5. **Every skill needs a clear `## When to Use` (triggers) and `## Instructions`.**
6. **Validate before considering it done.** Run `aiws-validate-skill` on any new or
   changed skill/agent/script/reference/codebase doc.
7. **Distribute deliberately.** Use `aiws-install-skill` to copy a skill (and its
   dependencies) into `~/.claude/` (global) or a project `.claude/`.

---

## 🚧 Guardrails

- **Read-only skills never write:** `aiws-ask-knowledge`, `aiws-validate-knowledge`,
  `aiws-validate-skill`. Do not let them create/edit/delete files.
- **`aiws-codebase-analyst` produces documentation only — never application code.**
- **`aiws-create-knowledge` is non-destructive:** don't delete a raw file until the
  curated entry is confirmed.
- **Prefer chaining skills** over improvising; follow the pipelines above.
- **Ask when required inputs are missing** (owner, sources, target location) instead
  of guessing — but otherwise take action.

---

## 🗂️ Directory Map

After `aiws-workspace-init`, **all workspace folders live under `.claude/`**
(project scope) — or under `~/.claude/` for a global install:

```
<project-root>/
├── CLAUDE.md                     ← Project memory (this file)
└── .claude/                      ← Everything Claude Code loads lives here
    ├── skills/                   ← Built-in aiws-* skills + your own skills
    │   ├── aiws-ask-knowledge/
    │   ├── aiws-create-knowledge/
    │   └── …                     ← 10 built-in aiws-* skills
    ├── knowledge/                ← Curated notes + raw/ staging
    │   ├── concepts/   systems/    workflows/
    │   ├── policies/   how-to/     references/
    │   └── raw/                   ← staging only (never cited)
    ├── agents/                   ← Agent persona definitions
    ├── codebases/                ← Per-project documentation (aiws-codebase-analyst)
    ├── references/               ← External specs/standards referenced by skills
    ├── scripts/                  ← Helper scripts
    └── docs/                     ← Contributing, standards, guides
```



