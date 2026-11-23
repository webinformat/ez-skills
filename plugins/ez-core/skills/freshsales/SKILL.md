---
name: freshsales
description: >-
  Reads contacts from a Freshsales CRM through the Freshworks CRM API: lists
  them, searches by name, email or phone and replies with a contact table,
  shows one contact's details and source, and lists one contact's activities
  (its events timeline). Reads only; deleting a contact is handed to the user
  as a command to run. Use when the user asks to find, look up, list or check
  a Freshsales contact, asks for a contact's source or events, asks to delete
  a Freshsales contact, says freshsales, or invokes /freshsales.
---

# freshsales

**Placeholders.** Where a path or value below still shows a `${…}` placeholder instead of a real value, fill it in yourself: the plugin-root placeholder (named `CLAUDE_PLUGIN_ROOT`) is this plugin's folder, two levels above the folder that holds this file; a settings placeholder (named `user_config.<name>`) is the value of `<name>` under `"ez-core"` in `~/.config/ez-skills/settings.json` (`$XDG_CONFIG_HOME/ez-skills/settings.json` when that variable is set). A missing file or key means the setting is empty.

Every call goes through the script. Reads use GET requests only. `delete`
removes contacts by exact email: the agent never runs it, it hands the
command to the user (§ Delete a contact). Nothing creates or updates anything
in Freshsales.

## Settings

- Script: `${CLAUDE_PLUGIN_ROOT}/skills/freshsales/scripts/contacts.py`
- Env file: `${user_config.freshsales_env}`. Empty → the script's default,
  `~/.config/ez-skills/freshsales.env`
  (`$XDG_CONFIG_HOME/ez-skills/freshsales.env` when that variable is set).

Below, `contacts` is `python3 <script>`, plus `--env <env file>` when the
setting is not empty. `--env` goes before the command.

## On invoke

1. Run the command that matches the request (§ Commands):

   ```bash
   contacts search "alex@example.com" --table
   contacts show 123
   contacts list --page 2
   ```

2. For "details" on a search result, run `show` with the id the search
   returned.
3. Report in chat only the fields the user asked for; when they asked for
   details in general, give name, email, phone, company, owner and id. A
   contact search is reported per § Contact search results.
4. An error: report the script's message as it is, with the command that
   produced it. Fix only a mistake in the command itself (a wrong id, a typo)
   and run it again; a missing env file, a missing value in it or a refused
   key goes to the user.

## Commands

Python 3, standard library only. The script prints the API response as JSON
on stdout; errors go to stderr with a non-zero exit. `search --table` prints
a markdown table instead, and `delete` prints one status line per email.

| # | Command | API call |
| --- | --- | --- |
| 1 | `views` | `GET /contacts/filters`: the contact views and their ids |
| 2 | `list [--view ID] [--page N] [--sort FIELD] [--sort-type asc\|desc]` | `GET /contacts/view/<ID>?page=N&sort=FIELD&sort_type=desc`: 25 per page; without `--view` it uses the `All Contacts` view; `--sort updated_at` or `created_at` lists the most recent first (unsorted, the view is not in date order) |
| 3 | `search QUERY [--per-page N] [--table]` | `GET /search?q=QUERY&include=contact&per_page=N`: name, email or phone; `per_page` defaults to 100, the API's maximum (its own default is 10); a stderr warning when the results reach `per_page`; `--table` prints the contact table, reading each contact once with `GET /contacts/<ID>` for its phone, which search results do not carry |
| 4 | `show ID [--include LIST]` | `GET /contacts/<ID>?include=LIST`: default `owner,sales_accounts,deals,source` |
| 5 | `activities ID [--limit N]` | `GET /contacts/<ID>/activities?limit=N`: default 50; the contact's events timeline |
| 6 | `delete EMAIL [EMAIL …]` | per email: `GET /search` for the contact, then `DELETE /contacts/<ID>` (Delete a Contact, not the `/forget` hard delete); deletes only when exactly one contact has that exact email (case ignored), else refuses that email; an argument without `@` is rejected; prints `deleted <email> — <name> — <ID>` or `not deleted: <email> — …`; exit code 1 when any email was not deleted; **the user runs it, never the agent** (§ Delete a contact) |

