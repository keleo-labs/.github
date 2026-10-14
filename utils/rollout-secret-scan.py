#!/usr/bin/env python3
"""Roll the shared secret-scan workflow out across the keleo-labs repositories.

Every repository gets a thin caller workflow pointing at the reusable jobs in
keleo-labs/.github, plus the two config files those jobs and the local hooks
need. Existing configs are never overwritten -- several repositories have
tuned their own rules and those are the authority.

Work happens in a throwaway git worktree checked out from origin's default
branch, so a repository with uncommitted changes is left untouched and the
branch cannot accidentally carry unrelated work.

Usage:
    rollout-secret-scan.py --list
    rollout-secret-scan.py --dry-run
    rollout-secret-scan.py --propose [--only NAME ...]
    rollout-secret-scan.py --propose --force      # replace existing workflows

Exit codes: 0 all good, 1 one or more repositories failed, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATES = HERE / "templates"
ORG = "keleo-labs"
SELF = ".github"
BRANCH = "chore/shared-secret-scan"

# Destination path in the target repository -> template file here. The caller
# workflow is the point of the exercise; the other two are what it depends on.
# GITLEAKS_CONFIG in the reusable workflow names .gitleaks.toml explicitly, so
# a repository without one fails the job rather than silently scanning with
# defaults.
FILES = {
    ".github/workflows/secret-scan.yml": "secret-scan-caller.yml",
    ".gitleaks.toml": "gitleaks.toml",
    ".pre-commit-config.yaml": "pre-commit-config.yaml",
}

# Only the caller workflow is replaced under --force. The other two are
# hand-tuned per repository and replacing them would silently drop allowlist
# entries someone added in response to a real finding.
REPLACEABLE = {".github/workflows/secret-scan.yml"}

COMMIT_MESSAGE = f"""Scan for secrets from the shared workflow

Point this repository at keleo-labs/.github's reusable secret-scan workflow
instead of carrying its own copy. The repositories that grew one independently
each worked around the same scanner quirks differently -- an unlicensed
gitleaks-action, a trufflehog action that cannot diff the first push of a
branch, a container uid that git will not read a repository from. Those fixes
now live in one file.

The licensed gitleaks-action replaces the release binary the workaround used,
which adds the job summary and the pull request comment on a finding. It also
scans only the pushed commit range, so the caller adds a weekly cron: full
history is scanned on schedule and workflow_dispatch events only.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
"""

PR_BODY = """## What changed

