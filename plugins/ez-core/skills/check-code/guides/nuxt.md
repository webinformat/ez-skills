# Nuxt 3 — coding guide

Nuxt-specific conventions. **Read [vue.md](./vue.md) first** — DRY, thin
components, composables, components, error handling, and audits live there.

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.

## Directory roles (Nuxt)

| Directory       | Purpose                                                           |
| --------------- | ----------------------------------------------------------------- |
| `pages/`        | File-based routes; minimal logic, compose sections                |
| `server/`       | Nitro API routes, server middleware, server-only utils            |
| `plugins/`      | App-level setup (client/server)                                   |

Shared directories (`components/`, `composables/`, `utils/`, `stores/`,
`services/`, `i18n/`) — see [vue.md § Directory roles](./vue.md#directory-roles).

Nuxt auto-imports `composables/*.ts` and one level of subfolder index files
(`composables/foo/index.ts`), plus `components/`. Composables nested deeper, or
non-index files inside subfolders, aren't scanned by default — register them
via `imports.dirs` in `nuxt.config`.

---

## Components (Nuxt add-ons)

From [vue.md § Components](./vue.md#components) — additionally:

- **Auto-import name** is built from path segments — see
  [Nuxt components](https://nuxt.com/docs/guide/directory-structure/components).
  Split folders (`Promo/Code/`) aid navigation; compound folders
  (`PromoCode/`) are equivalent for import names but harder to browse.
- Images: `<NuxtImg>`; see `docs/ui/` for image guidance when present.

---

## Nuxt UI customization

Nuxt UI components (`UButton`, `UBadge`, `UInput`, `UFormGroup`, etc.) should
use **project variants in `app.config.ts`** when the component supports it.
That keeps visual SSOT next to other design tokens — not scattered `:ui`
class strings.

### Preference order

1. **`app.config.ts`** — add or extend `ui.<component>.variant`, `color`,
   `size`, and related keys when the look is part of the design system or
   reused in **two or more** places. Document new keys in the matching
   `docs/ui/*` guide.
2. **Named props at call sites** — `variant` and `size` (or `color` where
   that is the Nuxt UI API) using names from `app.config.ts`. Consumers pick
   tokens; they do not repeat Tailwind for colors, borders, hover, or disabled
   states.
3. **Per-instance `:ui="{}"`** — **one-off** layout or edge-case tweaks
   only (e.g. `w-full` on a single screen). Do **not** put shared colors,
   typography, or state styles here.
4. **Wrapper components** (`components/Basic/*`) — when you need
   composition, slots, or chrome Nuxt UI does not provide (e.g.
   `BasicRadioCard`). The wrapper owns structure; underlying Nuxt UI
   children should still use `app.config` variants where possible.

### Before / after

```vue
<!-- ✗ same classes copied on every button -->
<UButton
  :ui="{
    base: 'font-semibold text-white bg-primary-500 hover:bg-primary-600 disabled:opacity-50',
  }"
>
  Continue
</UButton>
```

```vue
<!-- ✓ variant + size from app.config.ts -->
<UButton variant="primary" size="lg">
  Continue
</UButton>
```

- When adding a variant: get Figma specs → add the config entry in the active
  repo's `app.config.ts` → document in the matching `docs/ui/*` guide and
  verify on the target route before shipping.

---

## Data fetching

- Centralize HTTP in `services/` or `services/api/`; composables orchestrate
  loading/error state.
- Prefer `useFetch` / `useAsyncData` with stable keys; do not wrap the same
  endpoint in multiple places with different ad-hoc `fetch` calls.
- Feature flags: `useFeatureFlag.ts` — not raw `runtimeConfig` in components.

---

## Utils vs composables vs stores (Nuxt)

From [vue.md](./vue.md#utils-vs-composables-vs-stores) — Nuxt-specific layers:

4. **Server data** → `useFetch` / `useAsyncData` in composable with stable
   keys; API functions in `services/` or `services/api/`.
6. **Secrets or upstream APIs** → `server/api/` BFF when needed; client calls
   server route via `useFetch`.

---

## SSR and Nuxt specifics

- Browser-only APIs → `onMounted`, `<ClientOnly>`, or `.client` suffix plugins.
- Server-only code stays in `server/` or `.server` components; never import
  `#server` from client bundles.
- Use Nuxt auto-imports; run `nuxt dev` or `nuxt prepare` so composable types
  generate in `.nuxt/imports.d.ts`.

---

## Before you add code — Nuxt checklist

In addition to [vue.md § checklist](./vue.md#before-you-add-code--checklist):

1. Can this be an `app.config.ts` variant instead of inline `:ui` or local
   classes on a Nuxt UI component?

---

## Anti-patterns (Nuxt)

In addition to [vue.md § Anti-patterns](./vue.md#anti-patterns-smells-to-flag):

- The same endpoint fetched in several places with ad-hoc `$fetch` → one
  API-layer function + one composable; reuse the `useFetch` key.
- Reading `runtimeConfig` / env directly in a component → `useFeatureFlag` or a
  composable.
- The same Nuxt UI `:ui` class strings copied across files → add or use an
  `app.config.ts` variant (see **Nuxt UI customization** above).

---

## Performance

Nuxt SSR and hydration: **`performance.md`** plus [vue.md § Performance](./vue.md#performance).

---

## Further reading

- [Vue 3 coding guide](./vue.md)
- [Performance — fast Nuxt/Vue apps](./performance.md)
- [Nuxt 3 — Directory structure](https://nuxt.com/docs/guide/directory-structure/overview)
- [Nuxt 3 — Composables](https://nuxt.com/docs/guide/directory-structure/composables)
- [Nuxt 3 — Data fetching](https://nuxt.com/docs/getting-started/data-fetching)
