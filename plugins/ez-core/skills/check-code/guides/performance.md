# Performance — fast Nuxt/Vue apps

How to keep this project fast: what to measure, what to optimize, and what
to avoid. Complements `vue.md` (architecture) and `docs/ui/` (image
loading, if a guide exists there). **Measure before micro-optimizing** —
profile the real bottleneck, then fix the highest-impact item.


> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.



## Non-negotiables

These rules take priority when speed conflicts with convenience.

### Measure first

- Reproduce with **production build** (`npm run build` + preview) — dev mode
  is not representative.
- Run one baseline capture before editing and one comparison capture after.
- Save key numbers (LCP, INP, CLS, JS bytes, request count, TTFB) in the PR
  or task notes so reviewers can verify no regression.
- Use **Lighthouse** (mobile profile) for Core Web Vitals: LCP, INP, CLS.
- Use **Network** tab for duplicate requests, oversized payloads, render-
  blocking scripts.
- Use **Vue DevTools → Performance** for unnecessary component re-renders.
- Fix the **slowest layer** (network, JS parse, hydration, layout, paint)
  before tuning CSS or micro-refactors.

### Protect Core Web Vitals

| Metric | Target (field) | Primary levers in this repo |
| ------ | -------------- | --------------------------- |
| **LCP** | ≤ 2.5 s | Hero image eager + dimensions; font `display: swap`; defer third-party scripts |
| **INP** | ≤ 200 ms | Avoid long tasks on input; debounce heavy handlers; split large components |
| **CLS** | ≤ 0.1 | Explicit `width`/`height` on images; reserve space for async UI |

### Performance budgets (enforce in review)

Use route-level budgets as merge guardrails. Budgets are not a replacement for
CWV; they prevent predictable regressions before field data catches up.

| Route class | JS budget (initial) | Image budget (above fold) | Request budget (initial) |
| ----------- | ------------------- | -------------------------- | ------------------------ |
| Landing / homepage | ≤ 220 KB gz | ≤ 250 KB total | ≤ 25 requests |
| Checkout hot paths | ≤ 260 KB gz | ≤ 180 KB total | ≤ 30 requests |
| Content / secondary | ≤ 280 KB gz | ≤ 250 KB total | ≤ 35 requests |

If a change exceeds a budget, include measurement evidence and a rationale
before merge.

**Measuring bundle size** — `npx nuxi analyze` (run on a production build)
opens a treemap of the client chunks. Read the initial/entry chunk gz size and
compare it against the JS budget for the route class above. Use the same number
to gate new hot-path dependencies — see "Bundle growth governance" below.

### Lab vs field metrics

- **Lab (Lighthouse)** finds regressions quickly in controlled runs and should
  be used during development. Source: PageSpeed Insights (PSI) Lighthouse run
  or a local Lighthouse run on the production build.
- **Field (real users)** validates business impact and final quality in
  production. Sources: PageSpeed Insights → CrUX (28-day real Chrome-user LCP /
  INP / CLS) and Microsoft Clarity (RUM, session signals).
- Treat "lab improved but field regressed" as unresolved until field results
  stabilize.

### One fetch per resource

- Same API endpoint + params → one `useFetch` / `useAsyncData` key, one
  composable owner (see `vue.md` SSOT).
- Do not `$fetch` the same data in `onMounted` when SSR or a parent already
  fetched it.

### Defer non-critical work

- Below-fold data → `lazy: true` on `useFetch` / `useAsyncData` or
  `useLazyAsyncData`.
- Heavy or rare UI → `defineAsyncComponent`.
- Third-party widgets (chat, analytics) → load behind a runtime flag and
  defer until first interaction or a timeout — never block first paint.

### Measurement workflow (standard loop)

1. Reproduce on production build.
2. Capture baseline (Lighthouse + Network + Performance panel).
3. Apply smallest change likely to fix the bottleneck.
4. Re-run the same measurements with the same profile/device.
5. Compare deltas and keep only changes with clear net improvement.
6. Record before/after numbers in the task or PR notes.

### Evidence template

Paste into the PR/task notes for step 6. State the capture context — mobile
Lighthouse profile, production build — and fill from the lab/field sources
named above.

```md
Capture: mobile Lighthouse, production build

| Metric             | Before | After | Budget/Target |
| ------------------ | ------ | ----- | ------------- |
| LCP                |        |       | ≤ 2.5 s       |
| INP                |        |       | ≤ 200 ms      |
| CLS                |        |       | ≤ 0.1         |
| JS (initial, gz)   |        |       | route budget  |
| Requests (initial) |        |       | route budget  |
| TTFB               |        |       | —             |
```

---

## Recommended Nuxt defaults (example configuration)

