# Vue 3 + TypeScript — coding guide

Project conventions for structure, state, and logic. Curated from official
Vue guidance and established community patterns. **Design tokens and UI
components** have their own guides under `docs/ui/` — use those for visual
work; this guide covers architecture and code organization.

Nuxt 3 apps also have [nuxt.md](./nuxt.md) (pages, data fetching,
Nuxt UI, SSR).

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.

## Non-negotiables

These rules take priority over convenience or speed.

### DRY (Don't Repeat Yourself)

- One canonical implementation per behavior, constant, condition, or data shape.
- Repeated template logic → computed or small component.
- Repeated script logic → composable or util.
- Repeated API calls → API layer function (under `services/` or
  `services/api/`) used from one composable or store.
- Before adding new code, search for an existing composable, util, store
  method, or shared component that already does it.

### Thin components

`.vue` files are for **template + wiring**, not business logic.

- Keep `<script setup>` short: props/emits, store/composable calls, and glue.
- Move reactive logic, side effects, validation, and transforms to
  composables.
- Move pure functions (formatters, mappers, validators with no Vue deps) to
  `utils/`.
- Move cross-feature or persisted app state to Pinia `stores/`.
- If a component script grows past ~80–100 lines or mixes several concerns,
  extract.

### Single source of truth (SSOT)

Every piece of data or configuration has **one owner**:

| Kind                                    | Owner                                              | Consumers                  |
| --------------------------------------- | -------------------------------------------------- | -------------------------- |
| Design tokens (colors, buttons, badges) | `tailwind.config.js`, theme config, `docs/ui/*`    | Components via utilities   |
| API request/response shapes             | API layer (`services/` or `services/api/`) + types | Composables / stores       |
| Feature flags                           | `useFeatureFlag` composable (or project equivalent) | Components, routes         |
| User-facing copy                        | English source locale (see `translations.md`)      | `$t()` / `useI18n()`       |
| Feature / domain state                  | Pinia stores                                       | Components via composables |
| URL-reflecting state (filters, step)    | route query or store synced to route               | Views/pages, deep children |

Do not duplicate the same value in a component and a store, or in two
composables, without a clear derived relationship (`computed` from the
canonical source).

**The id-refetch trap:** when one page passes only an entity's **id** (e.g.
via a store) and the next page refetches the entity, write the result back
to the canonical owner — never into a new `ref` in another composable. Two
live refs that both claim to be "the invoice" (one populated per flow, the
other silently empty) is an SSOT violation even though each was populated
legitimately; consumers wired to the wrong ref read `0`/`undefined` with no
type error.

### Consistency in design and logic

- **Design:** follow `docs/ui/*` and existing components in the same feature
  folder before inventing new patterns.
- **Logic:** match naming, file placement, and abstractions used in sibling
  features.
- **Imports:** use project composables and stores; do not fork parallel
  implementations for the same domain.
- **Import paths:** use the `@/` alias with the **full path from `src/`**
  for project modules — components, composables, stores, `utils/`, views,
  `services/`, and other app code. Do not use relative paths (`./`, `../`)
  to reach them, including imports between files in the same folder.

  ```ts
  // ✓
  import MainBar from "@/components/Header/Simple/MainBar.vue";
  import { usePopup } from "@/composables/usePopup";

  // ✗
  import MainBar from "./MainBar.vue";
  import { usePopup } from "../composables/usePopup";
  ```

  Vite/Nuxt resolve `@` to `src/` (or the app equivalent). Prefer the explicit
  file path (e.g. `index.vue` when importing a folder entry) so every import
  is grep-friendly and stable when files move.
- When two approaches exist in the codebase, prefer the newer/canonical one
  over a legacy implementation unless the task explicitly targets legacy code.

### Early return

- Handle invalid input, missing data, and error branches first; `return`
  (or `throw` / `continue` in loops) before the main path.