Replace this repository's secret scanning with a call to the reusable workflow
in [`keleo-labs/.github`](https://github.com/keleo-labs/.github/blob/main/.github/workflows/secret-scan-reusable.yml).

- `gitleaks/gitleaks-action@v3`, authenticated with the `GITLEAKS_LICENSE`
  organisation secret, replaces the pinned release binary.
- `trufflesecurity/trufflehog:3.99.2` runs as a container over full history.
- `actions/checkout@v5` replaces `@v4`, which runs on the Node 20 runtime
  GitHub has announced it is removing from hosted runners.

## Why

Three repositories grew their own secret-scan workflow and each worked around
the same problems differently: `gitleaks-action` demands a paid licence on an
organisation-owned repository, the trufflehog action compares BASE to HEAD and
cannot do that on a branch's first push, and the trufflehog container runs as a
uid git will not read the checkout from. Six repositories had no scanning at
all. One file now holds those fixes, and a new repository gets them by adding
ten lines.

The licence key was bought, so the Action wrapper is usable. It buys the job
summary and a pull request comment on a finding, which the bare binary did not
give.

## The one regression, and its cover

`gitleaks-action` passes `--log-opts base..head` on `push` and `pull_request`,
so it scans the pushed range rather than full history -- narrower than the
binary call it replaces. Two things cover it: the caller adds a weekly cron,
and `schedule` is one of the two events where the action scans everything; and
the trufflehog job scans full history on every single run.

## How it was checked

- `actionlint` over the reusable workflow and every caller.
- The reusable workflow's scan scope was read from
  [`gitleaks-action/src/gitleaks.js`](https://github.com/gitleaks/gitleaks-action/blob/v3/src/gitleaks.js),
  not assumed.
- Workflow run on this branch, linked below.

No allowlist entry is added or relaxed by this change.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""


def run(args: list[str], cwd: Path | None = None, check: bool = True):
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{proc.stdout}{proc.stderr}")
    return proc


def slug(repo: Path) -> str | None:
    """The repository's name on GitHub, which is not always its directory name.

    The organisation profile repository is checked out as `dot.github` because
    a leading dot hides it, but GitHub knows it as `.github`. Deriving the name
    from origin rather than the directory is what keeps `gh` pointed at the
    right repository.
    """
    proc = run(["git", "remote", "get-url", "origin"], cwd=repo, check=False)
    if proc.returncode != 0:
        return None
    url = proc.stdout.strip()
    # GitLab-hosted repositories are skipped: a GitHub Action cannot run there,
    # and GitLab has its own secret detection to configure instead.
    path = url.replace(":", "/").removesuffix(".git")
    marker = f"/{ORG}/"
    if "github.com" not in url or marker not in path:
        return None
    return path.split(marker, 1)[1]


def discover(root: Path) -> list[Path]:
    """Sibling directories that are git repositories on the keleo-labs org.

    The organisation profile repository is excluded. It holds the reusable
    workflow, so its own caller uses the local ./ path rather than
    keleo-labs/.github/...@main, and rolling the template over it would
    replace a working self-reference with one that cannot be tested before
    merge. It is already wired up; there is nothing here for it.
    """
    return [child for child in sorted(root.iterdir())
            if (child / ".git").exists()
            and slug(child) not in (None, SELF)]


def default_branch(repo: Path) -> str:
    proc = run(["git", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"],
               cwd=repo, check=False)
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip().rsplit("/", 1)[-1]
    return "main"


def plan(tree: Path, force: bool) -> dict[str, str]:
    """What each destination path needs: write, replace, or keep."""
    actions = {}
    for dest in FILES:
        if not (tree / dest).exists():
            actions[dest] = "write"
        elif force and dest in REPLACEABLE:
            actions[dest] = "replace"
        else:
            actions[dest] = "keep"
    return actions


def apply(tree: Path, actions: dict[str, str]) -> list[str]:
    written = []
    for dest, action in actions.items():
        if action == "keep":
            continue
        target = tree / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(TEMPLATES / FILES[dest], target)
        written.append(dest)
    return written


def propose(repo: Path, force: bool) -> tuple[str, str]:
    """Branch, commit and open a pull request from a throwaway worktree."""
    name = slug(repo)
    base = default_branch(repo)
    run(["git", "fetch", "--quiet", "origin", base], cwd=repo)

    with tempfile.TemporaryDirectory(prefix=f"rollout-{name}-") as tmp:
        tree = Path(tmp) / "tree"
        run(["git", "worktree", "add", "--quiet", "--detach", str(tree),
             f"origin/{base}"], cwd=repo)
        try:
            # -C, not -c: a previous run that failed after creating the branch
            # leaves it behind in the repository even though its worktree is
            # gone, and -c then refuses with "branch already exists" on every
            # retry. The branch only ever holds this one generated commit, so
            # resetting it is safe.
            run(["git", "switch", "--quiet", "-C", BRANCH], cwd=tree)
            actions = plan(tree, force)
            written = apply(tree, actions)
            if not written:
                return "skipped", "already present"

            run(["git", "add", "--", *written], cwd=tree)
            # Nothing staged means the templates matched the existing files
            # byte for byte, which is a no-op worth reporting as one.
            if run(["git", "diff", "--cached", "--quiet"], cwd=tree,
                   check=False).returncode == 0:
                return "skipped", "identical to current"

            run(["git", "commit", "--quiet", "-m", COMMIT_MESSAGE], cwd=tree)
            run(["git", "push", "--quiet", "--force-with-lease",
                 "-u", "origin", BRANCH], cwd=tree)
            proc = run(["gh", "pr", "create", "--repo", f"{ORG}/{name}",
                        "--base", base, "--head", BRANCH,
                        "--title", "Scan for secrets from the shared workflow",
                        "--body", PR_BODY], cwd=tree, check=False)
            url = (proc.stdout + proc.stderr).strip().splitlines()[-1]
            return ("proposed" if proc.returncode == 0 else "pr failed"), url
        finally:
            run(["git", "worktree", "remove", "--force", str(tree)],
                cwd=repo, check=False)
            # Removing the worktree does not remove the branch it held, which
            # would otherwise accumulate in `git branch` output of a
            # repository nobody asked to have a local branch in. The pushed
            # copy on origin is the one that matters.
            run(["git", "branch", "--quiet", "-D", BRANCH],
                cwd=repo, check=False)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repos-root", type=Path,
                    default=HERE.parent.parent,
                    help="directory holding the repository checkouts")
    ap.add_argument("--only", nargs="+", metavar="NAME",
                    help="limit to these repository directory names")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--propose", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="replace an existing caller workflow")
    args = ap.parse_args()

    repos = discover(args.repos_root.resolve())
    if args.only:
        wanted = set(args.only)
        repos = [r for r in repos if wanted & {r.name, slug(r)}]
        missing = wanted - {r.name for r in repos} - {slug(r) for r in repos}
        if missing:
            print(f"not found on {ORG}: {', '.join(sorted(missing))}", file=sys.stderr)
            return 2
    if not repos:
        print("no matching repositories", file=sys.stderr)
        return 2

    if args.list:
        for repo in repos:
            print(f"{repo.name:32} {ORG}/{slug(repo)}")
        return 0

    if args.dry_run:
        for repo in repos:
            actions = plan(repo, args.force)
            changes = [f"{a} {d}" for d, a in actions.items() if a != "keep"]
            print(f"{repo.name:32} {', '.join(changes) or 'nothing to do'}")
        return 0

    failed = False
    for repo in repos:
        try:
            status, detail = propose(repo, args.force)
        except Exception as err:  # noqa: BLE001 - report and carry on
            # The last line, not the first: the first is the command that was
            # run, which you already know, and git puts the reason last. A
            # push that fails here is usually a remote still on https with no
            # credential helper, which `git remote set-url` to ssh resolves.
            lines = [ln for ln in str(err).splitlines() if ln.strip()]
            status, detail = "failed", lines[-1] if lines else str(err)
        if status in ("failed", "pr failed"):
            failed = True
        print(f"{repo.name:32} {status:10} {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
