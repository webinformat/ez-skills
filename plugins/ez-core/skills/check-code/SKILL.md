---
name: check-code
description: >-
  Audits changed or named code for DRY (duplicates and near-copies, including
  originals outside the diff), single source of truth, the language's and
  framework's best practices, and common best practices, against the
  project's own coding guides first. Fixes obvious findings, then asks fix or
  skip per finding (`auto-fix=false` asks about every one). Use when the user
  says check-code or check code, asks for a code audit, asks whether new code
  duplicates something that already exists, wants code checked for DRY, SSOT
  or best practices, or invokes /check-code. Not for bug hunting
  (/code-review) or lint.
argument-hint: "[paths | base-branch] [auto-fix=false]"
---

# check-code

Arguments: `$ARGUMENTS`

Four checks over a scope: **DRY**, **SSOT**, **language best practices** and
**common best practices**. Bugs are `/code-review`'s job and style errors the
linter's: passing lint or a clean `/code-review` is never a clean check-code.

## Settings

A plugin setting is not set when its value is empty or still shows as a
`${user_config…}` placeholder.

- Shared coding guides: `${user_config.coding_guides}` (comma-separated
  folders)
- Audit folder: `${user_config.audit_dir}` (`<project>` stands for the main
  repo's folder name: the parent of `git rev-parse --git-common-dir`, so a
  worktree maps to its main repo)

## Arguments

- Paths or folders → they are the scope.
- A branch name (`git rev-parse --verify <name>` succeeds) → the base; the
  scope is `git diff <base>...HEAD`.
- `auto-fix=false` (also `auto-fix: false`, `--auto-fix=false`) → ask about
  every finding. Any other wording or none → auto-fix is on.

## 1. Scope

1. Paths from the arguments or the message.
2. Else the changes: `git diff --name-only`, `git diff --cached --name-only`
   and `git ls-files --others --exclude-standard` (or `<base>...HEAD` when a
   base is given).
3. Nothing found → ask what to check (paths, folder, branch) and stop. Never
   audit the whole repo unless asked.

Leave out lockfiles, generated output, vendored code and binaries.

**Scope expansion (required).** Add every candidate the DRY and SSOT sweeps
turn up, including unchanged files outside the diff, and the nearest sibling
of each changed file. The original of a copy is by definition an unchanged
file: audit only the diff and the copy is invisible. Candidates are read to
judge the scope, not audited for their own faults.

## 2. Rules to check against

Read each in full this turn; a `grep` hit is evidence, not reading.

1. **The repo's own rules:** `CLAUDE.md`, `AGENTS.md`, and the coding docs in
   the repo (`ls docs/`; UI guides such as `docs/ui/*` when the scope touches
   visuals).
2. **Shared guides:** `ls` every folder in the coding guides setting. Read the
   general guide and every guide whose language, framework or topic the scope
   touches (the file names say which). The listing is the inventory, not
   memory.