Examples to aim for in `nuxt.config.ts`:

- **Long-cache static assets** — `routeRules` for `/_nuxt/**`, `/images/**`,
  `/_ipx/**`, `/scripts/**` (`max-age=31536000, immutable`).
- **Homepage CDN cache** — `/` uses `s-maxage` + `stale-while-revalidate`.
- **Production minify + compress** — Nitro `minify` and
  `compressPublicAssets`.
- **Fonts** — `font-display: swap` whether via `@nuxtjs/google-fonts`
  (`preload: false`, `prefetch: false`) or self-hosted `@font-face` CSS
  (avoid competing with LCP).
- **Nuxt Image** — WebP default, quality from env, densities `[1, 2]`.

When adding new static asset paths or routes, extend `routeRules` with the
same cache pattern.

### Cacheable SSR routes

For non-personalized pages, cache the SSR response at the CDN so repeat visits
skip the backend. Example homepage rule:

```ts
// nuxt.config.ts → nitro.routeRules
'/': {
  headers: {
    'cache-control': 'public, s-maxage=86400, stale-while-revalidate=604800',
  },
},
```

- `s-maxage=86400` — shared/CDN cache TTL (1 day); browsers ignore it, edges honor it.
- `stale-while-revalidate=604800` — for 7 days past expiry, serve the stale copy
  instantly while the edge refreshes it in the background (no user-facing wait).
- **Caveat** — non-personalized routes only. Never apply to account, cart, or
  checkout responses that vary per user; caching those leaks one user's data to
  another.

---

## Vue reactivity and rendering

### Prefer computed over template work

- ✗ Calling a function or doing `.filter().map()` in the template on every
  render.
- ✓ `computed` in composable; template reads the derived value.

### Stable list keys

- Always `:key` on `v-for` with a **stable id**, not array index (unless the
  list is static and never reordered).

### Large or external data

- Objects that do not need deep reactivity (maps, chart libs, API blobs) →
  `shallowRef` or `markRaw`.
- Do not put huge arrays in Pinia if only one component needs them — fetch
  and hold in a composable with a narrow scope.

### Reduce re-renders

- `v-memo` on expensive list rows when props are stable between scrolls.
- Split fat templates into small child components so parent updates do not
  re-render unrelated subtrees.
- Pinia: use `storeToRefs` when destructuring state in `<script setup>` so
  reactivity is not lost and subscriptions stay granular.

### Avoid watch abuse

- `watch` with `deep: true` on large objects is expensive — watch specific
  fields or use `computed` + `watchEffect` with narrow deps.
- Do not `watch` something that should be a one-time `onMounted` fetch.
- A composable that registers `watch` in its body multiplies watchers by the
  number of components that call it. When it mutates shared state (`useState`,
  Pinia), register the watchers **once** in a single always-mounted owner (the
  page/root) and expose only state + actions to children.
- Do not fire the same initializer from overlapping lifecycle hooks — e.g.
  `onMounted` and an `immediate` watch both calling `init()`. Pick one trigger
  or guard the initializer so setup work runs once per mount.

---

## Data fetching

- Centralize in `services/` or `services/api/`; orchestrate in composables (`vue.md`).
- **Stable keys** — `useFetch('/api/cart', { key: 'cart' })` or a unique
  string per param set; enables dedup across components.
- **SSR + client** — prefer `useAsyncData` / `useFetch` over raw `$fetch` in
  `onMounted` so data can render on the server and hydrate without a flash.
- **Below-fold / on interaction** — `lazy: true` or `useLazyAsyncData`.
- **No waterfall** — parallelize independent requests with `Promise.all` in
  one composable instead of sequential `await` chains in nested components.
- **Pagination / search** — debounce input; cancel or ignore stale responses
  when the query changes.
- **Invalidation strategy** — for each fetch owner, define when data is stale
  (mutation success, route change, TTL) and use one explicit refresh path
  instead of ad-hoc duplicate fetches in children.
- **SSR cacheability** — for non-personalized API responses, prefer cache-
  friendly route/API behavior so repeated visits do not pay full backend
  latency.

---

## Code splitting and lazy loading

- **Pages** — Nuxt auto-splits `pages/`; keep page scripts thin.
- **Heavy sections** — Nuxt's `<LazyXxx>` auto-import prefix, or
  `defineAsyncComponent(() => import('…'))`, for modals, carousels, maps,
  payment widgets not needed on first paint.
- **`v-if` is not code-splitting** — a statically referenced component stays in
  the parent chunk even when gated by `v-if` / `v-show`; only the `Lazy` prefix
  or `defineAsyncComponent` moves it to its own chunk. Combine both: `Lazy` to
  split, `v-if` to defer mount.
