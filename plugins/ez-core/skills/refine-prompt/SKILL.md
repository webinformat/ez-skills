---
name: refine-prompt
description: >-
  Refines the user's rough notes into a handoff prompt for a fresh chat: names
  the most important missing thing, asks one question per gap, and writes the
  prompt (XML sections, one text block) only after the answers; never does the
  task itself. Use when the user pastes rough notes and asks to refine, improve
  or enhance a prompt, asks for a handoff prompt, says refine-prompt, or
  invokes /refine-prompt. Not for reading back a request before work starts,
  or for a message to send to a person.
argument-hint: "[rough notes]"
---

# refine-prompt

Arguments: `$ARGUMENTS`

Turn the user's rough notes into a handoff prompt they paste into a fresh
chat. Name the most important thing missing, ask about the gaps, and write
the prompt only after the answers. Never do the task in the notes: no
search, no code, no draft of the result.

Why: rough notes leave out what a fresh chat needs (quantity, scope, what
"better" means), and a refiner that fills those gaps itself hands off
guesses as facts.

## Steps

1. **Facts.** List every fact the notes state (goal, subject, names, region,
   constraints, wanted outputs) in the user's words. Nothing else goes into
   the prompt as a fact. No notes in the arguments or the message → ask for
   them and stop.
2. **Gaps.** Apply the colleague test from Anthropic's
   [prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
   ("Be clear and direct"): each point a reader with no other context would
   have to guess is a gap. Never fill a gap with a guess or a default.
3. **Most important gap.** Name, in one sentence, the gap that would change
   the result most.
4. **Ask.** One question per gap, at most three per reply, the most
   important first. More than three gaps → ask the rest after these are
   answered. Then stop: no prompt yet.
5. **Answers.** Each answer becomes a fact. An answer that opens a new gap
   goes back to step 4.
6. **Handoff prompt.** When no gap is left, write the prompt in English, in
   these XML sections:
   1. `<role>`: who the fresh chat should act as.
   2. `<context>`: the facts and why the task matters.
   3. `<task>`: what to do, as numbered steps when order matters.
   4. `<constraints>`: the limits the user stated.
   5. `<output_format>`: the shape of the result the user wants.
   6. `<success_criteria>`: what a complete answer contains.
7. **Research tasks.** When the task is a search, `<task>` also asks to
   verify each fact in more than one source and to give the source link next
   to each fact, contact or price.

## Reply

1. **Ask turn** (steps 3–4): the most-important-gap sentence, then the
   questions last.
2. **Prompt turn** (step 6): the handoff prompt in one fenced `text` block
   so it copies as-is. Nothing after the block.

## Bad / good

| # | Bad | Good |
| --- | --- | --- |
| 1 | Notes say "olive oil, Brand X, suppliers in Spain, price comparison" → the prompt says "for 500 cases of 750 ml bottles, wholesale" | Pack size, quantity and wholesale or retail are asked, one question each, and enter the prompt only as answered |
| 2 | First reply is a finished prompt with a "you may want to add" list under it | First reply names the most important gap and asks; the prompt comes after the answers |
| 3 | The agent starts searching for suppliers in Spain itself | Only the prompt is written; the search runs in the fresh chat |
