# ai-workspace
A portable, tool-agnostic **AI agent workspace** — one repository that gives
**Claude Code**, **GitHub Copilot**, and **OpenAI Codex** the same governance rules,
the same set of built-in **skills**, and the same curated **knowledge** structure.
Clone it, open it in your AI coding tool of choice, and that tool automatically loads
its instruction file plus the ten built-in `aiws-*` skills.
---
## What is this?
`ai-workspace` is the single source of truth for **how AI coding agents behave, what
workflows they follow, and what they know about your projects.** It ships:
- **Governance instructions** for three AI tools, each in that tool's native format.
- **Ten built-in `aiws-*` skills** (AIWS = *AI WorkSpace*) that manage knowledge,
  scaffold workspaces, author/validate skills, analyse codebases, and install
  content — replicated identically for each tool.
- A **canonical workspace layout** (`knowledge/`, `skills/`, `agents/`, `codebases/`,
  `references/`, `scripts/`, `docs/`) that the skills create and maintain.
### Supported tools
| Tool | Instruction file (auto-loaded) | Workspace root | Built-in skills |
|---|---|---|---|
| **Claude Code** | `CLAUDE.md` | `.claude/` | `.claude/skills/` |
| **GitHub Copilot** | `.github/copilot-instructions.md` | `.github/` | `.github/skills/` |
| **OpenAI Codex** | `AGENTS.md` | `.codex/` | `.codex/skills/` |
Each instruction file encodes the same **Golden Rule**, skill catalog, routing rules,
and guardrails — only the paths differ.
---
## The Golden Rule — Knowledge & Skills First
Every instruction file directs the agent to, on **every** request:
1. **Check the knowledge layer first** (`aiws-ask-knowledge`) — answer from curated,
   cited notes, never from memory when a documented entry may exist.
2. **Check codebase docs** for project-specific context.
3. **Route to a built-in skill** instead of hand-rolling a workflow.
4. **Only then use general knowledge** — and say so explicitly.
5. **Never fabricate** — if the knowledge base is silent, say so.
---
## Built-in Skills (`aiws-*`)
Ten skills, identical across `.claude/skills/`, `.github/skills/`, and `.codex/skills/`:
| Skill | What it does | Safety |
|---|---|---|
| **`aiws-ask-knowledge`** | Grounded, cited Q&A over the knowledge layer | Read-only |
| **`aiws-codebase-analyst`** | Turns a codebase into structured architecture/module docs | Docs only |
| **`aiws-raw-to-markdown`** | Converts PDFs/Office/images/etc. in `raw/` to Markdown (MarkItDown) | Writes `raw/` |
| **`aiws-create-knowledge`** | Curates raw Markdown into standards-compliant knowledge entries | Writes entries |
| **`aiws-validate-knowledge`** | Checks knowledge entries against taxonomy + front-matter rules | Read-only |
| **`aiws-create-skill`** | Interactive authoring of a new standards-compliant skill | Writes one skill |
| **`aiws-validate-skill`** | Checks skills/agents/refs/docs against structure + format rules | Read-only |
| **`aiws-install-skill`** | Installs a skill/agent/script/reference (global or project) | Writes target |
| **`aiws-install-knowledge`** | Installs knowledge entries with their `related` links | Writes target |
| **`aiws-workspace-init`** | Scaffolds the full workspace folder tree + examples | Creates folders |
### Standard pipelines
```
Knowledge ingestion:  raw file ─▶ aiws-raw-to-markdown ─▶ aiws-create-knowledge ─▶ aiws-validate-knowledge
Skill authoring:      aiws-create-skill ─▶ aiws-validate-skill ─▶ aiws-install-skill
Ask anything:         aiws-ask-knowledge  (grounded + cited)
```
---
## Core Concepts
### Knowledge layer
A taxonomy of durable, curated notes — the single source of truth agents cite. A
file's folder MUST match its `type`:
| Folder | `type` | Holds |
|---|---|---|
| `knowledge/concepts/` | `concept` | "What is / how does X work" |
| `knowledge/systems/` | `system` | Internal services/systems |
| `knowledge/workflows/` | `workflow` | Multi-step processes |
| `knowledge/policies/` | `policy` | Rules, standards |
| `knowledge/how-to/` | `how-to` | Task-oriented guides |
| `knowledge/references/` | `reference` | Specs, cheat-sheets |
| `knowledge/raw/` | — | **Staging only — never cited** |
### Skill
A self-contained `SKILL.md` (in its own `kebab-case` folder) that tells an agent how
to perform one task. Built-in workspace skills use the `aiws-` prefix.
### Codebase doc
Structured `codebases/<slug>/` documentation (architecture, modules, patterns) that
gives agents **project-aware** answers.
### Agent
An `agents/<role>/AGENT.md` persona defining goals, constraints, and the skills it uses.
---
## Getting Started
1. **Clone the repo** and open it in your AI tool:
   ```bash
   git clone <this-repo-url> ai-workspace
   cd ai-workspace
   ```
