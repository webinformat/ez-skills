#!/usr/bin/env python3
"""Commit-message rule for ez-core: messages come only from olcm or ccf.

Hook modes (hooks/hooks.json):
  session-start  SessionStart: puts the standing rule in context at start,
                 resume, clear and compact.
  prompt         UserPromptSubmit: when the prompt asks to commit or for a
                 commit message, tells the agent to load ccf or olcm.

Reads the hook's JSON on stdin; prints nothing on any error.
"""
import json
import re
import sys

RULE = (
    "Commit rule (ez-core): never write a commit message yourself. Every commit "
    "message shown to the user comes from the olcm skill (one commit) or the ccf "
    "skill (several commits), including a commit that a skill's flow asks for "
    "(such as completing a task step) and a commit after a fix. A commit message "
    "never carries an internal task id (no `Task: <id>` line); a task is named only "
    "by its ticket. When work ends "
    "with uncommitted changes, report what changed and say it is uncommitted; "
    "do not volunteer a commit message or a commit command. Commit only after "
    "the user picks a message."
)

CCF = re.compile(
    r"\b(commit|stage)\s+(these|those|the|my|all|this|it|them|everything|now)\b"
    r"|\bgroup\b.*\bfor\s+commits?\b"
    r"|\bwhat\s+(files\s+)?changed\b"
    r"|\bready\s+to\s+commit\b"
    r"|\bcommit\s+and\s+push\b",
    re.IGNORECASE,
)
OLCM = re.compile(
    r"\bcommit\s+(message|msg)s?\b"
    r"|\bwhat\s+should\s+the\s+commit\s+say\b"
    r"|\bmesaj(ul)?\s+(de\s+)?commit\b",
    re.IGNORECASE,
)
INVOKED = re.compile(r"(^|\s)[/$]?(olcm|ccf)\b", re.IGNORECASE)


def context(event, text):
    return json.dumps(
        {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
    )


def prompt_hint(prompt):
    if not prompt or INVOKED.search(prompt):
        return None
    if OLCM.search(prompt):
        skill = "olcm"
    elif CCF.search(prompt):
        skill = "ccf"
    else:
        return None
    return (
        f"This prompt is about committing: load the {skill} skill (ez-core:{skill}) "
        "before writing any commit message. When a running skill has its own commit "
        "step (such as olcm for a task step's completion), that step decides which "
        "skill. " + RULE
    )


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    if mode == "session-start":
        print(context("SessionStart", RULE))
    elif mode == "prompt":
        hint = prompt_hint(data.get("prompt") or "")
        if hint:
            print(context("UserPromptSubmit", hint))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
