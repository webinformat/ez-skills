# Translations (Crowdin + source locales)

How to add or change user-facing copy.

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> **SSOT for every application repo.** Key naming, reuse, region overrides,
> and composition rules live **only here**. App repos may
> document locale **wiring** (e.g. `mergeLocaleMessages`, `localeConfig.ts`)
> in `docs/coding/translations.md` — not a second copy of these rules.
> **The project README overrides this guide.** Its **Translations** line or
> section (§ Project specifics) says which locale files an edit goes in and
> wins over the defaults below.

## Before editing

1. Read the project README's **Translations** line or section. No such
   line: ask the project owner which locale files an edit goes in, then
   save the answer as that line in the README so it is not asked again.
2. **Application repo in Crowdin** (the README says so, or the repo has a
   `crowdin.yml`): open **`crowdin.yml`** at the application repo root
   (next to `package.json`), read **`base_path`** and every
   **`files[].source`** entry, and resolve each source path: `base_path` +
   source without the leading `/` (e.g. `./src/i18n` + `/en.json` →
   `src/i18n/en.json`). Edit **only** those source files for copy changes,
   in every source file that owns the changed key. A task briefing or other
   documentation that names a target file does not override
   **`crowdin.yml`**; only the project README does.
3. **Application repo in Crowdin:** **never** hand-edit target locale files
   (`ar*`, `ru*`, etc.) — Crowdin manages them via upload/download.
4. **Application repo not in Crowdin:** its locale files are not on
   Crowdin, so nothing fills the other locales. Add or change the key in
   **every** locale file.
5. **Application repo in Crowdin:** source copy can go on any branch.
   Which branches Crowdin syncs is set in the project's Crowdin integration
   (selected branches or a branch-name pattern); Crowdin returns the
   translations as a merge request from a service branch (`l10n_<branch>`).
   The project README names the branches or pattern its integration syncs.

## Rules

- **In a repo in Crowdin, Crowdin syncs translated bundles.** Do **not**
  hand-edit non-English **target** locale files (e.g. `ar.json`,
  `ar-ae.json`, `ar-SA.json`, `ru.json`). Obtain targets via the project's
  Crowdin workflow — not by editing those files in the repo.
- **In a repo in Crowdin, add or update strings only in English source
  locale file(s)** listed in `crowdin.yml` `files[].source`. In a repo not
  in Crowdin, update the key in every locale file.
- A project may have **more than one** source file (e.g. `en.json` and
  `en-SA.json`). Update every source file that owns the keys you change.
- Use stable `vue-i18n` key paths in components (`$t('…')`); never hardcode
  user-facing strings — **except dev showcase pages** (`pages/dev/*`,
  `src/views/Dev/*`, and dev-only components under `components/dev/` or
  `src/components/dev/`). Hardcoded English is fine there; do not add locale
  keys for dev-only copy unless the user asks. `check-code` skips i18n
  findings on those paths.
- When helpful, list new keys in the PR or release notes for translators.

## Before adding a key

Run this checklist **in every project** before creating or editing locale
JSON (agents: also enforced by `check-code` when scope touches i18n):

1. **Grep the common English source** (`en.json` or project equivalent) for
   the text and for an existing key on the same semantic role.
2. **Reuse** if the key exists — use `$t('global.…')`, `$t('header.…')`, etc.
   Do not invent a parallel path (`simple_header.save_off` when
   `header.save_off` exists).
3. **Override, don't duplicate** — when regional wording differs, change
   only that key path in the regional **source** file (`en-SA.json`, etc.).
   Never copy an unchanged value from the common file into the override.
4. **Reusable generic copy → `global`** in the common file (CTAs, actions,
   labels used in more than one place) — not per-component keys, not in the
   override unless KSA/UAE wording differs. In an app whose source has a
   top-level `buttons` group, `buttons.*` counts as `global`: code that may
   read `global.*` may read `buttons.*`; new reusable labels still go to
   `global`.
5. **Region-gated UI** — keys for surfaces other regions never see belong in
   the regional source, not the common file (see § Region-gated copy).
6. **Key names = copy only** — no `_bold`, `_medium`, `_red`, etc. (see §
   Key names).
