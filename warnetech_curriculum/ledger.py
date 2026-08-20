"""Append-only, tamper-evident failure ledger.

The founding rule of this package: **a failure is never deleted.** Not when
it is fixed, not when it is superseded, not when it turns out to have been
misdiagnosed. The ledger is the institutional memory of the system, and a
memory you are allowed to edit is not a memory.

That is enforced structurally rather than by convention:

* The file is only ever opened in append mode ("a"). There is no update
  path and no delete path in this module's public API -- not a disabled
  one, not a guarded one. None.
* Every entry carries `prev_hash`, the hash of the entry before it, so the
  log is a chain. Removing or altering any entry breaks every hash after
  it, and `verify()` reports the exact sequence number where the chain
  parts. Deletion is therefore not merely disallowed, it is *detectable*.

Correcting the record is done by *appending* -- a `resolution` entry that
points back at the original `failure` entry by id. Both remain readable
forever. `Ledger.timeline(entry_id)` reassembles the whole story of one
failure, which is what turns a mistake into a lesson rather than an
embarrassment to be swept away.

Storage is plain JSON Lines: one object per line, no database, no daemon,
no network. It can be read with `cat`, which matters on Termux.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

GENESIS_HASH = "0" * 64

# Entry kinds. `failure` and `lesson` are the substance; `resolution` and
# `note` are how the record is corrected without erasing anything.
KIND_FAILURE = "failure"
KIND_LESSON = "lesson"
KIND_RESOLUTION = "resolution"
KIND_NOTE = "note"
VALID_KINDS = (KIND_FAILURE, KIND_LESSON, KIND_RESOLUTION, KIND_NOTE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical(payload: Dict[str, Any]) -> str:
    """Stable serialisation. Key order and spacing must never vary or the
    hash chain would depend on dict iteration order rather than content."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def entry_hash(prev_hash: str, payload: Dict[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "hash"}
    return hashlib.sha256((prev_hash + canonical(body)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LedgerEntry:
    """One immutable record. Frozen because nothing downstream should be
    able to hand a mutated copy back to the ledger and have it look real."""

    seq: int
    id: str
    kind: str
    title: str
    recorded_at: str
    detail: str = ""
    origin: Dict[str, Any] = field(default_factory=dict)
    rule: Optional[str] = None
    refs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    prev_hash: str = GENESIS_HASH
    hash: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seq": self.seq,
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "recorded_at": self.recorded_at,
            "detail": self.detail,
            "origin": self.origin,
            "rule": self.rule,
            "refs": self.refs,
            "tags": self.tags,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "LedgerEntry":
        return cls(
            seq=int(raw["seq"]),
            id=str(raw["id"]),
            kind=str(raw["kind"]),
            title=str(raw["title"]),
            recorded_at=str(raw["recorded_at"]),
            detail=str(raw.get("detail", "")),
            origin=dict(raw.get("origin") or {}),
            rule=raw.get("rule"),
            refs=list(raw.get("refs") or []),
            tags=list(raw.get("tags") or []),
            prev_hash=str(raw.get("prev_hash", GENESIS_HASH)),
            hash=str(raw.get("hash", "")),
        )


class LedgerIntegrityError(RuntimeError):
    """The chain does not verify: an entry was altered, removed, or the file
    was truncated mid-write."""


class Ledger:
    """Append-only store over a JSON Lines file.

    Deliberately has no `delete`, `update`, `truncate` or `compact` method.
    If you find yourself wanting one, append a `resolution` instead -- that
    is the supported way to say "this turned out to be wrong", and it keeps
    the wrong version legible, which is the entire point.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    # -- reading ---------------------------------------------------------

    def __iter__(self) -> Iterator[LedgerEntry]:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                yield LedgerEntry.from_dict(json.loads(line))

    def entries(self) -> List[LedgerEntry]:
        return list(self)

    def by_id(self, entry_id: str) -> Optional[LedgerEntry]:
        for entry in self:
            if entry.id == entry_id:
                return entry
        return None

    def of_kind(self, kind: str) -> List[LedgerEntry]:
        return [e for e in self if e.kind == kind]

    def timeline(self, entry_id: str) -> List[LedgerEntry]:
        """The original entry plus everything that later referred to it, in
        record order -- the full arc of one mistake."""
        return [e for e in self if e.id == entry_id or entry_id in e.refs]

    def head(self) -> tuple[int, str]:
        seq, prev = 0, GENESIS_HASH
        for entry in self:
            seq, prev = entry.seq, entry.hash
        return seq, prev

    # -- writing (append is the only mutation that exists) ---------------

    def append(
        self,
        *,
        kind: str,
        title: str,
        detail: str = "",
        entry_id: Optional[str] = None,
        origin: Optional[Dict[str, Any]] = None,
        rule: Optional[str] = None,
        refs: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> LedgerEntry:
        if kind not in VALID_KINDS:
            raise ValueError(f"unknown ledger kind {kind!r}; expected one of {VALID_KINDS}")
        if not title.strip():
            raise ValueError("a ledger entry must carry a title: an unnamed failure teaches nothing")

        seq, prev_hash = self.head()
        seq += 1
        payload = {
            "seq": seq,
            "id": entry_id or f"WL-{seq:04d}",
            "kind": kind,
            "title": title.strip(),
            "recorded_at": _now(),
            "detail": detail.strip(),
            "origin": dict(origin or {}),
            "rule": rule,
            "refs": list(refs or []),
            "tags": list(tags or []),
            "prev_hash": prev_hash,
        }
        payload["hash"] = entry_hash(prev_hash, payload)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Append mode, flushed and fsynced: a crash must not be able to
        # leave a half-written line that breaks the chain for every future
        # reader.
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical(payload) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return LedgerEntry.from_dict(payload)

    def record_failure(
        self,
        title: str,
        *,
        detail: str = "",
        origin: Optional[Dict[str, Any]] = None,
        rule: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> LedgerEntry:
        return self.append(
            kind=KIND_FAILURE, title=title, detail=detail, origin=origin, rule=rule, tags=tags
        )

    def record_resolution(self, failure_id: str, title: str, *, detail: str = "") -> LedgerEntry:
        """Mark a failure as understood -- by appending, never by editing.

        The failure entry itself is untouched and stays exactly where it is.
        """
        if self.by_id(failure_id) is None:
            raise ValueError(
                f"cannot resolve unknown entry {failure_id!r}: "
                "record the failure first so the record stays coherent"
            )
        return self.append(kind=KIND_RESOLUTION, title=title, detail=detail, refs=[failure_id])

    # -- integrity -------------------------------------------------------

    def verify(self) -> Dict[str, Any]:
        """Walk the chain. Reports the first break rather than raising, so a
        damaged ledger can still be inspected and repaired by appending."""
        prev_hash, expected_seq, count = GENESIS_HASH, 1, 0
        for entry in self:
            if entry.seq != expected_seq:
                return {
                    "ok": False,
                    "entries": count,
                    "broken_at": entry.seq,
                    "reason": f"sequence gap: expected {expected_seq}, found {entry.seq} "
                    "(an entry was removed)",
                }
            if entry.prev_hash != prev_hash:
                return {
                    "ok": False,
                    "entries": count,
                    "broken_at": entry.seq,
                    "reason": "prev_hash mismatch (an earlier entry was altered or removed)",
                }
            recomputed = entry_hash(entry.prev_hash, entry.to_dict())
            if recomputed != entry.hash:
                return {
                    "ok": False,
                    "entries": count,
                    "broken_at": entry.seq,
                    "reason": "hash mismatch (this entry's contents were altered in place)",
                }
            prev_hash, expected_seq, count = entry.hash, expected_seq + 1, count + 1
        return {"ok": True, "entries": count, "head": prev_hash}


def default_ledger_path() -> Path:
    """Where the curriculum lives on a real machine.

    WARNETECH_CURRICULUM_HOME wins if set. Otherwise ~/.warnetech/curriculum,
    alongside the operator's existing ~/.warnetech runtime -- one place for a
    Termux user to back up, which is what `warnetech backup` already targets.
    """
    override = os.environ.get("WARNETECH_CURRICULUM_HOME")
    root = Path(override) if override else Path.home() / ".warnetech" / "curriculum"
    return root / "ledger.jsonl"


def writable_ledger(path: Optional[Path] = None) -> Ledger:
    """Open the ledger, falling back to a temp location if the real one is
    unwritable (a read-only Termux $HOME, a locked-down CI container).

    A curriculum that crashes the tool it is supposed to protect has failed
    at its own job, so this degrades instead of raising.
    """
    target = Path(path) if path else default_ledger_path()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        probe = target.parent / ".write-probe"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return Ledger(target)
    except OSError:
        fallback = Path(tempfile.gettempdir()) / "warnetech-curriculum" / "ledger.jsonl"
        fallback.parent.mkdir(parents=True, exist_ok=True)
        return Ledger(fallback)
