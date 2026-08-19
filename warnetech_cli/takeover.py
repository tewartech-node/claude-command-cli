"""Takeover safety core: what an autonomous run is allowed to do.

When the correction layer offers to "take over" and fix something itself,
this module decides what it may actually execute. Three rules, in order:

  1. THE ENVELOPE. Every command is classified SAFE / NEEDS_APPROVAL /
     BLOCKED. Reads, builds, tests, installs and local git bookkeeping are
     SAFE. Anything destructive (rm, sudo, force-push, discarding work) or
     outward-facing (push, publish, raw curl) is NEEDS_APPROVAL -- a hard
     stop, never spent from the budget. A tiny catastrophic set is BLOCKED
     outright and cannot be approved from here at all.

  2. FAIL CLOSED. An unrecognised command is NEEDS_APPROVAL, not SAFE. So
     is anything this module cannot statically read: command substitution,
     unbalanced quotes, a redirect pointing outside the allowed roots. The
     safe list is an allow-list; being absent from it is disqualifying.

  3. STOP AT THE FIRST WALL. A run executes its leading SAFE steps and
     halts at the first step that is not SAFE -- it does not skip past it
     to reach later safe work. Combined with the budget, that makes the
     executable set a prefix of the plan, never a scattered subset.

The budget is a second, independent cap on top of the envelope: the user
approves at most N steps, so even an all-SAFE plan stops at N.

This module is pure logic -- no subprocess, no network, no daemon. It
decides; something else executes. That separation is what makes the
safety rules testable in isolation, which is the point.

WHAT THIS IS NOT: a sandbox. It reads command lines statically, so it
cannot see inside what those commands go on to run. `make test`, `pytest`,
and `python script.py` are all classified SAFE and all execute whatever
their target file happens to contain. Static classification raises the
cost of an accident and catches the obvious footguns (ARG_TRAPS exists
precisely because `python -c` would otherwise ride in on the safe list);
it does not contain a determined payload. Real containment would need
process isolation, which belongs at the executor, not here.
"""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# Default ceiling when a plan proposes more steps than a user is likely to
# want to hand over blind. The user can always approve fewer, never more.
DEFAULT_BUDGET_CAP = 5


class Verdict(str, Enum):
    """Ordered by severity; `str` mixin so these serialise straight to JSON."""

    SAFE = "safe"
    NEEDS_APPROVAL = "needs_approval"
    BLOCKED = "blocked"


_SEVERITY = {Verdict.SAFE: 0, Verdict.NEEDS_APPROVAL: 1, Verdict.BLOCKED: 2}

# -- the classifier's vocabulary -------------------------------------------------

# Read-only inspection, builds, tests, and local-only bookkeeping.
SAFE_COMMANDS = frozenset(
    {
        # inspection
        "ls", "cat", "head", "tail", "wc", "stat", "file", "find", "grep",
        "rg", "which", "pwd", "echo", "printf", "date", "df", "du", "uname",
        "whoami", "id", "env", "printenv", "sort", "uniq", "cut", "tr", "sed",
        "awk", "diff", "jq", "tree", "basename", "dirname", "readlink",
        # navigation / creation (non-destructive)
        "cd", "mkdir", "touch",
        # build + test toolchain
        "make", "pytest", "python", "python3", "node", "ruff",
        "eslint", "prettier", "jest", "tsc", "cargo", "go",
    }
)

# Commands that are safe in normal use but grow teeth with particular flags:
# `find` walks a tree until you hand it -delete, `python` prints a version
# until you hand it -c. Without this table those flags ride in on the safe
# list, which is the single easiest way to smuggle arbitrary code past a
# name-based classifier.
ARG_TRAPS: Dict[str, tuple] = {
    "python": (frozenset({"-c"}), "runs arbitrary inline code"),
    "python3": (frozenset({"-c"}), "runs arbitrary inline code"),
    "node": (frozenset({"-e", "--eval", "-p", "--print"}), "runs arbitrary inline code"),
    "find": (
        frozenset({"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fls"}),
        "deletes or executes against every match",
    ),
    "sed": (frozenset({"-i", "--in-place"}), "edits files in place"),
    "awk": (frozenset({"-i", "--in-place"}), "edits files in place"),
    "cargo": (frozenset({"publish", "install"}), "publishes or installs globally"),
    "go": (frozenset({"install"}), "installs globally"),
}

