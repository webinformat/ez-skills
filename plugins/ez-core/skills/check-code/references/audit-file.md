# Audit file

Path: `<audit folder>/YYYYMMDD_<scope-slug>_code.md` (date from `date
'+%Y%m%d'`). Written after the first fix, updated after each fix.

## Shape

````markdown
# Code audit — <scope in words>

- **Date:** YYYY-MM-DD
- **Scope:** <branch or worktree, base commit>: <files>
- **Guides:** <every guide and source read, by path or link>
- **Status:** open | closed

## 0. Sweep evidence

```text
<command> → <what it returned>
```

## 1. Scope

<the files reviewed>. Scope expansion pulled in <candidate and sibling files>.

## 2. Findings

```text
N. [severity] path:line — short title
   Rule: <guide section or source>
   Detail: <what breaks the rule>
```

## 2b. Reuse table

| Path | Candidates found | Verdict | Why |
| --- | --- | --- | --- |
| `components/Trust/Index.vue` | `Section/Testimonials/Video/` | `new` ✗ | should be `extended`, see finding 1 |

## 3. Refactor suggestions

```text
N. <action> — why, effort S/M/L
```

## Fixes applied

| # | Finding | Status | Change |
| --- | --- | --- | --- |
| 1 | near-copy of Testimonials/Video | done | extended the existing component |
````

## Rules

- Sweep evidence: two to five lines is normal; a file without it is not an
  audit.
- Number every finding; severity is `critical`, `major`, `minor` or `nit`.
- Reuse verdicts: `reused`, `extended`, `promoted` (moved to a shared
  place) or `new`. Mark ✗ when the audit disagrees with the choice the code
  made and cite the finding number. Nothing added → `No added files or
  symbols in scope.`
- Fixes applied: one row per finding; status `done`, `wontfix` (the user
  answered skip) or `open`. Status `closed` when no row is `open`.
- An `INDEX.md` in the audit folder gets one row per audit file:
  `| Date | Scope | Type | Open | File |`, Type `code`, Open = rows still
  `open`. Create the index when it is missing.
- Examples use generic names; never copy secrets or personal data into the
  file.
