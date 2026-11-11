---
name: short-message
description: >-
  Drafts a short plain-text message the user copies and sends to someone else
  (a colleague, a client): only the facts asked for, no greeting, no approval
  request, no markdown or special symbols, paths with >, returned in one text
  code block. Use when the user asks for a short message, a short reply or a
  simple message to send, says short-message, or invokes /short-message. Not
  for making the agent's own replies shorter.
argument-hint: "[what the message says]"
---

# short-message

Arguments: `$ARGUMENTS`

The message is a draft for the user to send; never send or post it.

## Settings

A plugin setting is not set when its value is empty or still shows as a
`${user_config…}` placeholder.

- Plain letters: `${user_config.plain_letters}` — `true` → write without
  diacritics from the first draft (Romanian `a`, `i`, `s`, `t`, not `ă`, `â`,
  `î`, `ș`, `ț`; the same for other languages). Not set or `false` → spell
  the language normally.

## Message rules

1. **Short and simple.** Only the facts the message needs: no background, no
   caveats the user did not ask for.
2. **No greeting.** No "Hi", "Hello" or the recipient's name as an opener.
3. **No call to action.** No "please confirm", "let me know", "approve" or
   "I'll go ahead".
4. **Plain text.** No markdown: no bold, italics, headings, backticks or
   bullets. Numbers at the start of a line (`1.`, `2.`) are fine.
5. **No special characters.** No arrows (`→`, `⇒`), decorative dashes, emoji
   or other symbols a chat app may not render.
6. **Navigation paths use `>`:** `Reports > Engagement > Events`.
7. **Asking means asking.** When the message is to get copy, wording or a
   decision from the recipient, ask for it. Never draft the title,
   description, body text or keywords for them to confirm, tweak or pick
   from.
8. **No options or suggestions.** No "same as X or different?", "reuse Y",
   proposed strings, or side details the user did not ask for (translation
   tool, missing keys, file paths).
9. **Match the ask.** Exactly what the user asked for, in the same framing
   and shape, nothing extra. Asked "say what we send to X and list the
   events" → open with `We send to X:` and name the events only: no
   implementation detail (SDK, repo, script flags), no when it fires, no
   payloads unless asked, no list of what is not sent.

## Reply

Only the whole message, in one fenced `text` block so it copies as-is; no
notes before or after it.

## Revisions

Apply each change the user asks for and return the whole message again under
the same rules. "Shorter" or "no explanation" → strip to the asked shape
only, often a one-line opener plus the list.

## Good

Formatting:

```text
Pixel: landing page leads are sent with landing_page_name = spring-lp, so they can already be told apart in the ads manager.

Analytics: we can send lead_type = Spring LP. It would show under Reports > Engagement > Events > generate_lead > lead_type.
```

Asking for copy:

```text
What are the EN title, meta description and intro text for the sample menu page?
```

A numbered reply to someone's numbered points:

```text
1. Videos are fixed on the live site.

2. The bundle offer only needs the pricing change from Alex.

3. The FAQ box now gets its answers from the FAQ service.

4. A possible reason for the 0.00 total is the price call failing. I could not reproduce it by removing the promo code. When the price fails to load, checkout now shows an error with a Retry button instead of 0.00.
```

Matching the ask ("say we send to the CRM and list the events"):

```text
We send to the CRM:

Added to cart
Download App
Identify visitor
```

## Bad / good

| # | Bad | Good |
| --- | --- | --- |
| 1 | `Hi Alex, **Pixel:** leads carry landing_page_name → Reports → Events. Please confirm and I'll go ahead.` | No greeting, no markdown, `>` for paths, no call to action |
| 2 | Drafts the page title and meta description and asks the recipient to "confirm or adjust" | Asks what the title and meta description are |
| 3 | Asks for the copy, then adds "same intro as the product page, or different?" | The question only, no option offered |
| 4 | Lists the events, then where they fire, the SDK, and what is not sent | `We send to the CRM:` and the event names |
| 5 | Asked to list what we send, opens with "The web app sends via the SDK:" | Opens in the user's own framing: `We send to the CRM:` |
