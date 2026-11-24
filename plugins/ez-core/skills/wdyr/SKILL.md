---
name: wdyr
description: >-
  What Do You Recommend. Researches a question against current official
  sources and answers with one sourced recommendation (Option 1), with
  alternatives only as "Option N when …". Use when the user asks "what do you
  recommend", "what's the best …", "best practice for …", "which should I use",
  "X or Y?", asks for a proposal or plan, or whenever the agent is about to
  recommend a tool, setup, approach or option. Not for explaining existing code.
---

# wdyr — What Do You Recommend

**Placeholders.** Where a path or value below still shows a `${…}` placeholder instead of a real value, fill it in yourself: the plugin-root placeholder (named `CLAUDE_PLUGIN_ROOT`) is this plugin's folder, two levels above the folder that holds this file; a settings placeholder (named `user_config.<name>`) is the value of `<name>` under `"ez-core"` in `~/.config/ez-skills/settings.json` (`$XDG_CONFIG_HOME/ez-skills/settings.json` when that variable is set). A missing file or key means the setting is empty.

Every recommendation comes from research done in this turn, never from memory.
The user gets one pick they can act on, not a survey.

## Workflow

1. **Pin the question.** What is being chosen, for what, under which
   constraints the user stated. For a project question, first read what the
   project already uses (manifests, config, its README): the pick must fit the
   existing stack, or say why it should change. Ask one question first only
   when the answer would change the pick.
2. **Research.** Sources, by weight:
   1. official docs, specs and maintainer guidance;
   2. vendor security or best-practice guides, standards bodies;
   3. project health: latest release, maintenance, deprecations, advisories;
   4. dated independent comparisons.

   Check every claim that decides the pick against at least two sources. Run
   every check that can be run before replying, including ones you raised
   yourself.
3. **Decide.** Rank against the constraints: fit with what exists,
   maintenance, security, simplicity, cost, performance (in that order unless
   the user named a priority). Pick one.
4. **Save** the research as a note named `YYYYMMDD-HHmm-<slug>.md`, with
   the question, timestamp, every option with its number and condition,
   sources with dates, and what was not checked. Where it goes, in this
   order:
   1. the plugin setting `research_command`:
      `${user_config.research_command}` — not set when that value is empty
      or the settings file has no such key. Write the note to a temporary
      file, then run the command with these arguments added after it:
      - a new note: `put <name> --new --file <temporary file>`;
      - the user's pick: `append <name> --file <temporary file>`, the file
        holding only the text to add, starting with a blank line.

      The command exits non-zero → the note is not saved: say so in one line
      with the command's error, and never save it anywhere else.
   2. when the setting is not set, the research folder the user's
      instructions name: the note is a file there;
   3. when neither is set, save nothing and leave **Saved** out of the
      reply.

   When the user picks, add `## Selected` (option, timestamp, the user's
   words) at the end of the note; rewrite nothing earlier.
5. **Reply** in the format below, then stop. A recommendation is not approval
   to implement it.

## Reply format

Short: readable in a few seconds.

1. **Recommendation** — one sentence, labelled **Option 1**.
2. **Why** — at most 3 bullets, each with its source link.
3. **Option 2, 3 …** — one line each: "when <condition>, <alternative>".
   Omit when there are none.
4. **Not checked** — one line, only for what cannot be checked at all.
5. **Saved** — the note as a link, when one was saved: the URL the command
   prints (a `page: <url>` line), else the file in the folder.

Every choice carries an `Option N` label so the user can answer with a digit.

## Auto-pick

When an auto-run or auto-pick mode is on, take Option 1 without asking, record
`auto-selected` as the user's words in `## Selected`, report the pick in one
line with its research link, and continue the work.
