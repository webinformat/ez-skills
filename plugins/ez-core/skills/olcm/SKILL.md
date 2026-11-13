---
name: olcm
description: >-
  Writes commit messages for every uncommitted change in the current repo
  (unstaged, staged and new files), or only for the scope the user names
  after olcm (staged files, a folder, a commit range): five numbered variants
  that say what the change does and what it fixes or delivers, plus a sixth
  short task-brief variant when a task resolves. May run the repo's formatter
  first; commits only after the user answers with a variant number or their
  own message. Use when the user asks for a commit message, asks what the
  commit should say, says olcm, or invokes /olcm. Not for grouping or staging
  files into several commits (use ccf).
argument-hint: "[scope: staged | <paths> | <commit range>]"
---

# olcm — commit messages

Arguments: `$ARGUMENTS`

Two turns, always: turn 1 is the messages and a question; turn 2 is the
user's answer, which commits. Never stage or commit in the reply that carries
the messages.

## Settings

A plugin setting is not set when its value is empty or still shows as a
`${user_config…}` placeholder.

- Org repo: `${user_config.org_repo}` — a second place to look for task docs.
- Ticket URL: `${user_config.ticket_url}` — base URL put before a ticket
  stored as a path (see **Ticket suffix**).

## 1. Scope

The repo is the current folder's repo (`git rev-parse --show-toplevel`; in a
git worktree, the worktree). Not in a git repo → say so and stop.

- **Default: every uncommitted change** — `git diff`, `git diff --staged`
  and `git ls-files --others --exclude-standard`. A new file is a change in
  the repo: include it, never ask.
- **A scope the user names** — any words after olcm that narrow it, in plain
  language, not a strict argument: "staged only" → `git diff --staged`; a
  folder or files → the three lists limited to those paths; "the last two
  commits" → that commit range. The messages and the commit after the answer
  cover only that scope; the user never restates it.
- Words that fit two different scopes → ask one question and stop.

**Empty scope** — nothing unstaged, staged or untracked in it → reply
`Nothing to message.` and stop: no variants, no task docs, no formatter.
Never fill an empty scope from somewhere else: no `main...HEAD` or other
range unless the user names one, no committed history, no task briefing,
ticket or chat in place of a diff.

## 2. Format, then read the diff

When the scope has code files and the repo has a format script in
`package.json` (else a configured formatter such as Prettier), run it on
the scope's code paths, preferring a path-scoped run. Then collect the scope
again, so the messages match what will be committed. Read every new file in
full.

- Formatting is the only write allowed here: no functional edits, no
  formatter config changes, no fixes after a formatter failure (report the
  failure instead).
- Skip for docs-only scopes and repos with no formatter.

## 3. Task context (when one resolves)

Find the task, first match:

1. The task the session is working on.
2. A task the user names (id, folder, ticket).
3. A task file visible in the chat.

Task docs live in `tasks/<id>_*/` in the repo, or in the org repo setting
(`<org repo>/<repo folder name>/tasks/`). Never invent a task id.

When found, read the briefing (`task_briefing.md`), `task_meta.json` and the
steps file (`suggested_steps.md`) when present. The step: the worktree
branch (`task/<id>-step-<N>`) → the step the session names → the current
step in `task_meta.json`; read its step spec when one exists.

Use the briefing's Request / Goal, the step Goal and the bugs or features
the session reported as the main frame for the wording, before what the diff
mechanics suggest. Cross-check the diff against them: what shipped, what is
step-scoped, what is extra.

**Summary phrase** (for variant 6), first that applies:

1. The briefing's Request / Goal / Scope as one short phrase
   (`delivery instructions on address notes`).
2. `task_meta.json` `notes`, else `title`, without board prefixes like
   `WEB |`.
3. The ticket subject, when a ticket exists but no task folder.

When the diff is clearly one step and that step's Goal is narrower but still
briefing-level, use the step Goal. Never a fix list, component names or step
numbers.

**Ticket suffix** — when `task_meta.json` has a non-empty `ticket`, append it
at the end of every variant, after a space; never as a prefix.

