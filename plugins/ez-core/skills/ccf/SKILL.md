---
name: ccf
description: >-
  Check Changed Files: lists uncommitted paths in a git repo, groups them into
  one commit per piece of work with suggested messages, then commits only
  after the user picks a numbered option. Works in the current repo by
  default; `ccf org` uses the org repo, `ccf <project>` that project's repo.
  Use when the user says ccf, asks what changed, asks to group changes for
  commits, or to stage and commit, or invokes /ccf.
argument-hint: "[org | <project>] [<project> after org]"
---

# ccf — check changed files

Arguments: `$ARGUMENTS`

Two turns, always: turn 1 is the report and a numbered question; turn 2 is
the user's answer. Never stage or commit in the reply that carries the
report, even when the request says "… and commit".

## Settings

A plugin setting is not set when its value is empty or still shows as a
`${user_config…}` placeholder.

- Org repo: `${user_config.org_repo}`
- Project folders: `${user_config.project_dirs}` (comma-separated; each
  holds project repos as subfolders)
- Daily logs: `${user_config.daily_logs}` (comma-separated globs with
  `YYYYMMDD`, relative to the repo root)

## 1. Pick the repo

| Arguments | Repo |
| --- | --- |
| none | the current folder's repo: `git rev-parse --show-toplevel` |
| `org` | the org repo setting |
| `org <project>` | the org repo, limited to `<project>/**` |
| `<project>` | that project's repo, first match: `<folder>/<project>` in a project folder → a sibling of the current repo named `<project>` → a folder named `<project>` in the org repo |

- `org` with no org repo setting, or a project not found: say so in one line
  and ask for the path; never guess.
- No arguments and the current folder is not in a git repo: say so and stop.
- In a git worktree, the worktree is the repo.

## 2. Collect paths

1. `git status -sb` (note ahead/behind from the first line; `git fetch` only
   when the remote matters).
2. `git diff --name-only`, `git diff --cached --name-only` (already staged:
   `git commit` takes these too, so they are grouped like any other path),
   `git ls-files --others --exclude-standard`.
3. Daily logs (setting set): today from `date '+%Y%m%d'`, never from session
   metadata. Files matching a daily-log glob with today's date are left out
   and never mentioned, not in the report and not after the commits; the
   user's working on them today is normal. Earlier days' files are grouped
   (step 3). Include today's file only when the user asks.

Nothing left → reply `Nothing to commit in <repo>.` and stop.

## 3. Group by work unit

One group = one shippable piece of work (a task step, a section, a fix, a
refactor), holding every path of it: code, page wiring, i18n keys, config,
assets, styles, dev pages and that work's docs. Group titles are work labels
(`Step 6 — trust stats band`), never folder or layer names.

Find the work units from, in order:

1. Task docs in the repo or the org repo (`tasks/<id>_*/` with a briefing,
   steps or `task_meta.json`): one group per step. The step: the worktree
   branch (`task/<id>-step-<N>`) → the step the session names → the current
   step in the task docs. Never invent task ids.
2. Component and section paths (`Section/Stats/*` → the stats group).
3. The diff itself.

Rules:

- Never split one work unit across Components / Pages / i18n / Config groups,
  and never park assets, styles or `.gitignore` in a catch-all: assign each to
  the feature it serves.
- A shared file (one page, one `en.json`) used by several groups: list it
  under each, or add one `Page wiring` group after the sections, plus a
  Coupling note (partial staging with `git add -p`, or commit the
  feature-only files first).
- A repo whose top folders are projects (the org repo): each project's paths
  form their own groups.
- Earlier-day daily logs: inside the work group they document (Coupling
  note), else one group per day after the work groups, oldest first
  (`daily logs YYYY-MM-DD`).
- No task or feature context at all: group by area (components, pages,
  composables or hooks, stores, services/server, types/utils, i18n, root
  config, other) and say `Fallback grouping (file type)`.

## 4. Turn 1 — report

First line: the repo path and the ahead/behind note. Then each group in step
or build order:

````text
### Group N — <work label>
Paths: (count)
1. path/one
2. path/two

Suggested commit: <message>
````

Messages:

- Say what the change does and what it delivers, in plain words, present
  tense; no `fix:` / `feat:` type prefix; only claims the diff or the session
  shows (`add inline trust stats band to the landing page`).
- A repo whose top folders are projects: prefix the folder
  (`shop-web: complete step 6 trust stats`).

After the groups, a `Coupling` section when shared files span groups. No
`git add` commands, no file sizes, binary or secret warnings, no checks this
skill does not list.

End with the staging question as plain text, a numbered list (never a
question tool). Count work groups only; daily-log groups do not count.

One work group:

```text
How should I commit this?

1. Commit
2. wdyr
```

Two or more:

```text
How should I commit the <N> groups?

1. Commit each group separately (Recommended)
2. Commit all groups as one
3. Report only
4. wdyr
```

Then stop.

## 5. Turn 2 — the answer

Only an option number answers. `commit`, `ccf commit` or any other wording
gets the same numbered question again, and nothing is staged. `wdyr` runs
the `wdyr` skill on the question; only the answer to that reply commits.
Approval covers this batch only, never a later one.

Reuse the report's groups and messages; re-run git only if the user says
paths changed.

| Option | Do |
| --- | --- |
| Commit (one group) | Commit that group, then each earlier-day daily-log group as its own commit. |
| Commit each group separately | One commit per group in report order, daily-log groups included; `git status` between commits. |
| Commit all groups as one | Stage every reported path and make one commit. |
| Report only | Nothing. |

- Stage by path only, never `git add -A` or `git add .`.
- Code in the group: before staging, run the project's format script (else
  its configured formatter) and lint script (else its configured linter) on
  the group's paths; add the files they change to the group. Skip for
  docs-only groups.
- Pre-commit hook fails → fix it and make a new commit; never amend.
- Never push unless asked.

Reply after the commits: the commits made (hash and message), nothing about
today's daily logs.
