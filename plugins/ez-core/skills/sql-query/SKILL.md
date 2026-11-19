---
name: sql-query
description: >-
  Runs one query on a named MSSQL, MySQL or PostgreSQL connection, directly or
  through an SSH jump host when the connection names one, limited to the
  statement kinds the connection's permissions allow (Select only by
  default). Use when the user asks to query SQL Server / MSSQL, MySQL or
  PostgreSQL, to check data in one of those databases, says sql-query, or
  invokes /sql-query.
---

# sql-query

**Placeholders.** Where a path or value below still shows a `${…}` placeholder instead of a real value, fill it in yourself: the plugin-root placeholder (named `CLAUDE_PLUGIN_ROOT`) is this plugin's folder, two levels above the folder that holds this file; a settings placeholder (named `user_config.<name>`) is the value of `<name>` under `"ez-core"` in `~/.config/ez-skills/settings.json` (`$XDG_CONFIG_HOME/ez-skills/settings.json` when that variable is set). A missing file or key means the setting is empty.

Every query goes through the script. Anything other than one statement the
connection's permissions allow is refused before a connection is opened.

## Settings

- Script: `${CLAUDE_PLUGIN_ROOT}/skills/sql-query/scripts/query.py`
- Connections file: `${user_config.sql_connections}`. Empty → the script's
  default, `~/.config/ez-skills/sql-connections.json`
  (`$XDG_CONFIG_HOME/ez-skills/sql-connections.json` when that variable is
  set).

Below, `query` is `python3 <script>`, plus `--config <connections file>` when
the setting is not empty.

## On invoke

1. No connection named by the user: list them (name and type).

   ```bash
   query --list
   ```

2. Run the query, written in the connection type's SQL dialect:

   ```bash
   query <name> "SELECT * FROM orders LIMIT 10"
   ```

   Options: `-d <database>` overrides the connection's database; `-f <file>`
   reads the query from a file; the query can also come on stdin;
   `--timeout <s>` sets the SSH tunnel wait (default 15).

3. Report the rows in chat.
4. Refusal, connection, tunnel or CLI error: report the script's message as
   it is, with the command that produced it. Fix only a mistake in the query
   itself (a wrong column, a dialect slip) and run it again; a refusal is
   final, and missing access or a missing CLI goes to the user.

## What the script does

Python 3, standard library only. It needs the CLI for the connection's type
and, for a tunnelled connection, working SSH access to the jump host.

| Type | CLI | Install | Default port | Password env |
| --- | --- | --- | --- | --- |
| `mssql` | `sqlcmd` | `brew install sqlcmd` | 1433 | `SQLCMDPASSWORD` |
| `mysql` | `mysql` | `brew install mysql-client` | 3306 | `MYSQL_PWD` |
| `postgresql` | `psql` | `brew install libpq` | 5432 | `PGPASSWORD` |

1. Loads the named connection and refuses it when `type` is unknown, `host`,
   `user`, `password` or `database` is missing, or `permissions` is not a list
   of permissions valid for its type (the error lists the valid ones).
2. Refuses the query unless it is one statement whose kind the connection's
   permissions allow (`SELECT` / `WITH … SELECT` → Select, `INSERT` → Insert,
   `UPDATE` → Update, `DELETE` → Delete), with no other write, DDL or
   session-changing keyword, checked with the rules of the connection's type:
   - `mssql` also refuses `SELECT … INTO`, sqlcmd commands (`:`, `!!`) and
     sqlcmd variables (`$(`).
   - `mysql` also refuses `SELECT … INTO`, `/*!` executable comments and
     backslash client commands.
   - `postgresql` also refuses `SELECT … INTO`, data-modifying CTEs and
     backslash meta-commands.
3. Without `ssh`, runs the CLI against `host:port`.
4. With `ssh`, opens
   `ssh -N [-i <ssh_key>] [-p <ssh_port>] -L 127.0.0.1:<free port>:<host>:<port> <ssh>`,
   runs the CLI against the local port, and closes the tunnel.
5. Passes the password through the type's environment variable, never on the
   command line, and exits with the CLI's exit code.

## Connections file

JSON, outside every repository, mode 600. One entry per server:

```json
{
  "shop-staging": {
    "type": "mssql | mysql | postgresql",
    "ssh": "<ssh config alias or user@host of the jump host>",
    "ssh_key": "<path to private key, e.g. ~/.ssh/jump.pem>",
    "ssh_port": 22,
    "host": "<database host, as reached from the jump host when ssh is set>",
    "port": 1433,
    "user": "<database login>",
    "password": "<database password>",
    "database": "<default database>",
    "trust_server_certificate": true,
    "permissions": ["Select"]
  }
}
```

- Required: `type`, `host`, `user`, `password`, `database`.
- Optional: `ssh` (empty or missing → direct connection), `ssh_key` and
  `ssh_port` (passed as `ssh -i` and `ssh -p`), `port` (type default).
- `mssql` only: `trust_server_certificate` adds `sqlcmd -C`.
- `permissions`: allowed statement kinds, any of `Select`, `Insert`,
  `Update`, `Delete` for every type (`TYPES[<type>]["permissions"]` in the
  script). Missing → `["Select"]`. Production connections get no field;
  staging and local ones may list more.

## Do not

1. Run a statement the connection's permissions do not allow by any other
   route (raw `ssh` plus a CLI, editing the checks, another client).
2. Put credentials in the script, the skill, chat or any tracked file.
3. Read the connections file or print its values; `--list` shows the names.
4. Change the connections file unless the user asks.
