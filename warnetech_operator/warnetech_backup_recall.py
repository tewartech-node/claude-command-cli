#!/usr/bin/env python3
"""Operator backup and recall for the Warnetech runtime.

Implements steps 1-4 of the recovery protocol in
docs/AI-FIREWALL-COMPLETE-REFERENCE.txt: export, store, rehydrate, and
validate checksums.

Each backup carries a manifest recording every item's ORIGINAL absolute
path. Recall restores from the manifest, so a file backed up from
~/.warnetech returns to ~/.warnetech rather than being dropped into the
repository directory.
"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import io
import json
import shutil
import sys
import tarfile
import time
from pathlib import Path
from typing import Optional

RUNTIME = Path.home() / ".warnetech"
BACKUP_DIR = RUNTIME / "backups"
STATE_FILE = RUNTIME / "state.json"
LOG_FILE = RUNTIME / "logs" / "backup_recall.log"
MANIFEST_NAME = "manifest.json"

DEFAULT_STATE = {"last_backup": None, "last_recall": None, "operator_events": []}

# Directories excluded from backups: regenerable, and copying them is slow.
EXCLUDE = shutil.ignore_patterns("__pycache__", "*.pyc", ".git", "node_modules")


def _repo_root() -> Path:
    return Path.home() / "claude-command-cli"


def backup_targets() -> list[Path]:
    """Runtime state only.

    Source directories are deliberately excluded: git already versions them,
    so restoring a backup over the working tree would silently revert
    committed work. Use `git checkout` to recover source. What is unique to
    this machine, and therefore worth backing up, is the runtime state.
    """
    return [
        STATE_FILE,
        RUNTIME / "logs",
        RUNTIME / "tmp",
    ]


# -- state ------------------------------------------------------------------


def load_state() -> dict:
    """Read operator state, tolerating a missing or corrupt file."""
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log(event: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a") as handle:
        handle.write(f"[{ts}] {event}\n")


# -- integrity --------------------------------------------------------------


def checksum(path: Path) -> str:
    """SHA-256 of a file, or of a directory's sorted file contents."""
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
        return digest.hexdigest()
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        if "__pycache__" in child.parts:
            continue
        digest.update(str(child.relative_to(path)).encode())
        digest.update(child.read_bytes())
    return digest.hexdigest()


def _resolve_backup(backup_name: str) -> Path:
    """Resolve a backup name, refusing anything outside BACKUP_DIR."""
    candidate = (BACKUP_DIR / backup_name).resolve()
    if not str(candidate).startswith(str(BACKUP_DIR.resolve())):
        raise ValueError(f"backup name escapes the backup directory: {backup_name}")
    return candidate


# -- backup -----------------------------------------------------------------


def create_backup(targets: Optional[list[Path]] = None) -> Path:
    """Copy each target into a timestamped backup with a manifest."""
    ts = int(time.time())
    backup_path = BACKUP_DIR / f"backup_{ts}"
    backup_path.mkdir(parents=True, exist_ok=True)

    manifest = {"created_at": ts, "items": []}

    for target in targets if targets is not None else backup_targets():
        if not target.exists():
            continue
        destination = backup_path / target.name
        if target.is_file():
            shutil.copy2(target, destination)
        else:
            shutil.copytree(target, destination, ignore=EXCLUDE)
        manifest["items"].append(
            {
                "name": target.name,
                "origin": str(target),
                "is_file": target.is_file(),
                "checksum": checksum(destination),
            }
        )

    (backup_path / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2))

    state = load_state()
    state["last_backup"] = ts
    save_state(state)

    log(f"Backup created: {backup_path} ({len(manifest['items'])} items)")
    return backup_path


def list_backups() -> list[str]:
    if not BACKUP_DIR.exists():
        return []
    return sorted(p.name for p in BACKUP_DIR.iterdir() if p.is_dir())


def verify_backup(backup_name: str) -> dict:
    """Re-checksum every item and report mismatches without restoring."""
    backup_path = _resolve_backup(backup_name)
    manifest_file = backup_path / MANIFEST_NAME
    if not manifest_file.exists():
        raise ValueError(f"backup has no manifest: {backup_name}")

    manifest = json.loads(manifest_file.read_text())
    results = []
    for item in manifest["items"]:
        stored = backup_path / item["name"]
        ok = stored.exists() and checksum(stored) == item["checksum"]
        results.append({"name": item["name"], "ok": ok})

    return {"backup": backup_name, "all_ok": all(r["ok"] for r in results), "items": results}


# -- recall -----------------------------------------------------------------


