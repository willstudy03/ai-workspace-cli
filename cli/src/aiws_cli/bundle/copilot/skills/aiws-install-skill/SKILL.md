---
name: "aiws-install-skill"
version: "1.0.0"
description: "Guides users through installing skills, agents, scripts, or references from the agent-skills repo into their global Copilot configuration (~/.copilot/) or a project-based .github/ folder, including automatic dependency resolution and pre-install sync with the tracked upstream branch (if configured)."
tags: ["install", "setup", "copilot", "skills", "agents", "references"]
applies-to: ["agent-skills repo"]
author: "William Theo (IT RDI IM TD)"
last-updated: "2026-06-24"
---

# Install Skill

Installs skills, agents, scripts, or references from this repository into a user's
global Copilot configuration or a project-specific `.github/` folder. Automatically
resolves and copies all required dependencies (references, scripts, supporting docs).

## When to Use

Trigger phrases: "install skill", "install agent", "set up skill", "add skill to my project",
"install reference", "set up copilot skill", "how do I use this skill",
"install into my project", "add to global copilot", "install globally"

---

## Purpose

After cloning this repository, users need a way to activate individual skills, agents,
scripts, or references in their own Copilot environment — either globally (available
across all projects) or scoped to a single project. This skill guides the full
installation flow: clarifying intent, syncing with the latest source, resolving all
file dependencies, and copying everything into the correct target location.

---

## Instructions

### Step 1 — Clarify What to Install

Ask the user what they would like to install. Present the currently available items
grouped by type by listing the repo directories:

```bash
# Run from the agent-skills repo root
echo "=== Skills ===" && ls skills/
echo "=== Agents ===" && ls agents/
echo "=== References ===" && ls references/
echo "=== Scripts ===" && ls scripts/
```

Display the results to the user in a clean grouped list:

```
📦 Available Items

Skills:
  - backend-system-analysis
  - code-generation
  - code-review
  - unit-test-generation

Agents:
  - developer

References:
  - backend-system-design
  - code-review-java
  - java-code-standard
  - java-unit-test

Scripts:
  - (list .sh files under scripts/)
```

Ask:
> **"Which item(s) would you like to install? You can name multiple
> (e.g., 'code-review and unit-test-generation')."**

Wait for the user's answer before continuing.

---

### Step 2 — Clarify Installation Target

Ask the user where they want to install the selected item(s):

> **"Where would you like to install?**
>
> - **[G] Global** — Available across all projects. Files will go into `~/.copilot/`
>   so Copilot can discover them system-wide.
> - **[P] Project** — Available only for one specific project. Files will go into
>   the project's `.github/` folder.
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

2. Construct the global target root: `$HOME/.copilot`

3. Check whether `~/.copilot` already exists:

```bash
ls -la "$HOME/.copilot" 2>/dev/null || echo "NOT_FOUND"
```

4. If it does **not** exist, create it:

```bash
mkdir -p "$HOME/.copilot"
echo "Created ~/.copilot"
```

5. Confirm to the user:
> ✅ Global target directory ready: `~/.copilot/`

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

3. Check whether `.github/` exists inside the project:

```bash
ls "<project-dir>/.github" 2>/dev/null || echo "NOT_FOUND"
```

4. If `.github/` does **not** exist, create it:

```bash
mkdir -p "<project-dir>/.github"
echo "Created .github/ in project"
```

5. Confirm to the user:
> ✅ Project target directory ready: `<project-dir>/.github/`

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

### Step 5 — Resolve Dependencies

For each item the user wants to install, identify **all files that must be copied**
to make the item work correctly.

#### 5.1 Dependency Discovery Rules

**For a Skill** (`skills/<skill-name>/SKILL.md`):

1. Read `skills/<skill-name>/SKILL.md`
2. Scan the entire file for the following path patterns and collect every match:
   - `` `references/<ref-name>/` `` or `` `references/<ref-name>/<file>` ``
   - `` `scripts/<script-name>.sh` ``
   - `` `docs/<doc-name>.md` ``
3. Also parse the `## References` section for any relative links pointing to
   `references/`, `scripts/`, or `docs/`.
4. If a `.github/skills/<skill-name>/SKILL.md` version also exists, note it —
   prefer copying that version as it is the Copilot-loadable form.

**For an Agent** (`agents/<role>/AGENT.md`):

1. Read `agents/<role>/AGENT.md`
2. Collect all skill paths listed in the `## Skills` section
   (pattern: `` `skills/<skill-name>/SKILL.md` ``)
3. For each referenced skill, apply the **Skill discovery rules** above recursively
4. Collect all reference paths in `## Tech Stack Guidelines` or similar sections
   (pattern: `` `references/<ref-name>/<file>` ``)
5. Include any files under `agents/<role>/context/`

**For a Reference** (`references/<ref-name>/`):

- Include all files found under `references/<ref-name>/`

**For a Script** (`scripts/<script-name>.sh`):

- Include `scripts/<script-name>.sh`
- Scan the script for any `source` or `.` commands that reference other scripts
  and include those too

#### 5.2 Build the File Manifest

Deduplicate and compile all resolved paths into a **File Manifest** — every source
file and its intended destination. Example for `code-review`:

```
INSTALL MANIFEST — skills/code-review
──────────────────────────────────────────────
Source                                         → Destination
skills/code-review/SKILL.md                   → <target>/skills/code-review/SKILL.md
references/code-review-java/code-review-java.md → <target>/references/code-review-java/code-review-java.md
references/java-code-standard/java-code-standard.md → <target>/references/java-code-standard/java-code-standard.md
```