| `ticket` value | Suffix |
| --- | --- |
| an id (`INC-1001`, `SR-1001`) or a full URL | as stored |
| a path (`boards/…/pulses/…`) | ticket URL setting + the path; setting not set → as stored |

## 4. Writing the messages

Analyze the whole scope first: list every changed file, new ones included,
and group related edits by area or feature, so no file or change group is
left out.

Each message says **what the diff changes** and **what that fixes or
delivers**, so a reader of `git log` learns both without opening the diff.

- **Subject**: one line, the change and its outcome in plain, general words.
  Exact screen text and symptom detail go in the body.
- **Body**: after a blank line, one to three short lines: the cause (present
  tense, not only the symptom) and what the change does now.
- **Name the mechanism** in words a reader of the code recognises
  (`read the login cookie without useCookie`). Never a bare file list, never
  only the symptom.
- **Full scope**: every variant covers every major change area; a diff over
  several areas joins them with commas in the subject and gives each its
  cause in the body. A large diff gets a comprehensive summary, not a narrow
  one or a file inventory.
- **Side changes in the body only**: a lockfile, formatter or tooling config,
  or a small unrelated fix is named in the body, never in the subject.
- **Only what the evidence shows**: every claim (cause, effect, who sees
  what) comes from the diff or was observed in the session. An effect nobody
  observed is left out.
- No `fix:` / `feat:` / `refactor:` type prefix; start with the change.
- Fix or feature: word it as a fix when it corrects wrong behavior, as a
  delivered capability when it adds behavior.
- The five variants differ in emphasis or wording, not near-duplicates; when
  two framings fit equally, vary which one leads. Every variant says what
  the change does now: none opens with a past-tense symptom ("users could
  place a second order …") or with the audience ("admins no longer see …").

| Avoid | Prefer |
| --- | --- |
| `update useCrossTabAuthSync and profile plugin` (files only) | `read the login cookie without useCookie so other tabs stop deleting it` |
| `login no longer lost across tabs` (symptom only) | the subject above, plus a body with the cause |
| `add ScrollNav component` (files only) | `add a shared scroll nav so category pages get sticky day tabs` |
| `add back link to category page` (one area of five) | `refresh category pages with back nav, shared scroll tabs, unified breadcrumbs and a hide-scrollbar utility` |

## 5. Turn 1 — the reply

The question line first, then variants 1–5, each as the bare number in prose
and its own fenced block. No lead-in, no angle summaries, no descriptions.

````text
Commit with one of the following options or commit with "message"

1.

```
read the login cookie without useCookie so other tabs stop deleting it

useCookie writes a delete when the cookie is absent. The cross-tab sync and
the profile plugin created it in tabs that had not seen the new cookie yet.
Both now read the cookie from document.cookie and never write it.
```

2.

```
other tabs keep a fresh login: the token cookie is only read there

The cross-tab sync and the profile plugin used useCookie, which deletes an
absent cookie on creation. They now read the cookie without writing it.
```
````

(3–5 the same way.)

When a task resolves, add variant **6** last, in the same format: the
summary phrase plus the ticket suffix, nothing else, no explanation:

````text
6.

```
delivery instructions on address notes INC-1001
```
````

No task → no variant 6 and no line about it. No coverage table unless the
user asks. Then stop.

**Coverage (on request only)**: a table with one row per change group
(`Area | Changes`) to check every area is covered, optionally naming the
variants that cover the full scope best.

## 6. Turn 2 — the answer

A bare number `N` commits with variant N; `commit with "<message>"` commits
with the user's text. Any other wording is not an answer: nothing is staged.

- The commit covers the olcm scope only: the default scope stages every
  changed and new path in it; a named scope stages only that scope. Stage by
  path, never `git add -A` or `git add .`; files the formatter changed are
  part of the scope.
- A pre-commit hook fails → fix it and make a new commit; never amend.
- A commit-range scope is already committed: nothing to stage; do only what
  the user says next (reword, squash).
- Never push unless asked. Approval covers this commit only.

Reply after the commit: the hash and subject.