3. **Official sources:** detect the stack from manifests (`package.json`,
   `composer.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, …) and file
   extensions. For a language or framework no guide above covers, use its
   source in [references/languages.md](references/languages.md).

Precedence: repo rules > shared guides > official sources > general
knowledge. Every finding cites the rule it breaks; a preference with no
source is at most `nit`.

## 3. The four checks

### DRY — duplication sweep

Runs backwards: for every added file or added exported symbol, hunt the
original that already existed. Run from the repo root and record each command
with what it returned (this is the sweep evidence).

1. **What is new:** `git diff --name-status` matching the scope; `A` rows and
   new exported symbols in `M` rows are the targets.
2. **Role search** on the role noun (what the thing is, never the page,
   feature or campaign name): `rg -il "<role>"` across the shared code folders
   (components, composables, hooks, utils, lib, helpers, services, stores).
3. **Symbol and literal search:** exported names, endpoint paths, i18n keys,
   table names, regexes, distinctive strings and magic numbers the new code
   carries.
4. **Structure search:** `fd -t d "<Role>"`: does a folder for this role
   exist?

Open the top three candidates per target and compare the real surface:
signature, props, emits, slots, template, behavior. A different name is not a
different thing; two functions doing the same transform are duplicates. Also
flag repeated blocks, copy-pasted branches and the same condition in several
places inside the scope.

A near-copy (a renamed prop, a dropped slot, a trimmed body) is `major`, and
`critical` when the copies already disagree. Never downgrade it because it is
"only similar".

### SSOT — one owner per fact

For every piece of data, config, constant, type, business rule, endpoint,
translation or design token the scope adds or changes, find its owner. Flag:

- a second owner: the same constant, config, rule or type defined again
  instead of imported (search by value and by name);
- an endpoint or query called outside the layer that owns it (API client,
  service, repository) when that layer exists;
- derived state stored and kept in sync instead of computed from its source;
- the same value in several config or env files, or hardcoded where config
  owns it;
- a type copied field by field from a shared type or schema instead of
  derived from it (`Pick`, `z.infer`, generated types);
- docs or comments that restate a value the code owns.

Owners that already disagree → `critical`; otherwise `major`.

### Language and framework best practices

Check against the rules from step 2: idioms, naming, file placement, where
logic lives (component, hook or composable, util, service, store), typing,
framework rules (reactivity, SSR safety, hook rules), styling, i18n.

**Sibling conformance.** Name each changed file's nearest existing analogue
and compare placement, naming, where logic lives, size, error-handling shape,
i18n and styling. A divergence is a finding that cites the sibling's path.
When the sibling is the one that is wrong, say so and do not copy it.

### Common best practices

Language-independent; a guide from step 2 overrides any item.

- One job per function; guard clauses over deep nesting; size limits from the
  guides, else flag a function past ~50 lines or 3 nesting levels.
- Names say what a thing is; no abbreviations the reader must decode.
- Errors: none swallowed (empty `catch`, a log-only `catch` on a user action);
  a user action shows its failure; busy flags cleared in `finally`; no
  un-awaited promise from a user event.
- No dead code, commented-out code, leftover debug output, or `TODO` without
  an owner.
- Comments say why, never narrate what.
- Security basics: no secrets in code, input validated at boundaries, no SQL,
  shell or HTML built from input by string concatenation.
- Environment values (URLs, hosts, ids) in config, not in code.
- Changed behavior has a test when the repo tests that area.

## 4. Parallel agents

Count the files after scope expansion. Five or fewer: run everything inline.
More than five: spawn three read-only `Explore` agents in one batch, each
given the file list, the repo root and the guide paths:

| Agent | Owns | Returns |
| --- | --- | --- |
| DRY + SSOT | both sweeps | commands run and their hits; candidates with a comparison per added file |
| Language | language check and sibling conformance | violations with file:line, rule source, proposed severity |
| Common | common check | violations with file:line, rule source, proposed severity |

Agents return unnumbered items. The main agent alone resolves the scope,
merges (dedupes, settles severity, numbers the findings), fixes, asks and
writes the audit file. No agent writes the report.

## 5. Severity

The guide's severity table wins when one exists. Else:

| Severity | Meaning |
| --- | --- |
| `critical` | wrong behavior, or copies or owners that already disagree |
| `major` | a clear rule break or near-term maintenance pain; fix before merge |
| `minor` | real but low impact |
| `nit` | style or preference only |

## 6. Clean-bill gate

Report "no findings" only when every item holds; otherwise report **audit
incomplete** and what is missing:

1. Sweep evidence recorded (commands and what they returned).
2. Reuse table filled: one row per added file or symbol, or `No added files
   or symbols in scope.`
3. Every applicable guide opened and read this turn, listed by path.
4. Each changed file compared with its sibling.
5. All four checks run on the changed lines. The task briefing explains why
   code changed; it never replaces the audit.

## 7. Fix and ask

After the merge, worst first.

- **auto-fix on (default):** apply every fix that is obvious from the rule
  and the code, including ones that remove, rename or move code; invoking
  check-code approves those. Then run the project's lint and type-check
  scripts on the touched files and fix what they report. Report the fixes in
  one short summary, then ask about the rest.
- **auto-fix off:** no fix before the user answers `fix` on that finding.
- **Not obvious:** two reasonable fixes exist, the fix changes a public API
  or behavior, or it changes what the user sees.
- **Visible changes are checked on screen first** (an icon, a component swap,
  spacing): render the current element and the replacement side by side at
  the same size and color; the question says whether they match exactly.

One question per message, in this shape:

```text
Finding N of M — should we fix this?

<What is wrong, naming the file. What the fix would change.>

1. fix
2. skip
3. tell me more
4. wdyr
```

- N and M count only the findings asked about, never ones already fixed.
- Two sentences at most: no severity, rule names or code; `tell me more`
  gives those.
- Apply a `fix` at once, confirm in one line, ask the next finding. `wdyr`
  runs the wdyr skill on the finding.
- Stop when the user stops; never dump the remaining findings.
- **Auto-run or auto-pick mode on:** no questions. Each finding runs the wdyr
  skill with `fix` and `skip` as candidates and takes its Option 1 (either,
  never `fix` by default); report one line with the research link. Commit,
  push, deploy and delete are still asked.

## 8. Report and audit file

- **Chat:** the fix summary, then the questions. Nothing else; the full
  report only on request, in the audit file's shape.
- **Audit file:** when the audit folder setting is set and that folder
  exists, write it after the first fix and update it after each one, per
  [references/audit-file.md](references/audit-file.md). Nothing fixed → no
  file. Setting set but folder missing → say so in one line, no file.
- The audit never commits; commit only when the user asks.
