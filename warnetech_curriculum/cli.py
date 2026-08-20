"""Terminal / Termux entry point for the curriculum.

    python -m warnetech_curriculum <command>

Design constraints, all of them Termux-driven: standard library only, no
network, no colour unless the terminal actually supports it, ASCII output,
and exit codes that mean something to a shell script. Every command works
with the phone in aeroplane mode.

Exit codes
    0  clean / informational
    1  blocking findings -- do not proceed with the action
    2  usage error, or a ledger whose chain does not verify
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from .inspector import Inspector
from .ledger import writable_ledger
from .preflight import changed_files, preflight
from .rules import RULES, SEVERITY_ORDER
from .seed import OPEN_LESSONS, seed

EXIT_OK, EXIT_BLOCKED, EXIT_ERROR = 0, 1, 2


def _colour() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _colour() else text


def _severity_tag(severity: str) -> str:
    colours = {"critical": "31;1", "high": "33;1", "medium": "36", "low": "37"}
    return _paint(f"{severity:<8}", colours.get(severity, "37"))


def _repo_root(explicit: Optional[str]) -> Path:
    if explicit:
        return Path(explicit).resolve()
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").exists():
            return candidate
    return here


def _print_findings(findings: List[dict]) -> None:
    if not findings:
        print(_paint("  no findings", "32"))
        return
    for finding in findings:
        print(f"  {_severity_tag(finding['severity'])} {finding['rule']}  "
              f"{finding['path']}:{finding['line']}")
        print(f"           {finding['message']}")
        if finding.get("evidence"):
            print(_paint(f"           {finding['evidence']}", "90"))


# -- commands ------------------------------------------------------------------


def cmd_check(args: argparse.Namespace) -> int:
    root = _repo_root(args.root)
    paths = [Path(p).resolve() for p in args.paths] if args.paths else None
    verdict = preflight(root, paths=paths, record=not args.no_record, only=args.rule)
    if args.json:
        print(json.dumps(verdict, indent=2))
        return EXIT_OK if verdict["ok"] else EXIT_BLOCKED

    counts = verdict["counts"]
    print(f"\ncurriculum check -- {verdict['files_examined']} files ({verdict['scope']})\n")
    _print_findings(verdict["findings"])
    print()
    if verdict["newly_recorded"]:
        print(_paint(f"  {len(verdict['newly_recorded'])} new finding(s) added to the ledger", "90"))
    if verdict["ok"]:
        print(_paint(f"  PASS  {counts['total']} finding(s), none blocking", "32;1"))
        return EXIT_OK
    print(_paint(f"  BLOCKED  {counts['critical']} critical finding(s)", "31;1"))
    print("  These rest on things that provably do not exist. Fix, or record")
    print("  a deliberate exception with:  warnetech-curriculum learn \"...\"")
    return EXIT_BLOCKED


def cmd_preflight(args: argparse.Namespace) -> int:
    root = _repo_root(args.root)
    paths = changed_files(root, since=args.since)
    if not paths:
        print("preflight: no changed Python files against HEAD -- nothing to check")
        return EXIT_OK
    verdict = preflight(root, paths=paths, record=not args.no_record)
    if args.json:
        print(json.dumps(verdict, indent=2))
        return EXIT_OK if verdict["ok"] else EXIT_BLOCKED
    print(f"\npreflight -- {len(paths)} changed file(s)\n")
    for path in paths:
        print(_paint(f"    {path.relative_to(root)}", "90"))
    print()
    _print_findings(verdict["findings"])
    print()
    if verdict["ok"]:
        print(_paint("  PASS  safe to proceed", "32;1"))
        return EXIT_OK
    print(_paint("  BLOCKED  do not commit this as-is", "31;1"))
    return EXIT_BLOCKED


def cmd_learn(args: argparse.Namespace) -> int:
    book = writable_ledger(Path(args.ledger) if args.ledger else None)
    entry = book.record_failure(
        args.title, detail=args.detail or "", tags=args.tag or [], rule=args.rule
    )
    print(f"recorded {entry.id}: {entry.title}")
    print(_paint(f"  ledger: {book.path}", "90"))
    print(_paint("  this entry is permanent -- it can be superseded, never removed", "90"))
    return EXIT_OK


def cmd_resolve(args: argparse.Namespace) -> int:
    book = writable_ledger(Path(args.ledger) if args.ledger else None)
    try:
        entry = book.record_resolution(args.id, args.title, detail=args.detail or "")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    print(f"recorded {entry.id}, superseding {args.id}")
    print(_paint(f"  {args.id} remains in the ledger and stays readable", "90"))
    return EXIT_OK


def cmd_log(args: argparse.Namespace) -> int:
    book = writable_ledger(Path(args.ledger) if args.ledger else None)
    all_entries = book.entries()
    entries = all_entries
    if args.kind:
        entries = [e for e in entries if e.kind == args.kind]
    if args.id:
        entries = book.timeline(args.id)
    if args.json:
        print(json.dumps([e.to_dict() for e in entries], indent=2))
        return EXIT_OK
    if not entries:
        # An empty ledger and an over-narrow filter are different problems,
        # and telling someone to seed a ledger that already has entries just
        # sends them the wrong way.
        if not all_entries:
            print("ledger is empty -- run `warnetech-curriculum seed` to install the base curriculum")
        elif args.id:
            print(f"no entry {args.id} in the ledger ({len(all_entries)} entries) -- "
                  "check the id with `warnetech-curriculum log`")
        else:
            print(f"no {args.kind} entries in the ledger ({len(all_entries)} entries in total)")
        return EXIT_OK
    for entry in entries[-args.limit:]:
        marker = {"failure": "!", "lesson": "*", "resolution": "+", "note": "."}.get(entry.kind, "?")
        kind = _paint(f"{entry.kind:<11}", "90")
        print(f"{marker} {entry.id:<14} {kind} {entry.title}")
        if args.verbose and entry.detail:
            for line in entry.detail.split("\n"):
                print(_paint(f"      {line}", "90"))
    print()
    print(_paint(f"  {len(entries)} entr{'y' if len(entries)==1 else 'ies'} -- {book.path}", "90"))
    return EXIT_OK


def cmd_verify(args: argparse.Namespace) -> int:
    book = writable_ledger(Path(args.ledger) if args.ledger else None)
    result = book.verify()
    if args.json:
        print(json.dumps(result, indent=2))
        return EXIT_OK if result["ok"] else EXIT_ERROR
    if result["ok"]:
        print(_paint(f"  INTACT  {result['entries']} entries, chain verifies", "32;1"))
        print(_paint(f"  head: {result['head'][:32]}...", "90"))
        return EXIT_OK
    print(_paint(f"  BROKEN  at entry {result['broken_at']}: {result['reason']}", "31;1"))
    print("  The ledger is append-only by design; a break means it was edited")
    print("  outside this tool. The surviving entries are still readable.")
    return EXIT_ERROR


def cmd_curriculum(args: argparse.Namespace) -> int:
    if args.json:
        print(json.dumps({
            "enforced": [
                {"id": r.id, "title": r.title, "severity": r.severity,
                 "origin": r.origin, "lesson": r.lesson}
                for r in RULES
            ],
            "open": OPEN_LESSONS,
        }, indent=2))
        return EXIT_OK

    print(_paint("\nENFORCED -- learned, and now checked automatically\n", "1"))
    for rule in sorted(RULES, key=lambda r: SEVERITY_ORDER.get(r.severity, 9)):
        print(f"  {_severity_tag(rule.severity)} {rule.id}  {rule.title}")
        print(_paint(f"           origin: {rule.origin}", "90"))
        for line in _wrap(rule.lesson, 76):
            print(f"           {line}")
        print()

    print(_paint("OPEN -- recorded and understood, no rule catches it yet\n", "1"))
    for lesson in OPEN_LESSONS:
        print(f"  {_paint('open    ', '33')} {lesson['id']}  {lesson['title']}")
        for line in _wrap(lesson["detail"], 76):
            print(f"           {line}")
        print()
    print(_paint(f"  {len(RULES)} enforced, {len(OPEN_LESSONS)} open\n", "90"))
    return EXIT_OK


def _wrap(text: str, width: int) -> List[str]:
    import textwrap

    return textwrap.wrap(" ".join(text.split()), width=width)


def cmd_seed(args: argparse.Namespace) -> int:
    book = writable_ledger(Path(args.ledger) if args.ledger else None)
    result = seed(book)
    if args.json:
        print(json.dumps(result, indent=2))
        return EXIT_OK
    if result["added"]:
        print(f"installed {len(result['added'])} lesson(s): {', '.join(result['added'])}")
    else:
        print("base curriculum already installed -- nothing to add")
    print(_paint(f"  {result['total']} total entries at {book.path}", "90"))
    return EXIT_OK


def cmd_rules(args: argparse.Namespace) -> int:
    inspector = Inspector(_repo_root(args.root))
    print(f"first-party packages under {inspector.root.name}/:")
    for package in sorted(inspector.first_party):
        print(f"  {package}")
    return EXIT_OK


# -- parser --------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="warnetech-curriculum",
        description="Deterministic, parameter-free preflight and failure ledger for Warnetech.",
        epilog="No model, no API key, no network. Works offline on Termux.",
    )
    parser.add_argument("--ledger", help="path to the ledger file (default: ~/.warnetech/curriculum)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="run the curriculum over the tree")
    check.add_argument("paths", nargs="*", help="specific files (default: all first-party)")
    check.add_argument("--root", help="repository root")
    check.add_argument("--rule", action="append", help="limit to specific rule ids")
    check.add_argument("--no-record", action="store_true", help="do not append findings to the ledger")
    check.set_defaults(func=cmd_check)

    pre = sub.add_parser("preflight", help="check only files changed against HEAD")
    pre.add_argument("--root", help="repository root")
    pre.add_argument("--since", help="git ref to diff against (e.g. origin/main), for CI")
    pre.add_argument("--no-record", action="store_true")
    pre.set_defaults(func=cmd_preflight)

    learn = sub.add_parser("learn", help="record a failure -- permanently")
    learn.add_argument("title")
    learn.add_argument("--detail", help="what happened, and what it teaches")
    learn.add_argument("--rule", help="rule id this relates to, if any")
    learn.add_argument("--tag", action="append")
    learn.set_defaults(func=cmd_learn)

    resolve = sub.add_parser("resolve", help="supersede an entry (the original is kept)")
    resolve.add_argument("id")
    resolve.add_argument("title")
    resolve.add_argument("--detail")
    resolve.set_defaults(func=cmd_resolve)

    log = sub.add_parser("log", help="read the ledger")
    log.add_argument("--kind", choices=["failure", "lesson", "resolution", "note"])
    log.add_argument("--id", help="show the full timeline of one entry")
    log.add_argument("--limit", type=int, default=40)
    log.add_argument("-v", "--verbose", action="store_true")
    log.set_defaults(func=cmd_log)

    verify = sub.add_parser("verify", help="check the ledger's hash chain")
    verify.set_defaults(func=cmd_verify)

    curriculum = sub.add_parser("curriculum", help="show what has been learned")
    curriculum.set_defaults(func=cmd_curriculum)

    seed_cmd = sub.add_parser("seed", help="install the pre-installed base curriculum")
    seed_cmd.set_defaults(func=cmd_seed)

    packages = sub.add_parser("packages", help="list first-party packages in scope")
    packages.add_argument("--root", help="repository root")
    packages.set_defaults(func=cmd_rules)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return EXIT_ERROR
    except BrokenPipeError:  # `| head` on a long log
        return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