- **Client-only APIs** — `<ClientOnly>`, `.client` plugins, or `onMounted`;
  never import browser-only libs in universal code paths.
- **Icons / illustrations** — async icon sets instead of importing every
  variant in the parent bundle.

Before adding a new top-level import, ask: is this needed for LCP or first
interaction? If not, lazy-load it.

### Bundle growth governance

- New dependency on hot paths (landing, checkout, shared layout) requires
  measured impact or lazy-loading plan.
- Prefer existing utilities/components before adding another package that
  duplicates capabilities.
- Check chunk growth during review when adding imports used by many routes.

### Isolate heavy or optional dependencies

- Never import a heavy or optional lib at the top of a **shared** composable —
  every consumer of that composable bundles it, even consumers that never use
  the feature. Move the lib into its own composable imported only by the real
  consumers.

  ```ts
  // bad — useSchema() builds ~15 schemas, used by ~20 forms; all pay for this
  import creditCardType from 'credit-card-type'
  export function useSchema() { /* paymentCardSchema uses creditCardType */ }

  // good — only the card forms import this; other forms stay clean
  // composables/usePaymentCardSchema.ts
  import creditCardType from 'credit-card-type'
  export function usePaymentCardSchema() { /* … */ }
  ```

- A dynamic `import()` only defers loading when its **call site** is deferred.
  An unconditional `await import()` inside a function that runs on first paint
  still loads the lib on first paint.

  ```ts
  // bad — runs during profile fetch on page load, so the lib loads on load
  export async function mapSavedCards(cards) {
    const { default: creditCardType } = await import('credit-card-type')
    // …
  }

  // good — use the server-supplied field; no client lib at all
  export function mapSavedCards(cards) {
    return cards.map((c) => ({ cardType: c.card_type || '', /* … */ }))
  }
  ```

- Prefer server-supplied data over pulling in a client lib to recompute it, and
  keep server-only code (Redis, cookies, `H3Event`) out of universal composables
  — move it to `server/utils/` so it never ships to the client.

### Hunt an eagerly-loaded dependency

When a lib loads on first paint but is only needed on interaction:

1. Reproduce on a **production** build, not dev (dev serves modules unbundled).
2. Open Network, hard-reload the route, find the unexpected `.js` chunk.
3. Read its **Initiator** column/chain back to the module that imports it.
4. Cut that one chain: `Lazy`-load the component, move the import into its own
   composable / a deferred call site, or drop the dep (see above).
5. Hard-reload and re-check. The **same asset with a new initiator** means
   another independent import chain reaches it — repeat from step 2.
6. Confirm the chunk now loads only on the intended interaction.

A single shared module (e.g. a kitchen-sink schema composable used by an
always-mounted step) can be the chain that survives every component-level `Lazy`
fix. When lazying components does not remove the load, inspect the shared
composables in the import chain. (`v-if` alone never helps here — it gates mount,
not bundling; see the `v-if` is not code-splitting note above.)

### Navigation and prefetch

- `<NuxtLink>` prefetches the linked page's chunk on viewport-enter by default —
  keep it for likely next hops (landing → plan → checkout entry).
- `prefetch-on="interaction"` for lower-priority links (footer, secondary nav)
  so they fetch on hover/focus instead of on sight.
- `:prefetch="false"` for rarely-clicked links — prefetching every visible link
  can blow the initial request budget; opt out of the unlikely ones.
- Checkout **step** transitions are component-level, not route navigations —
  use async component imports (see Code splitting and the Checkout hot-path
  guardrails), not prefetch.

---

## Images and fonts

Follow `docs/ui/` image guidance if a guide exists there. Performance
highlights:

- **LCP hero** — `loading="eager"` + `fetchpriority="high"` + explicit
  `width` / `height` (display pixels).
- **Everything else** — `preset="default"` + `loading="lazy"`.
- **Art direction** — `BasicPicture`; never two `NuxtImg` with
  `lg:hidden` / `lg:block` (browser downloads both).
- **Dimensions** — always set width/height to prevent CLS.

Use `font-display: swap` (`@nuxtjs/google-fonts` or self-hosted CSS). Do not
re-enable font preload without measuring LCP impact.

---

## Third-party scripts

Analytics (GTM, Meta Pixel, Clarity), chat, maps, and payment SDKs are the
most common main-thread regressions.

- Gate with a runtime flag where applicable.
- Defer loading until first user interaction or a fallback timeout, never
  synchronously on page load.
- Do not add synchronous `<script>` tags in `app.head` for non-critical
  vendors.
