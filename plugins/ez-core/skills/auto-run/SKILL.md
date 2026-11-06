---
name: auto-run
description: >-
  Auto-run mode for the rest of the session: the agent works through the
  active task step or the agreed plan without stopping for choices, decides
  each choice with the wdyr skill's Option 1, and stops only when the work is
  done, at an approval gate (commit, push, deploy, delete, send, a command on
  a server) or when blocked. Pairs with the built-in /goal command, which keeps
  the session running. `auto-run off` ends the mode.
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

1. **Scope.** The active task step (its briefing, steps and done conditions)
   or the plan agreed in chat. Neither → ask for one in one line and stop.
2. **Goal condition.** Write one condition the `/goal` evaluator can judge
   from the conversation (it reads the transcript, it runs nothing):
   - the step's done conditions, each with the check that proves it;
   - "or the agent has stopped to ask the user to approve a commit, push,
     deploy, delete, send or a command on a server";
   - "or the agent reports it is blocked with nothing authorized left";
   - "or stop after 40 turns".
3. **Reply** in two lines, then start the work in the same turn:
   - `auto-run on — <scope>`
   - the ready command in a `text` block: `/goal <condition>`, for the user to run.

## While on

1. **Choices decide themselves.** Every choice, rule conflict, unclear meaning
   or gap in a source goes through the wdyr skill and takes Option 1, saved as
   auto-selected. Report each pick in one line:
   `auto-run: Option 1 — <pick> (<research link>)`.
2. **Never decided, mode or not.** Stop and ask for: commit, push, deploy,
   deleting files or data, sending or publishing anything, and any command
   that runs on a server.
3. **No stop for progress.** A finished subtask, test or check is a progress
   line, never a reason to end the turn or ask whether to continue. A blocked
   item does not stop independent work: note its blocker and do the rest.
4. **Nothing else is waived.** Every other rule from the user's instructions
   still applies.
5. **At the end** (work done, approval gate or blocked) reply with a short
   report: outcome, evidence, open items, the exact next action. Marking a
   task step complete stays with the user.
