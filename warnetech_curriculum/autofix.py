"""Applies the TextEdits that R001/R002 compute for high-confidence,
unambiguous renames -- the curriculum's auto-correct.

Deliberately narrow. Only a rename with one clearly-best candidate ever
gets a `Finding.fix` in the first place (see rules._confident_nearest);
what this module adds is the second, independent safety net around
*applying* one:

  1. Re-verify the edit's `original` text against the file on disk, right
     before writing -- not just at detection time. Two edits queued for
     the same file, or a file that changed between check and fix, could
     otherwise make an offset stale.
  2. Apply every edit in one file from bottom to top. Editing top-to-bottom
     would shift every later line/column the moment an edit changes the
     file's length; bottom-to-top means earlier, not-yet-applied positions
     are never invalidated by a later edit.
  3. Re-parse the whole file after edits, before writing anything. A
     result that fails to parse is treated as this module's own bug, not
     the user's problem: the write is skipped and the failure reported.

No fix is ever partially applied to a file: either every edit for that
file lands and the parse comes back clean, or nothing is written.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

from .rules import Finding


def _line_offsets(text: str) -> List[int]:
    """Character offset at which each 1-indexed line starts, so a
    (line, col) pair from `ast` can be turned into a flat string index."""
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _apply_to_text(text: str, fixes: List[Finding]) -> tuple[str, List[str]]:
    """Applies every fixable finding's edit to `text`, bottom-to-top.
    Returns the new text and a list of human-readable descriptions of what
    was actually applied (an edit whose `original` no longer matches is
    skipped, not forced)."""
    offsets = _line_offsets(text)
    applied: List[str] = []

    # Sort by position, descending, so each splice leaves earlier
    # (line, col) pairs in the same string valid for the next splice.
    ordered = sorted(
        (f for f in fixes if f.fix is not None),
        key=lambda f: (f.fix.line, f.fix.col),
        reverse=True,
    )
    for finding in ordered:
        edit = finding.fix
        start = offsets[edit.line - 1] + edit.col
        end = offsets[edit.end_line - 1] + edit.end_col
        if text[start:end] != edit.original:
            continue
        text = text[:start] + edit.replacement + text[end:]
        applied.append(f"{edit.path}:{edit.line}: {edit.description}")
    return text, applied


def apply_fixes(findings: List[Finding], root: Path) -> Dict[str, Any]:
    """Groups fixable findings by file and applies each file's edits as one
    atomic write: every edit lands and the result parses, or the file is
    left untouched and the failure is reported."""
    root = Path(root).resolve()
    by_path: Dict[str, List[Finding]] = {}
    for finding in findings:
        if finding.fix is not None:
            by_path.setdefault(finding.fix.path, []).append(finding)

    applied_files: List[str] = []
    applied_edits: List[str] = []
    skipped: List[Dict[str, str]] = []

    for relative_path, file_findings in sorted(by_path.items()):
        absolute = (root / relative_path).resolve()
        try:
            original_text = absolute.read_text(encoding="utf-8")
        except OSError as exc:
            skipped.append({"path": relative_path, "reason": f"could not read file: {exc}"})
            continue

        new_text, applied = _apply_to_text(original_text, file_findings)
        if not applied:
            skipped.append({
                "path": relative_path,
                "reason": "no edit's original text still matched the file on disk",
            })
            continue

        try:
            ast.parse(new_text, filename=str(absolute))
        except SyntaxError as exc:
            skipped.append({
                "path": relative_path,
                "reason": f"fix would leave the file unparseable ({exc}); nothing written",
            })
            continue

        absolute.write_text(new_text, encoding="utf-8")
        applied_files.append(relative_path)
        applied_edits.extend(applied)

    return {
        "files_changed": applied_files,
        "edits_applied": applied_edits,
        "skipped": skipped,
        "edit_count": len(applied_edits),
    }