- Maps — load the maps SDK only on routes/components that render a map.
- Assign an owner and loading policy for every new vendor:
  - **critical** (must run near startup; rare, needs explicit justification),
  - **delayed** (post-LCP timeout),
  - **interaction-only** (load after user action).
- Unowned scripts or scripts without a policy are blocking review findings.

---

## Pinia and persistence

- `pinia-plugin-persistedstate` — persist **only** fields needed across
  sessions; large JSON blobs slow hydration and block the main thread.
- Prefer server as source of truth for cart/order; re-fetch on load instead
  of persisting stale snapshots.
- Actions for mutations; avoid widespread direct state assignment that
  triggers many subscribers.

---

## SSR and hydration

- Server HTML must match client first render — no `Date.now()`, `Math.random()`,
  or `window` access during setup without guards.
- Browser-only values → `onMounted` or `<ClientOnly>` with a sized fallback
  skeleton to limit CLS.
- Keep server components and `server/` code out of client bundles.

### Nuxt payload and hydration cost

- Keep serialized payloads small; avoid returning unused fields to pages.
- Avoid large deeply reactive blobs when plain objects or `shallowRef` are
  enough.
- Do not push large persistent snapshots into initial hydration when data can
  be re-fetched cheaply.

---

## Templates and CSS

- No heavy logic in templates — move to `computed` or composable.
- Prefer CSS transforms/opacity for animations (compositor-friendly).
- Large lists → virtualize or paginate; do not render hundreds of DOM nodes
  when only ~10 are visible.
- Tailwind: avoid enormous arbitrary class strings on hot paths; extract to
  component or `app.config.ts` variant.

---

## Checkout hot-path guardrails

Checkout is a no-regression path. Before merge:

- No new synchronous third-party scripts.
- No duplicate requests for account/address/start-date/payment state.
- No added hydration mismatch risk in step components.
- Any new SDK/UI dependency must be lazy or justified with measurements.

---

## Before you ship — checklist

1. Did I measure on a production build (not dev)?
2. Is the LCP image eager, sized, and using the smallest adequate format?
3. Are third-party scripts deferred until after interaction or timeout?
4. Is each API endpoint fetched once per page with a stable key?
5. Are large/rare components async-imported?
6. Will this change increase persisted store size or deep watchers?
7. Does SSR output match the client first paint (no hydration mismatch)?
8. Did I stay within route performance budgets, or document a measured
   exception?
9. Did I compare both lab and field metrics for high-impact route changes?

---

## Anti-patterns (smells to flag)

| Smell | Impact | Fix |
| ----- | ------ | --- |
| Duplicate `$fetch` / `useFetch` for same endpoint | Extra network + main-thread JSON parse | One composable, shared key |
| Function call in template | Re-runs every render | `computed` |
| `v-for` without stable `:key` | DOM thrash on update | Id-based key |
| Deep `watch` on large objects | Main-thread cost | Narrow deps / `shallowRef` |
| Sync third-party script in head | Blocks parse, hurts LCP/INP | Defer behind a runtime flag + interaction/timeout |
| Two `NuxtImg` for responsive swap | Double image download | `BasicPicture` |
| Huge persisted Pinia state | Slow startup | Trim persistence |
| Importing maps/payment SDK globally | Bloated initial chunk | Route/component lazy import |
| `onMounted` fetch for SSR-visible data | Loading flash, double fetch | `useAsyncData` / `useFetch` |
| Composable registers `watch` in its body, used in N components | N× watchers + redundant work on shared state | Register once in a single owner; guard re-entry |
| Overlapping init triggers (`onMounted` + `immediate` watch) | Setup runs twice per mount | One trigger; guard the initializer |

---

## Severity (for performance audits)

When auditing performance findings, rate each bottleneck:

| Severity   | Meaning | Examples |
| ---------- | ------- | -------- |
| `critical` | Measurable user-facing regression or violates a hard rule | Render-blocking script on checkout; duplicate payment-status fetch; LCP image lazy-loaded |
| `major`    | Clear perf risk; fix before merge on hot paths | Template method doing array work; missing lazy on below-fold fetch; unpersisted heavy import on landing |
| `minor`    | Real but low impact — fix when touching the file | Index keys on static list; slightly oversized image preset |
| `nit`      | Micro-optimization; only if already in the file | Naming; optional `v-memo` on cheap rows |

---

## Further reading

- [Web Vitals](https://web.dev/vitals/)
- [Vue — Performance](https://vuejs.org/guide/best-practices/performance.html)
- [Nuxt — Performance](https://nuxt.com/docs/guide/best-practices/performance)
- [Nuxt — Data fetching](https://nuxt.com/docs/getting-started/data-fetching)
- Project: `docs/ui/`, [vue.md](./vue.md), [nuxt.md](./nuxt.md)
