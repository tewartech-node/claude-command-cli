"""The pre-installed curriculum: what this system already learned the hard way.

These entries ship *with the code*, in the base structure, so a fresh clone
on a fresh Termux install starts out knowing what went wrong before rather
than starting from zero and rediscovering it. Every one of them is a real
event in this repository's history with a commit or a file:line you can go
and read.

Two kinds live here:

  ENFORCED -- a failure that now has a rule watching for its recurrence.
  OPEN     -- a failure that is understood and recorded but that no rule
              catches yet. These are not hidden and not deleted. They are
              the curriculum's own backlog, and `warnetech-curriculum
              curriculum` prints them next to the enforced ones so the gap
              between "we know" and "we check" is always visible.

Seeding is idempotent and additive: it appends only what is missing, and it
never rewrites or removes an existing entry, because the ledger does not
permit that in the first place.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .ledger import Ledger
from .rules import RULES

# Failures that are recorded and understood, but not yet mechanically
# enforced. Kept visible on purpose -- an honest backlog beats a clean board.
OPEN_LESSONS: List[Dict[str, Any]] = [
    {
        "id": "WL-OPEN-001",
        "title": "documented crypto that was never implemented",
        "detail": (
            "SECURITY.md and CLAUDE.md both promise a ChaCha20-Poly1305 fallback and "
            "Argon2id key derivation. worker/utils/crypto.js carries a comment claiming the "
            "ChaCha20 fallback and implements none; argon2-browser is a declared npm "
            "dependency that is never imported; the real derivation is PBKDF2. Documentation "
            "that describes intentions in the present tense becomes a lie the moment someone "
            "trusts it. No rule catches doc/code drift yet."
        ),
        "tags": ["security", "documentation", "drift"],
    },
    {
        "id": "WL-OPEN-002",
        "title": "two crypto implementations silently disagreed on the wire",
        "detail": (
            "Commits caaa185 and dfe5f5a: the legacy CLI and the Worker each had a correct "
            "AES-GCM implementation, and they could not talk to each other -- different "
            "layouts for the same envelope. This is why CLAUDE.md now says to extend "
            "warnetech_envelope and never add a second implementation. Cross-language "
            "agreement is now pinned by tests/security/test_envelope_interop.py, but no "
            "rule prevents a third implementation from being introduced."
        ),
        "tags": ["security", "architecture", "interop"],
    },
    {
        "id": "WL-OPEN-003",
        "title": "a CLI flag that silently did nothing",
        "detail": (
            "`evolve --dry-run` read options[\"dry-run\"], but Commander binds camelCase, so "
            "it read undefined and the flag was ignored -- the destructive path ran while the "
            "user believed they had asked for a dry run. A wrong key in a dynamic language "
            "is not an error, it is a None. No rule checks flag-name binding yet."
        ),
        "tags": ["cli", "correctness", "silent-failure"],
    },
    {
        "id": "WL-OPEN-004",
        "title": "the test suite is not protected by CI",
        "detail": (
            "The only GitHub Actions workflow is an unmodified SLSA template that builds two "
            "literal placeholder files. Nothing runs pytest, ruff, jest or eslint on push, "
            "while CLAUDE.md claims Actions deploys to staging. Every rule in this curriculum "
            "is advisory until something runs it automatically."
        ),
        "tags": ["ci", "process"],
    },
    {
        "id": "WL-OPEN-005",
        "title": "CLI commands that bypass the server layer entirely",
        "detail": (
            "slice, compress, ghost_create and ghost_recall are implemented locally inside "
            "warnetech_cli/commands.py using CLI-local managers, while warnetech_server "
            "registers /slice, /compress, /ghost/create and /ghost/recall that route to the "
            "control plane. Two divergent implementations of one operation, and Layer 1 doing "
            "Layer 2's work. R005 detects the orphaned routes; nothing yet detects the "
            "duplicated logic behind them."
        ),
        "tags": ["architecture", "layering"],
    },
]


def seeded_ids(ledger: Ledger) -> set:
    return {entry.id for entry in ledger}


def seed(ledger: Ledger) -> Dict[str, Any]:
    """Install any missing pre-installed lessons. Never modifies existing ones."""
    existing = seeded_ids(ledger)
    added: List[str] = []

    for rule in RULES:
        entry_id = f"WL-{rule.id}"
        if entry_id in existing:
            continue
        ledger.append(
            kind="lesson",
            entry_id=entry_id,
            title=rule.title,
            detail=rule.lesson,
            origin={"commit": rule.origin},
            rule=rule.id,
            tags=["enforced", rule.severity],
        )
        added.append(entry_id)

    for lesson in OPEN_LESSONS:
        if lesson["id"] in existing:
            continue
        ledger.append(
            kind="lesson",
            entry_id=lesson["id"],
            title=lesson["title"],
            detail=lesson["detail"],
            rule=None,
            tags=["open"] + list(lesson.get("tags", [])),
        )
        added.append(lesson["id"])

    return {
        "added": added,
        "total": len(ledger.entries()),
        "enforced": len(RULES),
        "open": len(OPEN_LESSONS),
    }