- Prefer guard clauses over wrapping the happy path in `if (ok) { … }`.
- Keep the success path at the lowest nesting level.
- In Vue handlers and server routes, return early before side effects when
  validation fails.

### Function size

- One job per function; target ~25–40 lines for the body.
- Extract helpers, composables, or utils when a function exceeds ~40 lines,
  nests more than 2–3 levels, or mixes concerns (e.g. validate + fetch + map
  + store update).
- Component script limit (~80–100 lines) is file-level; functions inside must
  stay smaller.
- Same limits apply to composables, utils, store actions, and server-side
  handlers.

---

## Patterns (before → after)

**Thin component** — move logic into a composable:

```vue
<!-- ✗ logic in the component -->
<script setup lang="ts">
const items = ref([])
onMounted(async () => {
  const res = await cartService.fetch()
  items.value = res.data
    .filter((i) => i.active)
    .map((i) => ({ ...i, total: i.qty * i.price }))
})
const subtotal = computed(() => items.value.reduce((s, i) => s + i.total, 0))
</script>
```

```vue
<!-- ✓ component just wires; useCart owns fetch + transform + subtotal -->
<script setup lang="ts">
const { items, subtotal } = useCart()
</script>
```

**DRY** — one owner for a repeated call or rule:

- ✗ the same cart fetch + mapping pasted into two components.
- ✓ one `services/cart.ts` or `services/api/cart.ts` fetch + one `useCart`
  composable, consumed in both.

**SSOT** — derive, don't copy:

```ts
// ✗ a second copy that drifts
const subtotal = ref(store.subtotal)
// ✓ computed from the canonical source
const subtotal = computed(() => store.subtotal)
```

**Early return** — guard clauses instead of nested `if`:

```ts
// ✗ nested happy path
async function submitOrder(cart: Cart | null) {
  if (cart) {
    if (cart.items.length > 0) {
      if (cart.total > 0) {
        await charge(cart)
      }
    }
  }
}
```

```ts
// ✓ validate first; main path stays flat
async function submitOrder(cart: Cart | null) {
  if (!cart) return
  if (cart.items.length === 0) return
  if (cart.total <= 0) return

  await charge(cart)
}
```

**Named event handlers** — no multi-statement inline arrows in templates:

```vue
<!-- ✗ inline arrow with side effects in the template -->
<UButton
  @click="() => {
    step = 2
    loadItems(selectedCategory)
  }"
>
  {{ $t('global.next') }}
</UButton>
```

```vue
<!-- ✓ named handler in <script setup> -->
<script setup lang="ts">
const goToItemsStep = () => {
  step.value = 2
  loadItems(selectedCategory.value)
}
</script>

<UButton @click="goToItemsStep">
  {{ $t('global.next') }}
</UButton>
```

Simple one-liners (`@click="step--"`, `@click="submit()"`) are fine.
Use a named function when the handler does more than one thing or calls
async logic.

---

## Directory roles

| Directory                    | Purpose                                         |
| ---------------------------- | ----------------------------------------------- |
| `components/`                | Presentational and feature UI; see § Components   |
| `composables/`               | Reusable reactive logic; `useX.ts` naming         |
| `utils/`                     | Pure, stateless functions (no `ref`/`reactive`)   |
| `stores/`                    | Pinia — shared app state by domain                |
| `services/` or `services/api/` | HTTP calls and API types                        |
| `i18n/`                      | Translation source locale files                 |
| `views/` or route-level dirs | Top-level route views (stack-specific layout)     |

Route file layout differs by stack (`pages/` in Nuxt — see `nuxt.md`;
`src/views/` in many vue-cli apps). Match the active repo.

---

## Components

- Always `<script setup lang="ts">` — no Options API.

### Reuse-first (before creating a component)

Design components generic and reusable by default. Before adding a new
component, work this decision tree in order:

1. **Search `components/` for the UI role first.** Look for an existing
   component that already does this job (e.g. a testimonial video row, a
   lead form, a stats band) before creating anything.
