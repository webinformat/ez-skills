---
name: ssh-cmd
description: >-
  Runs one shell command on a named server over SSH, limited to what the
  connection's permissions allow (Read only by default: a fixed list of read
  commands, with no redirects or chaining). Use when the user asks to run a
  command on a server, to check a server's logs, disk, processes, services or
  containers over SSH, says ssh-cmd, or invokes /ssh-cmd.
---

# ssh-cmd

**Placeholders.** Where a path or value below still shows a `${…}` placeholder instead of a real value, fill it in yourself: the plugin-root placeholder (named `CLAUDE_PLUGIN_ROOT`) is this plugin's folder, two levels above the folder that holds this file; a settings placeholder (named `user_config.<name>`) is the value of `<name>` under `"ez-core"` in `~/.config/ez-skills/settings.json` (`$XDG_CONFIG_HOME/ez-skills/settings.json` when that variable is set). A missing file or key means the setting is empty.

Every command goes through the script. A command the connection's
permissions do not allow is refused before SSH is opened: nothing reaches the
server.

## Settings

- Script: `${CLAUDE_PLUGIN_ROOT}/skills/ssh-cmd/scripts/run.py`
- Connections file: `${user_config.ssh_connections}`. Empty → the script's
  default, `~/.config/ez-skills/ssh-connections.json`
  (`$XDG_CONFIG_HOME/ez-skills/ssh-connections.json` when that variable is
  set).

Below, `run` is `python3 <script>`, plus `--config <connections file>` when
the setting is not empty.

## On invoke

1. No connection named by the user: list them (name and permissions).

   ```bash
   run --list
   ```

2. Run the command:

   ```bash
   run <name> "df -h"
   ```

   Options: the command can also come on stdin; `--timeout <s>` sets the SSH
   connect timeout (default 15).

3. Follow mode (`tail -f`, `tail -F`, `journalctl -f`, `docker logs -f`, or
   `--follow`) never exits: run it in the background, read its output as it
   arrives, and stop it when done.
4. Report the output in chat.
5. Refusal, connection error or non-zero exit: report the script's message as
   it is, with the command that produced it. Fix only a mistake in the command
   itself (a wrong path, a typo) and run it again; a refusal is final, and
   missing access or a missing key goes to the user.

## What the script does

Python 3, standard library only. It needs `ssh` and the connection's key.

1. Loads the named connection and refuses it when `host` or `user` is
   missing, when `permissions` is not a list of `Read` / `Write` / `Sudo`, or
   when it has `Sudo` without `Write`.
2. **Read** (no `Write` in permissions) refuses the command unless:
   1. it contains none of `;`, `&` (so no `&&`), `>`, `<`, `` ` ``, `$(`,
      `||`, or a newline;
   2. every command in a `|` pipe is on the Read list below;
   3. it passes the per-command limits below.
3. **Write** refuses only a command containing `sudo`, unless the connection
   also has **Sudo**; anything else is sent as typed.
4. Runs
   `ssh -o BatchMode=yes -o ConnectTimeout=<timeout> -T [-i <ssh_key>] [-p <ssh_port>] <user>@<host> -- <command>`
   and exits with its exit code. On Read, every argument that is not a plain
   path, flag or glob is single-quoted, so the remote shell expands nothing
   but globs and `~`.

### Read list

| # | Command | Limit |
| --- | --- | --- |
| 1 | `ls`, `cat`, `grep`, `head`, `tail`, `wc`, `du`, `df`, `ps`, `free`, `uptime`, `whoami`, `pwd` | none |
| 2 | `hostname` | no arguments |
| 3 | `find` | no `-delete`, `-exec`, `-execdir`, `-ok`, `-okdir`, `-fprint`, `-fprint0`, `-fprintf`, `-fls` |
| 4 | `journalctl` | no `--vacuum-*`, `--rotate`, `--flush`, `--sync`, `--relinquish-var`, `--smart-relinquish-var`, `--setup-keys`, `--update-catalog` |
| 5 | `systemctl` | `status` only |
| 6 | `docker` | `ps` and `logs` only |

## Connections file

JSON, outside every repository, mode 600. One entry per server:

```json
{
  "shop-staging": {
    "host": "<ip or hostname>",
    "user": "<ssh login>",
    "ssh_key": "<path to private key, e.g. ~/.ssh/shop.pem>",
    "ssh_port": 22,
    "permissions": ["Read"]
  }
}
```

- Required: `host`, `user`.
- Optional: `ssh_key` and `ssh_port` (passed as `ssh -i` and `ssh -p`).
- `permissions`: `["Read"]`, `["Read", "Write"]` or
  `["Read", "Write", "Sudo"]`. Missing → `["Read"]`. `Sudo` requires `Write`.
- A `sudo` command changes the server: post the plan (the server, the
  command, its effect) and run it only after the user approves it.

## Do not

1. Run a command the connection's permissions do not allow by any other route
   (raw `ssh`, another SSH wrapper, editing the checks).
2. Put keys or passwords in the script, the skill, chat or any tracked file.
3. Read the connections file or print its values; `--list` shows the names.
4. Change the connections file unless the user asks.
