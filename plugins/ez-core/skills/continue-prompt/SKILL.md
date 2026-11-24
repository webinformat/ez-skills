---
name: continue-prompt
description: >-
  Writes a handoff prompt that lets a new session (Claude, Codex, Cursor)
  continue this session's work: the goal, what is done, the repo state checked
  live this turn, the user's decisions and corrections, the next steps and the
  open questions, in XML sections in one text block. Never does the next step
  and never starts a session itself. Use when the user asks for a prompt to
  continue the work in another session, a new chat or another agent, asks to
  hand this session off, says continue-prompt, or invokes /continue-prompt.
  Not for turning rough notes into a prompt (use refine-prompt).
argument-hint: "[what the next session should focus on]"
---

# continue-prompt

Arguments: `$ARGUMENTS`

Write a prompt the user pastes into a new session so it continues this
session's work without the conversation. Only write the prompt: no next step,
no commit, no new session started, unless the user asks for that separately.

Why: a new session sees the repo but not the conversation. What it needs from
here is what the repo does not hold: the goal, the decisions, what was tried,
and what comes next. A fresh context is good at finding state in the files, so
the prompt points to files and tells the session how to check them, instead
of copying them (Anthropic,
[prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices),
section "Workflows across multiple context windows").

## Steps

1. **Scope.** The arguments name what the next session should do. No
   arguments → all the work of this session that is still open. When the
   conversation does not show what comes next and the arguments do not say,
   ask that one question and stop.
2. **From the conversation**, in the user's words where they gave them:
   1. the goal and why it matters;
   2. what was done, with the files and commits;
   3. the decisions and corrections the user made, quoted with who said them;
   4. the limits the user set in this session (what not to touch, what to
      ask before);
   5. what was tried and did not work, so it is not tried again;
   6. the open questions and who answers each.
3. **Live state, checked this turn.** Run the checks; never copy state from
   earlier in the conversation:
   1. folder: the absolute path, and the worktree when there is one;
   2. git: `git branch --show-current`, `git status --short`,
      `git log --oneline -5`, and whether the branch is pushed (`git fetch`,
      then `git status -sb`);
   3. tests or builds: only those run in this session, with the command and
      the result; when code changed after the last run, say so;
   4. anything still running that the work needs (a dev server, a job), as
      found now.
   A fact that cannot be checked now goes into `<start>` as something the
   next session checks first, never into the prompt as a fact.
4. **Leave out** what the next session reads by itself (the project's
   `CLAUDE.md`, `AGENTS.md`, README, rules): name the file instead of copying
   it. Never put a secret in the prompt (tokens, passwords, `.env` values):
   name the file or setting that holds it.
5. **Write the prompt** in English, in these XML sections; leave out a
   section that would be empty:
   1. `<context>`: the goal, why it matters, the folder, branch and worktree.
   2. `<done>`: what is done, with files and commits.
   3. `<state>`: the live state from step 3, with the time it was checked.
   4. `<decisions>`: the user's decisions and corrections, quoted.
   5. `<constraints>`: the limits the user set in this session.
   6. `<dead_ends>`: what was tried and did not work, and why.
   7. `<next_steps>`: numbered, the next one first; each open question with
      who answers it.
   8. `<start>`: how the session begins: go to the folder, read the files
      named in the prompt, run `git status` and `git log`, compare with
      `<state>`; when they differ, the live state wins and the session says
      what changed before doing anything; never redo work listed in
      `<done>`.
   9. `<success_criteria>`: what finished looks like.
6. **Size.** As short as it can be while the next session needs nothing from
   the conversation: one line per fact, file paths instead of file contents.

## Reply

The prompt in one fenced `text` block so it copies as it is. Nothing after
the block.

## Bad / good

| # | Bad | Good |
| --- | --- | --- |
| 1 | `<state>` says "all changes committed" because a commit was made an hour ago | `git status --short` runs now; the two files changed since are listed as uncommitted |
| 2 | "Tests pass" with no command, after the code changed again | "`npm test` passed at 14:10; `src/cart.ts` changed after it" |
| 3 | The prompt copies the project's `CLAUDE.md` rules | "Read `CLAUDE.md` first" |
| 4 | "The user prefers small commits" from the agent's own reading | The user's words, quoted: "one commit per fix (Alex)" |
| 5 | `.env` has `API_KEY=sk-…` in the prompt | "The API key is in `.env` (`API_KEY`)" |
| 6 | The agent writes the prompt, then starts the next step | Only the prompt; the next step runs in the new session |