7. **Composed lines** — glue punctuation (` - `, ` · `) in the template, not
   trailing on one `$t()` fragment (see § Composed lines).
8. **Numbers are values** — `{percentage}`, `{count}`, etc. from code, not
   literal digits in JSON (see § Copy vs values).

## Minimize translation surface

Prefer **fewer, reusable strings** over many near-duplicate keys.
Translators and Crowdin work cost scale with string count — and stable
strings are easier to maintain when values change.

### Copy vs values

Translation strings hold **copy** — words and grammar translators adapt per
locale.

**Values** are runtime data from config, API, or programme logic: numbers
(counts, ages, percentages, amounts), dates, durations, currency, regions,
and any other fact that may change without rewriting the sentence.

**Numbers are values.** Literal digits must **not** appear in locale JSON —
not in dedicated stat/value fields and not embedded in labels, headlines,
or body copy (`age 60`, `50%`, `25–65`, `40.`). Use named placeholders
(`{age}`, `{ageNumber}`, `{count}`, `{ageStart}`, `{ageEnd}`)
and pass the figures from code via `t()` / `rt()` params.

Even when a number reads as part of the sentence (“remains by age 60”,
“risk doubles by age 40”), it is still a value — not copy translators should
own in every locale.

### Placeholder naming

Placeholders must be **easy to identify** in Crowdin and in code. **Param
keys in `rt()` / `t()` must match** the placeholder name in the string.

- **Markup tags** — exact `useLocaleTags` keys: `{colorOrangeStart}`,
  `{brTag}`, `{semiboldStart}`. No aliases (`accentStart`).
- **Runtime values** — name what the value **is** (`age`, `ageNumber`,
  `programmeWeeks`). Use surrounding copy for context; no abstract names
  (`headlineHighlight`) or redundant prefixes (`statAge` when prose says
  “by age”).

| | |
| --- | --- |
| **Bad** | `{headlineHighlight}` — unclear what is highlighted |
| **Bad** | `{statAge}` in `"lost by age {statAge}"` — redundant prefix |
| **Good** | `{ageNumber}` in `"halves by {ageNumber}"` — an age figure |
| **Good** | `{age}` in `"lost by age {age}"` — prose already names it |
| **Bad** | `"remains by age {statAge}"` with `statAge: 60` in code |
| **Good** | `"remains by age {age}"` with `age: 60` in code |

### Placeholders over duplicate keys

Use **vue-i18n interpolation** for values — numbers, dates, regions, and
any other part that may change without rewriting the sentence.

| | |
| --- | --- |
| **Bad** | `recipes_uae: "30 recipes"` and `recipes_ksa: "20 recipes"` as separate keys |
| **Good** | `recipes_count: "{count} recipes"` — pass `count: 30` or `20` from region config |
| **Bad** | `"label": "remains by age 60"` — age frozen in copy |
| **Good** | `"label": "remains by age {age}"` — `age: 60` from component meta or config |
| **Bad** | `"label": "risk doubles by age 40"` or `"value": "50%"` in locale JSON |
| **Good** | Label: `"risk doubles by age {age}"`; stat figure from `statValues` in code, not `en.json` |

When the offer changes from 30 to 33 recipes, update the placeholder
value in code or config — not a new Crowdin string in every locale.

Same idea for region names, currency amounts, plan durations, and any
other variable embedded in marketing copy.

### Region-gated copy (locale source file)

When a route, page, or component is **only shown for one region** (router
`meta.region`, region fallback redirect, or task/docs mark the surface as
KSA-only / UAE-only):

- Put **region-only keys** in the regional English source (`en-SA.json`, etc.)
  when other regions never see that UI — e.g. copy for a KSA-only campaign
  page, not the common `en.json` base.
- Common `en.json` is for copy shared by `en-ae` **and** merged override
  locales, or for keys every region needs.
- Before adding keys, check the route table and app `docs/coding/translations.md`
  for `mergeLocaleMessages` / override locale wiring.

**Do not duplicate `en.json` in the override file.** Regional sources are
**overrides**, not a second copy of the common tree:

