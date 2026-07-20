---
name: "aiws-ask-knowledge"
version: "1.0.0"
description: "Grounded question-answering over the knowledge/ layer — a lightweight RAG-style workflow that searches curated knowledge entries, answers strictly from what is documented with citations, and explicitly says when something is not documented instead of guessing."
tags: ["rag", "knowledge", "retrieval", "grounding", "qa"]
applies-to: ["agent-skills repo", "any project with a knowledge/ folder"]
author: "William Theo (IT RDI IM TD)"
last-updated: "2026-07-20"
---

# Ask Knowledge

Answers a user's question using **only** the curated notes in the `knowledge/`
layer. This is a lightweight, local RAG / internal-wiki workflow: it retrieves the
most relevant knowledge entries, grounds its response in them, cites the source
files, and — critically — **never invents an answer**. If the knowledge base does
not cover the question, it says so plainly.

## When to Use

Trigger phrases: "ask knowledge", "what do we know about", "look it up in the knowledge base",
"what's documented about", "check the knowledge folder", "according to our knowledge",
"is there a note on", "grounded answer", "answer from knowledge only"

Use this skill whenever the user wants an answer that is **trustworthy and sourced**
from the organization's documented knowledge rather than the model's general
training. It is ideal for internal concepts, systems, policies, workflows, and
how-tos captured under `knowledge/`.

---

## Purpose

LLMs answer confidently even when they are wrong. For internal, project-specific,
or policy questions, a hallucinated answer is worse than no answer. The
`knowledge/` layer exists precisely to hold **durable, curated, authoritative**
notes.

This skill enforces a strict retrieval-and-grounding discipline: read the relevant
knowledge entries first, answer **only** from what they say, quote/cite the exact
files used, and refuse to fabricate anything the knowledge base does not contain.
The output is a sourced answer plus a clear statement of any gaps.

---

## Core Principles (Non-Negotiable)

1. **Grounding first.** Every factual claim in the answer must trace to a specific
   knowledge entry. If a claim cannot be traced, it must not be stated as fact.
2. **No fabrication.** Never fill gaps with general/training knowledge presented as
   documented fact. If the knowledge base is silent, say so.
3. **Cite everything.** Always list the exact source file paths the answer draws from.
4. **Prefer authoritative entries.** Curated taxonomy folders (`concepts/`,
   `systems/`, `workflows/`, `policies/`, `how-to/`, `references/`) are
   authoritative. `raw/` is staging — use it only as a weak signal and label it
   clearly as unverified.
5. **Respect status.** Entries with `status: deprecated` must be flagged as such;
   prefer `active` entries. Note `draft` entries as provisional.
6. **Separate fact from inference.** If you reason beyond the text, label it
   explicitly as inference, not as documented knowledge.

---

## Knowledge Layer Reference

Entries live under `knowledge/`, filed by `type`:

| Folder | `type` | Typical questions it answers |
|---|---|---|
| `knowledge/concepts/` | `concept` | "What is X?", "How does X work?" |
| `knowledge/systems/` | `system` | "What does service X do?" |
| `knowledge/workflows/` | `workflow` | "What's our process for X?" |
| `knowledge/policies/` | `policy` | "Are we allowed to X?", "What's the rule on X?" |
| `knowledge/how-to/` | `how-to` | "How do I do X?" |
| `knowledge/references/` | `reference` | "What's the value/definition of X?" |
| `knowledge/raw/` | — | Uncurated staging — treat as unverified |

Each entry has YAML front-matter (`title`, `type`, `owner`, `status`,
`last_updated`, `tags`, optional `related`) and a `## Summary` body.

---

## Instructions

### Step 1 — Locate the Knowledge Root

Find the `knowledge/` folder to search. Check, in order:

1. `knowledge/` at the workspace root.
2. `.github/knowledge/` (project-scoped install).
3. `~/.copilot/knowledge/` (global install).

```bash
for p in "knowledge" ".github/knowledge" "$HOME/.copilot/knowledge"; do
  [ -d "$p" ] && echo "FOUND: $p"
done
```

If none exist, report:
> ⚠️ No `knowledge/` folder found. I can only answer from documented knowledge, and
> there is none available here. Consider running `aiws-workspace-init` or adding entries.

and stop (do not answer from general knowledge).

If multiple exist, search all of them; note which root each hit came from.

### Step 2 — Extract Query Terms

From the user's question, derive search terms:

- Key nouns / domain terms (e.g., "idempotency", "payment retry", "secret rotation").
- Synonyms and likely tag words (lowercase, no spaces — matches the `tags` schema).
- The likely `type` (a "how do I…" question → `how-to`; "are we allowed…" → `policy`).

### Step 3 — Retrieve Candidate Entries

Search the knowledge root(s) across filenames, front-matter, and body:

```bash
# Replace <ROOT> with each found knowledge root, and <TERMS> with a regex of query terms
grep -rniE "<term1|term2|term3>" "<ROOT>" --include="*.md" -l
```

Also scan front-matter directly for strong signals:

```bash
grep -rniE "^(title|tags|type):" "<ROOT>" --include="*.md"
```

