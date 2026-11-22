#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")

DEFAULT_CONFIG = CONFIG_HOME / "ez-skills" / "ssh-connections.json"

REQUIRED = ("host", "user")

VALID_PERMISSIONS = ("Read", "Write", "Sudo")

DEFAULT_PERMISSIONS = ["Read"]

READ_COMMANDS = {
    "ls", "cat", "tail", "grep", "df", "ps", "systemctl", "head", "wc", "du",
    "free", "uptime", "whoami", "hostname", "pwd", "find", "journalctl", "docker",
}

FORBIDDEN_CHARACTERS = {
    ";": "';'",
    "&": "'&' and '&&'",
    ">": "redirects",
    "<": "redirects",
    "`": "backticks",
    "\n": "multiple lines",
    "\r": "multiple lines",
}

FIND_FORBIDDEN = {
    "-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprint0",
    "-fprintf", "-fls",
}

JOURNALCTL_FORBIDDEN = re.compile(
    r"^--(vacuum-[a-z]+|rotate|flush|sync|relinquish-var|smart-relinquish-var|setup-keys|update-catalog)(=|$)"
)

SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_./*?\-=:,@+%~\[\]]+$")


def fail(message):
    print(f"ssh-cmd: {message}", file=sys.stderr)
    return 1


def segment_error(tokens):
    if not tokens:
        return "empty command in pipe"
    name, args = tokens[0], tokens[1:]
    if name not in READ_COMMANDS:
        return f"'{name}' is not a read command; allowed: {', '.join(sorted(READ_COMMANDS))}"
    if name == "systemctl" and (not args or args[0] != "status"):
        return "only 'systemctl status' is allowed"
    if name == "docker" and (not args or args[0] not in ("ps", "logs")):
        return "only 'docker ps' and 'docker logs' are allowed"
    if name == "hostname" and args:
        return "'hostname' takes no arguments on Read"
    if name == "find":
        bad = sorted(set(args) & FIND_FORBIDDEN)
        if bad:
            return "find action not allowed: " + ", ".join(bad)
    if name == "journalctl":
        bad = [arg for arg in args if JOURNALCTL_FORBIDDEN.match(arg)]
        if bad:
            return "journalctl option not allowed: " + ", ".join(bad)
    return None


def read_command(command):
    for character, label in FORBIDDEN_CHARACTERS.items():
        if character in command:
            return None, f"{label} not allowed on Read"
    if "$(" in command:
        return None, "command substitution not allowed on Read"
    if "||" in command:
        return None, "'||' not allowed on Read"
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError as error:
        return None, f"cannot parse command: {error}"
    segments = [[]]
    for token in tokens:
        if token == "|":
            segments.append([])
        elif set(token) == {"|"}:
            return None, f"'{token}' not allowed on Read"
        else:
            segments[-1].append(token)
    parts = []
    for segment in segments:
        error = segment_error(segment)
        if error:
            return None, error
        parts.append(" ".join(t if SAFE_TOKEN.match(t) else shlex.quote(t) for t in segment))
    return " | ".join(parts), None


def write_command(command, allow_sudo):
    if not allow_sudo and re.search(r"(^|[^A-Za-z0-9_-])sudo([^A-Za-z0-9_-]|$)", command):
        return None, "sudo is not allowed without the Sudo permission"
    return command, None


def load_connections(config):
    if not config.exists():
        return None
    return json.loads(config.read_text())


def connection_error(name, conn):
    missing = [field for field in REQUIRED if not conn.get(field)]
    if missing:
        return f"connection '{name}' is missing: {', '.join(missing)}"
    permissions = conn.get("permissions", DEFAULT_PERMISSIONS)
    if not isinstance(permissions, list):
        return f"connection '{name}' permissions must be a list; valid: {', '.join(VALID_PERMISSIONS)}"
    invalid = [p for p in permissions if p not in VALID_PERMISSIONS]
    if invalid:
        return f"connection '{name}' has invalid permissions: {', '.join(map(str, invalid))}; valid: {', '.join(VALID_PERMISSIONS)}"
    if "Sudo" in permissions and "Write" not in permissions:
        return f"connection '{name}' has Sudo without Write; Sudo requires Write"
    return None


def main():
    parser = argparse.ArgumentParser(description="Run a permitted command on a server over SSH.")
    parser.add_argument("connection", nargs="?", help="connection name from the connections file")
    parser.add_argument("command", nargs="?", help="command allowed by the connection's permissions (or use stdin)")
    parser.add_argument("--config", help=f"connections file (default {DEFAULT_CONFIG})")
    parser.add_argument("--list", action="store_true", help="list connection names and permissions")
    parser.add_argument("--timeout", type=int, default=15, help="seconds to wait for the SSH connection")
    args = parser.parse_args()

    config = Path(os.path.expanduser(args.config)) if args.config else DEFAULT_CONFIG
    connections = load_connections(config)
    if connections is None:
        return fail(f"missing {config}")

    if args.list:
        for name in sorted(connections):
            print(f"{name}\t{','.join(connections[name].get('permissions', DEFAULT_PERMISSIONS))}")
        return 0

    if not args.connection:
        return fail("connection name is required (see --list)")
    conn = connections.get(args.connection)
    if conn is None:
        return fail(f"unknown connection '{args.connection}'; known: {', '.join(sorted(connections)) or 'none'}")

    error = connection_error(args.connection, conn)
    if error:
        return fail(error)

    if args.command:
        command = args.command
    elif not sys.stdin.isatty():
        command = sys.stdin.read().strip()
    else:
        return fail("command is required")
    if not command.strip():
        return fail("command is required")

    permissions = conn.get("permissions", DEFAULT_PERMISSIONS)
    if "Write" in permissions:
        remote, error = write_command(command, "Sudo" in permissions)
    else:
        remote, error = read_command(command)
    if error:
        return fail(f"refused: {error}")

    ssh_command = [
        "ssh",
        "-o", "BatchMode=yes",
        "-o", f"ConnectTimeout={args.timeout}",
        "-T",
    ]
    if conn.get("ssh_key"):
        ssh_command += ["-i", os.path.expanduser(conn["ssh_key"])]
    if conn.get("ssh_port"):
        ssh_command += ["-p", str(conn["ssh_port"])]
    ssh_command += [f"{conn['user']}@{conn['host']}", "--", remote]
    return subprocess.run(ssh_command, stdin=subprocess.DEVNULL).returncode


if __name__ == "__main__":
    sys.exit(main())
