# User notifications — toast

Global success/error feedback uses Nuxt UI toast via `useExtendedToast()` in
`composables/useExtendedToast.ts`. Several Nuxt apps ship this wrapper; API
details depend on the app’s Nuxt UI major version (see below).

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.

Do **not** call `useToast()` or `toast.add()` directly in application
code. The wrapper owns color, icon, duration, and related defaults.

## When to use toast

| Scenario | Use |
| --- | --- |
| Form submit success/error | `useExtendedToast()` |
| Payment failure, API error, logout | `useExtendedToast()` |
| Validation or status **inside** a form card | Prefer an inline alert component if your app provides one (project docs) |

## Setup

Layouts wrap content in `<UApp :toaster="appConfig.toaster">`. Toast
position and styling live in `app.config.ts` (`ui.toaster`, `ui.toast`).

## `useExtendedToast()` API

Every wrapper exposes `success(message, …)` and `error(message, …)`. Check
`composables/useExtendedToast.ts` in the active repo for the exact
signature.

### Nuxt UI v3

Second argument is **`duration`** (milliseconds) passed to `toast.add`.
Semantic color names (`success`, `error`). Optional **`progress`** bar.

```ts
const toast = useExtendedToast()

toast.success(message)              // default duration 5000ms
toast.error(message)                // default duration 7000ms
toast.error(message, 0)             // persistent (user dismisses)
```

Optional parameters (rare — prefer defaults):

```ts
toast.error(message, duration, title?, color?, icon?, progress?)
toast.success(message, duration, title?, color?, icon?, progress?)
```

- **First argument** — user-visible copy (resolved i18n string or API
  message). Stored in the toast `title` slot when no separate `title` is
  passed.
- **Second argument** — `duration` in ms; pass `0` for persistent
  (checkout/payment errors that must stay until dismissed).
- **Third argument** — optional heading; when set, first argument becomes
  `description` and third becomes `title`.

| Method | Color | Icon | Default duration | Progress bar |
| --- | --- | --- | --- | --- |
| `success` | `success` | `i-heroicons-check-circle` | 5000 | hidden |
| `error` | `error` | `i-heroicons-x-circle` | 7000 | hidden |

### Nuxt UI v2

Second argument is **`timeout`** (milliseconds). Color strings `green` /
`red`. No `progress` parameter on the wrapper.

```ts
const toast = useExtendedToast()

toast.success(message)              // default timeout 5000ms
toast.error(message)                // default timeout 7000ms
toast.error(message, 0)             // persistent
```

Optional parameters:

```ts
toast.error(message, timeout, title?, color?, icon?)
toast.success(message, timeout, title?, color?, icon?)
```

- **First argument** — message text (stored in `description` when `title`
  is set, otherwise shown per wrapper implementation).
- **Second argument** — `timeout` in ms; pass `0` for persistent.

| Method | Color | Icon | Default timeout |
| --- | --- | --- | --- |
| `success` | `green` | `i-heroicons-check-circle` | 5000 |
| `error` | `red` | `i-heroicons-exclamation-circle` | 7000 |

## Examples

```ts
const toast = useExtendedToast()
const { t } = useI18n()

try {
  const resp = await submitForm(data)
  toast.success(resp.message)
} catch (error) {
  toast.error(error.message ?? t('error_messages.generic_error'))
}

// blocking bootstrap error (checkout)
toast.error(t('error_messages.invoice_not_found'), 0)
```

## Inline alerts (project-specific)

Some apps use an inline banner inside a form card (not global toast). That
pattern is **not** shared across repos — document it under the app’s
`docs/coding/` or `docs/ui/`, not here.
