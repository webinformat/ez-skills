# Laravel — coding guide

Conventions for applications built with [Laravel](https://laravel.com) 13.x.
**Read [general.md](./general.md) first** — comments, early return, function
size, and audit severity live there. Translations for Laravel apps live in
[translations-laravel.md](./translations-laravel.md).

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.
> Checked against the Laravel 13.x docs on 2026-10-13.

## Version baseline

| # | Item | Value |
| --- | --- | --- |
| 1 | Current major | Laravel 13, released 17 March 2026 |
| 2 | PHP | 8.3 minimum (8.3–8.5 supported) |
| 3 | Bug fixes / security fixes | until Q3 2027 / until 17 March 2028 |
| 4 | Laravel 12 | security fixes only, until 24 February 2027 |
| 5 | Constraint | `"laravel/framework": "^13.0"` |

Each major gets 18 months of bug fixes and 2 years of security fixes; a new
major ships about once a year.

## Non-negotiables

1. **Thin HTTP layer.** Controllers and console commands only receive input,
   call application code, and return a response. Business rules live in
   classes under `app/` that know nothing about the request.
2. **Every input is validated before use.** Use a Form Request (or
   `$request->validate()` for one-off cases) and read only
   `$request->validated()` or `$request->safe()->only([...])`.
3. **Authorization before business logic.** Policies for model actions,
   gates for actions not tied to a model.
4. **`env()` only inside `config/`.** After `config:cache` the `.env` file is
   not loaded, so `env()` elsewhere returns `null` in production. Read
   values with `config()`.
5. **No lazy loading outside production.** Turn on
   `Model::preventLazyLoading()` so N+1 queries fail in development and
   tests.
6. **No user-facing strings in PHP or Blade.** Every string goes through
   `__()` / `trans_choice()` (see
   [translations-laravel.md](./translations-laravel.md)).
7. **`APP_DEBUG=false` in production.** Debug pages expose config values
   and secrets.

## Directory roles

Laravel places almost no limits on where a class lives as long as Composer
can autoload it (`App\` → `app/`, PSR-4).

| # | Directory | Purpose |
| --- | --- | --- |
| 1 | `app/Http/Controllers/` | Thin controllers; single-action `__invoke` controllers for one-route endpoints. |
| 2 | `app/Http/Requests/` | Form Requests — `authorize()` and `rules()`. |
| 3 | `app/Http/Resources/` | API Resources — the only shape a model takes in JSON. |
| 4 | `app/Http/Middleware/` | App middleware (including locale detection). |
| 5 | `app/Models/` | Eloquent models — relations, casts, scopes. |
| 6 | `app/Policies/` | One policy per model. |
| 7 | `app/Actions/` or `app/Services/` | Business logic. Laravel prescribes no folder; pick one per app and keep it. |
| 8 | `app/Jobs/`, `app/Notifications/`, `app/Mail/` | Queued work and outbound messages. |
| 9 | `bootstrap/app.php` | Routing, middleware, exception handling, schedule. |
| 10 | `config/` | The only place `env()` is called. |
| 11 | `lang/` | Translation files (created by `php artisan lang:publish`). |

## HTTP layer

- **Form Requests** (`php artisan make:request`): `authorize()` returning
  `false` gives a 403; `rules()` holds the validation. Write rules as arrays,
  not `|` strings.
- **API Resources** (`php artisan make:resource`): return models through a
  `JsonResource` — never raw models or arrays built in the controller.
  Laravel 13 also ships JSON:API resources.
- **Route model binding** instead of `Model::findOrFail($id)` in the
  controller. Nested bindings are scoped to their parent.
- **Attributes on controllers** (Laravel 13): `#[Middleware('auth')]` and
  `#[Authorize('create', [Comment::class, 'post'])]` keep the rule next to
  the action.
- Resource controllers use plural resource names.

## Eloquent

- **N+1:** eager load with `with()`, `load()`, `loadMissing()`,
  `withCount()`. In `AppServiceProvider::boot`:

  ```php
  Model::preventLazyLoading(! $this->app->isProduction());
  Model::preventSilentlyDiscardingAttributes(! $this->app->isProduction());
  ```

  `Model::handleLazyLoadingViolationUsing()` can log instead of throw.
- **Mass assignment:** keep models guarded. Declare fillable fields
  (`#[Fillable([...])]` in Laravel 13, or `$fillable`). Never
  `$guarded = []`, never unguard, and use `forceFill` / `forceCreate` only
  with validated arrays. JSON column keys must be listed as fillable.
- **Casts and accessors:** declare casts on the model; accessors and
  mutators return an `Attribute` instance.
- **Scopes:** local scopes with the `#[Scope]` attribute on a protected
  method; repeated `where` chains become a scope.
- **Large datasets:** `chunk()` / `lazy()` for batches; `chunkById()` /
  `lazyById()` when the loop updates the column it filters on. `cursor()`
  cannot eager load and can still exhaust memory.
- **Transactions:** wrap multi-write operations in
  `DB::transaction(fn () => …, attempts: 5)` — it rolls back on exception and
  retries on deadlock.

## Configuration

- Call `env()` only in `config/*.php`; everywhere else use `config()` or the
  typed getters (`Config::string()`, `Config::integer()`).
- Third-party credentials go in `config/services.php`.
- Run `config:cache` in deployment, not in local development.
- Never commit `.env`. To ship encrypted env files, use
  `php artisan env:encrypt` and supply `LARAVEL_ENV_ENCRYPTION_KEY` at
  deploy time.

## Errors and logging

- Configure exception handling once with `withExceptions()` in
  `bootstrap/app.php`: `report()`, `render()`, `dontReport()`, `context()`,
  `throttle()`, `shouldRenderJsonWhen()`.
- Domain exceptions may define their own `report()` / `render()`; return
  `false` to fall back to the default handling.
- Logs use channels from `config/logging.php` (default `stack`). Log
  metadata, never secrets or full payloads.

## Security checklist

1. **CSRF:** `@csrf` in every POST/PUT/PATCH/DELETE form. Laravel 13's
   `PreventRequestForgery` middleware checks `Sec-Fetch-Site` and falls back
   to the token.
2. **XSS:** output with `{{ }}`. Use `{!! !!}` only for content the app
   produced itself — never user input.
3. **SQL:** query builder and bindings (`DB::select('… where id = ?', [$id])`).
   Never put user input in raw expressions, `DB::unprepared`, or column names
   (including `orderBy` columns) — map them through an allow-list.
4. **Rate limiting:** define limiters with `RateLimiter::for()` and apply
   `throttle:` middleware; limit by user, not only by IP.
5. **API auth:** Sanctum — API tokens with abilities, or cookie auth for a
   first-party SPA.
6. **Passwords:** `Hash::make()` (bcrypt or Argon2).
7. **Public links** (unsubscribe, download): `URL::temporarySignedRoute()`
   and check `hasValidSignature()`.
8. **Uploads:** validate with `mimes` / `mimetypes`, not `extensions` alone.
   The `image` rule rejects SVG by default — keep it that way unless the SVG
   is sanitized. Store with `hashName()`; never trust
   `getClientOriginalName()` / `getClientOriginalExtension()`.
9. **Sessions:** `http_only` on, `secure` on for HTTPS-only apps,
   `same_site` `lax` or `strict`.
10. **Dependencies:** no packages with known vulnerabilities.

## Queues and scheduling

- Slow or external work goes in a job implementing `ShouldQueue`.
- Set retries per job (`#[Tries]`, `#[Backoff]`, `#[Timeout]` attributes in
  Laravel 13, or properties) rather than relying on worker flags.
- Use `ShouldBeUnique` or the `WithoutOverlapping` middleware when two
  copies of a job must not run at once; `ThrottlesExceptions` for flaky
  upstream APIs.
- Dispatch with `->afterCommit()` (or `after_commit` on the connection) when
  the job reads rows written in the same transaction.
- Schedule tasks in `routes/console.php`; the server runs one cron entry.
  Add `withoutOverlapping()` to long tasks.
- Horizon for Redis queues; protect its dashboard with its gate.

## Testing

- Pest or PHPUnit — both run with `php artisan test`. Pest 5 requires
  PHP 8.4+, so pick the Pest major that matches the app's PHP.
- Use `.env.testing`; run `php artisan config:clear` before tests.
- `RefreshDatabase` on database tests; build data with factories.
- HTTP tests through `getJson()` / `postJson()` with status and JSON
  assertions. Cover, per endpoint: success, each validation failure,
  authorization failure.
- Fake side effects: `Queue::fake()`, `Mail::fake()`,
  `Notification::fake()`, `Http::fake()`.
- `Http::preventStrayRequests()` so no test reaches a real API.

## Tooling

| # | Tool | Use |
| --- | --- | --- |
| 1 | Laravel Pint | Code style, installed by default (`laravel` preset). `pint --test` in CI, `pint --dirty` locally. |
| 2 | Larastan | Static analysis (PHPStan for Laravel). Start at level 5; use `--generate-baseline` on legacy code; raise the level over time (10 is the highest). |
| 3 | Rector + rector-laravel | Major upgrades — `->withComposerBased(laravel: true)`. |

## Deployment

1. `composer install --no-dev --optimize-autoloader`
2. `php artisan migrate --force`
3. `php artisan optimize` (caches config, events, routes, views)
4. `php artisan storage:link` (first deploy)
5. `php artisan queue:restart` — workers are long-lived and keep old code.

Laravel serves a health check at `/up`.

## Internationalization

Laravel `lang/` files, placeholders, locale per request, validation, mail,
numbers, RTL and Crowdin: [translations-laravel.md](./translations-laravel.md).

## Anti-patterns (smells to flag)

1. Validation, queries, and response shaping in a controller method → Form
   Request + action/service + API Resource.
2. `$request->all()` passed to `create()` / `update()` → `validated()`.
3. `env('X')` outside `config/` → `config('…')`.
4. Relations read in a loop without `with()` → eager load; lazy-loading
   prevention on.
5. `$guarded = []` or `Model::unguard()` → declare fillable fields.
6. `DB::raw()` / `orderBy($request->sort)` built from user input → bindings
   and an allow-list.
7. `{!! $userInput !!}` in Blade → `{{ }}`.
8. Hardcoded user-facing strings in PHP, Blade, mail, or validation messages
   → `__()` keys in the source locale.
9. Workers not restarted after deploy → `queue:restart` in the deploy
   script.

## Further reading

1. [Laravel — Release notes](https://laravel.com/docs/releases)
2. [Laravel — Directory structure](https://laravel.com/docs/structure)
3. [Laravel — Validation](https://laravel.com/docs/validation)
4. [Laravel — Eloquent API resources](https://laravel.com/docs/eloquent-resources)
5. [Laravel — Authorization](https://laravel.com/docs/authorization)
6. [Laravel — Eloquent](https://laravel.com/docs/eloquent)
7. [Laravel — Eloquent relationships](https://laravel.com/docs/eloquent-relationships)
8. [Laravel — Configuration](https://laravel.com/docs/configuration)
9. [Laravel — Error handling](https://laravel.com/docs/errors)
10. [Laravel — CSRF protection](https://laravel.com/docs/csrf)
11. [Laravel — Queues](https://laravel.com/docs/queues)
12. [Laravel — Testing](https://laravel.com/docs/testing)
13. [Laravel — HTTP client](https://laravel.com/docs/http-client)
14. [Laravel — Pint](https://laravel.com/docs/pint)
15. [Laravel — Deployment](https://laravel.com/docs/deployment)
16. [OWASP — Laravel cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html)
17. [Larastan](https://github.com/larastan/larastan)
18. [rector-laravel](https://github.com/driftingly/rector-laravel)
19. [Pest — Installation](https://pestphp.com/docs/installation)
20. [Spatie — Laravel guidelines](https://spatie.be/guidelines/laravel) (community)