2. **Extend, don't fork.** If one exists, adapt it via props, slots, or
   theme variants. Do not copy it into a page-specific variant.
3. **Name by role/domain, never by page, route, or campaign.** No page
   slug, route key, or campaign name in component paths.
4. **Page-scoped only when genuinely single-use.** Create a one-page
   component only when the UI truly cannot be reused; state why.
5. **Promote on second use.** When a second consumer appears, move the
   component to a role-based shared path instead of duplicating it.

| Don't (page/campaign-scoped) | Do (role-based) |
| --- | --- |
| `Section/CampaignX/Form/` | `Section/Lead/Form/` |
| `Section/PromoY/Card/` | `Section/Promo/Card/` |
| `Section/CampaignX/Trust/` | `Section/Testimonials/Video/` |
| `Section/Product/Lp/Feature/` | `Section/Product/Feature/` |

Shared sections used by both a landing page and another surface (e.g. product
page) live under the **domain** folder (`Section/Product/…`), never under
`Lp/` or any other page/campaign segment. Reserve `…/Lp/…` for true
landing-page-only UI.

### Folder naming

Each PascalCase name segment is one folder. Never glue multiple segments into
one compound folder name. Folder names use PascalCase for the segment (e.g.
`Footer/`, `Simple/`).

Role and layout folders follow the same rule (`Body/`, `Summary/`, `Tabby/Row/`,
not `TabbyRow/`).

**Why nest:** group by feature and colocate related parts (e.g. section `Body`,
`Summary`, sub-rows).

| ✓ | ✗ |
| --- | --- |
| `Section/Footer/Simple/` | `Section/FooterSimple/` |
| `Checkout/Sections/Contact/Details/Body/` | `Checkout/Sections/ContactDetails/` |
| `Checkout/Sections/Date/Time/Body/` | `Checkout/Sections/DateTime/` |
| `Checkout/Sections/Promo/Code/Body/` | `Checkout/Sections/PromoCode/` |
| `Checkout/Sections/Payment/Method/Tabby/Row/` | `Checkout/Sections/PaymentMethod/TabbyRow/` |

- Prefer shared shells (e.g. `StepCard`) over one-off padding/layout in a
  single step.

### Template — keep logic in script

Templates wire markup to state — they do not decide it.

- **No ternary (`?:`) in the template** — not in `:class`, `:is`, `:variant`,
  or `{{ }}`. Put the branch in `<script setup>` (`computed`, or `if`/`return`
  inside a computed) and bind the result.
- **No `v-if` / `v-else-if` ladders** for layout or styling variants — extract
  a child component, or at most one `v-if` / `v-else` pair when the two
  branches are structurally different trees (not class tweaks).
- **Responsive show/hide is fine** — a single `v-if` on a breakpoint flag
  (e.g. `mdAndLarger`) or a dedicated sub-component is OK; chains of three or
  more `v-else-if` branches are not.
- **`:class` object/array syntax is fine** when every key is a fixed class
  name bound to a boolean computed in script — not when the class string itself
  is built with `?:` inline.

```vue
<!-- ✗ logic in template -->
<h2 :class="isPromo ? 'text-xl font-semibold text-gray-800' : 'text-2xl font-bold'">
<AppButton :variant="isPromo ? 'green' : 'yellow'" />
<component :is="isPromo ? 'div' : 'section'">

<!-- ✓ same decisions in script -->
<h2 :class="titleClass">
<AppButton :variant="buttonVariant" />
<component :is="rootTag">
```

```ts
const titleClass = computed(() => {
  if (isPromo.value) return "text-xl font-semibold text-gray-800 lg:text-3xl";
  return "text-2xl font-bold sm:text-4xl";
});
```

- User-facing strings → `$t('key')` / `useI18n()`; see `translations.md` for the
  source-locale / Crowdin workflow.
