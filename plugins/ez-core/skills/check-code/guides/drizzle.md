# Drizzle — coding guide

Conventions for data access with [Drizzle ORM](https://orm.drizzle.team) and
Drizzle Kit in TypeScript services (typically a Hono/Node API).
**Read [general.md](./general.md) first**, and [hono.md](./hono.md) when the
service is a Hono API.

> **Scope:** Shared guide that check-code reads next to the repo's own rules.
> Examples below are **recommendations**; the active app repo may differ.
>
> **Version:** targets the stable **0.x** line (`drizzle-orm` 0.45,
> `drizzle-kit` 0.31 — what `npm i` installs). The docs site now documents
> the v1 release candidate; see **v1 differences** before copying examples
> from it.

## Non-negotiables

1. **Schema in code is the source of truth.** Tables live in TypeScript
   under `src/db/`; the database is changed only through generated
   migrations.
2. **Migrations are generated, reviewed and committed.** `drizzle-kit
   generate` produces SQL; a human reads it before it ships. `drizzle-kit
   push` never runs against staging or production.
3. **Queries live in one layer.** Only `src/db/queries/` (or repositories)
   import the `db` client; routes and services call named query functions.
4. **Never interpolate raw input into SQL.** Use the query builder or the
   `sql` template tag, which parameterises values. `sql.raw()` only for
   trusted constants.
5. **Types come from the schema.** Row types are `$inferSelect` /
   `$inferInsert`; request schemas come from `drizzle-zod`. No hand-written
   duplicates of table shapes.

## Directory roles

| # | Path | Purpose |
| --- | --- | --- |
| 1 | `drizzle.config.ts` | Drizzle Kit config — dialect, schema path, `out`, credentials from env. |
| 2 | `src/db/schema/` | One file per domain (`users.ts`, `jobs.ts`), re-exported from `index.ts`. Every table, enum and relation is exported. |
| 3 | `src/db/relations.ts` | `relations()` definitions (or keep them next to their table). |
| 4 | `src/db/client.ts` | Creates the driver connection and `drizzle()` instance; exports `db` and its type. |
| 5 | `src/db/queries/` | Named query functions — the only place that builds queries. |
| 6 | `src/db/migrate.ts` | Applies migrations at deploy or startup. |
| 7 | `drizzle/` | Generated migrations and snapshots — committed, never hand-edited except to add data backfills. |

## Schema

1. **Naming** — tables plural `snake_case` (`blog_posts`), columns
   `snake_case` in the database and camelCase in TypeScript. Set
   `casing: 'snake_case'` on both `drizzle()` and `drizzle.config.ts` instead
   of aliasing every column; the two must match or queries and migrations
   disagree.
2. **Primary keys** — PostgreSQL: `integer().primaryKey().generatedAlwaysAsIdentity()`
   instead of `serial`. SQLite: `integer({ mode: 'number' }).primaryKey({ autoIncrement: true })`
   or a text id. Use UUID/ULID text ids when ids are exposed publicly or
   generated before insert.
3. **Nullability is explicit** — add `.notNull()` to every column that must
   have a value; a missing `.notNull()` makes the inferred type `| null`
   everywhere.
4. **Foreign keys** — declare `.references(() => parent.id, { onDelete })`
   with the delete rule chosen on purpose (`cascade`, `restrict`,
   `set null`). Index every foreign-key column that is filtered or joined
   on.
5. **Indexes and constraints** go in the table's third argument as an array:
   `(t) => [index('jobs_status_idx').on(t.status), unique().on(t.a, t.b)]`.
   Name indexes explicitly.
6. **Shared columns** — define `timestamps` once and spread them
   (`...timestamps`) into tables; use `.$onUpdate(() => new Date())` for
   `updatedAt`.
7. **Enums** — `pgEnum` on PostgreSQL; on SQLite and MySQL use
   `text({ enum: [...] })` / `mysqlEnum` and keep the value list in one
   exported `as const` array.
8. **JSON columns** — type them with `.$type<Shape>()` and validate the
   shape on write; the database does not.
9. **Money** — `numeric`/`decimal` (returned as string) or integer minor
   units. Never `real`/`float`.

## Relations

1. `relations()` only powers the relational query API (`db.query.*`); it does
   not create foreign keys. Declare both: `.references()` for the database,
   `relations()` for queries.
2. Define both sides of each relation (`one` on the child with `fields` /
   `references`, `many` on the parent).
3. Pass the whole schema, relations included, to `drizzle({ schema })`,
   otherwise `db.query` is empty.

## Client and connections

1. Create **one** `db` instance per process in `src/db/client.ts`; never
   create a client per request.
2. Read the connection string from validated config, never from
   `process.env` inside the client module.
3. Close the underlying driver (`pool.end()`, `sqlite.close()`) during
   graceful shutdown.
4. **SQLite** — on open, set `journal_mode = WAL`, `foreign_keys = ON`
   (off by default in SQLite), and a `busy_timeout`. Keep the database file
   on persistent storage, and use a single writer process.
5. **PostgreSQL / MySQL** — use a pool with an explicit `max`, and for
   serverless drivers follow the driver's connection guidance.

## Queries

1. Default to the SQL-like builder (`db.select()…`); use `db.query.*.findMany`
   with `with` for nested reads where it removes manual joins and mapping.
2. **Select only the columns the caller needs** — `db.select({ id, name })`
   or `columns: { … }`. Never return raw rows to the client.
3. Bound every list query with `limit`; use keyset (cursor) pagination on an
   indexed column for large tables instead of deep `offset`.
4. **Avoid N+1** — never query inside a loop over rows; use a join,
   `inArray()`, or a relational `with`.
5. Conditional filters: build an array of conditions and pass
   `and(...conditions)`; `undefined` entries are ignored.
6. Upserts use `onConflictDoUpdate({ target, set })` /
   `onConflictDoNothing()`, not select-then-insert.
7. Use `.returning()` (PostgreSQL, SQLite) to get written rows instead of a
   second select.
8. `db.$count(table, where)` for counts.
9. Hot paths may use prepared statements with `sql.placeholder('name')`;
   prepare once at module load, execute many times.
10. Log generated SQL only in development (`logger: true`); never in
    production with parameter values.

## Transactions

1. Wrap multi-statement writes that must succeed together in
   `db.transaction(async (tx) => { … })`, and use `tx` — not `db` — inside
   it.
2. Throw (or call `tx.rollback()`) to roll back; the error propagates to
   the caller.
3. Keep transactions short: no network calls, no model or upstream API
   calls inside them.
4. Nested `tx.transaction()` creates a savepoint.
5. **SQLite with `better-sqlite3`** — the driver is synchronous; a
   transaction callback must not await other I/O. Use `behavior: 'immediate'`
   for write transactions to avoid `SQLITE_BUSY` on lock upgrade.
6. PostgreSQL accepts `isolationLevel`, `accessMode` and `deferrable`
   options; pick a stricter level only where a race was identified.

## Migrations

1. Workflow: edit schema → `drizzle-kit generate --name <what_changed>` →
   review the SQL → commit schema and `drizzle/` together → apply with
   `migrate`.
2. Wrap Drizzle Kit in package scripts (`db:generate`, `db:migrate`,
   `db:studio`) so every developer runs the same config.
3. Set `strict: true` and `verbose: true` in `drizzle.config.ts` so Kit
   asks before destructive statements.
4. When Kit asks whether a column was renamed or dropped and created, answer
   carefully — the wrong answer loses data.
5. Apply migrations **once per deploy**, before the new code serves
   traffic: either a deploy step (`drizzle-kit migrate`) or `migrate(db, {
   migrationsFolder })` from the driver's `…/migrator` module at startup in
   a single-instance service.
6. Never edit a migration that has already run anywhere; add a new one.
7. Destructive changes ship in two deploys: stop using the column, then drop
   it.
8. `drizzle-kit push` is for local prototyping and throwaway databases only.
9. Data backfills go in their own migration (`generate --custom`) or a
   one-off script — not in application startup.
10. SQLite cannot alter most constraints in place; Kit recreates the table.
    Read those migrations with extra care and keep `foreign_keys` handling in
    mind.

## Types and validation

1. `type User = typeof users.$inferSelect`, `type NewUser = typeof
   users.$inferInsert` — export them from the schema module.
2. Build request validators with `drizzle-zod` (`createInsertSchema`,
   `createUpdateSchema`, `createSelectSchema`) and refine fields there
   (`email: (s) => s.email()`); pick or omit fields the client may not set
   (ids, timestamps, ownership).
3. Response shapes are their own schemas — never expose the select schema
   of a whole table.

## Testing

1. Run query tests against a real database of the same dialect: an
   in-memory or temp-file SQLite, or a disposable PostgreSQL container.
   Do not mock the query builder.
2. Apply the real migrations to the test database before the suite
   (`migrate()`), not `push`.
3. Isolate tests with a fresh database per file, or a transaction rolled
   back after each test.
4. Seed with small factory functions that return `$inferInsert` objects.

## Anti-patterns (smells to flag)

1. `db` imported in a route handler → move the query to `src/db/queries/`.
2. `` sql`… ${userInput} …` `` inside `sql.raw()` or string concatenation →
   builder or `sql` template parameters.
3. Query inside `for`/`map` over rows → join, `inArray()` or `with`.
4. `select()` of every column returned straight to the client → explicit
   columns and a response schema.
5. `drizzle-kit push` in a deploy script → `generate` + `migrate`.
6. Hand-edited or deleted migration files that already ran → new migration.
7. Hand-written interface duplicating a table → `$inferSelect` /
   `$inferInsert`.
8. `relations()` without matching `.references()` → foreign key missing in
   the database.
9. List endpoint without `limit` → bounded, paginated query.
10. SQLite opened without `foreign_keys = ON` → constraints silently not
    enforced.

## v1 differences

The v1 release candidate (`drizzle-orm@rc`) changes APIs this guide uses.
Do not mix the two lines in one repo.

1. Relations: `defineRelations(schema, (r) => …)` replaces `relations()`,
   and `db.query` filters become objects (`where: { id: 1 }`).
2. Validators move into `drizzle-orm/zod` (and siblings); `drizzle-zod` is
   not used.
3. Casing: `snakeCase.table(…)` builders are available.
4. Migrations: one folder per migration (`migration.sql` +
   `snapshot.json`) instead of a flat `drizzle/` folder with a journal.

## Further reading

1. [Drizzle — Schema](https://orm.drizzle.team/docs/sql-schema-declaration)
2. [Drizzle — Indexes & constraints](https://orm.drizzle.team/docs/indexes-constraints)
3. [Drizzle — Migrations](https://orm.drizzle.team/docs/migrations)
4. [Drizzle Kit — Config file](https://orm.drizzle.team/docs/drizzle-config-file)
5. [Drizzle — Transactions](https://orm.drizzle.team/docs/transactions)
6. [Drizzle — Query performance](https://orm.drizzle.team/docs/perf-queries)
7. [Drizzle — Relational queries](https://orm.drizzle.team/docs/rqb)
8. [Drizzle — Zod](https://orm.drizzle.team/docs/zod)
9. [Drizzle ORM PostgreSQL best practices (community gist)](https://gist.github.com/productdevbook/7c9ce3bbeb96b3fabc3c7c2aa2abc717)
