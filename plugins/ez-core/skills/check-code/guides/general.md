# General coding rules

Cross-language conventions for all application code — Vue,
Nuxt, PHP, scripts, and any other language in an app repo.

Framework- or stack-specific guides ([vue.md](./vue.md),
[nuxt.md](./nuxt.md), [hono.md](./hono.md), [laravel.md](./laravel.md), [drizzle.md](./drizzle.md), …) extend this document. They must not contradict it.

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.

## Non-negotiables

### Comments

- Prefer self-explanatory names and structure over comments.
- Do not narrate what the code does (`// increment counter`).
- Do not add section labels when reorganizing files (e.g. `// 1. Imports`).

### Early return

- Handle invalid input, missing data, and error branches first; `return`
  (or `throw` / `continue` in loops) before the main path.
- Prefer guard clauses over wrapping the happy path in `if (ok) { … }`.
- Keep the success path at the lowest nesting level.

### Function size

- One job per function; target ~25–40 lines for the body.
- Extract helpers, composables, or utils when a function exceeds ~40 lines,
  nests more than 2–3 levels, or mixes concerns (e.g. validate + fetch + map
  + store update).

## Anti-patterns (smells to flag)

- New comments that restate the code or label sections → do not add (see
  **Comments** above).
- Deep `if/else` nesting where guard clauses would flatten the flow → early
  returns at the top of the function.
- Long multi-concern functions (>40 lines or mixed responsibilities) → extract
  helpers or smaller functions.

## Severity (for code audits)

When auditing a change against this guide, rate each finding:

| Severity   | Meaning                                                                                          | Examples                                                                                    |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| `critical` | Will cause wrong behavior or data/state corruption, or breaks a hard rule with real consequences | Divergent copies of a money/auth rule; duplicated logic that already disagrees              |
| `major`    | Clear non-negotiable violation; bugs or real maintenance pain soon — fix before merge            | Function over 50 lines or mixing validate + fetch + map + persist; noisy or misleading comments |
| `minor`    | Real but low-impact — fix when convenient                                                        | Single-purpose function in the 40–50 line range                                               |
| `nit`      | Style/preference, no functional impact                                                           | Naming, member order, wording                                                               |

## Related guides

| Area | Path |
| --- | --- |
| Vue architecture | [vue.md](./vue.md) |
| Nuxt 3 add-ons | [nuxt.md](./nuxt.md) |
| Hono APIs | [hono.md](./hono.md) |
| Laravel | [laravel.md](./laravel.md) |
| Drizzle ORM | [drizzle.md](./drizzle.md) |
| Performance | [performance.md](./performance.md) |
| i18n / Crowdin | [translations.md](./translations.md) |
| i18n — Laravel | [translations-laravel.md](./translations-laravel.md) |
| Notifications | [notifications.md](./notifications.md) |
