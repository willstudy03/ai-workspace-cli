---
name: "aiws-install-knowledge"
description: "Guides users through installing knowledge entries (concepts, systems, workflows, policies, how-tos, references) from the agent-skills repo's knowledge/ layer into their global Claude Code configuration (~/.claude/knowledge/) or a project-based .claude/knowledge/ folder, resolving related cross-linked entries and syncing with the tracked upstream branch first (if configured)."
tags: ["install", "setup", "claude", "knowledge", "documentation"]
applies-to: ["agent-skills repo"]
author: "William Theo (IT RDI IM TD)"
last-updated: "2026-07-20"
---

# Install Knowledge

Installs knowledge entries from this repository's `knowledge/` layer into a user's
global Claude Code configuration or a project-specific `.claude/` folder. Automatically
resolves and copies every cross-linked entry declared in each entry's `related`
front-matter field so the installed knowledge stays internally consistent.

## When to Use

Trigger phrases: "install knowledge", "install knowledge entry", "add knowledge to my project",
"install concept", "install policy", "install workflow", "set up knowledge base",
"install into my project", "add knowledge to global Claude Code", "install knowledge globally"

---

## Purpose

The `knowledge/` layer is a taxonomy of durable, curated notes (concepts, systems,
workflows, policies, how-tos, and references) that AI agents and humans look up.
After cloning this repository, users need a way to activate individual knowledge
entries in their own Claude Code environment — either globally (available across all
projects) or scoped to a single project.

This skill guides the full installation flow: clarifying intent, syncing with the
latest source, resolving all cross-linked (`related`) entries, and copying every
file into the correct target location while preserving the taxonomy folder layout.

---

## Knowledge Taxonomy Reference

Every knowledge entry lives in the folder that matches its `type`:

| Folder | Purpose | `type` |
|---|---|---|
| `knowledge/concepts/` | General ideas and explanations | `concept` |
| `knowledge/systems/` | Concrete systems, services, or products | `system` |
| `knowledge/workflows/` | Processes and decision flows | `workflow` |
| `knowledge/policies/` | Rules, requirements, and governance | `policy` |
| `knowledge/how-to/` | Instructional, step-by-step task guidance | `how-to` |
| `knowledge/references/` | Lookup material — cheatsheets, checklists, definitions | `reference` |
| `knowledge/source/raw/` | Uncurated staging area (not authoritative) | — |

> **Note:** `knowledge/references/` is the knowledge layer's own lookup material.
> It is **not** the same as the repo-root `references/` folder (external specs cited
> by skills). Never mix the two.

---

## Instructions

### Step 1 — Clarify What to Install

Ask the user which knowledge entry (or entries) they want to install. Present the
currently available entries grouped by type by listing the taxonomy folders:

```bash
# Run from the agent-skills repo root
for d in concepts systems workflows policies how-to references; do
  echo "=== ${d} ==="
  ls "knowledge/${d}/" 2>/dev/null | grep -v '^README.md$'
done
```

Display the results in a clean grouped list:

```
📚 Available Knowledge Entries

Concepts:
  - example-idempotency.md

Systems:
  - example-payment-service.md

Workflows:
  - example-incident-response.md

Policies:
  - example-secret-management.md

How-To:
  - example-rotate-api-keys.md

References:
  - example-http-status-codes.md
```

Ask:
> **"Which knowledge entry (or entries) would you like to install? You can name
> multiple (e.g., 'idempotency and incident-response'), or say 'all concepts'."**

Wait for the user's answer before continuing.

---

### Step 2 — Clarify Installation Target

Ask the user where they want to install the selected entry (or entries):

> **"Where would you like to install?**
>
> - **[G] Global** — Available across all projects. Files will go into
>   `~/.claude/knowledge/` so Claude Code can discover them system-wide.
> - **[P] Project** — Available only for one specific project. Files will go into
>   the project's `.claude/knowledge/` folder.
>
> Reply with **G** for global or **P** for project."

Wait for the user's answer before continuing.

---

### Step 3 — Prepare the Target Directory

#### 3A — Global Installation

1. Identify the user's home directory:

```bash
echo "$HOME"
```

2. Construct the global target root: `$HOME/.claude/knowledge`

3. Check whether it already exists:

```bash
ls -la "$HOME/.claude/knowledge" 2>/dev/null || echo "NOT_FOUND"
```

4. If it does **not** exist, create it:

```bash
mkdir -p "$HOME/.claude/knowledge"
echo "Created ~/.claude/knowledge"
```

5. Confirm to the user:
> ✅ Global target directory ready: `~/.claude/knowledge/`

