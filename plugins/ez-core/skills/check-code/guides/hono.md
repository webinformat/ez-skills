# Hono — coding guide

Conventions for HTTP APIs built with [Hono](https://hono.dev) on Node.js.
**Read [general.md](./general.md) first** — comments, early return, function
size, and audit severity live there.

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.

## Non-negotiables

1. **Handlers inline, not controllers.** Write the handler directly in the
   route definition so path params and validated input are inferred. When a
   handler must live in another file, build it with
   `createFactory().createHandlers(...)` from `hono/factory` — never a bare
   `(c: Context) => …` function.
2. **Every input is validated before use.** Body, query, params, headers and
   cookies go through a validator middleware; handlers read only
   `c.req.valid('<target>')`.
3. **One error shape.** All errors leave through `app.onError` and
   `app.notFound` in a single format. Handlers throw; they do not hand-build
   error bodies.
4. **Config is parsed once.** Environment variables are validated at startup
   (schema, fail fast) and passed in; nothing reads `process.env` inside a
   route.
5. **Secrets and internals never reach the client.** No stack traces,
   upstream/provider messages, SQL, or config values in responses.

## Directory roles

| # | Directory | Purpose |
| --- | --- | --- |
| 1 | `src/app.ts` | `createApp()` — builds the Hono instance, global middleware, mounts route modules. No `serve()` here, so tests import it directly. |
| 2 | `src/server.ts` | Entry point: load config, open resources, `serve()`, graceful shutdown. |
| 3 | `src/routes/` | One sub-app per resource or endpoint group, mounted with `app.route()`. |
| 4 | `src/middleware/` | Reusable middleware built with `createMiddleware()`. |
| 5 | `src/services/` | Business logic and upstream API calls — no Hono types in signatures. |
| 6 | `src/db/` | Schema, client, queries. |
| 7 | `src/config/` | Env schema and loader. |
| 8 | `src/schemas/` | Request/response schemas shared by validators, OpenAPI and tests. |

Routes stay thin: validate → call a service → map to a response. Business
rules live in `services/`, never in the handler body.

## App structure

- Split by resource and mount with `app.route('/books', books)`; each module
  exports its own `new Hono()` instance.
- Type app-wide context once and reuse it everywhere:
  `new Hono<{ Variables: AppVariables }>()`. Middleware adds variables via
  `createMiddleware<{ Variables: … }>()`; handlers read them with `c.var.x`.
- Keep `createApp()` free of side effects (no listening, no timers, no DB
  open) so tests can build as many apps as they need. Pass dependencies in as
  arguments.
- Do not define `HEAD` routes — Hono answers `HEAD` from the `GET` route
  automatically.

## Middleware

Middleware runs as an onion: code before `await next()` runs in registration
order, code after it in reverse. Register in this order:

1. `requestId()` — every log line and error carries it.
2. Access logging / timing (after `next()` to capture status and duration).
3. `secureHeaders()` — sensible defaults (removes `X-Powered-By`, sets
   `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, …);
   disable individual headers by setting them to `false`.
4. `cors()` — only when browsers call the API; list exact origins, never `*`
   with credentials.
5. `bodyLimit({ maxSize, onError })` — per route group, sized to that route
   (default is 100 KB).
6. Authentication.
7. Rate limiting / quotas (needs the authenticated identity).
8. Validators, then the handler.

Write reusable middleware in `src/middleware/` with `createMiddleware()` so
its variables are typed; do not put multi-line logic inline in `app.use()`.

## Validation

- Use `@hono/zod-validator` (`zValidator('json', schema)`) or
  `@hono/standard-validator` for any Standard Schema library.
- Validate each target separately: `json`, `form`, `query`, `param`,
  `header`, `cookie`.
- JSON and form validation only work when the request sends the matching
  `Content-Type`; without it the body parses as `{}`. Reject such requests
  rather than treating them as empty.
- Header keys are lowercase in the validator (`'idempotency-key'`).
- Use the validator's hook to turn failures into the shared error shape —
  field names only, never echo the rejected values.
- Define schemas once in `src/schemas/` and reuse them for validation,
  OpenAPI generation and tests.

## Errors

- Throw `HTTPException(status, { message, cause })` for expected failures;
  let `app.onError` map it with a stable machine-readable code.
- `app.onError` handles unknown errors as `500` with a generic body and logs
  the full error server-side with the request ID.
- `app.notFound` returns the same error shape as `onError`.
- `HTTPException.getResponse()` has no access to the context: headers set on
  `c` (for example a request ID) must be copied onto the response in
  `onError`.
- Prefer one standard body such as RFC 9457 Problem Details
  (`application/problem+json`) across every endpoint.

## Responses

- Use `c.json(data, status)`; set the status explicitly for anything other
  than `200`.
- Define response schemas and validate outbound data that comes from an
  untrusted source (upstream APIs, model output) before returning it.
- Return only the fields the client needs — never raw database rows.

## Node.js runtime

- Serve with `@hono/node-server` `serve({ fetch: app.fetch, port })`.
- **Graceful shutdown is manual on Node.** On `SIGTERM` and `SIGINT`: stop
  accepting connections (`server.close()`), let in-flight requests finish
  within a grace period, then cancel what remains and close resources
  (database, timers).
- Raw Node objects are available as `c.env.incoming` / `c.env.outgoing` when
  needed (for example the remote address behind no proxy).
- Behind a reverse proxy, bind to `127.0.0.1` or a private interface and
  terminate TLS at the proxy.

## Security checklist

1. Validation on every input target (see **Validation**).
2. `bodyLimit` on every route that accepts a body.
3. `secureHeaders()` globally; `cors()` only with explicit origins.
4. Authentication before any business logic; compare secrets in constant
   time (`crypto.timingSafeEqual` on equal-length buffers or hashes).
5. Rate limits and quotas per client identity, not per IP only.
6. `timeout` or `AbortSignal` on every upstream call.
7. Error bodies carry a code and request ID only.
8. No secrets in logs; log metadata, not payloads.

## Testing

- Test through `app.request(path, init)` against `createApp()` — no network,
  no listening port.
- Build the app with test doubles for services and an in-memory or temporary
  database.
- Cover, per route: success, each validation failure, auth failure, and the
  error shape.
- `testClient` from `hono/testing` gives a typed client for route modules
  that are chained (`new Hono().get(...).post(...)`).

## Anti-patterns (smells to flag)

1. Controller functions typed `(c: Context)` living outside route files →
   inline handlers or `factory.createHandlers()`.
2. `await c.req.json()` in a handler without a validator → validator
   middleware + `c.req.valid('json')`.
3. `try/catch` in every handler building its own error JSON → throw
   `HTTPException`; one `onError`.
4. `process.env.X` read inside routes or services → validated config passed
   in.
5. `serve()` or timers started inside `createApp()` → keep them in
   `server.ts`.
6. Same middleware chain repeated on several routes → one sub-app with
   `use()` or a shared `createMiddleware()` export.
7. Business logic in handlers → move to `services/`.
8. Upstream error text forwarded to the client → map to a stable code.

## Further reading

1. [Hono — Best practices](https://hono.dev/docs/guides/best-practices)
2. [Hono — Middleware](https://hono.dev/docs/guides/middleware)
3. [Hono — Validation](https://hono.dev/docs/guides/validation)
4. [Hono — Exception handling](https://hono.dev/docs/api/exception)
5. [Hono — Testing](https://hono.dev/docs/guides/testing)
6. [Hono — Node.js](https://hono.dev/docs/getting-started/nodejs)
7. [Hono — Secure headers](https://hono.dev/docs/middleware/builtin/secure-headers)
8. [Hono — Body limit](https://hono.dev/docs/middleware/builtin/body-limit)
9. [Hono — Request ID](https://hono.dev/docs/middleware/builtin/request-id)
