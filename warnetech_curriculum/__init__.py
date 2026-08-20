"""Warnetech curriculum: a system that learns from its own failures.

Three ideas, in order of importance:

1. **Nothing is ever deleted.** Failures are appended to a hash-chained
   ledger. A correction is a new entry pointing at the old one; both stay
   readable forever. Removing or editing an entry breaks the chain and is
   reported by `verify()` with the exact sequence number. See `ledger`.

2. **Decisions are verified, not guessed.** Before an action, the rules in
   `rules` prove -- by parsing the source tree with `ast` -- that the
   modules, symbols and attributes it depends on genuinely exist. This is
   the class of failure that produced the `ai_diagnose` bug, where an entire
   module was written against an API nobody had opened. See `inspector`.

3. **Every rule traces to a real failure.** `rules.RULES` carries an
   `origin` (a commit, a file:line) and a `lesson` for each one. A rule with
   no origin has not been learned, only assumed.

Parameter-free by construction: standard library only, no model weights, no
API key, no network, no clock-dependence. The same tree yields the same
verdict on a workstation or on a phone in aeroplane mode -- which is the
point, because Termux is where this runs.

    python -m warnetech_curriculum curriculum     # what has been learned
    python -m warnetech_curriculum check          # verify the whole tree
    python -m warnetech_curriculum preflight      # gate before committing
    python -m warnetech_curriculum learn "..."    # record a new failure
    python -m warnetech_curriculum verify         # prove nothing was removed
"""

from __future__ import annotations

from .autofix import apply_fixes
from .inspector import ClassSurface, Inspector, ModuleSurface
from .ledger import Ledger, LedgerEntry, LedgerIntegrityError, default_ledger_path, writable_ledger
from .preflight import preflight
from .rules import RULES, RULES_BY_ID, Finding, Rule, TextEdit, run_rules
from .seed import OPEN_LESSONS, seed

__all__ = [
    "Inspector",
    "ModuleSurface",
    "ClassSurface",
    "Ledger",
    "LedgerEntry",
    "LedgerIntegrityError",
    "default_ledger_path",
    "writable_ledger",
    "preflight",
    "RULES",
    "RULES_BY_ID",
    "Rule",
    "Finding",
    "TextEdit",
    "run_rules",
    "apply_fixes",
    "seed",
    "OPEN_LESSONS",
]
