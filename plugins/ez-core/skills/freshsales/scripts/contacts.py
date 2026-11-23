#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")

DEFAULT_ENV = CONFIG_HOME / "ez-skills" / "freshsales.env"

ENV_KEYS = ("FRESHSALES_BASE_URL", "FRESHSALES_API_KEY")

# Freshworks search returns 10 results by default; 100 is the documented maximum for per_page
SEARCH_PER_PAGE_MAX = 100

# Filled once in main() from the env file
API = {}


def fail(message):
    print(f"freshsales: {message}", file=sys.stderr)
    return 1


def load_env(env_file):
    if not env_file.exists():
        raise SystemExit(fail(f"missing {env_file} (a file with {' and '.join(ENV_KEYS)})"))
    values = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    for key in ENV_KEYS:
        if not values.get(key):
            raise SystemExit(fail(f"{key} is not set in {env_file}"))
    return {"base_url": values["FRESHSALES_BASE_URL"].rstrip("/"), "api_key": values["FRESHSALES_API_KEY"]}


class ApiError(Exception):
    pass


def send(method, path, params=None):
    url = f"{API['base_url']}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        method=method,
        headers={
            "Authorization": f"Token token={API['api_key']}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode(errors="replace")
            return json.loads(body) if body.strip() else {"status": response.status}
    except urllib.error.HTTPError as error:
        body = error.read().decode(errors="replace")
        raise ApiError(f"HTTP {error.code} for {method} {path}: {body}")
    except urllib.error.URLError as error:
        raise ApiError(f"cannot reach {url}: {error.reason}")


def get(path, params=None):
    try:
        return send("GET", path, params)
    except ApiError as error:
        raise SystemExit(fail(str(error)))


def all_contacts_view_id():
    filters = get("contacts/filters").get("filters", [])
    for view in filters:
        if view.get("name") == "All Contacts":
            return view["id"]
    raise SystemExit(fail("no 'All Contacts' view found; pass --view (see 'views')"))


def per_page_value(text):
    value = int(text)
    if not 1 <= value <= SEARCH_PER_PAGE_MAX:
        raise argparse.ArgumentTypeError(f"must be 1-{SEARCH_PER_PAGE_MAX}")
    return value


def search_contacts(query, per_page):
    results = get("search", {"q": query, "include": "contact", "per_page": per_page})
    if len(results) >= per_page:
        print(f"freshsales: {len(results)} results — the list may be cut off at per_page={per_page}; narrow the query", file=sys.stderr)
    return results


def cell(value):
    return str(value).replace("|", "\\|") if value else "—"


def print_contact_table(results):
    # Search results carry no phone, so each contact is read once for it
    # Email and phone first; no # column, since every row carries its contact id
    print("| Email | Phone | Name | ID |")
    print("| --- | --- | --- | --- |")
    for hit in results:
        contact = get(f"contacts/{hit['id']}").get("contact", {})
        phone = contact.get("mobile_number") or contact.get("work_number")
        print(f"| {cell(hit.get('email'))} | {cell(phone)} | {cell(hit.get('name'))} | {hit['id']} |")


def contact_by_email(email):
    # Only an exact email match counts, so the command the user reads names who is deleted
    hits = get("search", {"q": email, "include": "contact", "per_page": SEARCH_PER_PAGE_MAX})
    matches = [hit for hit in hits if (hit.get("email") or "").lower() == email.lower()]
    if len(matches) != 1:
        return None, f"{len(matches)} contacts have this exact email"
    return matches[0], None


def delete_contact(email):
    contact, reason = contact_by_email(email)
    if not contact:
        print(f"not deleted: {email} — {reason}")
        return 1
    label = f"{email} — {contact.get('name') or '—'} — {contact['id']}"
    try:
        result = send("DELETE", f"contacts/{contact['id']}")
    except ApiError as error:
        print(f"not deleted: {label} — {error}")
        return 1
    if result is True:
        print(f"deleted {label}")
        return 0
    print(f"not deleted: {label} — API answered {json.dumps(result, ensure_ascii=False)}")
    return 1


def delete_contacts(emails):
    failures = sum(delete_contact(email) for email in emails)
    return 1 if failures else 0


def email_value(text):
    if "@" not in text:
        raise argparse.ArgumentTypeError(f"{text} is not an email; delete takes emails, not ids")
    return text.strip()


def main():
    parser = argparse.ArgumentParser(description="Freshsales contacts: read them, and delete contacts by email (delete is run by the user, never by an agent)")
    parser.add_argument("--env", help=f"env file with {' and '.join(ENV_KEYS)} (default {DEFAULT_ENV})")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("views")

    list_parser = commands.add_parser("list")
    list_parser.add_argument("--view", type=int)
    list_parser.add_argument("--page", type=int, default=1)
    list_parser.add_argument("--sort", help="field to sort by, e.g. updated_at or created_at")
    list_parser.add_argument("--sort-type", choices=["asc", "desc"], default="desc")

    search_parser = commands.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--per-page", type=per_page_value, default=SEARCH_PER_PAGE_MAX, metavar="1-100")
    search_parser.add_argument("--table", action="store_true", help="print a markdown table: Email, Phone, Name, ID")

    show_parser = commands.add_parser("show")
    show_parser.add_argument("id", type=int)
    show_parser.add_argument("--include", default="owner,sales_accounts,deals,source")

    activities_parser = commands.add_parser("activities")
    activities_parser.add_argument("id", type=int)
    activities_parser.add_argument("--limit", type=int, default=50)

    delete_parser = commands.add_parser("delete", help="DELETE contacts by exact email; the user runs this, never an agent")
    delete_parser.add_argument("emails", nargs="+", type=email_value, metavar="EMAIL")

    args = parser.parse_args()

    API.update(load_env(Path(os.path.expanduser(args.env)) if args.env else DEFAULT_ENV))

    if args.command == "views":
        result = get("contacts/filters")
    elif args.command == "list":
        view_id = args.view or all_contacts_view_id()
        params = {"page": args.page}
        if args.sort:
            params.update(sort=args.sort, sort_type=args.sort_type)
        result = get(f"contacts/view/{view_id}", params)
    elif args.command == "search":
        result = search_contacts(args.query, args.per_page)
        if args.table:
            print_contact_table(result)
            return 0
    elif args.command == "activities":
        result = get(f"contacts/{args.id}/activities", {"limit": args.limit})
    elif args.command == "delete":
        return delete_contacts(args.emails)
    else:
        result = get(f"contacts/{args.id}", {"include": args.include})

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
