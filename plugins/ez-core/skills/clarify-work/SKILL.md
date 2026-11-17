---
name: clarify-work
description: >-
  Builds a verified artifact page for complex work the user has to understand
  before deciding: one card per named issue or pending item, each with the
  issue, request or briefing, what was found in plain words, the open
  question, the decided solution, what is pending and how it was solved, each
  section with its own hidden, numbered sources; the user refines it through
  comments. Use when the user says clarify-work, invokes /clarify-work, or
  asks to present issues or pending items as an artifact to understand or
  clarify work whose code or flow they do not know. Not for listing open
  items, or for one recommendation (use wdyr).
argument-hint: "[items to clarify]"
---

# clarify-work

Arguments: `$ARGUMENTS`

Complex work (code and flows the user does not know, pending items that need
a detailed exchange) is hard to decide on in chat: facts, sources and
discussion spread over many replies. This skill puts each item on one page
the user can check, with the text changing in one place.

## Rules

1. **Only the named items.** The artifact holds only the issues or pending
   items the request names.
2. **An artifact, never a report.** Publish it as a private artifact, one
   HTML page, with the Artifact tool (run its quickstart first). An agent
   without an Artifact tool writes the page as a local HTML file and gives
   its path.
3. **Every fact is checked.** Read the code, ticket, thread or document
   before writing a fact. A fact not checked is not on the page. Each fact's
   source goes in the Sources block of the section that states it (see
   [The card](#the-card)).
4. **Code links** go to the exact file and lines on the remote that hosts it
   (GitLab, GitHub), at a fixed commit, never a branch. Code pushed nowhere
   gets no link, and the source says so. A line at the end of the page names
   each commit the links use.
5. **Neutral wording.** No "please fix", no "ask X", no judging anyone's
   decision, no person named unless the user asks or a source names who
   asked for the item.
6. **Nothing unexplained.** What someone said is quoted with who said it; a
   calculation or rule is spelled out in full with exact values.
7. **Order.** One numbered card per item, in the order to solve them when a
   source gives one, else in the order the request names them. When the
   items share a flow, a short flow summary comes first, above the cards.
8. **A plan already decided** is written as the Solution, never as a
   question.
9. **An item for a separate step** records its current state and says it is
   handled in that step, with no question.
10. **A security item** gets a red card.
11. **A clarification is not an answer.** A pending item is answered and
    resolved only when the user asks for their answer to be recorded, in a
    comment or in the session ("record as my answer").
12. **The artifact only.** The reply in chat is the artifact link alone, no
    summary of its content.
13. **Comments change the page in place.** For each comment: edit the page
    text, republish to the same link, reply in the thread with what changed,
    and leave the thread open.

## Draft and copy to send

The work always starts as the draft: its title ends in ` Draft` (for
example `Reply to Alex Feedback Draft`).

When the user asks for a copy to send:

1. Ask the user for the copy's name before publishing it.
2. Publish a separate artifact with no comments, titled with that name
   (`Reply to Alex Feedback`), and rename the draft to the same name plus
   ` Draft`.
3. From then on every edit goes to the draft only. The copy is updated from
   the draft only when the user asks.
4. Renaming one renames the other, keeping the ` Draft` suffix on the draft.

## The card

Sections in this exact order. A section shows only when it has content.

**Toggles.** Each card is a native `<details open>` with the card's number
and title as its `<summary>`; each section inside it is a `<details open>`
with the section name as its `<summary>`. Both start open. Every toggle
(card, section, Sources block) is remembered per browser in `localStorage`,
keyed by card number, section name and, for a Sources block, `sources`.
Wrap every storage read and write in try/catch so the page still works when
storage is blocked; the state survives a refresh and a republish to the same
link.

**Sources stay apart from the content.** A section's text holds no source:
no link, file, quote attribution or source date, except the quote and its
speaker in the first section. A section that has sources ends with its own
Sources block below its content: a `<details>` without `open`, with
`Sources` as its `<summary>`, hidden until clicked and remembered once
opened. It lists the code links and other sources for that section's facts,
including who said a quoted line, where and when. The card has no Sources
section of its own.

**Numbered sources.** The Sources block is a numbered list, restarting at 1
in each section. Each fact in the section text ends with a small superscript
link to its source, `<sup><a href="#…">1</a></sup>`. A click on the number
opens the section's Sources block, scrolls to that source and highlights it
briefly.

1. **The issue, The request, The briefing or Found issue**, named after what
   started the item:
   - **The issue**: someone reported a problem.
   - **The request**: someone asked for something.
   - **The briefing**: the item comes from a handover or brief.
   - **Found issue**: a problem nobody reported, found during the
     investigation; it names no one.

   The first three quote the exact words and who said them in the section
   text; where and when go in its Sources block. When the source does not
   name the author, quote the words and say nothing about who said them.
2. **What was found**: the investigation's results, how it works now, in
   plain words. No code, file or line references in the text (they go in
   Sources).
3. **Question**: only when one is open.
4. **Solution**: the decided fix only. It describes the fix and never says
   it is done. A card with no decided fix has no Solution and no proposed
   fix; the open point goes in the Question. When a recorded answer decides
   the fix, the Solution states the fix, and the answer's quote, with who,
   where and when, goes in the Solution's Sources block.
5. **Pending**: what is still open, in its own colour: purple, `#5b3f8c` in
   light mode and `#c4a8f0` in dark mode.
6. **How it was solved**: how the item was actually solved, with its date.
   It shows only once the fix is actually done; a recorded answer alone does
   not count. "Done" is written only here.

## Writing a card

1. **Short.** Only the important points; cut details that do not change the
   decision.
2. **On the reported issue.** Stay on what was reported, not on what happens
   before or after it in the flow.
3. **What was found matches the issue** as it was described.
4. **Only its own item.** Each card answers its item, not all the items.
5. **No judging.** Never say the reader is right, or that someone's decision
   is good or bad.
6. **Name who asked** for the item when a source names them; otherwise say
   nothing about it.
7. **A shared fix is reused word for word** on every card it fits.
8. **No internal references.** No substeps, internal rule names, version
   numbers or tooling the reader does not know.

## Bad / good

| # | Bad | Good |
| --- | --- | --- |
| 1 | "What was found" names `src/cart/total.ts:42` | Plain words with a superscript number; the link to lines 42–48 at a fixed commit is in that section's Sources |
| 2 | A link to the file on `main` | A link at the commit the agent read, named at the end of the page |
| 3 | Solution: "Round VAT on the total (decided by Alex in the 3 May call)" | Solution: "Round VAT on the total"; Alex's quote, where and when go in its Sources |
| 4 | A card with no decision proposes a fix | No Solution; the open point is the Question |
| 5 | Solution says "Done, deployed" | Solution describes the fix; "How it was solved" says it was done, with the date |
| 6 | A comment asks for a change; a new page with a new link is published | The same page is edited and republished at the same link, with a thread reply naming what changed |
