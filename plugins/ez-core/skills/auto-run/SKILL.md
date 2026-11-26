---
name: auto-run
description: >-
  Auto-run mode for the rest of the session: the agent works through the
  active task (step after step) or the agreed plan without stopping for
  choices, decides each choice with the wdyr skill's Option 1, commits with
  olcm's first variant, and stops only when the work is done, at the one push
  question at the end, at a deploy, delete, send or server command, at a
  question a rule keeps under auto-run, or when blocked. Pairs with the
  built-in /goal command, which keeps the session running. `auto-run off` ends
  the mode.
disable-model-invocation: true
argument-hint: "[off]"
---

# auto-run

Arguments: `$ARGUMENTS`

## `off`

When the argument is `off`: from now on stop applying the rules below, and
reply in one line: auto-run is off; run `/goal clear` if a goal is still
active. Stop there.

## Start (no argument)

1. **Scope.** The active task, from its current step through its last one
   (briefing, steps and done conditions), or the plan agreed in chat.
   Neither → ask for one in one line and stop.
2. **Goal condition.** Write one condition the `/goal` evaluator can judge
   from the conversation (it reads the transcript, it runs nothing):
   - the done conditions, each with the check that proves it;
   - "or the agent has stopped to ask the user to approve the push, a deploy,
     a delete, a send or a command on a server";
   - "or the agent has stopped at a question a rule keeps under auto-run";
   - "or the agent reports it is blocked with nothing authorized left";
   - "or stop after 40 turns".
3. **Reply** in two lines, then start the work in the same turn:
   - `auto-run on — <scope>`
   - the ready command in a `text` block: `/goal <condition>`, for the user to run.

## While on

1. **Choices decide themselves.** Every choice, rule conflict, unclear meaning
   or gap in a source that no rule keeps for the user (item 6) goes through
   the wdyr skill and takes Option 1, saved as
   auto-selected. Report each pick in one line:
   `auto-run: Option 1 — <pick> (<research link>)`.
2. **Commits without asking.** Each commit gets its message from olcm's
   auto-run mode (variant 1, committed in the same turn). Report each commit
   in one line: hash and subject.
3. **Push once, at the end.** No push and no push question while work
   remains. When everything else in the goal is done, ask one question that
   covers every pending push (repo, branch, commits, and whether it deploys).
   A done condition never waits for that push: it is checked on the change
   where it is (the worktree or branch). Only a step whose goal is a deploy
   is checked on the live deploy, after the yes, then reported.
4. **Still asked, mode or not.** Stop and ask for: the push above, deploy,
   deleting files or data, sending or publishing anything, and any command
   that runs on a server.
5. **No stop for progress.** A finished subtask, step, test or check is a
   progress line, never a reason to end the turn or ask whether to continue.
   A blocked item does not stop independent work: note its blocker and do
   the rest.
6. **Other rules' questions.** A rule that says to ask the user is waived
   only where that rule itself names an auto-run exception (for example:
   under auto-run, wdyr decides). Without one, it still asks: the agent asks
   that question, keeps working on whatever does not depend on the answer,
   and counts it as a stop in the goal condition. Every other rule from the
   user's instructions still applies.
7. **At the end** (work done, the push question, another approval or a kept
   question, or blocked) reply with a short report: outcome, evidence, every
   commit, every auto-selected pick, open items, the exact next action.