1. **Grep `en.json` first** for the exact text or an existing key.
2. If the string **already exists** in `en.json` — **reuse that key** in
   code (`$t('global.get_started')`, etc.). **Do not** add the same value
   again under `en-SA.json` or under a component-specific path.
3. Add to `en-SA.json` **only** when the KSA wording **differs** from
   `en.json`, or when the key path is **locale-only** (no `en.json` entry
   and UAE never needs it).

**Reusable generic copy → `global` in `en.json`.** Strings that are not tied
to one component/section and can be reused across the app (CTAs, common
labels, actions) belong under `global` in the common file — not duplicated
per component and not parked in `en-SA.json` unless KSA wording differs.

| | |
| --- | --- |
| **Bad** | `simple_header.get_started` in `en-SA.json` when `global.get_started` already exists in `en.json` |
| **Bad** | `simple_header.save_off` when `header.save_off` already exists — override `header.save_off` in `en-SA.json` instead |
| **Bad** | `simple_header` campaign strip keys in `en.json` for a page gated to `meta.region: "sa"` |
| **Good** | KSA strip overrides `header.save_off` in `en-SA.json`; CTA uses `$t('global.get_started')` |
| **Good** | Override in `en-SA.json` only when KSA copy differs: `"rated_in_uae"` → `"Rated in KSA"` |

`check-code` audits flag wrong source file **and** duplicate `en.json`
values in `en-SA.json` as `major` when scope includes locale JSON or
region-gated routes.

### Key names — copy only, not presentation

Locale keys name **what the string says**, not how it looks in one layout.

| | |
| --- | --- |
| **Bad** | `save_off_bold`, `title_medium`, `label_red` — typography or colour in the key |
| **Good** | `save_off`, `title`, `label` — apply `font-bold`, `font-medium`, colour in the Vue template |

Presentation (weight, size, colour, underline) belongs in markup/classes or
theme props — never in the JSON key path.

### Composed lines — punctuation stays out of locale JSON

When one visual line is built from **multiple translated segments** (separate
`<span>`s with different styles, or slots in `i18n-t`):

- Each key holds **words only** for that segment — no trailing or leading
  punctuation used only to glue segments together.
- **Separators** (` - `, ` · `, `|`, line breaks between blocks) go in the
  **template**, not in locale JSON. Translators should not receive a dash on
  one fragment and an exclamation on the next unless that punctuation is
  part of the phrase itself (e.g. `"LIMITED TIME OFFER!"`).

| | |
| --- | --- |
| **Bad** | `"save_off": "SAVE {percentage}% OFF -"` plus `"limited_time_offer": "LIMITED TIME OFFER!"` — the dash is layout glue, not copy |
| **Good** | `"save_off": "SAVE {percentage}% OFF"` and `"limited_time_offer": "LIMITED TIME OFFER!"` with ` - ` in the template between spans |
| **Good** | One `i18n-t` key with named slots when word order must change per locale (see **Rich copy** below) |

If grammar requires different punctuation per locale, use one composed key
with placeholders/slots — do not split on punctuation that only exists for
English layout.

`check-code` flags presentation in key names and glue punctuation on
composed segments as `major` when scope includes locale JSON.

### Repeated similar strings (lists / steps)

Prefer **one JSON array of objects** over a family of numbered flat
keys. Resolve with vue-i18n `tm` (read the array) + `rt` (resolve each
field; pass named values for placeholders).

| | |
| --- | --- |
| **Bad** | `step_01_title` / `step_01_body` … `step_06_title` / `step_06_body` |
| **Good** | `steps: [{ "title": "…", "body": "…" }, …]` then `tm` + `rt` |

Keep icons and other non-copy presentation in code, indexed by array
order.

### One line, one key

- **One logical line → one key** unless pluralisation or grammar forces
  a split (e.g. ICU plural rules).
- **Reuse** existing keys before adding new ones — grep the English
  source for the text first.
- **Rich copy** (line breaks, color, links inside a sentence): use
  named placeholders or a project composable (e.g. `useLocaleTags()`)
  that maps tokens to markup in TypeScript — **do not** embed HTML or
  Tailwind classes in source JSON.

Agents: before editing locale JSON, read the project README's
Translations line, `crowdin.yml` for a project in Crowdin, and this doc.