# Destructive or outward-facing: always a hard stop, never budget-spendable.
NEEDS_APPROVAL_COMMANDS = frozenset(
    {
        # destroys or relocates data
        "rm", "rmdir", "unlink", "shred", "truncate", "mv", "cp", "ln",
        # permissions / ownership
        "chmod", "chown", "chgrp",
        # process + service control
        "kill", "pkill", "killall", "systemctl", "service", "sv", "termux-services",
        # scheduling and persistence
        "crontab", "at",
        # raw network: fetching is usually fine, but curl|sh and POST exfil
        # are not statically distinguishable from it, so the whole family stops.
        "curl", "wget", "nc", "netcat", "ssh", "scp", "rsync", "ftp", "telnet",
        # privilege escalation
        "sudo", "su", "doas", "pkexec",
        # disk / device level
        "dd", "fdisk", "parted", "wipefs", "mount", "umount", "losetup",
    }
)

# Never runnable from a takeover, with or without approval. Deliberately tiny:
# each entry is something with no legitimate role in fixing a failed command.
BLOCKED_PATTERNS = (
    (re.compile(r"\brm\s+(-[a-zA-Z]*\s+)*-?[a-zA-Z]*[rf][a-zA-Z]*\s+/\s*$"), "recursive delete of /"),
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r"), "rm -rf"),
    (re.compile(r"\bmkfs(\.\w+)?\b"), "filesystem creation"),
    (re.compile(r"\bdd\b[^|;&]*\bof=/dev/"), "raw write to a block device"),
    (re.compile(r">\s*/dev/(sd|nvme|mmcblk|hd)"), "redirect over a block device"),
    (re.compile(r":\(\)\s*\{.*\|.*&.*\}\s*;?\s*:"), "fork bomb"),
    (re.compile(r"\bchmod\s+(-[a-zA-Z]+\s+)*777\s+/\s*$"), "world-writable root"),
)

# Sub-command tables. A bare `git` tells you nothing; `git push` and
# `git status` sit on opposite sides of the envelope.
SAFE_GIT_SUBCOMMANDS = frozenset(
    {"status", "diff", "log", "show", "add", "commit", "fetch", "stash",
     "remote", "rev-parse", "ls-files", "blame", "describe", "config", "init"}
)
# Flags that turn an otherwise-safe git subcommand destructive.
DESTRUCTIVE_GIT_FLAGS = frozenset({"-D", "-d", "--delete", "--force", "-f", "--hard", "--prune"})

SAFE_SUBCOMMANDS: Dict[str, frozenset] = {
    "npm": frozenset({"test", "run", "ci", "install", "i", "ls", "list", "audit", "view", "outdated"}),
    "pnpm": frozenset({"test", "run", "install", "i", "ls", "list"}),
    "yarn": frozenset({"test", "run", "install", "list"}),
    "pip": frozenset({"install", "list", "show", "freeze", "check"}),
    "pip3": frozenset({"install", "list", "show", "freeze", "check"}),
    "pkg": frozenset({"install", "list-installed", "search", "show", "update", "upgrade"}),
    "apt": frozenset({"install", "list", "search", "show", "update"}),
    "apt-get": frozenset({"install", "update"}),
}


@dataclass
class Classification:
    """Why a single command landed where it did. `reason` is user-facing:
    it is what gets printed at a hard stop, so it explains rather than labels."""

    command: str
    verdict: Verdict
    reason: str

    @property
    def is_safe(self) -> bool:
        return self.verdict is Verdict.SAFE

    def to_dict(self) -> Dict[str, Any]:
        return {"command": self.command, "verdict": self.verdict.value, "reason": self.reason}


