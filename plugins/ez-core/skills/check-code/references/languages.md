# Official best-practice sources

Use a source only for a language or framework that the repo's rules and the
shared guides do not cover. Cite the source and its section in the finding.
Fetch the page when a finding depends on its exact wording.

## Contents

- Any language
- Web: JavaScript, TypeScript, frameworks, CSS
- Backend and scripting languages
- Mobile and JVM

## Any language

| Topic | Source |
| --- | --- |
| What a review looks for (design, complexity, naming, comments, tests) | [Google eng-practices — What to look for](https://google.github.io/eng-practices/review/reviewer/looking-for.html) |
| Code smells (duplicate code, long method, shotgun surgery, data clumps) | [Refactoring.Guru — Code smells](https://refactoring.guru/refactoring/smells) |
| Security risks | [OWASP Top 10](https://owasp.org/www-project-top-ten/), [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/) |

## Web: JavaScript, TypeScript, frameworks, CSS

| Stack | Source | Check first |
| --- | --- | --- |
| JavaScript | [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html) | `const`/`let` only, no implicit globals, `===` |
| TypeScript | [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html), [TS Do's and Don'ts](https://www.typescriptlang.org/docs/handbook/declaration-files/do-s-and-don-ts.html) | no `any` where a type exists, no non-null `!` to silence errors, types derived not copied |
| Vue | [Vue Style Guide](https://vuejs.org/style-guide/) | multi-word component names, detailed prop definitions, `key` with `v-for`, no `v-if` with `v-for` |
| Nuxt | [Nuxt performance best practices](https://nuxt.com/docs/4.x/guide/best-practices/performance), [Hydration](https://nuxt.com/docs/4.x/guide/best-practices/hydration) | `useFetch`/`useAsyncData` so data is not fetched twice, `Lazy` components, `<NuxtLink>`/`<NuxtImg>`, composables over needless plugins |
| React | [Rules of React](https://react.dev/reference/rules) | pure components, hooks only at top level, no state mutation |
| Hono | [Hono best practices](https://hono.dev/docs/guides/best-practices) | handlers on the route (no RoR-style controllers), `factory.createHandlers()` for groups, `app.route()` per resource |
| Drizzle | [Drizzle docs](https://orm.drizzle.team/docs/overview) | one schema owner, queries in the data layer |
| Tailwind | [Styling with utility classes](https://tailwindcss.com/docs/styling-with-utility-classes) | utilities over custom CSS, repeated class sets moved into a component |

## Backend and scripting languages

| Stack | Source | Check first |
| --- | --- | --- |
| Python | [PEP 8](https://peps.python.org/pep-0008/), [PEP 20](https://peps.python.org/pep-0020/) | naming, no bare `except`, no mutable default arguments |
| Go | [Effective Go](https://go.dev/doc/effective_go), [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) | errors handled not discarded, small interfaces, `context` first |
| Rust | [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/), [Clippy](https://doc.rust-lang.org/clippy/) | no `unwrap` in library paths, idiomatic naming, Clippy clean |
| PHP | [PER Coding Style](https://www.php-fig.org/per/coding-style/) | strict types, typed properties and returns |
| Laravel | [Laravel docs](https://laravel.com/docs) | validation in Form Requests, Eloquent over raw SQL, config via `config()` not `env()` outside config files |
| Ruby | [Ruby Style Guide](https://rubystyle.guide/) | naming, guard clauses, no `rescue Exception` |
| C# | [.NET coding conventions](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions) | naming, `async` all the way, `using` for disposables |
| Shell | [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html), [ShellCheck wiki](https://www.shellcheck.net/wiki/) | quoted variables, `set -euo pipefail` where it fits, ShellCheck clean |

## Mobile and JVM

| Stack | Source | Check first |
| --- | --- | --- |
| Swift | [Swift API Design Guidelines](https://www.swift.org/documentation/api-design-guidelines/) | clarity at the point of use, naming by role |
| Kotlin | [Kotlin coding conventions](https://kotlinlang.org/docs/coding-conventions.html) | `val` over `var`, null safety without `!!` |
| Java | [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html) | naming, no swallowed exceptions |