- RTL: prefer logical spacing (`ps-*`, `pe-*`, `ms-*`, `me-*`) over
  directional (`pl-*`/`pr-*`, `ml-*`/`mr-*`) so Arabic mirrors correctly.
- Images: follow `docs/ui/` image guidance when present in the active repo.

### Styling — Tailwind over scoped CSS

Express layout, color, spacing, and motion with **Tailwind utilities** on
template nodes, `:class`, and component theme props / global config. Do **not**
add `<style scoped>` blocks with bespoke class names when utilities can do the
job.

- **Tokens:** use theme utilities from `tailwind.config.js` and project CSS;
  for colors see `docs/ui/colors.md` when present. Prefer scale utilities over
  arbitrary bracket values unless no token fits.
- **RTL:** keep using logical spacing (`ps-*`, `pe-*`, `ms-*`, `me-*`) — see
  the RTL bullet above.
- **Vue `<transition>`:** bind Tailwind classes on the transition element —
  `enter-active-class`, `leave-active-class`, `enter-from-class`,
  `enter-to-class`, `leave-from-class`, `leave-to-class`. Do **not** use
  `name="…"` with paired scoped CSS hooks (`.foo-enter-active`, etc.).

```vue
<!-- ✗ scoped transition hooks -->
<transition name="panel-slide">
  <div v-show="open">…</div>
</transition>

<style scoped>
.panel-slide-enter-active { transition: all 0.3s ease; max-height: 500px; }
.panel-slide-enter-from { max-height: 0; opacity: 0; }
</style>
```

```vue
<!-- ✓ Tailwind on <transition> -->
<transition
  enter-active-class="transition-all duration-300 ease-in-out overflow-hidden"
  leave-active-class="transition-all duration-300 ease-in-out overflow-hidden"
  enter-from-class="max-h-0 opacity-0"
  enter-to-class="max-h-[500px] opacity-100"
  leave-from-class="max-h-[500px] opacity-100"
  leave-to-class="max-h-0 opacity-0"
>
  <div v-show="open">…</div>
</transition>
```

**Exceptions (narrow):**

- `:deep()` when a child component cannot be styled via props or theme slots.
- Global `@keyframes` in `assets/css` when motion cannot be expressed with
  transition utilities.
- Third-party DOM the project does not own.

---

## Composables

- File name and export: `useSomething.ts` → `useSomething()`.
- **One composable per file.** A file exports exactly one public `use*()`, and
  its name matches. A second one — even a small helper the first wraps, even
  when the two are tightly coupled — goes in its own `useX.ts` and is imported.
  Types and constants may sit alongside the composable that owns them.
- **Single responsibility** — one job per composable; split large ones (e.g.
  `useFetchCart`, `useAddToCart` instead of one mega `useCart`).
- Return a stable contract: refs/computed and methods; use `toValue()` for
  flexible inputs when appropriate.
- Side effects (listeners, timers, subscriptions) → register in composable,
  clean up in `onUnmounted`.
- Composables may call other composables; avoid circular dependencies.
- Call composables synchronously in `<script setup>` (or lifecycle hooks when
  documented).
- Test business logic here with Vitest — not inside components.

User-facing success/error toasts: use `useExtendedToast()` — see
[notifications.md](notifications.md). Do not call `useToast()` /
`toast.add()` directly in app code (Nuxt UI apps).

When organizing code inside a `.vue` file, use a consistent member order:
imports, props/emits, store & composable calls, local state, computed,
watchers, lifecycle hooks, then functions.

---

## Utils vs composables vs stores

Use the **state ladder** — pick the lowest layer that fits:

1. **Local UI state** (toggle, input draft) → `ref` / `reactive` in component.
2. **Shared within a feature** (step flow helpers) → composable colocated or
   under `composables/`.
3. **Pure transform** (format date, map API DTO) → `utils/`.
4. **Server data** → API layer (`services/` or `services/api/`) + composable
   orchestrates fetch and loading/error state; avoid duplicate fetches for the
   same resource.
