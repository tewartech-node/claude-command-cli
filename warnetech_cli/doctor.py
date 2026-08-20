"""Environment self-check for the Warnetech CLI on Termux.

Answers one question before anything else runs: is this machine actually
set up to do what the CLI is about to ask of it? Termux is not a normal
Linux install -- no system package manager parity, `cryptography` needs
`rust` + `binutils` on the PATH to build its native wheel at all (see
bootstrap_termux.sh's comment on this), and a phone can be mid-storage-full
or mid-interrupted-`pkg-upgrade` in ways a dev laptop rarely is. Finding
that out from a `ModuleNotFoundError` three commands into a session is
worse than finding it out here, once, with a plain-English next step.

Every check is a small function returning a CheckResult; nothing here
prints or exits on its own, so the whole battery of checks is testable
without touching stdout, an interactive terminal, or a real Termux install.
main() is the only place that formats or exits.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import locale
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

OK, WARN, FAIL, SKIP = "ok", "warn", "fail", "skip"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    message: str
    hint: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "status": self.status, "message": self.message, "hint": self.hint}


def _can_import(module_name: str) -> bool:
    """True if `module_name` is importable, without actually importing it --
    a doctor that imports the thing it is checking risks the same
    module-level side effects and slow startup it exists to catch early."""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


# -- individual checks --------------------------------------------------------
#
# Each takes no required arguments so `CHECKS` can list them uniformly, but
# reads real state only through a small set of stdlib entry points
# (sys.version_info, os.environ, shutil.which, Path.home()) -- narrow enough
# that tests can monkeypatch exactly one of them per test rather than faking
# an entire environment.


def check_python_version() -> CheckResult:
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 10):
        return CheckResult("python_version", OK, f"Python {major}.{minor}")
    return CheckResult(
        "python_version", FAIL, f"Python {major}.{minor} (need >= 3.10)",
        hint="pyproject.toml sets requires-python >= 3.10; upgrade Python first.",
    )


def check_required_dependency() -> CheckResult:
    """cryptography backs warnetech_envelope's AES-256-GCM; without it every
    encrypted command raises immediately (see pyproject.toml's comment on
    this exact dependency). On Termux this is the single most common
    first-run failure, because the wheel needs to build from source."""
    if _can_import("cryptography"):
        return CheckResult("cryptography", OK, "cryptography is installed")
    return CheckResult(
        "cryptography", FAIL, "cryptography is NOT installed",
        hint="pip install -e '.[dev]'  -- on Termux, first: pkg install rust binutils "
             "(cryptography builds its native wheel from source there).",
    )


_OPTIONAL_EXTRAS = {
    "lz4": "compression extra (warnetech_cli.compression)",
    "zstandard": "compression extra (warnetech_cli.compression)",
    "pyarrow": "parquet extra",
    "boto3": "s3 extra (offsite backup tier, see docs/11_BACKUP_AND_RECOVERY.md)",
}


def check_optional_dependencies() -> List[CheckResult]:
    results = []
    for module_name, describes in _OPTIONAL_EXTRAS.items():
        if _can_import(module_name):
            results.append(CheckResult(f"optional:{module_name}", OK, f"{module_name} is installed"))
        else:
            results.append(CheckResult(
                f"optional:{module_name}", SKIP, f"{module_name} not installed ({describes})",
                hint=f"only needed if you use the {describes.split(' (')[0]}",
            ))
    return results


def check_git() -> CheckResult:
    if shutil.which("git"):
        return CheckResult("git", OK, "git is on PATH")
    return CheckResult(
        "git", FAIL, "git is not on PATH",
        hint="pkg install git" if _is_termux() else "install git for your platform",
    )


def check_envelope_round_trip() -> CheckResult:
    """The same self-test bootstrap_termux.sh runs at the end of setup,
    available on demand here too: encrypt/decrypt one string and confirm it
    comes back unchanged. Catches a `cryptography` install that imports
    fine but is missing the backend AES-GCM actually needs at runtime."""
    if not _can_import("cryptography"):
        return CheckResult("envelope_round_trip", SKIP, "skipped: cryptography not installed")
    try:
        from warnetech_envelope import decrypt_data, encrypt_data

        probe = "warnetech-doctor-probe"
        if decrypt_data(encrypt_data(probe, "k"), "k") == probe:
            return CheckResult("envelope_round_trip", OK, "encrypt/decrypt round-trip OK")
        return CheckResult(
            "envelope_round_trip", FAIL, "round-trip produced the wrong plaintext",
            hint="this should not be possible; file an issue with your platform/Python version",
        )
    except Exception as exc:  # noqa: BLE001 - a doctor check must report, never crash the doctor
        return CheckResult(
            "envelope_round_trip", FAIL, f"round-trip failed: {exc}",
            hint="the cryptography install is broken; reinstall it (see the cryptography check above)",
        )


def _is_termux() -> bool:
    return "com.termux" in os.environ.get("PREFIX", "") or "com.termux" in os.environ.get("HOME", "")


def check_runtime_directory() -> CheckResult:
    runtime = Path.home() / ".warnetech"
    if not runtime.exists():
        return CheckResult(
            "runtime_directory", WARN, f"{runtime} does not exist yet",
            hint="created automatically on first backup/config write; "
                 "or run: mkdir -p ~/.warnetech/{logs,backups,tmp}",
        )
    probe = runtime / ".doctor-write-probe"
    try:
        probe.write_text("", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return CheckResult(
            "runtime_directory", FAIL, f"{runtime} exists but is not writable: {exc}",
        )
    return CheckResult("runtime_directory", OK, f"{runtime} exists and is writable")


def check_curriculum_hook(root: Optional[Path] = None) -> CheckResult:
    repo_root = root or _find_repo_root()
    if repo_root is None:
        return CheckResult("curriculum_hook", SKIP, "not inside a git checkout")
    hook = repo_root / ".git" / "hooks" / "pre-commit"
    if not hook.is_file():
        return CheckResult(
            "curriculum_hook", WARN, "no pre-commit hook installed",
            hint="./scripts/install-curriculum-hook.sh",
        )
    try:
        installed = "warnetech-curriculum" in hook.read_text(encoding="utf-8")
    except OSError:
        installed = False
    if installed:
        return CheckResult("curriculum_hook", OK, "curriculum pre-commit hook is installed")
    return CheckResult(
        "curriculum_hook", WARN, "a pre-commit hook exists but is not the curriculum's",
        hint="see scripts/install-curriculum-hook.sh if you want the curriculum gate too",
    )


def check_curriculum_ledger() -> CheckResult:
    if not _can_import("warnetech_curriculum"):
        return CheckResult("curriculum_ledger", SKIP, "warnetech_curriculum not importable")
    try:
        from warnetech_curriculum import default_ledger_path, writable_ledger

        path = default_ledger_path()
        if not path.exists():
            return CheckResult(
                "curriculum_ledger", WARN, f"no ledger yet at {path}",
                hint="warnetech-curriculum seed",
            )
        result = writable_ledger(path).verify()
        if result["ok"]:
            return CheckResult("curriculum_ledger", OK, f"ledger intact ({result['entries']} entries)")
        return CheckResult(
            "curriculum_ledger", FAIL,
            f"ledger chain broken at entry {result['broken_at']}: {result['reason']}",
        )
    except Exception as exc:  # noqa: BLE001 - report, do not crash the doctor
        return CheckResult("curriculum_ledger", FAIL, f"could not verify ledger: {exc}")


def check_terminal() -> CheckResult:
    is_tty = sys.stdout.isatty()
    encoding = (locale.getpreferredencoding(False) or "").lower()
    utf8 = "utf" in encoding
    if is_tty and utf8:
        return CheckResult("terminal", OK, f"interactive TTY, {encoding}")
    if not is_tty:
        return CheckResult("terminal", SKIP, "not an interactive terminal (fine for scripts/CI)")
    return CheckResult(
        "terminal", WARN, f"locale encoding is {encoding or 'unknown'}, not UTF-8",
        hint="export LANG=en_US.UTF-8 (or your preferred UTF-8 locale) in ~/.bashrc",
    )


def check_termux() -> CheckResult:
    if _is_termux():
        return CheckResult("platform", OK, "running on Termux")
    return CheckResult("platform", SKIP, "not running on Termux")


def _find_repo_root() -> Optional[Path]:
    here = Path.cwd().resolve()
    for candidate in (here, *here.parents):
        if (candidate / "pyproject.toml").is_file() or (candidate / ".git").exists():
            return candidate
    return None


# -- orchestration --------------------------------------------------------------


def run_checks(root: Optional[Path] = None) -> List[CheckResult]:
    checks: List[Callable[[], object]] = [
        check_python_version,
        check_termux,
        check_terminal,
        check_required_dependency,
        check_optional_dependencies,
        check_git,
        check_envelope_round_trip,
        check_runtime_directory,
        check_curriculum_ledger,
        lambda: check_curriculum_hook(root),
    ]
    results: List[CheckResult] = []
    for check in checks:
        try:
            outcome = check()
        except Exception as exc:  # noqa: BLE001 - one broken check must not sink the whole report
            results.append(CheckResult(getattr(check, "__name__", "unknown"), FAIL, f"check raised: {exc}"))
            continue
        if isinstance(outcome, list):
            results.extend(outcome)
        else:
            results.append(outcome)
    return results


# -- CLI --------------------------------------------------------------------------

_SYMBOLS = {OK: "✓", WARN: "!", FAIL: "✗", SKIP: "-"}
_COLORS = {OK: "32", WARN: "33", FAIL: "31;1", SKIP: "90"}


def _colour() -> bool:
    return sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _paint(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _colour() else text


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="warnetech-doctor",
        description="Checks whether this machine is set up to run the Warnetech CLI.",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--root", help="repository root (default: autodetected)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else None
    results = run_checks(root)

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
        return 1 if any(r.status == FAIL for r in results) else 0

    print("\nwarnetech-doctor\n")
    for result in results:
        symbol = _paint(_SYMBOLS[result.status], _COLORS[result.status])
        print(f"  {symbol} {result.name}: {result.message}")
        if result.hint and result.status in (WARN, FAIL):
            print(_paint(f"      -> {result.hint}", "90"))

    failed = [r for r in results if r.status == FAIL]
    warned = [r for r in results if r.status == WARN]
    print()
    if not failed and not warned:
        print(_paint("  All checks passed.", "32;1"))
        return 0
    if failed:
        print(_paint(f"  {len(failed)} check(s) failed, {len(warned)} warning(s).", "31;1"))
        return 1
    print(_paint(f"  {len(warned)} warning(s), nothing failing.", "33;1"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
