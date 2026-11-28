---
name: check-code-full
description: >-
  Full review chain over one scope, in this order: the check-code skill (DRY,
  SSOT and best practices; it moves and merges code), then a bug review that
  applies its fixes (/code-review high --fix in Claude Code), then a security
  review (/security-review in Claude Code) whose findings are fixed or asked
  one by one, so the last two reviews see the final code. /simplify runs only
  when asked. Works in Codex and Cursor with their own review commands or the
  agent's own pass. Use when the user says check-code-full or full check,
  asks for the whole review chain or a full code review before a merge, or
  invokes /check-code-full. Not for one check alone (use check-code,
  /code-review or /security-review).
argument-hint: "[paths | base-branch] [auto-fix=false] [simplify]"
---

# check-code-full

Arguments: `$ARGUMENTS`

Three reviews over the same scope, one after the other. Each step ends (its
fixes applied, its questions answered) before the next starts, so the bug
and security reviews read the code check-code left.

## Arguments

- Paths, folders or a base branch → the scope, exactly as check-code takes
  it (check-code § Arguments and § 1). None → the uncommitted changes.
- `auto-fix=false` (also `auto-fix: false`, `--auto-fix=false`) → no step
  applies a fix before the user answers `fix` on that finding.
- `simplify` → also run step 1b. Meant for a large change or code where
  performance matters.

## Steps

### 1. check-code

Run the check-code skill with the scope and `auto-fix=false` when given. It
applies the obvious fixes and asks fix or skip about the rest (check-code
§ 7). Go on only when its questions are done.

### 1b. /simplify (only with `simplify`)

Claude Code: invoke the `simplify` skill with the same target as step 2. It
applies its own fixes. Other agents: skip it and say so in one line.

### 2. Bug review

**Claude Code:** invoke the `code-review` skill (the Skill tool) at effort
`high`, with `--fix` unless `auto-fix=false`, and the target from the scope:

| Scope | Arguments |
| --- | --- |
| paths or folders | `high --fix <paths>` |
| a base branch | `high --fix <base>...HEAD` |
| the uncommitted changes | `high --fix` (no target: it reviews the branch's commits ahead of its upstream plus the uncommitted changes) |

Wait for the review to finish and its fixes to be applied. With
`auto-fix=false`, its findings go through check-code § 7 as below.

**Codex:** run `codex review` with the scope flag: `--base <base>` for a
base branch, else `--uncommitted`; for paths, keep only the findings in
those paths. It only reports. The command fails (sandbox, network, login) →
say so in one line with its error and do the agent's own bug pass instead.

**Cursor:** run its built-in `/review` skill on the scope when this Cursor
has it; else the agent's own bug pass.

**Agent's own bug pass:** read the scope's diff and the code it calls, and
list correctness bugs only (wrong results, crashes, races, broken error
paths, missed edge cases), each with file and line.

Findings that were reported but not applied go through check-code § 7:
obvious ones fixed, the rest one fix-or-skip question each, in its shape.

### 3. Security review

**Claude Code:** invoke the `security-review` skill (the Skill tool). It
takes no arguments: it reviews the current branch's diff against origin's
default branch and needs an `origin` remote. The repo has no `origin`
remote, or the review fails → say so in one line and do the agent's own
security pass instead.

**Codex, Cursor and other agents:** the agent's own security pass.

**Agent's own security pass:** read the scope's diff and the code it calls,
and list injection (SQL, shell, HTML or template, file paths), missing or
wrong authentication and authorization, and data exposure (secrets, personal
data in logs, URLs or responses), each with file and line.

Every security finding goes through check-code § 7: obvious fixes applied
(none with `auto-fix=false`), the rest one fix-or-skip question each. A
finding outside the scope (the security review reads the whole branch diff)
is not asked: the final reply names it in one line.

## Stop

The user stops answering a step's questions → the chain stops there; the
final reply names the steps that did not run.

## Reply

After the last step:

1. The first line: done, or stopped at step N.
2. One line per step that ran: what it fixed and what was skipped, in plain
   words.
3. One line for each step not run or run as the agent's own pass, with the
   reason.

Nothing is committed or pushed; commit only when the user asks.