5. **Many distant consumers / persistence** → Pinia store (`storeToRefs` when
   destructuring).
6. **Secrets or upstream APIs** → backend/BFF layer when needed; client
   composable calls it.

**Pinia:** one store per domain; mutations via store actions, not direct
assignment from random components. Cross-store imports — rare and explicit.

Nuxt apps: see `nuxt.md` for `useFetch`, `server/api/`, and related
patterns.

---

## Error handling

Composables own loading and error state for feature actions. Every async path
must handle failure and must not leak loading flags.

### `apiFetch` responses

When the project uses `useApi().apiFetch`, it resolves with
`{ data, errors }` — it does not throw for typical API error payloads. A
resolved promise is **not** success.

- After every `apiFetch` call, check `resp.errors` (and domain-specific
  failure shapes in `resp.data` when the API uses them).
- Map validation errors to a single user-facing string (first field message
  or `resp.errors`); do not expose stack traces or raw response blobs.

### User-initiated actions

Applies to submit, apply, delete, and any handler the user explicitly triggers.

- Surface failure via an inline error `ref` bound in the template
  (`UFormField` `error`, section message, etc.).
- Use translated copy (`$t` / `useI18n`) for generic fallbacks.
- In `catch`: log for diagnostics (`console.error`); do not stop at logging —
  the user must see that the action failed.

### Loading and submitting flags

When toggling `loading`, `submitting`, `applyLoading`, or similar refs:

- Set `true` before the async work; clear in a `finally` block so failure
  cannot leave the UI stuck.
- Pair `try/finally` (or `try/catch/finally`) with every flag toggle.

### When to use `try/catch`

- **`apiFetch` only** — check `resp.errors`; `try/catch` is still required
  when later `await` calls can throw (e.g. `refetchInvoice()`).
- **Raw HTTP client / `fetch`** — wrap in `try/catch` in the service or
  composable; return or surface a typed error contract.

### Background and refresh fetches

Watchers and passive sync (e.g. list on `orderId` change) may degrade
gracefully (empty list, keep prior data) but must:

- Clear loading in `finally`.
- Log unexpected throws.
- Avoid silent failure on data the UI presents as authoritative without an
  empty or error state.

### Hunt checklist (async function review)

1. Does every `apiFetch` result check `errors`?
2. Is every loading/submitting flag cleared in `finally`?
3. Do user-triggered handlers show an error on failure?
4. Are chained `await`s after the API call inside the same `try` (or
   separately caught)?
5. Are fire-and-forget promises from user actions avoided or explicitly
   handled?

**Missing vs correct handling:**

```ts
// ✗ resolved promise treated as success; loading may leak on throw
async function applyCode(code: string) {
  loading.value = true
  const resp = await applyPromoCode(orderId, { code })
  await refetchInvoice()
  loading.value = false
}
```

```ts
// ✓ check API errors, catch throws, always clear loading, surface error
async function applyCode(code: string) {
  loading.value = true
  try {
    const resp = await applyPromoCode(orderId, { code })
    const errorMessage = getApiError(resp)
    if (errorMessage) {
      submitError.value = errorMessage
      return false
    }
    await refetchInvoice()
    return true
  } catch (err) {
    console.error('applyCode error:', err)
    submitError.value = t('error_messages.generic_error')
    return false
  } finally {
    loading.value = false
  }
}
```

---

## TypeScript

- Type composable inputs and return shapes; type API responses in the API
  layer (`services/` or `services/api/`).
- Prefer explicit types over `any`; use generated or shared interfaces for DTOs.

---

## Before you add code — checklist

1. Is there already a composable, util, store, or component that does this?
2. Is this the right layer (util vs composable vs store vs component)?
3. Does design match `docs/ui/*` and neighboring files?
4. Can styling use Tailwind utilities instead of new `<style scoped>` custom
   classes?