def recall_backup(backup_name: str, dry_run: bool = False) -> dict:
    """Restore a backup to each item's recorded origin.

    Refuses to run if any checksum fails, so a corrupt backup cannot
    overwrite good source. Pass dry_run=True to see the plan without
    touching the filesystem.
    """
    backup_path = _resolve_backup(backup_name)
    if not backup_path.exists():
        raise ValueError(f"Backup not found: {backup_name}")

    manifest_file = backup_path / MANIFEST_NAME
    if not manifest_file.exists():
        raise ValueError(
            f"Backup {backup_name} has no manifest and cannot be safely restored"
        )

    verification = verify_backup(backup_name)
    if not verification["all_ok"]:
        failed = [r["name"] for r in verification["items"] if not r["ok"]]
        raise ValueError(f"checksum mismatch, refusing to restore: {failed}")

    manifest = json.loads(manifest_file.read_text())
    planned = [{"name": i["name"], "restores_to": i["origin"]} for i in manifest["items"]]

    if dry_run:
        return {"dry_run": True, "backup": backup_name, "planned": planned}

    for item in manifest["items"]:
        source = backup_path / item["name"]
        target = Path(item["origin"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.is_file():
                target.unlink()
            else:
                shutil.rmtree(target)
        if item["is_file"]:
            shutil.copy2(source, target)
        else:
            shutil.copytree(source, target)

    # Reloaded after restore: state.json is itself a restored item.
    state = load_state()
    state["last_recall"] = backup_name
    save_state(state)

    log(f"Backup recalled: {backup_name} ({len(manifest['items'])} items)")
    return {"dry_run": False, "backup": backup_name, "restored": planned}


# -- offsite tier (S3, client-side encrypted) --------------------------------
#
# A local backup (above) protects against losing this machine's runtime
# state; it does nothing if the machine itself is lost, stolen, or its disk
# fails. This tier adds an encrypted offsite copy of one local backup,
# reusing that backup's own manifest and checksums rather than inventing a
# second notion of what "one backup" contains.
#
# Sealing happens via warnetech_envelope.seal_archive() -- the passphrase-
# protected mode of the canonical envelope -- before anything reaches the
# network. warnetech_connectors.s3_backup then talks to AWS with the sealed
# bytes only; it never sees the passphrase's plaintext target or handles the
# key itself. See CLAUDE.md: encryption extends warnetech_envelope, it does
# not get reimplemented here.


def _s3_backup_module():
    """Import warnetech_connectors.s3_backup lazily and on demand, so a
    machine with no `s3` extra installed can still use every local backup
    command above without hitting an ImportError at module load time."""
    from warnetech_connectors import s3_backup

    return s3_backup


def _s3_object_key(backup_name: str) -> str:
    return f"{backup_name}.tar"


def _archive_backup_to_bytes(backup_path: Path) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        archive.add(backup_path, arcname=backup_path.name)
    return buffer.getvalue()


def _safe_extract(archive: tarfile.TarFile, destination: Path) -> None:
    """Extract every member of `archive` under `destination`, refusing
    anything that would land outside it.

    tarfile.extractall() does not do this by default on every supported
    Python version here (the protective `filter` argument is 3.12+); a
    crafted archive with a `../../etc/cron.d/x` member, or a symlink member
    pointing outside the tree, can otherwise write anywhere the process can.
    A backup fetched from S3 is data from the network -- it does not get to
    be trusted just because it round-tripped through this module's own
    upload path once.
    """
    destination = destination.resolve()
    for member in archive.getmembers():
        if member.issym() or member.islnk():
            raise ValueError(f"refusing to extract link member: {member.name}")
        target = (destination / member.name).resolve()
        if target != destination and destination not in target.parents:
            raise ValueError(f"refusing to extract member outside the target directory: {member.name}")
    archive.extractall(destination)


def push_to_s3(
    backup_name: str, bucket: str, passphrase: str, region: Optional[str] = None
) -> dict:
    """Seal one local backup and upload it as a single object.

    Raises ValueError for a bad backup_name (mirrors recall_backup's
    contract); returns the connector's own {"ok": ...} dict for every
    network-reachable failure, since those are expected and recoverable,
    not programmer errors.
    """
    backup_path = _resolve_backup(backup_name)
    if not backup_path.exists():
        raise ValueError(f"Backup not found: {backup_name}")

    s3_backup = _s3_backup_module()
    setup = s3_backup.ensure_bucket(bucket, region=region)
    if not setup.get("ok"):
        return setup

    data = _archive_backup_to_bytes(backup_path)
    result = s3_backup.upload_backup(bucket, _s3_object_key(backup_name), data, passphrase, region=region)

    if result.get("ok"):
        state = load_state()
        state["last_s3_push"] = {"backup": backup_name, "bucket": bucket, "at": int(time.time())}
        save_state(state)
        log(f"Backup pushed to S3: {backup_name} -> s3://{bucket}/{_s3_object_key(backup_name)}")
    else:
        log(f"S3 push failed for {backup_name}: {result.get('error')}")

    return result


def pull_from_s3(
    backup_name: str, bucket: str, passphrase: str, region: Optional[str] = None
) -> dict:
    """Download and unseal one backup from S3, extract it under BACKUP_DIR,
    then re-verify its checksums against the manifest it was created with --
    the AEAD tag already guarantees the sealed bytes were not tampered with
    in transit or at rest, but this also catches a defect anywhere in the
    tar/extract path itself, not only in the network leg.
    """
    s3_backup = _s3_backup_module()
    fetched = s3_backup.download_backup(bucket, _s3_object_key(backup_name), passphrase, region=region)
    if not fetched.get("ok"):
        log(f"S3 pull failed for {backup_name}: {fetched.get('error')}")
        return fetched

    destination = _resolve_backup(backup_name)
    if destination.exists():
        raise ValueError(
            f"a local backup named {backup_name} already exists; "
            "remove it first or pull under a different name"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tarfile.open(fileobj=io.BytesIO(fetched["data"]), mode="r") as archive:
        _safe_extract(archive, destination.parent)

    verification = verify_backup(backup_name)
    state = load_state()
    state["last_s3_pull"] = {"backup": backup_name, "bucket": bucket, "at": int(time.time())}
    save_state(state)
    log(f"Backup pulled from S3: {backup_name} <- s3://{bucket}/{_s3_object_key(backup_name)} "
        f"(checksums {'ok' if verification['all_ok'] else 'MISMATCH'})")

    return {"ok": verification["all_ok"], "backup": backup_name, "verification": verification}


def _prompt_passphrase(confirm: bool) -> str:
    """Reads a passphrase from the terminal without echoing it.

    `confirm=True` (writes -- pushing a new object) asks twice and refuses
    to proceed on a mismatch, so a typo does not silently seal a backup
    under a key nobody actually knows. `confirm=False` (reads) asks once,
    since a wrong read passphrase merely fails to decrypt -- it does not
    destroy anything.
    """
    first = getpass.getpass("S3 backup passphrase: ")
    if not confirm:
        return first
    second = getpass.getpass("Confirm passphrase: ")
    if first != second:
        raise ValueError("passphrases did not match")
    return first


# -- CLI --------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="warnetech-backup-recall")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("backup", help="create a new backup")
    sub.add_parser("list", help="list available backups")

    verify = sub.add_parser("verify", help="check a backup's checksums")
    verify.add_argument("name")

    recall = sub.add_parser("recall", help="restore a backup")
    recall.add_argument("name")
    recall.add_argument(
        "--dry-run", action="store_true", help="show what would be restored"
    )
    recall.add_argument(
        "--yes", action="store_true", help="skip the confirmation prompt"
    )

    push = sub.add_parser("push-s3", help="seal a local backup and upload it offsite")
    push.add_argument("name")
    push.add_argument("--bucket", required=True, help="S3 bucket (must already exist or be creatable)")
    push.add_argument("--region", default=None)

    pull = sub.add_parser("pull-s3", help="download and unseal a backup from S3")
    pull.add_argument("name")
    pull.add_argument("--bucket", required=True)
    pull.add_argument("--region", default=None)

    args = parser.parse_args(argv)

    if args.command == "backup":
        print(f"Backup created at: {create_backup()}")
        return 0

    if args.command == "list":
        names = list_backups()
        print("\n".join(names) if names else "No backups found.")
        return 0

    if args.command == "verify":
        result = verify_backup(args.name)
        print(json.dumps(result, indent=2))
        return 0 if result["all_ok"] else 1

    if args.command == "recall":
        if args.dry_run:
            print(json.dumps(recall_backup(args.name, dry_run=True), indent=2))
            return 0
        if not args.yes:
            plan = recall_backup(args.name, dry_run=True)
            print("This will OVERWRITE:")
            for item in plan["planned"]:
                print(f"  {item['restores_to']}")
            if input("Proceed? [y/N] ").strip().lower() != "y":
                print("Aborted.")
                return 1
        recall_backup(args.name)
        print("Backup recalled.")
        return 0

    if args.command == "push-s3":
        passphrase = _prompt_passphrase(confirm=True)
        result = push_to_s3(args.name, args.bucket, passphrase, region=args.region)
        print(json.dumps({k: v for k, v in result.items() if k != "data"}, indent=2))
        # Unlike the standalone script this replaces, a failed push must
        # exit non-zero -- a backup tool that reports success on failure is
        # worse than no backup tool.
        return 0 if result.get("ok") else 1

    if args.command == "pull-s3":
        passphrase = _prompt_passphrase(confirm=False)
        result = pull_from_s3(args.name, args.bucket, passphrase, region=args.region)
        print(json.dumps({k: v for k, v in result.items() if k != "data"}, indent=2))
        return 0 if result.get("ok") else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