Rank candidates by:
1. Match in `title` / filename (strongest)
2. Match in `tags`
3. `type` matches the question's intent
4. Match in body `## Summary`
5. `status: active` outranks `draft`; `deprecated` is demoted/flagged

Select the top relevant entries (typically 1–5). **Read the full content** of each
selected entry before answering — never answer from the grep line alone.

### Step 4 — Follow Related Links

For each selected entry, check its `related:` front-matter list and any inline
links into `knowledge/`. Read those too if they add relevant context. Do **not**
pull in `raw/` targets as authoritative.

### Step 5 — Decide: Answerable or Not

- **Fully covered** → the entries directly answer the question. Proceed to Step 6A.
- **Partially covered** → some aspects are documented, others are not. Proceed to
  Step 6B — answer the covered part, explicitly flag the gaps.
- **Not covered** → nothing relevant found. Proceed to Step 6C — do not answer from
  general knowledge.

### Step 6 — Compose the Grounded Response

#### 6A — Fully Answerable

```
📖 Answer (from knowledge base)

<Concise answer, composed strictly from the cited entries.>

Sources:
- knowledge/concepts/idempotency.md  (concept, active, updated 2026-05-01)
- knowledge/policies/secret-management.md  (policy, active)
```

#### 6B — Partially Answerable

```
📖 Answer (from knowledge base)

<Answer the documented part, grounded and cited.>

⚠️ Not documented:
- <Specific sub-question the knowledge base does not cover.>

Sources:
- knowledge/systems/payment-service.md  (system, active)
```

#### 6C — Not Answerable

```
🚫 Not documented

I searched the knowledge base and found no entry covering "<question>".
I won't guess an answer.

Searched: <root(s)>  |  Terms: <terms>
Closest related entries (may not answer your question):
- knowledge/concepts/<nearest>.md

Suggestion: add a knowledge entry for this topic (see aiws-workspace-init /
the aiws-create-knowledge skill), then ask again.
```

### Step 7 — Quality Guardrails Before Sending

Before returning any answer, verify:

- [ ] Every factual sentence maps to a cited entry.
- [ ] No claim relies on general/training knowledge presented as documented fact.
- [ ] Sources are listed with file paths and (where useful) `type` / `status`.
- [ ] Deprecated/draft entries are flagged; deprecated info is not presented as current.
- [ ] Any inference beyond the text is explicitly labeled as inference.
- [ ] If nothing was found, the response is a clear "not documented" — **not** a guess.

---

## Examples

### ✅ Good — Grounded Answer with Citations

**User:** "What's our policy on rotating API keys?"

1. Root found: `knowledge/`
2. Terms: `api key`, `rotation`, `rotate`, `secret`; intent → `policy` / `how-to`
3. Hits: `knowledge/how-to/example-rotate-api-keys.md`, `knowledge/policies/example-secret-management.md`
4. Read both; policy covers cadence, how-to covers steps
5. Answer:

```
📖 Answer (from knowledge base)

Keys must be rotated every 90 days, and immediately on suspected compromise
(per the secret-management policy). The rotation procedure is: generate a new
key, deploy it, verify, then revoke the old key.

Sources:
- knowledge/policies/example-secret-management.md  (policy, active)
- knowledge/how-to/example-rotate-api-keys.md  (how-to, active)
```

### ✅ Good — Honest "Not Documented"

**User:** "What's our Kafka partition strategy?"

- Search returns no relevant entry.
- Response:

```
🚫 Not documented

I searched the knowledge base and found no entry covering Kafka partitioning.
I won't guess an answer.

Suggestion: add a knowledge/systems/ or knowledge/concepts/ entry for it.
```

### ❌ Bad — What This Skill Must NOT Do

**User:** "What's our Kafka partition strategy?"

> ❌ "Typically you'd partition by key using a hash of the customer ID and aim for
> 6–12 partitions per topic…"

This is **forbidden**: it fabricates an answer from general knowledge and presents
it as if it were documented. When nothing is found, use the 6C format instead.

### ❌ Bad — Uncited Claims

> ❌ "Our retry policy is 3 attempts with exponential backoff."

Forbidden if no knowledge entry states this. Every factual claim needs a citation;
otherwise it must be omitted or labeled as unverified inference.

---

## Quick Reference

| Situation | Do |
|---|---|
| Entry directly answers | Answer + cite sources (6A) |
| Some parts documented | Answer documented part, flag gaps (6B) |
| Nothing found | State "not documented", don't guess (6C) |
| Only `raw/` matches | Use cautiously, label as unverified staging |
| `deprecated` entry matches | Flag it; prefer active alternatives |
| Reasoning beyond text | Label explicitly as inference |

---

## References
- The knowledge taxonomy and front-matter fields this skill reads are described
  inline in this skill (see **Knowledge Layer Reference**).
- [Install Knowledge](../aiws-install-knowledge/SKILL.md)
- [Validate Knowledge](../aiws-validate-knowledge/SKILL.md)
- [Workspace Init](../aiws-workspace-init/SKILL.md)
