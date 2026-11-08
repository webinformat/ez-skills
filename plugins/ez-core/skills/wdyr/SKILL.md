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
4. **Save** the research to a folder, picked in this order:
   1. the plugin setting `research_dir`: `${user_config.research_dir}` — not
      set when that value is empty or still shows as a `${user_config…}`
      placeholder;
   2. when the setting is not set, the research folder the user's
      instructions name;
   3. when neither names a folder, save nothing and leave **Saved** out of
      the reply.

   The file is `YYYYMMDD-HHmm-<slug>.md` with the question, timestamp, every
   option with its number and condition, sources with dates, and what was not
   checked. When the user picks, append `## Selected` (option, timestamp, the
   user's words); rewrite nothing earlier.
5. **Reply** in the format below, then stop. A recommendation is not approval
   to implement it.

## Reply format

Short: readable in a few seconds.

1. **Recommendation** — one sentence, labelled **Option 1**.
2. **Why** — at most 3 bullets, each with its source link.
3. **Option 2, 3 …** — one line each: "when <condition>, <alternative>".
   Omit when there are none.
4. **Not checked** — one line, only for what cannot be checked at all.
5. **Saved** — the research file as a link, when one was saved.

Every choice carries an `Option N` label so the user can answer with a digit.

## Auto-pick

When an auto-run or auto-pick mode is on, take Option 1 without asking, record
`auto-selected` as the user's words in `## Selected`, report the pick in one
line with its research link, and continue the work.
