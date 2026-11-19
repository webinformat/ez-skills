#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")

DEFAULT_CONFIG = CONFIG_HOME / "ez-skills" / "sql-connections.json"

REQUIRED = ("host", "user", "password", "database")

DEFAULT_PERMISSIONS = ["Select"]

STATEMENT_PERMISSIONS = {
    "select": "Select",
    "with": "Select",
    "insert": "Insert",
    "update": "Update",
    "delete": "Delete",
}

MSSQL_FORBIDDEN = {
    "insert", "update", "delete", "merge", "drop", "alter", "create", "truncate",
    "exec", "execute", "grant", "revoke", "deny", "into", "backup", "restore",
    "dbcc", "shutdown", "kill", "use", "openrowset", "opendatasource", "openquery",
    "openxml", "bulk", "waitfor", "declare", "set", "begin", "commit", "rollback",
    "save", "reconfigure", "go",
}

MYSQL_FORBIDDEN = {
    "insert", "update", "delete", "drop", "alter", "create", "truncate", "rename",
    "grant", "revoke", "into", "call", "do", "handler", "set", "use", "prepare",
    "execute", "deallocate", "begin", "commit", "rollback", "savepoint", "kill",
    "shutdown", "flush", "install", "uninstall", "load_file", "sleep", "benchmark",
}

POSTGRESQL_FORBIDDEN = {
    "insert", "update", "delete", "merge", "drop", "alter", "create", "truncate",
    "grant", "revoke", "into", "copy", "call", "do", "execute", "prepare",
    "deallocate", "set", "reset", "begin", "commit", "rollback", "savepoint",
    "listen", "notify", "vacuum", "cluster", "reindex", "refresh", "discard",
    "checkpoint", "set_config", "nextval", "setval", "pg_sleep",
    "pg_terminate_backend", "pg_cancel_backend", "pg_read_file",
    "pg_read_binary_file", "pg_ls_dir", "lo_import", "lo_export", "dblink_exec",
}

MSSQL_NOISE = re.compile(r"/\*.*?\*/|--[^\n]*|N?'(?:[^']|'')*'|\"[^\"]*\"|\[[^\]]*\]", re.S)

MYSQL_NOISE = re.compile(
    r"/\*.*?\*/|(?:#|--(?=\s|$))[^\n]*|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|`[^`]*`",
    re.S,
)

POSTGRESQL_NOISE = re.compile(
    r"/\*.*?\*/|--[^\n]*|[eE]'(?:[^'\\]|\\.|'')*'|'(?:[^']|'')*'"
    r"|\$([a-zA-Z_][a-zA-Z0-9_]*|)\$.*?\$\1\$|\"(?:[^\"]|\"\")*\"",
    re.S,
)


def fail(message):
    print(f"sql-query: {message}", file=sys.stderr)
    return 1


def statement_error(sql, noise, forbidden, permissions, allowed_keywords):
    body = noise.sub(" x ", sql).strip().rstrip(";").strip()
    if ";" in body:
        return "only one statement is allowed"
    words = re.findall(r"[a-z_][a-z0-9_@#$]*", body.lower())
    permission = STATEMENT_PERMISSIONS.get(words[0]) if words else None
    if permission not in permissions:
        return "only " + ", ".join(permissions) + " statements are allowed on this connection"
    bad = sorted(set(words) & (forbidden - allowed_keywords[permission]))
    if bad:
        return "forbidden keyword: " + ", ".join(bad)
    return None


def mssql_error(sql, permissions):
    if re.search(r"^\s*(:|!!)", sql, re.M):
        return "sqlcmd commands are not allowed"
    if "$(" in sql:
        return "sqlcmd variables are not allowed"
    return statement_error(sql, MSSQL_NOISE, MSSQL_FORBIDDEN, permissions, TYPES["mssql"]["permissions"])


def mysql_error(sql, permissions):
    if "/*!" in sql:
        return "executable comments are not allowed"
    if "\\" in MYSQL_NOISE.sub(" x ", sql):
        return "mysql client commands are not allowed"
    return statement_error(sql, MYSQL_NOISE, MYSQL_FORBIDDEN, permissions, TYPES["mysql"]["permissions"])


def postgresql_error(sql, permissions):
    if "\\" in POSTGRESQL_NOISE.sub(" x ", sql):
        return "psql meta-commands are not allowed"
    return statement_error(sql, POSTGRESQL_NOISE, POSTGRESQL_FORBIDDEN, permissions, TYPES["postgresql"]["permissions"])


def mssql_command(conn, host, port, database, sql):
    command = [
        "sqlcmd",
        "-S", f"tcp:{host},{port}",
        "-U", conn["user"],
        "-d", database,
        "-W", "-s", "\t", "-b",
        "-Q", sql,
    ]
    if conn.get("trust_server_certificate"):
        command.append("-C")
    return command


def mysql_command(conn, host, port, database, sql):
    return [
        "mysql",
        "--protocol=TCP",
        "-h", host,
        "-P", str(port),
        "-u", conn["user"],
        "-D", database,
        "--batch",
        "-e", sql,
    ]


def postgresql_command(conn, host, port, database, sql):
    return [
        "psql",
        "-h", host,
        "-p", str(port),
        "-U", conn["user"],
        "-d", database,
        "-w",
        "-A", "-F", "\t",
        "-c", sql,
    ]