# -- path confinement ------------------------------------------------------------


def _resolve(path_text: str, cwd: Path) -> Path:
    """Resolve without requiring existence -- these paths are about to be
    created as often as not."""
    expanded = Path(os.path.expanduser(path_text))
    if not expanded.is_absolute():
        expanded = cwd / expanded
    return Path(os.path.normpath(str(expanded)))


def _within_roots(path_text: str, roots: Sequence[Path], cwd: Path) -> bool:
    target = _resolve(path_text, cwd)
    for root in roots:
        try:
            if target.is_relative_to(Path(os.path.normpath(str(root)))):
                return True
        except (ValueError, TypeError):
            continue
    return False


def default_allowed_roots() -> List[Path]:
    """Writes are confined to the repo being worked on and the Warnetech
    runtime directory. Anything else -- including $HOME at large -- is a stop."""
    return [Path.cwd(), Path.home() / ".warnetech"]


# -- the classifier ---------------------------------------------------------------

_REDIRECT_TOKENS = {">", ">>", "1>", "2>", "&>", ">|"}
_SEGMENT_SEPARATORS = {"|", "||", "&&", ";", "&"}


def _worst(classifications: Sequence[Classification]) -> Classification:
    return max(classifications, key=lambda c: _SEVERITY[c.verdict])


def classify_command(
    command: str,
    allowed_roots: Optional[Sequence[Path]] = None,
    cwd: Optional[Path] = None,
) -> Classification:
    """Classify one shell command line, including pipelines and chains.

    Every segment of a compound command is classified independently and the
    worst verdict wins: `pytest && rm -rf build` is not safe just because it
    starts safe.
    """
    raw = (command or "").strip()
    roots = list(allowed_roots) if allowed_roots is not None else default_allowed_roots()
    working_dir = cwd or Path.cwd()

    if not raw:
        return Classification(raw, Verdict.NEEDS_APPROVAL, "empty command")

    for pattern, why in BLOCKED_PATTERNS:
        if pattern.search(raw):
            return Classification(raw, Verdict.BLOCKED, f"blocked: {why}")

    # Command substitution can hide anything at all behind a safe-looking
    # outer command, and it cannot be resolved without running it.
    if "$(" in raw or "`" in raw:
        return Classification(raw, Verdict.NEEDS_APPROVAL, "contains command substitution")

    try:
        tokens = shlex.split(raw)
    except ValueError as exc:
        return Classification(raw, Verdict.NEEDS_APPROVAL, f"could not parse: {exc}")

    if not tokens:
        return Classification(raw, Verdict.NEEDS_APPROVAL, "empty command")

    segments: List[List[str]] = [[]]
    for token in tokens:
        if token in _SEGMENT_SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(token)

    results = [
        _classify_segment(segment, raw, roots, working_dir)
        for segment in segments
        if segment
    ]
    if not results:
        return Classification(raw, Verdict.NEEDS_APPROVAL, "empty command")
    return _worst(results)