API reference: [Freshworks CRM API](https://developers.freshworks.com/crm/api/)
(sections Search, List all Contacts, View a Contact, List all Activities,
Delete a Contact, Pagination).

## Contact search results

1. Every contact search (finding one or more contacts by name, email or
   phone) runs `search QUERY --table` and replies with its table as printed:
   Email, Phone, Name, ID, in that order, with no `#` column because each row
   carries its contact id.
2. Several queries for one request (for example one email pattern that needs
   narrower queries) → one table with each contact once.
3. A stderr warning that the list may be cut off → narrow the query and run
   it again; never report the cut-off list as complete.
4. Other fields (owner, source, company) only when the user asks for them.

## Contact source

1. The **Source** shown on a contact in the CRM is the field
   `lead_source_id`.
2. Its value comes back only with `include=source`: the contact gets
   `lead_source_id`, and the response gets a top-level `lead_source` list
   with the source's `id` and `name`. `show` includes it by default.
3. `include=lead_source` is not a valid value: the response then has no
   `lead_source_id` and no source name. Never use it.

## Contact events (activities)

1. Events on a contact (custom events, page views, journeys, WhatsApp
   messages) come only from `activities ID`; `show --include` does not return
   them. Never ask the user how to read a contact's events: run `search`,
   then `activities` with the id.
2. Each activity has `action_type`, `created_at` and `action_data`:
   1. `FM_APP_EVENTS`: a custom event sent by the browser tracking code or
      the marketer events API; `action_data.name` is the event name, and
      repeats of the same name are one activity with a `count` and a
      `last_occurrence`, not separate rows;
   2. `APP_EVENTS`: a custom event sent from a server, with the same fields.
      A search for custom events counts **both** types;
   3. `FM_PAGE_VIEWS`: tracked web page views;
   4. `FM_ENTERED_JOURNEY` / `FM_EXITED_JOURNEY`: `action_data.journey_name`;
   5. `FM_WHATSAPP_MESSAGE_…` (`…_DELIVERED`, `…_READ`, `…_SEND_ERROR`):
      `action_data.campaign_name`;
   6. CRM changes such as `CREATE`, `OWNER_CHANGE`, `CONTACT_STATUS_CHANGED`.
3. Browser events can show up minutes after they are sent, and not
   necessarily on the contact of the email in the payload: events sent for a
   second email from the same browser can land on the first email's contact.
   Freshworks identifies a contact by email address and browser cookie ID,
   and the same browser session updates the existing contact
   ([How to set up the tracking code?](https://crmsupport.freshworks.com/support/solutions/articles/50000003312-how-to-set-up-the-tracking-code-)).
   Check again before concluding an event is missing, and test each account
   in a fresh browser profile or a private window.

## Delete a contact

1. One contact per approval. The user names the contact to delete; run
   `search EMAIL --table` first and report its email, phone, name and id.
2. **Hand the command over; never run it.** The delete command goes alone in
   one fenced `bash` block, on one line, for the user to run. It is written
   out in full: `python3`, the script's real path, `--env <env file>` when the
   setting is not empty, then `delete` and the email; never the `contacts`
   shorthand or a placeholder. It names the contact by **email, never by
   id**, so the user can read who is deleted:

   ```bash
   python3 <script> --env <env file> delete alex@example.com
   ```

3. After the user has run it, run `search EMAIL --table`, or `show ID` with
   the id the delete printed, to confirm the contact is gone.

## Env file

Outside every repository, mode 600:

```text
FRESHSALES_BASE_URL=https://<domain>.myfreshworks.com/crm/sales/api
FRESHSALES_API_KEY=<api key>
```

- Both values are required. The base URL is the CRM's address followed by
  `/crm/sales/api`.
- The API key is in Freshsales under the profile picture → Profile Settings →
  API Settings.

## Do not

1. Call any Freshsales endpoint other than GET, by this script or any other
   route (`curl`, editing the script). The only exception is `delete EMAIL`,
   and only the user runs it (§ Delete a contact).
2. Put the API key in the script, the skill, chat or any tracked file.
3. Read the env file or print its values.
4. Change the env file unless the user asks.
