---
name: fc
description: >-
  Figma cache ("ensure cached"): saves Figma MCP read responses (design
  context, metadata, variables, screenshots, images, assets) as JSON files in
  a cache folder, re-fetches entries older than seven days, keeps a category
  index, and makes every UI value come from cached node data with its cached-at
  time, never from a screenshot. Use whenever a Figma design URL appears, the
  agent needs a Figma frame or value for the current task, the user asks to
  cache, refresh or ensure Figma frames or export Figma assets, says fc, or
  invokes /fc.
---

# fc — Figma cache

**Placeholders.** Where a path or value below still shows a `${…}` placeholder instead of a real value, fill it in yourself: the plugin-root placeholder (named `CLAUDE_PLUGIN_ROOT`) is this plugin's folder, two levels above the folder that holds this file; a settings placeholder (named `user_config.<name>`) is the value of `<name>` under `"ez-core"` in `~/.config/ez-skills/settings.json` (`$XDG_CONFIG_HOME/ez-skills/settings.json` when that variable is set). A missing file or key means the setting is empty.

The cache folder is the only lasting store for Figma specs. A live MCP read
happens only inside the fetch script, on a miss or a stale entry.

## Settings

- Cache folder: `${user_config.figma_cache_dir}`. Empty → `figma/cache` in
  the current repo's root.
- Fetch script: `${CLAUDE_PLUGIN_ROOT}/skills/fc/scripts/figma_cache_fetch.py`
- Index script: `${CLAUDE_PLUGIN_ROOT}/skills/fc/scripts/figma_cache_index.py`

Below, `<cache>` is the cache folder and `fetch` / `index` are
`python3 <script> --cache-root <cache>`.

## Always ensure cached

Whenever a Figma design URL appears in the user's message or the task needs a
frame:

1. Run **Ensure cached** in the same turn, before using the spec, fixing any
   UI value or citing Figma in a plan.
2. Do not call a Figma MCP tool yourself for a read the fetch script can do.
3. Never write cache JSON by hand from MCP output.

`whoami` is always live and never cached.

## Ensure cached

1. **Resolve** from the URL: `fileKey` (the path segment after `/design/`, or
   after `/branch/` for a branch URL), `nodeId` (query `node-id`, hyphen form
   such as `1-1355`), and the action (default `get_design_context`).
2. **Path:** `<cache>/<action>/<fileKey>__<nodeId>.json`; with no `node-id`,
   `<fileKey>__pages.json`.
3. **Fresh hit** (file exists, `cachedAt` at most 7 days old, UTC): read it and
   use only its `response` field. No MCP call.
4. **Miss or stale:** run `fetch --url '<url>' --action <action>`, then read
   the written file.
   - Needs the Figma desktop app with the Dev Mode MCP Server on
     (`http://127.0.0.1:3845/mcp`). Unreachable → tell the user to turn it on
     (Figma desktop → Preferences → Enable Dev Mode MCP Server); no retry loop.
   - Category: take it from `<cache>/categories.yml` or the task's sources
     when obvious; otherwise ask one question listing the slugs in
     `categories.yml`.
   - After a write, add the rule `<fileKey>__<nodeId>: <category>` under
     `node_ids` in `categories.yml`, then run `index`. The fetch script
     already rebuilds the index after a write; run it again after editing
     `categories.yml`.
   - The script writes nothing on failure: report the blocker and do not fall
     back to a live read or an expired file as the lasting source.
5. **Look up** entries through `<cache>/INDEX.md` and `<category>.md` rather
   than raw JSON file names.

For `get_design_context`, screenshots stay out of the cache unless the user
asks (`--include-screenshot`).

## Freshness

- TTL is 7 days. The script re-fetches a stale entry by itself (prints
  `cache stale: … — refreshing`).
- `--refresh` always re-fetches; so does an explicit user ask to refresh.
- `--no-refresh-stale` keeps an old file; use it only when the user asks.

## Citing cache in replies

Every value taken from the cache (colour, spacing, copy, layout) names its
file and its `cachedAt`; values from several files carry each file's time. A
live read says "live". Example:
`P100 #F3F6F5 — cached at 2026-08-05T18:32:46Z from <cache>/get_design_context/<fileKey>__34437-61031.json`

## Never implement from a screenshot

Every value in code comes from node data, never from a rendered frame.
Screenshots show layout and state only. A pixel is a composite (fill ×
opacity × blend × what is behind it, resampled), so reading it back gives a
value that exists nowhere in the design system.

- Values come from `get_design_context` fills, `get_variable_defs`, or the
  design-system palette frame, each cached as above.