5. Is there a single owner for this state or constant?
6. Will this duplicate an API call or business rule elsewhere?
7. Does every async path handle errors, surface user-action failures, and
   clear loading state in `finally`?

---

## Anti-patterns (smells to flag)

- Business logic or data transforms in a template / `<script setup>` → move to
  a composable or util.
- The same endpoint fetched in several places with ad-hoc calls → one API-layer
  function + one composable.
- Hardcoded user-facing strings → `$t('…')`.
- Reading runtime config / env directly in a component → feature-flag composable
  or a dedicated composable.
- Mutating store state directly from a component → go through a store action.
- Copying a value into a local `ref` instead of `computed` from its owner →
  derive it.
- Two composables each holding their own `ref` for the same domain entity
  (e.g. an invoice in both `useCheckout` and `useOrder`) → one owner (store);
  refetches/refreshes write back to it (see **SSOT — the id-refetch trap**).
- A composable reading another composable's internal state (`useX()` calling
  `useY()` just to read `useY`'s ref) instead of accepting it as a parameter
  or reading the store owner → hidden coupling, silently wrong when consumed
  outside `useY`'s flow.
- Prop-drilling shared state through many layers → a store or provide/inject.
- `any` on API/DTO shapes → typed interfaces in the API layer.
- Layout, color, spacing, or transition styling in `<style scoped>` when
  Tailwind utilities or `<transition>` class props suffice → see **Styling —
  Tailwind over scoped CSS** above.
- Deep `if/else` nesting where guard clauses would flatten the flow → early
  returns at the top of the function.
- Long multi-concern functions (>40 lines or mixed responsibilities) → extract
  helpers, composables, or utils.
- Multi-statement inline `@click` / `@submit` arrow functions in templates →
  named handler in `<script setup>` (see **Named event handlers** above).
- `apiFetch` result used without checking `resp.errors` → treat as failure
  path; map message for the user (see **Error handling**).
- Loading/submitting `ref(true)` without `finally { ref(false) }` → loading
  leak on error or throw.
- User-initiated async handler with no user-visible error (silent fail, empty
  `catch`, or `catch` that only logs) → inline error `ref` or translated
  message in the template.
- Chained `await` after an API call outside `try/catch` while loading flag is
  set → wrap full flow or clear flag in `finally`.

---

## Severity (for code audits)

When auditing a change against this guide, rate each finding:

| Severity   | Meaning                                                                                          | Examples                                                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `critical` | Will cause wrong behavior or data/state corruption, or breaks a hard rule with real consequences | Divergent copies of a money/auth rule; hand-editing Crowdin target locales; duplicated logic that already disagrees                        |
| `major`    | Clear non-negotiable violation; bugs or real maintenance pain soon — fix before merge            | Business logic in a component; duplicated API call or business rule; parallel sources of truth; diverging from the sibling-feature pattern; function over 50 lines or mixing validate + fetch + map + persist; ternary or `v-else-if` ladder in a template (see § Template — keep logic in script) |
| `minor`    | Real but low-impact — fix when convenient                                                        | Slightly fat script; wrong layer choice; missing type on a return shape; single-purpose function in the 40–50 line range                                                                                   |
| `nit`      | Style/preference, no functional impact                                                           | Naming, member order, wording                                                                                                              |

---

## Performance

Speed and Core Web Vitals have a dedicated guide: **`performance.md`**
(measure-first workflow, reactivity, fetching, lazy loading, images, third-
party scripts, Pinia persistence).

Nuxt SSR: see `nuxt.md` and `performance.md`.

---

## Further reading

- [Performance — fast Vue apps](./performance.md) (project guide)
- [Nuxt 3 add-ons](./nuxt.md) (Nuxt apps only)
- [Vue.js — Composition API](https://vuejs.org/guide/extras/composition-api-faq.html)
- [Vue.js — State management](https://vuejs.org/guide/scaling-up/state-management.html)
- [Pinia](https://pinia.vuejs.org/core-concepts/)