---

### Step 6 — Present Installation Plan and Confirm

Before executing any file operations, show the user the full plan:

```
📋 Installation Plan
─────────────────────────────────────────────
Installing : skills/code-review
Target     : ~/.copilot/  (Global)

Files to copy:
  ✅ skills/code-review/SKILL.md
     → ~/.copilot/skills/code-review/SKILL.md

  ✅ references/code-review-java/code-review-java.md
     → ~/.copilot/references/code-review-java/code-review-java.md

  ✅ references/java-code-standard/java-code-standard.md
     → ~/.copilot/references/java-code-standard/java-code-standard.md

Directories to create (if not existing):
  ~/.copilot/skills/code-review/
  ~/.copilot/references/code-review-java/
  ~/.copilot/references/java-code-standard/
─────────────────────────────────────────────
Total: 3 file(s)
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
Installed : skills/code-review  (+2 dependencies)
Target    : ~/.copilot/

Files installed:
  ✅ ~/.copilot/skills/code-review/SKILL.md
  ✅ ~/.copilot/references/code-review-java/code-review-java.md
  ✅ ~/.copilot/references/java-code-standard/java-code-standard.md

How to use:
  Copilot will now automatically discover the installed skill.
  Open a Copilot chat and say "review my code" or
  "@workspace review this file" to activate the code-review skill.
─────────────────────────────────────────────
```

If any files failed, show both successes and failures:

```
⚠️ Installation Completed with Errors
─────────────────────────────────────────────
  ✅ ~/.copilot/skills/code-review/SKILL.md
  ❌ ~/.copilot/references/code-review-java/code-review-java.md
     Reason: Permission denied
     Fix:    Run manually →
             cp "<repo-root>/references/code-review-java/code-review-java.md" \
                "~/.copilot/references/code-review-java/code-review-java.md"
─────────────────────────────────────────────
```

---

## Target Directory Structure Reference

### Global Install (`~/.copilot/`)

```
~/.copilot/
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
├── agents/
│   └── <role>/
│       ├── AGENT.md
│       └── context/
│           └── working-context.md
├── references/
│   └── <reference-name>/
│       └── <files>
└── scripts/
    └── <script-name>.sh
```

### Project Install (`<project-dir>/.github/`)

```
<project-dir>/
└── .github/
    ├── skills/
    │   └── <skill-name>/
    │       └── SKILL.md
    ├── agents/
    │   └── <role>/
    │       ├── AGENT.md
    │       └── context/
    │           └── working-context.md
    ├── references/
    │   └── <reference-name>/
    │       └── <files>
    └── scripts/
        └── <script-name>.sh
```

---

## Dependency Map Reference

Use this as a quick-lookup while building the manifest. Always confirm by doing
live discovery (Step 5) in case new dependencies have been added.

| Item | Type | Primary File | Known Dependencies |
|---|---|---|---|
| `code-review` | Skill | `skills/code-review/SKILL.md` | `references/code-review-java/`, `references/java-code-standard/` |
| `unit-test-generation` | Skill | `skills/unit-test-generation/SKILL.md` | `references/java-unit-test/` |
| `code-generation` | Skill | `skills/code-generation/SKILL.md` | Scan file for references |
| `backend-system-analysis` | Skill | `skills/backend-system-analysis/SKILL.md` | `references/backend-system-design/` |
| `developer` | Agent | `agents/developer/AGENT.md` | All 4 skills above + all referenced references + `agents/developer/context/` |

---

## Examples

### Example 1 — Install a Single Skill Globally

**User:** "Install the code-review skill globally."

1. Identify: `skills/code-review` → global target `~/.copilot/`
2. Sync with the tracked upstream branch (if configured)
3. Discover dependencies: `references/code-review-java/`, `references/java-code-standard/`
4. Show plan → user confirms **YES**
5. Create dirs: `~/.copilot/skills/code-review/`, `~/.copilot/references/code-review-java/`,
   `~/.copilot/references/java-code-standard/`
6. Copy 3 files → verify → report ✅

---

### Example 2 — Install an Agent into a Project

**User:** "Install the developer agent into my project at `/home/alice/projects/my-api`."

1. Identify: `agents/developer` → project target `/home/alice/projects/my-api/.github/`
2. Sync with the tracked upstream branch (if configured)
3. Discover dependencies (Agent → all referenced skills → all referenced references):
   - Skills: `backend-system-analysis`, `code-generation`, `code-review`, `unit-test-generation`
   - References: `backend-system-design/`, `code-review-java/`, `java-code-standard/`, `java-unit-test/`
   - Context: `agents/developer/context/working-context.md`
4. Show full plan → user confirms **YES**
5. Create all necessary dirs under `/home/alice/projects/my-api/.github/`
6. Copy all files → verify → report ✅

---

### Example 3 — Install a Reference Only

**User:** "Install just the java-code-standard reference into my project."

1. Identify: `references/java-code-standard` → project target
2. Sync with the tracked upstream branch (if configured)
3. Manifest: all files under `references/java-code-standard/`
4. Show plan → user confirms → copy → report ✅

---

## References
- The source layout this skill installs from (`skills/`, `agents/`, `references/`,
  `scripts/`) and the target rules are described inline in this skill's Instructions.
- [Install Knowledge](../aiws-install-knowledge/SKILL.md)
- [Validate Skill](../aiws-validate-skill/SKILL.md)