- When the cached payload lacks a value (structure-only `get_design_context`
  is common), fetch that node or its `get_variable_defs` and cache it too.
- When the data cannot be had, ask. Never sample pixels, eyedrop a PNG, or
  infer a token by comparing a render with the palette.
- This holds for every value: colours, radii, gaps, font sizes, opacity.

Bad: the cached context has no fills, so the agent samples a badge from the
PNG (`#FF8477`), ships that hex, then invents a new token for it; the real
fill was an existing token with opacity. Good: the agent fetches
`get_variable_defs` for the node, reads the token, ships it, and the cache now
holds the fills. Good: Figma desktop is closed, so the agent reports the
blocker and asks for the fill.

## Actions

- `get_design_context`: implementation spec (layout, styles, generated code).
  `--client-languages` / `--client-frameworks` default to `typescript,vue` /
  `vue,nuxt`; pass the project's own.
- `get_metadata`: node tree and sizes; works without `node-id`.
- `get_variable_defs`: variables resolved on a node (`node-id` required).
- `get_screenshot`: visual reference only, never a shipped file.
- `get_image`: rendered node PNG at 1×, a preview only.
- `search_design_system` (`--query` required), `get_libraries`,
  `download_assets` (`--scale`): exist only on Figma's remote MCP server, not
  on the desktop server, so they work only when `--server` points to a server
  that has them.

Cache file names: `<fileKey>__<nodeId>.json`, `<fileKey>__pages.json`,
`<fileKey>__search__<query-slug>.json`, `<fileKey>__libraries.json`
(`__libraries__offset<N>.json` with `--libraries-offset`). Each JSON holds
`cachedAt`, `url`, `fileKey`, `nodeId`, `action`, `toolArgs`, `response`, and
`searchQuery` or `librariesOffset` when used.

## Asset files

With Figma desktop open, `--save-files` downloads asset bytes without
hand-exporting; it writes them plus `manifest.json` (paths and sizes) to
`--files-dir` (default `<cache>/assets/<action>/<fileKey>__<nodeId>`). A fresh
cache hit re-downloads without an MCP call.

`get_design_context` already embeds the asset URLs, for example
`const imgFrame = "http://localhost:3845/assets/a8f8….svg";`. Find the `img…`
names in the cached JSON (`response.content[0].text`).

- SVG icon: `get_design_context` on the parent frame, `--save-files
  --asset-var imgFrame --only svg`.
- Photo source (for a crop): `get_design_context` on the frame that holds it,
  `--save-files --asset-var <imgName>`.
- Frame PNG for a visual check: `--action get_image --save-files` (1× only).
- Raster committed to an app: export at 2× the frame size (`download_assets`
  with `--scale 2` on a server that has it, or the user's export); never
  commit a 1× `get_image` file. Then follow the project's own image rules.
- Positions and sizes: `get_design_context` on the page frame, no
  `--save-files`.

Then copy the files into the app repo (clean SVGs to `currentColor` where the
project does), and leave committing to the user.

Examples (run from any folder; `<cache>` as above):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/fc/scripts/figma_cache_fetch.py --cache-root <cache> --url 'https://www.figma.com/design/<fileKey>/...?node-id=33352-80922'
```

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/fc/scripts/figma_cache_fetch.py --cache-root <cache> --url 'https://www.figma.com/design/<fileKey>/...?node-id=33352-80922' --save-files --asset-var imgFrame --only svg --files-dir <cache>/assets/icons/mail-check
```

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/fc/scripts/figma_cache_fetch.py --cache-root <cache> --action get_variable_defs --url 'https://www.figma.com/design/<fileKey>/...?node-id=34437-61031'
```

## Index

- `INDEX.md`: entry counts and links per category.
- `<category>.md`: one table per category (layer name, action, file,
  explanation, cached time).
- `categories.yml`: rules in priority order `node_ids` → `layer_names` →
  `patterns` → `fallback`, plus optional `titles` (`<slug>: <Title>`); listed
  titles sort first in `INDEX.md`.

The index files are generated; never edit them by hand.

## User invoke (`/fc`)

`/fc <url> [<url> …]`, optionally with an action (`/fc get_metadata <url>`).
Run **Ensure cached** per URL; on a miss, ask the category question if needed
and list the URLs before fetching. Report per URL: fresh hit (path,
`cachedAt`, category), stale refreshed (old and new `cachedAt`), written
(path, size, category), or failed (reason).

## Do not

- Cache `whoami`.
- Call a Figma MCP tool when a fresh cache file exists.
- Cite cached Figma values without their cached time.
- Retry in a loop on rate-limit or quota errors: use the cache if present,
  otherwise tell the user and stop.