def _classify_segment(
    tokens: List[str], raw: str, roots: Sequence[Path], cwd: Path
) -> Classification:
    """Classify one pipeline segment (no separators inside)."""
    # Redirect targets must land inside the allowed roots; `> ~/.bashrc` is a
    # write to a file this run has no business touching.
    for index, token in enumerate(tokens):
        if token in _REDIRECT_TOKENS and index + 1 < len(tokens):
            target = tokens[index + 1]
            if not _within_roots(target, roots, cwd):
                return Classification(
                    raw, Verdict.NEEDS_APPROVAL, f"writes outside the allowed roots: {target}"
                )

    # Drop redirect operators together with their targets, then any leading
    # VAR=value assignments, so words[0] is the actual command.
    words: List[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token in _REDIRECT_TOKENS:
            skip_next = True
            continue
        words.append(token)
    while words and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0]):
        words.pop(0)

    if not words:
        return Classification(raw, Verdict.NEEDS_APPROVAL, "no command found in segment")

    name = os.path.basename(words[0])
    args = words[1:]

    if name in NEEDS_APPROVAL_COMMANDS:
        return Classification(raw, Verdict.NEEDS_APPROVAL, f"'{name}' is destructive or outward-facing")

    if name == "git":
        return _classify_git(args, raw)

    if name in SAFE_SUBCOMMANDS:
        subcommand = next((a for a in args if not a.startswith("-")), None)
        if subcommand is None:
            return Classification(raw, Verdict.SAFE, f"'{name}' with no sub-command")
        if subcommand in SAFE_SUBCOMMANDS[name]:
            if "-g" in args or "--global" in args:
                return Classification(raw, Verdict.NEEDS_APPROVAL, f"'{name} {subcommand}' modifies global state")
            return Classification(raw, Verdict.SAFE, f"'{name} {subcommand}' is a safe sub-command")
        return Classification(
            raw, Verdict.NEEDS_APPROVAL, f"'{name} {subcommand}' is not on the safe sub-command list"
        )

    if name in SAFE_COMMANDS:
        trapped_flags, why = ARG_TRAPS.get(name, (frozenset(), ""))
        hit = sorted(set(args) & trapped_flags)
        if hit:
            return Classification(
                raw, Verdict.NEEDS_APPROVAL, f"'{name} {hit[0]}' {why}"
            )
        # A redirect inside an awk/sed program string never reaches the shell
        # tokenizer, so the earlier redirect check cannot see it.
        if name in {"awk", "sed"} and any(">" in a for a in args):
            return Classification(raw, Verdict.NEEDS_APPROVAL, f"'{name}' program writes to a file")
        return Classification(raw, Verdict.SAFE, f"'{name}' is read-only or build/test tooling")

    # Fail closed: unknown means unvetted, which means it stops.
    return Classification(raw, Verdict.NEEDS_APPROVAL, f"'{name}' is not on the safe list")


def _classify_git(args: List[str], raw: str) -> Classification:
    subcommand = next((a for a in args if not a.startswith("-")), None)
    if subcommand is None:
        return Classification(raw, Verdict.SAFE, "'git' with no sub-command")

    if subcommand not in SAFE_GIT_SUBCOMMANDS:
        return Classification(
            raw, Verdict.NEEDS_APPROVAL, f"'git {subcommand}' can publish or discard work"
        )

    destructive_flags = sorted(set(args) & DESTRUCTIVE_GIT_FLAGS)
    if destructive_flags:
        return Classification(
            raw,
            Verdict.NEEDS_APPROVAL,
            f"'git {subcommand}' with {', '.join(destructive_flags)} is destructive",
        )
    return Classification(raw, Verdict.SAFE, f"'git {subcommand}' is local and non-destructive")


# -- objective, assumptions, plan ---------------------------------------------------


@dataclass
class Assumption:
    """One reading of an ambiguous objective, offered for the user to pick.

    The whole point of surfacing these is that the run does NOT proceed on a
    guess: an assumed objective with nothing chosen is not runnable.
    """

    id: str
    text: str
    chosen: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "text": self.text, "chosen": self.chosen}


@dataclass
class TakeoverStep:
    command: str
    rationale: str
    classification: Optional[Classification] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "rationale": self.rationale,
            "classification": self.classification.to_dict() if self.classification else None,
        }