---

#### 3B — Project Installation

1. Ask the user for the full path to their project directory:
> **"Please provide the absolute path to your project directory
> (e.g., `/home/user/projects/my-app` or `C:\Users\me\projects\my-app`)."**

2. Verify the directory exists:

```bash
ls "<project-dir>" 2>/dev/null || echo "NOT_FOUND"
```

If `NOT_FOUND`, report the error and ask the user to re-enter the path.

3. Check whether `.claude/knowledge/` exists inside the project:

```bash
ls "<project-dir>/.claude/knowledge" 2>/dev/null || echo "NOT_FOUND"
```

4. If it does **not** exist, create it:

```bash
mkdir -p "<project-dir>/.claude/knowledge"
echo "Created .claude/knowledge/ in project"
```

5. Confirm to the user:
> ✅ Project target directory ready: `<project-dir>/.claude/knowledge/`

---

### Step 4 — Sync with the Tracked Upstream (Optional)

Before installing, optionally refresh the source from the **tracked upstream repo**
recorded during `aiws init`. There is **no default remote or branch** — syncing only
happens when an upstream is explicitly configured. The workspace config lives at
`<workspace>/.aiws/config.toml`:

```toml
upstream_repo = "..."   # blank or absent → no upstream is tracked
upstream_ref  = "..."   # the dedicated branch to pull from
```

1. Read the tracked upstream (if any):

```bash
cat .aiws/config.toml 2>/dev/null || echo "NO_AIWS_CONFIG"
```

2. Decide based on `upstream_repo`:

- **Blank / absent** → **Skip syncing.** Install from the local copy as-is.
  Report: `ℹ No upstream tracked — installing from the local copy.`
- **Set** → Fetch and check out the **dedicated branch** named in `upstream_ref`
  (never a hardcoded `main`/`master`):

  ```bash
  cd "<repo-root>"
  git fetch "<upstream_repo>" "<upstream_ref>"
  git checkout "<upstream_ref>"
  git pull "<upstream_repo>" "<upstream_ref>"
  ```

3. Report the outcome:
- **Up to date** → `✅ Already at the latest version of <upstream_ref>.`
- **Updated** → `✅ Pulled latest changes from <upstream_repo> (<upstream_ref>). (<N> new commits)`
- **Fetch fails** (no network / wrong remote) → Report the error and ask the user
  whether to proceed with the current local copy or abort. Default to proceeding.

---

### Step 5 — Resolve Cross-Linked Dependencies

Knowledge entries can reference each other via the `related` front-matter field.
For each entry the user wants to install, resolve **all cross-linked entries** so
the installed set stays internally consistent.

#### 5.1 Dependency Discovery Rules

For every selected entry (`knowledge/<type-folder>/<entry>.md`):

1. Read the file's YAML front-matter.
2. Parse the `related:` list. Each item is a relative path from the `knowledge/`
   root, e.g. `policies/example-secret-management.md`.
3. For each related path, add `knowledge/<related-path>` to the manifest.
4. Recurse: read each newly added entry and repeat, following its `related` links.
5. Also scan the entry body for inline Markdown links pointing into `knowledge/`
   and include those targets.
6. Deduplicate. Stop when no new entries are discovered (guard against cycles by
   tracking already-visited paths).

> Entries under `knowledge/source/raw/` are **uncurated** — never auto-install them as a
> dependency. If a selected entry links to a `source/raw/` file, warn the user and skip it.

#### 5.2 Build the File Manifest

Compile all resolved paths into a **File Manifest** — every source file and its
intended destination. The destination preserves the taxonomy subfolder.

```
INSTALL MANIFEST — knowledge/concepts/example-idempotency.md
──────────────────────────────────────────────────────────────
Source                                            → Destination
knowledge/concepts/example-idempotency.md         → <target>/knowledge/concepts/example-idempotency.md
knowledge/policies/example-secret-management.md    → <target>/knowledge/policies/example-secret-management.md
```

---

### Step 6 — Present Installation Plan and Confirm

Before executing any file operations, show the user the full plan:

```
📋 Installation Plan
─────────────────────────────────────────────
Installing : knowledge/concepts/example-idempotency.md
Target     : ~/.claude/knowledge/  (Global)

Files to copy:
  ✅ knowledge/concepts/example-idempotency.md
     → ~/.claude/knowledge/concepts/example-idempotency.md

  ✅ knowledge/policies/example-secret-management.md   (related)
     → ~/.claude/knowledge/policies/example-secret-management.md

Directories to create (if not existing):
  ~/.claude/knowledge/concepts/
  ~/.claude/knowledge/policies/
─────────────────────────────────────────────
Total: 2 file(s)  (1 selected + 1 related)
```

