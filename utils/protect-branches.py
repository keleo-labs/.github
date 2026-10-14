#!/usr/bin/env python3
"""Protect the default branch of every keleo-labs repository.

Blocks force pushes and branch deletion on the default branch, with repository
admins able to bypass. It deliberately does not require a pull request: the
rule here is aimed at the accident -- a force push that rewrites shared
history, a branch deleted by a stale script -- not at review process.

Organisation-wide rulesets need GitHub Team, so on the free plan this applies
the same ruleset to each repository individually. Repositories are discovered
through the API rather than from local checkouts, so one that was never cloned
is still covered.

Idempotent. A ruleset of the same name is updated in place rather than
duplicated, and the result is read back and compared with what was sent, since
the RepositoryRole bypass id is not officially documented.

Usage:
    protect-branches.py --list
    protect-branches.py --dry-run
    protect-branches.py --apply [--only NAME ...]
    protect-branches.py --remove [--only NAME ...]

Exit codes: 0 all good, 1 one or more repositories failed, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

ORG = "keleo-labs"
RULESET_NAME = "protect default branch"

# actor_id 5 is the repository admin role. GitHub has never documented the
# well-known RepositoryRole ids (github/rest-api-description#4406); 5 is what
# the UI emits when "Repository admin" is added as a bypass actor. verify()
# reads the ruleset back so a wrong id shows up as a mismatch rather than as a
# rule nobody can bypass.
ADMIN_ROLE_ID = 5

RULESET = {
    "name": RULESET_NAME,
    "target": "branch",
    "enforcement": "active",
    "bypass_actors": [
        {
            "actor_id": ADMIN_ROLE_ID,
            "actor_type": "RepositoryRole",
            "bypass_mode": "always",
        }
    ],
    # ~DEFAULT_BRANCH rather than a literal "main": two repositories could
    # rename their default branch and this would follow them.
    "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
    "rules": [
        # Only allow users with bypass permissions to delete the branch.
        {"type": "deletion"},
        # Prevent users with push access from force pushing.
        {"type": "non_fast_forward"},
    ],
}

WANT_RULES = {rule["type"] for rule in RULESET["rules"]}


def gh(*args: str, stdin: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(["gh", *args], input=stdin,
                          capture_output=True, text=True)
    return proc.returncode, (proc.stdout or proc.stderr).strip()


def repos() -> list[str]:
    """Every non-archived repository in the organisation, by name."""
    rc, out = gh("api", "--paginate", f"orgs/{ORG}/repos",
                 "--jq", ".[] | select(.archived | not) | .name")
    if rc != 0:
        raise RuntimeError(f"could not list {ORG} repositories: {out}")
    return sorted(out.splitlines())


def existing(repo: str) -> dict | None:
    """The ruleset this script manages, if the repository already has one.

    Fetched by id rather than taken from the list response: listing returns a
    summary with no `rules` array at all, so comparing against it reports
    every correctly configured repository as having no rules.
    """
    rc, out = gh("api", f"repos/{ORG}/{repo}/rulesets")
    if rc != 0:
        raise RuntimeError(out)
    for summary in json.loads(out):
        if summary.get("name") == RULESET_NAME:
            rc, detail = gh("api", f"repos/{ORG}/{repo}/rulesets/{summary['id']}")
            if rc != 0:
                raise RuntimeError(detail)
            return json.loads(detail)
    return None


def verify(repo: str, ruleset_id: int) -> str:
    """Read the ruleset back and report how it differs from what was sent."""
    rc, out = gh("api", f"repos/{ORG}/{repo}/rulesets/{ruleset_id}")
    if rc != 0:
        return f"could not read back: {out}"
    got = json.loads(out)
    problems = []
    if got.get("enforcement") != "active":
        problems.append(f"enforcement={got.get('enforcement')}")
    if {rule["type"] for rule in got.get("rules", [])} != WANT_RULES:
        problems.append("rules differ")
    # bypass_actors comes back only to a caller with write access to the
    # ruleset, so its absence is not evidence of anything.
    actors = got.get("bypass_actors")
    if actors is not None and not any(
        a.get("actor_type") == "RepositoryRole" and a.get("actor_id") == ADMIN_ROLE_ID
        for a in actors
    ):
        problems.append("admin bypass missing")
    return ", ".join(problems)


def apply(repo: str) -> tuple[str, str]:
    current = existing(repo)
    body = json.dumps(RULESET)
    if current:
        rc, out = gh("api", "-X", "PUT",
                     f"repos/{ORG}/{repo}/rulesets/{current['id']}",
                     "--input", "-", stdin=body)
        action = "updated"
    else:
        rc, out = gh("api", "-X", "POST", f"repos/{ORG}/{repo}/rulesets",
                     "--input", "-", stdin=body)
        action = "created"
    if rc != 0:
        return "failed", out.splitlines()[-1] if out else "unknown error"
    problem = verify(repo, json.loads(out)["id"])
    return ("mismatch", problem) if problem else (action, "force-push + deletion blocked")


def remove(repo: str) -> tuple[str, str]:
    current = existing(repo)
    if not current:
        return "absent", "nothing to remove"
    rc, out = gh("api", "-X", "DELETE",
                 f"repos/{ORG}/{repo}/rulesets/{current['id']}")
    if rc != 0:
        return "failed", out.splitlines()[-1] if out else "unknown error"
    return "removed", ""


def describe(repo: str) -> tuple[str, str]:
    current = existing(repo)
    if not current:
        return "unprotected", "would create"
    rules = {rule["type"] for rule in current.get("rules", [])}
    if rules == WANT_RULES and current.get("enforcement") == "active":
        return "protected", "already correct"
    return "drifted", f"would update (has {', '.join(sorted(rules)) or 'no rules'})"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="limit to these repository names")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--remove", action="store_true")
    args = ap.parse_args()

    try:
        names = repos()
    except RuntimeError as err:
        print(err, file=sys.stderr)
        return 2

    if args.only:
        wanted = set(args.only)
        missing = wanted - set(names)
        if missing:
            print(f"not found on {ORG}: {', '.join(sorted(missing))}",
                  file=sys.stderr)
            return 2
        names = [n for n in names if n in wanted]

    action = {"list": describe, "dry_run": describe,
              "apply": apply, "remove": remove}[
        "list" if args.list else "dry_run" if args.dry_run
        else "apply" if args.apply else "remove"]

    failed = False
    for name in names:
        try:
            status, detail = action(name)
        except Exception as err:  # noqa: BLE001 - report and carry on
            status, detail = "failed", str(err).splitlines()[-1]
        if status in ("failed", "mismatch"):
            failed = True
        print(f"{name:32} {status:12} {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