@dataclass
class TakeoverPlan:
    """A proposed autonomous run, and the rules governing how much of it runs.

    `objective_known=False` means the objective was inferred rather than
    stated, which forces the assumption list to be resolved before anything
    executes.
    """

    objective: str
    steps: List[TakeoverStep]
    objective_known: bool = True
    assumptions: List[Assumption] = field(default_factory=list)
    approved_budget: Optional[int] = None
    allowed_roots: Optional[List[Path]] = None
    cwd: Optional[Path] = None

    def __post_init__(self) -> None:
        self.classify()

    # -- classification ------------------------------------------------------

    def classify(self) -> None:
        for step in self.steps:
            step.classification = classify_command(step.command, self.allowed_roots, self.cwd)

    # -- budget --------------------------------------------------------------

    def proposed_budget(self, cap: int = DEFAULT_BUDGET_CAP) -> int:
        """What to offer the user: the safe prefix, never more than the cap.

        Proposing steps the envelope would refuse anyway would be theatre --
        the number shown is a number that can actually run.
        """
        return min(self.safe_prefix_length(), cap)

    def approve(self, budget: int) -> None:
        if budget < 0:
            raise ValueError("budget cannot be negative")
        self.approved_budget = min(budget, len(self.steps))

    # -- what may actually run -----------------------------------------------

    def safe_prefix_length(self) -> int:
        """Steps from the top that are SAFE, stopping at the first that is not."""
        count = 0
        for step in self.steps:
            if step.classification is None or not step.classification.is_safe:
                break
            count += 1
        return count

    def blocking_step(self) -> Optional[TakeoverStep]:
        """The step that ends the run, if the plan does not run to completion."""
        index = self.safe_prefix_length()
        return self.steps[index] if index < len(self.steps) else None

    def is_runnable(self) -> tuple[bool, str]:
        """Gate before anything executes at all."""
        if not self.objective_known and not any(a.chosen for a in self.assumptions):
            return False, "objective is assumed and no assumption has been chosen"
        if self.approved_budget is None:
            return False, "no budget approved"
        if self.approved_budget == 0:
            return False, "budget is zero"
        if self.safe_prefix_length() == 0:
            return False, "the first step needs approval"
        return True, ""

    def executable_steps(self) -> List[TakeoverStep]:
        """The steps this run may execute: the safe prefix, capped by budget.

        Both limits apply; whichever bites first wins.
        """
        runnable, _ = self.is_runnable()
        if not runnable:
            return []
        limit = min(self.safe_prefix_length(), self.approved_budget or 0)
        return self.steps[:limit]

    def choose_assumption(self, assumption_id: str) -> None:
        """Exactly one assumption holds at a time -- choosing clears the rest."""
        if not any(a.id == assumption_id for a in self.assumptions):
            raise KeyError(f"no such assumption: {assumption_id}")
        for assumption in self.assumptions:
            assumption.chosen = assumption.id == assumption_id

    # -- presentation ---------------------------------------------------------

    def render_briefing(self) -> str:
        """What gets shown before a takeover: the objective as understood, the
        assumptions if it was inferred, and exactly where the run will stop."""
        lines: List[str] = []
        header = "Objective" if self.objective_known else "Objective (assumed)"
        lines.append(f"{header}: {self.objective}")

        if self.assumptions:
            lines.append("")
            lines.append("I am not certain of the objective. Choose one:")
            for assumption in self.assumptions:
                mark = "x" if assumption.chosen else " "
                lines.append(f"  [{mark}] {assumption.id}. {assumption.text}")

        lines.append("")
        lines.append(f"Plan ({len(self.steps)} steps):")
        for index, step in enumerate(self.steps, start=1):
            verdict = step.classification.verdict.value if step.classification else "?"
            marker = "->" if step.classification and step.classification.is_safe else "!!"
            lines.append(f"  {marker} {index}. {step.command}    [{verdict}]")
            if step.rationale:
                lines.append(f"        {step.rationale}")

        blocker = self.blocking_step()
        lines.append("")
        if blocker is not None and blocker.classification is not None:
            lines.append(f"I will stop before step {self.safe_prefix_length() + 1}: {blocker.classification.reason}.")
        else:
            lines.append("Every step is within the safe envelope.")
        lines.append(f"I propose taking {self.proposed_budget()} step(s). You can approve fewer.")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective": self.objective,
            "objective_known": self.objective_known,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "steps": [s.to_dict() for s in self.steps],
            "proposed_budget": self.proposed_budget(),
            "approved_budget": self.approved_budget,
            "safe_prefix_length": self.safe_prefix_length(),
        }