TYPES = {
    "mssql": {
        "port": 1433,
        "cli": "sqlcmd",
        "install": "brew install sqlcmd",
        "password_env": "SQLCMDPASSWORD",
        "permissions": {
            "Select": set(),
            "Insert": {"insert", "into"},
            "Update": {"update", "set"},
            "Delete": {"delete"},
        },
        "check": mssql_error,
        "command": mssql_command,
    },
    "mysql": {
        "port": 3306,
        "cli": "mysql",
        "install": "brew install mysql-client",
        "password_env": "MYSQL_PWD",
        "permissions": {
            "Select": set(),
            "Insert": {"insert", "into", "set"},
            "Update": {"update", "set"},
            "Delete": {"delete"},
        },
        "check": mysql_error,
        "command": mysql_command,
    },
    "postgresql": {
        "port": 5432,
        "cli": "psql",
        "install": "brew install libpq",
        "password_env": "PGPASSWORD",
        "permissions": {
            "Select": set(),
            "Insert": {"insert", "into"},
            "Update": {"update", "set"},
            "Delete": {"delete"},
        },
        "check": postgresql_error,
        "command": postgresql_command,
    },
}


def load_connections(config):
    if not config.exists():
        return None
    return json.loads(config.read_text())


def connection_error(name, conn):
    kind = conn.get("type")
    if kind not in TYPES:
        return f"connection '{name}' has type '{kind}'; expected one of: {', '.join(TYPES)}"
    missing = [field for field in REQUIRED if not conn.get(field)]
    if missing:
        return f"connection '{name}' is missing: {', '.join(missing)}"
    valid = TYPES[kind]["permissions"]
    permissions = conn.get("permissions", DEFAULT_PERMISSIONS)
    if not isinstance(permissions, list):
        return f"connection '{name}' permissions must be a list; valid for {kind}: {', '.join(valid)}"
    invalid = [p for p in permissions if p not in valid]
    if invalid:
        return f"connection '{name}' has invalid permissions: {', '.join(map(str, invalid))}; valid for {kind}: {', '.join(valid)}"
    return None


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_for_port(port, proc, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def run_client(spec, conn, host, port, database, sql):
    command = spec["command"](conn, host, port, database, sql)
    env = dict(os.environ, **{spec["password_env"]: conn["password"]})
    return subprocess.run(command, env=env).returncode


def main():
    parser = argparse.ArgumentParser(description="Run a permitted query on an MSSQL, MySQL, or PostgreSQL server, directly or through an SSH tunnel.")
    parser.add_argument("connection", nargs="?", help="connection name from the connections file")
    parser.add_argument("query", nargs="?", help="query allowed by the connection's permissions (or use --file, or stdin)")
    parser.add_argument("-f", "--file", help="read the query from a file")
    parser.add_argument("-d", "--database", help="override the connection's database")
    parser.add_argument("--config", help=f"connections file (default {DEFAULT_CONFIG})")
    parser.add_argument("--list", action="store_true", help="list connection names and types")
    parser.add_argument("--timeout", type=int, default=15, help="seconds to wait for the SSH tunnel")
    args = parser.parse_args()

    config = Path(os.path.expanduser(args.config)) if args.config else DEFAULT_CONFIG
    connections = load_connections(config)
    if connections is None:
        return fail(f"missing {config}")

    if args.list:
        for name in sorted(connections):
            print(f"{name}\t{connections[name].get('type')}")
        return 0

    if not args.connection:
        return fail("connection name is required (see --list)")
    conn = connections.get(args.connection)
    if conn is None:
        return fail(f"unknown connection '{args.connection}'; known: {', '.join(sorted(connections)) or 'none'}")

    error = connection_error(args.connection, conn)
    if error:
        return fail(error)
    spec = TYPES[conn["type"]]

    if args.file:
        sql = Path(args.file).read_text()
    elif args.query:
        sql = args.query
    elif not sys.stdin.isatty():
        sql = sys.stdin.read()
    else:
        return fail("query is required")

    error = spec["check"](sql, conn.get("permissions", DEFAULT_PERMISSIONS))
    if error:
        return fail(f"refused: {error}")

    if not shutil.which(spec["cli"]):
        return fail(f"{spec['cli']} not found; install with: {spec['install']}")

    database = args.database or conn["database"]
    port = conn.get("port", spec["port"])
    if not conn.get("ssh"):
        return run_client(spec, conn, conn["host"], port, database, sql)

    local_port = free_port()
    ssh_command = ["ssh", "-N", "-o", "BatchMode=yes", "-o", "ExitOnForwardFailure=yes"]
    if conn.get("ssh_key"):
        ssh_command += ["-i", os.path.expanduser(conn["ssh_key"])]
    if conn.get("ssh_port"):
        ssh_command += ["-p", str(conn["ssh_port"])]
    ssh_command += ["-L", f"127.0.0.1:{local_port}:{conn['host']}:{port}", conn["ssh"]]
    ssh = subprocess.Popen(
        ssh_command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        if not wait_for_port(local_port, ssh, args.timeout):
            if ssh.poll() is None:
                ssh.terminate()
            detail = ssh.communicate()[1].decode(errors="replace").strip()
            return fail(f"ssh tunnel via {conn['ssh']} failed: {detail or 'timed out'}")
        return run_client(spec, conn, "127.0.0.1", local_port, database, sql)
    finally:
        if ssh.poll() is None:
            ssh.terminate()
            try:
                ssh.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ssh.kill()


if __name__ == "__main__":
    sys.exit(main())
