"""Backup-before-mutate guard: nothing is destroyed unrecorded.

Rule this module enforces: if a step is going to delete or overwrite
something, a verified backup of that something exists first, or the step
does not run. Backup failure is not a warning here -- it is a refusal.
Deleting a file you failed to copy is exactly the outcome the guard
exists to prevent.

It builds on warnetech_operator.warnetech_backup_recall rather than
introducing a second backup format: that module already provides
timestamped backups, per-item SHA-256 manifests, checksum verification,
and restore-to-origin recall. CLAUDE.md asks for extension over
duplication, and reusing it means anything captured here is restorable
with the operator tooling the user already has (`warnetech-backup-recall
list | verify | recall`).

What a ChangeRecord gives you afterwards, which a bare backup does not:
a per-path before/after comparison, so a completed step can say what it
REMOVED, what it MODIFIED and what it left alone -- and can be replayed
in reverse if the step corrupted something.

LIMITS, stated plainly:
  * Paths are extracted by static parsing, so this covers what a command
    names. A command that computes its targets at runtime (a script, a
    glob expanded by the shell into something unexpected, `find -delete`)
    can touch files that were never backed up. Those commands classify as
    NEEDS_APPROVAL in takeover.py precisely because this guard cannot see
    into them.
  * Backups are local, to ~/.warnetech/backups. They survive a bad edit,
    not a lost or wiped device.
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from warnetech_operator import warnetech_backup_recall as operator_backup

# A phone is the target device. Silently copying gigabytes before a delete
# would be its own kind of damage, so an oversized target refuses instead.
MAX_BACKUP_BYTES = 256 * 1024 * 1024


class SafeguardError(RuntimeError):
    """Raised when a mutation cannot be made safe, and so must not proceed."""


# -- what a command will touch -----------------------------------------------------


def extract_paths(command: str, cwd: Optional[Path] = None) -> List[Path]:
    """Existing filesystem paths a command names as arguments.

    Deliberately conservative in both directions: it returns only paths that
    exist right now (a path that is not there cannot be backed up, and its
    absence is itself recorded in the pre-state), and it ignores flags and
    the command name itself.
    """
    working_dir = cwd or Path.cwd()
    try:
        tokens = shlex.split(command or "")
    except ValueError:
        return []

    candidates: List[Path] = []
    for token in tokens[1:]:
        if token.startswith("-"):
            continue
        if token in {"|", "||", "&&", ";", "&", ">", ">>"}:
            continue
        # VAR=value, not a path
        if "=" in token and "/" not in token.split("=", 1)[0]:
            continue
        expanded = Path(os.path.expanduser(token))
        resolved = expanded if expanded.is_absolute() else working_dir / expanded
        resolved = Path(os.path.normpath(str(resolved)))
        if resolved.exists() and resolved not in candidates:
            candidates.append(resolved)
    return candidates


def _tree_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(child.stat().st_size for child in path.rglob("*") if child.is_file())


def _state_of(paths: Sequence[Path]) -> Dict[str, Optional[str]]:
    """Checksum each path, or None where it does not exist.

    None is meaningful, not missing data: it is how a removal and a creation
    are told apart when the after-state is compared.
    """
    state: Dict[str, Optional[str]] = {}
    for path in paths:
        state[str(path)] = operator_backup.checksum(path) if path.exists() else None
    return state


# -- the record ----------------------------------------------------------------------


@dataclass
class ChangeRecord:
    """Before/after evidence for one mutating step."""

    command: str
    paths: List[Path]
    backups: List[str] = field(default_factory=list)
    pre_state: Dict[str, Optional[str]] = field(default_factory=dict)
    post_state: Dict[str, Optional[str]] = field(default_factory=dict)
    completed: bool = False

    def compare(self) -> Dict[str, str]:
        """Classify each path as removed / modified / created / unchanged."""
        if not self.completed:
            return {}
        verdicts: Dict[str, str] = {}
        for key, before in self.pre_state.items():
            after = self.post_state.get(key)
            if before is not None and after is None:
                verdicts[key] = "removed"
            elif before is None and after is not None:
                verdicts[key] = "created"
            elif before != after:
                verdicts[key] = "modified"
            else:
                verdicts[key] = "unchanged"
        return verdicts

    def summary(self) -> str:
        verdicts = self.compare()
        if not self.completed:
            return f"pending: {len(self.paths)} path(s) backed up, step not yet run"
        changed = {k: v for k, v in verdicts.items() if v != "unchanged"}
        if not changed:
            return "no files changed"
        lines = [f"{verdict}: {path}" for path, verdict in sorted(changed.items())]
        restore = f"restore with: warnetech-backup-recall recall {self.backups[0]}" if self.backups else ""
        return "\n".join(lines + ([restore] if restore else []))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "paths": [str(p) for p in self.paths],
            "backups": self.backups,
            "pre_state": self.pre_state,
            "post_state": self.post_state,
            "completed": self.completed,
            "changes": self.compare(),
        }


# -- the guard --------------------------------------------------------------------------


def _collision_free_batches(paths: Sequence[Path]) -> List[List[Path]]:
    """Group paths so no batch contains two entries with the same basename.

    operator_backup.create_backup() stores each item as `backup_dir/<name>`,
    so backing up a/config.json and b/config.json in one call would have the
    second silently overwrite the first -- losing exactly the file the guard
    promised to preserve. Splitting into separate backups avoids that without
    changing the operator manifest format that recall depends on.
    """
    batches: List[List[Path]] = []
    for path in paths:
        for batch in batches:
            if all(existing.name != path.name for existing in batch):
                batch.append(path)
                break
        else:
            batches.append([path])
    return batches


def guard(
    command: str,
    cwd: Optional[Path] = None,
    max_bytes: int = MAX_BACKUP_BYTES,
) -> ChangeRecord:
    """Back up everything `command` names, and verify it, before it runs.

    Returns the ChangeRecord to pass to :func:`finalize` afterwards. Raises
    SafeguardError if a backup could not be made or could not be verified --
    the caller must treat that as "do not run the step".
    """
    paths = extract_paths(command, cwd)
    record = ChangeRecord(command=command, paths=paths)
    record.pre_state = _state_of(paths)

    existing = [p for p in paths if p.exists()]
    if not existing:
        # Nothing on disk to lose; the empty pre-state is still recorded so
        # anything the step creates shows up as "created" afterwards.
        return record

    total = sum(_tree_size(p) for p in existing)
    if total > max_bytes:
        raise SafeguardError(
            f"refusing to proceed: {total} bytes to back up exceeds the "
            f"{max_bytes}-byte limit. Back up manually, or raise max_bytes deliberately."
        )

    for batch in _collision_free_batches(existing):
        try:
            backup_path = operator_backup.create_backup(batch)
        except Exception as exc:  # noqa: BLE001 - any failure must stop the step
            raise SafeguardError(f"backup failed, refusing to proceed: {exc}") from exc

        verification = operator_backup.verify_backup(backup_path.name)
        if not verification["all_ok"]:
            failed = [i["name"] for i in verification["items"] if not i["ok"]]
            raise SafeguardError(
                f"backup verification failed for {failed}, refusing to proceed"
            )
        record.backups.append(backup_path.name)

    return record


def finalize(record: ChangeRecord) -> ChangeRecord:
    """Capture the after-state so the record can say what actually changed."""
    record.post_state = _state_of(record.paths)
    record.completed = True
    return record


def restore(record: ChangeRecord) -> List[Dict[str, Any]]:
    """Undo a guarded step by recalling its backups to their origins.

    Used when a step errored or corrupted its target. Recall itself refuses
    on a checksum mismatch, so a damaged backup cannot overwrite good files.
    """
    if not record.backups:
        raise SafeguardError("this record has no backups to restore from")
    return [operator_backup.recall_backup(name) for name in reversed(record.backups)]
