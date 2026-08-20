"""Foresight: run the curriculum *before* the action, not after the incident.

`preflight()` is the gate. It takes the files an action is about to affect,
runs every enforced rule over them, and returns a verdict the caller is
expected to obey. Nothing here is advisory-by-design: a `critical` finding
means the decision about to be made rests on something that provably does
not exist, and proceeding would repeat a failure this repository has already
paid for once.

The learning loop closes here. Any finding not already known to the ledger is
appended to it, so the record grows on its own as the system meets new
instances -- self-added learning, in the user's words, on top of the
pre-installed base. Nothing is ever removed on the way through: a finding
that later turns out to be a false alarm gets a `resolution` appended beside
it, and both stay readable.

Deliberately free of parameters, network and clock-dependence: same tree in,
same verdict out, on a laptop or on a phone with aeroplane mode on.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .inspector import Inspector
from .ledger import Ledger, writable_ledger
from .rules import CRITICAL, HIGH, Finding, run_rules

BLOCKING = (CRITICAL,)


def fingerprint(finding: Finding) -> str:
    """Stable identity for a finding, so meeting the same defect twice does
    not fill the ledger with duplicates."""
    raw = f"{finding.rule}|{finding.path}|{finding.message}"
    return "WF-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def changed_files(root: Path, since: Optional[str] = None) -> List[Path]:
    """Files touched relative to HEAD (or `since`), for a pre-commit gate.

    `since` takes a git ref -- in CI, pass the base branch so a pull request
    is judged on what it actually changes. That is the ratchet: existing
    debt is tracked in the ledger and does not block, while new work is held
    to the full curriculum.

    Three sources, because any one of them alone leaves a hole:

      * unstaged edits against HEAD,
      * staged edits (what `git commit` is about to take),
      * **untracked files** -- a brand-new module is precisely the case
        this gate exists for, and `git diff` never mentions it.

    Returns an empty list when git is unavailable or this is not a checkout.
    On Termux git may simply not be installed, and a gate that raises there
    would block work rather than protect it.
    """

    def ask(*args: str) -> str:
        try:
            done = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True, text=True, timeout=15, check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return ""
        return done.stdout if done.returncode == 0 else ""

    names = set()
    if since:
        # Three dots: what this branch changed, ignoring what moved on base.
        names |= set(ask("diff", "--name-only", "--diff-filter=ACM", f"{since}...HEAD").split())
    names |= set(ask("diff", "--name-only", "--diff-filter=ACM", "HEAD").split())
    names |= set(ask("diff", "--name-only", "--diff-filter=ACM", "--cached").split())
    names |= set(ask("ls-files", "--others", "--exclude-standard").split())
    watched = (".py", ".js")
    return [root / n for n in sorted(names) if n.endswith(watched) and (root / n).is_file()]


def preflight(
    root: Path,
    *,
    paths: Optional[List[Path]] = None,
    ledger: Optional[Ledger] = None,
    record: bool = True,
    only: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run the curriculum over `paths` (default: the whole first-party tree).

    Returns a verdict dict. `ok` is False when anything blocking was found;
    the caller is expected to stop rather than continue.
    """
    inspector = Inspector(root)
    targets = list(paths) if paths else None

    # Rules that reason across the whole repository (route wiring) cannot be
    # evaluated from a partial file list, so a scoped run skips them rather
    # than reporting a false orphan from missing context.
    scoped = targets is not None
    active = only or (["R001", "R002", "R003", "R004"] if scoped else None)

    findings = run_rules(inspector, targets, only=active)
    blocking = [f for f in findings if f.severity in BLOCKING]

    recorded: List[str] = []
    if record and findings:
        book = ledger or writable_ledger()
        known = {entry.id for entry in book}
        for finding in findings:
            marker = fingerprint(finding)
            if marker in known:
                continue
            book.record_failure(
                finding.message,
                detail=f"{finding.path}:{finding.line} -- {finding.evidence}",
                origin={"path": finding.path, "line": finding.line, "detected_by": finding.rule},
                rule=finding.rule,
                tags=["detected", finding.severity],
            )
            # record_failure mints its own sequential id; re-record the
            # fingerprint as a note so the dedupe key is itself durable.
            book.append(
                kind="note", entry_id=marker,
                title=f"fingerprint for {finding.rule} at {finding.path}:{finding.line}",
                tags=["fingerprint"],
            )
            recorded.append(marker)

    return {
        "ok": not blocking,
        "scope": "changed" if scoped else "full-tree",
        "files_examined": len(targets) if targets else len(inspector.source_files()),
        "findings": [f.to_dict() for f in findings],
        "blocking": [f.to_dict() for f in blocking],
        "counts": {
            "total": len(findings),
            "critical": sum(1 for f in findings if f.severity == CRITICAL),
            "high": sum(1 for f in findings if f.severity == HIGH),
        },
        "newly_recorded": recorded,
    }
