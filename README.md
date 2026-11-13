# ez-skills

Ciprian's shared agent skills. Edit them only here; agents install them from
this repository.

## Plugins

| Plugin | Skills |
| --- | --- |
| `ez-core` | `wdyr` — researched recommendations; `auto-run` — work without stopping (with `/goal`); `ccf` — group changed files into commits; `check-code` — DRY, SSOT and best-practice audit; `short-message` — plain-text message to send; `olcm` — commit messages for the current changes |

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
```

Skills follow the Agent Skills format (`SKILL.md` with `name` and
`description`), so Cursor and Codex can use them too.