Ask:
> **"Does this look correct? Reply YES to proceed or NO to cancel."**

If the user says **NO**, ask what they would like to change and return to the
relevant step.

---

### Step 7 — Execute Installation

Once the user confirms, execute the installation.

#### 7.1 Create Directories

For every required directory in the manifest:

```bash
mkdir -p "<target-directory>"
```

#### 7.2 Copy Files

For each file in the manifest:

```bash
cp "<repo-root>/<source-file>" "<target-root>/<dest-file>"
```

> If a `cp` fails (permission denied, path not found, etc.), report the specific
> error and provide the exact manual command the user can run themselves.

#### 7.3 Verify Installation

After all copies, verify each file is present at its target:

```bash
ls -la "<target-root>/<dest-file>"
```

- ✅ **Found** — file copied successfully
- ❌ **Missing** — copy failed; report the exact path and the manual copy command

---

### Step 8 — Post-Installation Summary

Present a final summary of all outcomes:

```
✅ Installation Complete
─────────────────────────────────────────────
Installed : knowledge/concepts/example-idempotency.md  (+1 related)
Target    : ~/.claude/knowledge/

Files installed:
  ✅ ~/.claude/knowledge/concepts/example-idempotency.md
  ✅ ~/.claude/knowledge/policies/example-secret-management.md

How to use:
  Claude Code will now discover the installed knowledge entries. Ask a question that
  matches the entry's topic (e.g., "how do we handle idempotency?") and the agent
  can look up the installed note.
─────────────────────────────────────────────
```

If any files failed, show both successes and failures:

```
⚠️ Installation Completed with Errors
─────────────────────────────────────────────
  ✅ ~/.claude/knowledge/concepts/example-idempotency.md
  ❌ ~/.claude/knowledge/policies/example-secret-management.md
     Reason: Permission denied
     Fix:    Run manually →
             cp "<repo-root>/knowledge/policies/example-secret-management.md" \
                "~/.claude/knowledge/policies/example-secret-management.md"
─────────────────────────────────────────────
```

---

## Target Directory Structure Reference

### Global Install (`~/.claude/knowledge/`)

```
~/.claude/knowledge/
├── concepts/
│   └── <entry>.md
├── systems/
│   └── <entry>.md
├── workflows/
│   └── <entry>.md
├── policies/
│   └── <entry>.md
├── how-to/
│   └── <entry>.md
└── references/
    └── <entry>.md
```

### Project Install (`<project-dir>/.claude/knowledge/`)

```
<project-dir>/
└── .claude/
    └── knowledge/
        ├── concepts/
        │   └── <entry>.md
        ├── systems/
        │   └── <entry>.md
        ├── workflows/
        │   └── <entry>.md
        ├── policies/
        │   └── <entry>.md
        ├── how-to/
        │   └── <entry>.md
        └── references/
            └── <entry>.md
```

---

## Examples

### Example 1 — Install a Single Concept Globally

**User:** "Install the idempotency concept globally."

1. Identify: `knowledge/concepts/example-idempotency.md` → global target `~/.claude/knowledge/`
2. Sync with the tracked upstream branch (if configured)
3. Resolve `related` links → e.g. `policies/example-secret-management.md`
4. Show plan → user confirms **YES**
5. Create dirs: `~/.claude/knowledge/concepts/`, `~/.claude/knowledge/policies/`
6. Copy files → verify → report ✅

---

### Example 2 — Install a Workflow into a Project

**User:** "Install the incident-response workflow into my project at `/home/alice/projects/my-api`."

1. Identify: `knowledge/workflows/example-incident-response.md` → project target `/home/alice/projects/my-api/.claude/knowledge/`
2. Sync with the tracked upstream branch (if configured)
3. Resolve all `related` entries recursively
4. Show full plan → user confirms **YES**
5. Create all necessary dirs under `.claude/knowledge/`
6. Copy all files → verify → report ✅

---

### Example 3 — Install All Policies

**User:** "Install all policy entries globally."

1. Identify: every `.md` under `knowledge/policies/` (excluding `README.md`)
2. Sync with the tracked upstream branch (if configured)
3. Resolve each entry's `related` links
4. Show plan → user confirms → copy → report ✅

---

## References
- The knowledge taxonomy this skill installs into is described inline in this skill.
- [Install Skill](../aiws-install-skill/SKILL.md)
- [Validate Knowledge](../aiws-validate-knowledge/SKILL.md)
