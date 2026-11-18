---
name: cr
description: >-
  Confirm request: reads the user's request back as a numbered summary of 1 to
  5 items and does nothing else that turn, so the user can check that it
  landed before any work starts. The request stays open until the user sends
  `acr`; every other reply is a revision and gets a new full summary. Use only
  when the user says cr, /cr or "confirm request". Not for a change request
  that does not say it, and not to confirm running a named skill the user
  invoked (follow that skill instead).
argument-hint: "[the request to read back]"
---

# cr

Arguments: `$ARGUMENTS`

**Confirm request.** `cr` means confirm; `acr` means approve the confirmed
request.

When the user's message has `cr`, `/cr` or "confirm request": **stop.** Reply
with a short summary of the request and nothing else. Do not answer, plan,
search, edit a file or run a command in that turn. The request then stays
open until the user sends `acr` in a later message.

The user may put `cr` and the work in one message (`/cr` plus "change every
project so that …"). That work text is what gets restated. It is not
permission to start, and it never overrides `cr`.

## Flow

| Step | Who | Action |
| --- | --- | --- |
| 1 | User | Says `cr`, `/cr` or "confirm request", with or without the work in the same message. |
| 2 | Agent | Replies with a numbered summary of 1 to 5 items and the closing line **Confirm request**, then stops. |
| 3 | User | Approves by sending `acr` in a later message. |
| 4 | Agent | Starts the work from the settled summary, only after step 3. |

## What is not approval

Only a reply that contains the token `acr` approves. None of these do:

- "yes", "correct", "looks good", "that's right";
- "go ahead", "implement", "make the change", "do it";
- any other reply without `acr`.

Treat such a reply as a revision (below) or as no approval, and keep waiting.

## Revision loop

A later message without `acr` (a change, a dropped item, a question):

1. Do not start the work.
2. Answer each question in it first. Read-only lookups (reading a file, a
   search, the web) are allowed for that answer only: no edits and no
   preparation for the work.
3. Fold every change into the request: a new ask becomes a new item, a change
   rewrites its item, a dropped item is removed.
4. Restate the whole request as a new full numbered summary, never as a list
   of what changed, and close with **Confirm request** again.
5. Wait for `acr`.

Repeat until the user sends `acr`.

## The reply

1. Only in a reply to a later message that asks a question: the answer first,
   in prose.
2. A numbered list of 1 to 5 short items that restate the request: what to
   do, what it affects, and each constraint the user stated. The agent's own
   words, not a pile of quotes. Several requests in one message get one item
   each, in the order given.
3. The last line, in bold, exactly: **Confirm request**

Keep it under about 10 lines: no headings, no tables, no code blocks. This
shape replaces any other reply format the agent normally follows.

The summary comes from the conversation only. Never open a file to check
what the user meant: what they did not say is unclear, and an unclear point
is asked, not looked up.

## Forbidden in a cr reply

- Any tool call other than the one that loaded this skill: no reading,
  searching or listing files, no web, no subagent, no other skill.
- Creating, editing or deleting any file, including notes, logs and task
  records.
- Starting, planning or partly doing the work.
- Design opinions, risks, alternatives, estimates, next steps or "want me
  to …" offers.
- An "Unclear:" line or any other hedge inside the summary.

## Unclear requests and edge cases

- **Nothing was requested yet:** say so in one line and stop. Do not invent a
  request.
- **The request can be read more than one way:** settle it before the
  read-back. Ask the one question that changes the work, with numbered
  options, wait for the answer, and put the answer in the summary as a
  settled item. Whatever a careful colleague would settle with an obvious
  default is decided, written as an item, and not asked.
- **The user named a skill to run** (`/ccf`, `olcm`, a deploy skill): that is
  not material for a read-back. Load that skill and follow it; its own
  confirmation steps apply. When the same message also says `cr`, `cr` wins:
  read the request back and do not start the other skill.
- **A change request without `cr`** is ordinary work. Never add a read-back
  the user did not ask for.

## Example

User: `/cr add a search box to the orders page, only for admins`

```text
1. Add a search box to the orders page.
2. Only admins see and use it.

**Confirm request**
```

Revision, then approval:

User: `it should search by order number and customer name`

```text
1. Add a search box to the orders page.
2. It searches by order number and by customer name.
3. Only admins see and use it.

**Confirm request**
```

User: `acr`

The agent starts the work.

## Bad / good

| # | Bad | Good |
| --- | --- | --- |
| 1 | `cr` plus a change request in one message; the agent reads two files "to prepare" and then summarizes | The summary from the message alone, no tool call |
| 2 | After the read-back the user says "looks good, go ahead"; the agent starts | The agent says it waits for `acr` and starts nothing |
| 3 | A read-back is open; the user writes "use the staging account. what does archiving do there?"; the agent asks permission to look it up | The agent looks it up, answers the question first, then posts the full summary with the staging account folded in |
| 4 | The summary ends with "Unclear: which page?" | The agent asks which page first, then reads the request back with the answer in it |
| 5 | The summary adds "this may be risky, an alternative is …" | Only what the user asked, restated |