2. **Your tool auto-loads its instructions + built-in skills:**
   - Claude Code → `CLAUDE.md` + `.claude/skills/`
   - GitHub Copilot → `.github/copilot-instructions.md` + `.github/skills/`
   - OpenAI Codex → `AGENTS.md` + `.codex/skills/`
3. **Just ask** — describe your task naturally and the matching skill activates:
| Say to your agent | Skill that runs |
|---|---|
| *"Set up the workspace structure"* | `aiws-workspace-init` |
| *"What do we know about idempotency?"* | `aiws-ask-knowledge` |
| *"I dropped a PDF in raw — convert it"* | `aiws-raw-to-markdown` |
| *"Curate the notes in `raw/`"* | `aiws-create-knowledge` |
| *"Document this codebase"* | `aiws-codebase-analyst` |
| *"Create a skill for X"* | `aiws-create-skill` |
| *"Validate my new files"* | `aiws-validate-skill` / `aiws-validate-knowledge` |
| *"Install `aiws-codebase-analyst` into my project"* | `aiws-install-skill` |
Global installs land in `~/.claude/`, `~/.copilot/`, or `~/.codex/`; project installs
land in a project's `.claude/`, `.github/`, or `.codex/`.
---
## Repository Structure
```
ai-workspace/
├── README.md                       ← You are here
├── CLAUDE.md                       ← Claude Code instructions (Golden Rule + skill catalog)
├── AGENTS.md                       ← OpenAI Codex instructions
├── .github/
│   ├── copilot-instructions.md     ← GitHub Copilot instructions
│   └── skills/                     ← 10 built-in aiws-* skills
├── .claude/
│   └── skills/                     ← 10 built-in aiws-* skills
└── .codex/
    └── skills/                     ← 10 built-in aiws-* skills
```
> The `knowledge/`, `skills/`, `agents/`, `codebases/`, `references/`, `scripts/`, and
> `docs/` folders are the **canonical workspace layout** that `aiws-workspace-init`
> scaffolds under your chosen tool root (`.claude/`, `.github/`, or `.codex/`) — or a
> global root (`~/.claude/`, `~/.copilot/`, `~/.codex/`).
### Workspace layout (created by `aiws-workspace-init`)
```
<tool-root>/
├── skills/       ← Reusable skills (aiws-* built-ins + your own)
├── knowledge/    ← concepts/ systems/ workflows/ policies/ how-to/ references/ + raw/
├── agents/       ← Agent persona definitions
├── codebases/    ← Per-project architecture & module docs
├── references/   ← External specs/standards referenced by skills
├── scripts/      ← Helper scripts
└── docs/         ← Contributing, standards, guides
```
---
## Naming Conventions
| Thing | Convention | Example |
|---|---|---|
| Skill folder | `kebab-case` (built-ins use the `aiws-` prefix) | `aiws-ask-knowledge` |
| Agent role folder | `kebab-case` | `developer` |
| Codebase slug | `kebab-case` | `my-ecommerce-app` |
| Primary concept file | `UPPERCASE.md` | `SKILL.md`, `AGENT.md`, `OVERVIEW.md` |
| Knowledge entry `type` | must match its folder | `concept` ↔ `knowledge/concepts/` |
---
## Further Reading
- [`CLAUDE.md`](./CLAUDE.md) — Claude Code guidance
- [`AGENTS.md`](./AGENTS.md) — OpenAI Codex guidance
- [`.github/copilot-instructions.md`](./.github/copilot-instructions.md) — GitHub Copilot guidance
- A built-in skill, e.g. [`.claude/skills/aiws-workspace-init/SKILL.md`](./.claude/skills/aiws-workspace-init/SKILL.md)
