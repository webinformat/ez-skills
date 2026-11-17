# ez-skills

Ciprian's shared agent skills. Edit them only here; agents install them from
this repository.

## Plugins

| Plugin | Skills |
| --- | --- |
| `ez-core` | `wdyr` — researched recommendations; `auto-run` — work without stopping (with `/goal`); `ccf` — group changed files into commits; `check-code` — DRY, SSOT and best-practice audit; `short-message` — plain-text message to send; `olcm` — commit messages for the current changes; `refine-prompt` — handoff prompt for a fresh chat from rough notes; hook: commit messages only from `olcm` or `ccf` |

## Install in Claude Code

```bash
claude plugin marketplace add webinformat/ez-skills
```

```bash
claude plugin install ez-core@ez-skills
```

Updates: turn on auto-update for `ez-skills` in `/plugin` → Marketplaces, or
run `claude plugin marketplace update ez-skills`. Plugins carry no `version`,
so every pushed commit is a new version.

## Layout

```text
.claude-plugin/marketplace.json   catalog
plugins/<plugin>/.claude-plugin/plugin.json
plugins/<plugin>/skills/<skill>/SKILL.md
plugins/<plugin>/hooks/hooks.json     Claude Code hooks (ez-core: commit rule)
```

Skills follow the Agent Skills format (`SKILL.md` with `name` and
`description`), so Cursor and Codex can use them too.

## Use in Codex and Cursor

Claude Code fills two placeholders in skill text itself: the plugin-root
placeholder and the plugin settings. Codex and Cursor do not, so each skill
that uses them starts with a short note telling the agent to fill them in.

Settings live in one file, `~/.config/ez-skills/settings.json`
(`$XDG_CONFIG_HOME/ez-skills/settings.json` when that variable is set), keyed
by plugin name and then by the setting name from the plugin's `userConfig`:

```json
{"ez-core": {"research_dir": "/path/to/research/"}}
```

A missing file or key means the setting is empty.
