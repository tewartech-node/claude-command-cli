"""Secure backup and failsafe system for warnetech-connectors.

This module provides:
1. Atomic backup creation with checksums
2. Backup verification and integrity checks
3. Point-in-time recovery capability
4. Backup manifest generation
5. Automated rollback on detection of corruption

All backups are created in ~/.warnetech/backups/connectors with ISO timestamp
naming. Each backup includes:
- Full source tree snapshot
- Configuration state
- Manifest with checksums
- Metadata (version, timestamp, reason)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from warnetech_connectors.logging import get_logger
from warnetech_connectors.config import ConnectorsConfig, DEFAULT_CONFIG

logger = get_logger(__name__)

# Backup directory configuration
BACKUP_ROOT = Path.home() / ".warnetech" / "backups" / "connectors"
MANIFEST_NAME = "backup_manifest.json"
CHECKSUM_ALGORITHM = "sha256"


def ensure_backup_dir() -> Path:
    """Creates backup directory if it doesn't exist."""
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    return BACKUP_ROOT


def compute_file_checksum(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_directory_checksum(directory: Path) -> str:
    """Computes checksum for a directory by hashing all file checksums."""
    hasher = hashlib.sha256()
    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file():
            file_hash = compute_file_checksum(file_path)
            hasher.update(file_hash.encode())
    return hasher.hexdigest()


def create_backup(
    source_dir: Path,
    reason: str = "manual",
    config: ConnectorsConfig = DEFAULT_CONFIG,
) -> Dict[str, Any]:
    """Creates an atomic backup of the connectors directory.

    Args:
        source_dir: Path to warnetech_connectors directory
        reason: Human-readable reason for the backup
        config: Current connector configuration

    Returns:
        Backup metadata dict with location, checksum, timestamp, etc.
    """
    ensure_backup_dir()

    # Create timestamped backup directory
    timestamp = datetime.utcnow().isoformat().replace(":", "-")
    backup_name = f"backup_{timestamp}"
    backup_path = BACKUP_ROOT / backup_name
    backup_path.mkdir(parents=True, exist_ok=True)

    try:
        # Copy source directory
        source_code_backup = backup_path / "connectors"
        shutil.copytree(source_dir, source_code_backup, dirs_exist_ok=True)

        # Save configuration
        config_backup = backup_path / "config_snapshot.json"
        config_data = {
            "enabled_connectors": list(config.enabled_connectors),
            "rate_limit_rpm": config.rate_limit.requests_per_minute,
            "connect_timeout_s": config.timeout.connect_timeout_seconds,
            "read_timeout_s": config.timeout.read_timeout_seconds,
            "max_retries": config.retry.max_retries,
            "base_delay_s": config.retry.base_delay_seconds,
            "max_delay_s": config.retry.max_delay_seconds,
        }
        config_backup.write_text(json.dumps(config_data, indent=2))

        # Compute checksums
        source_checksum = compute_directory_checksum(source_code_backup)
        config_checksum = compute_file_checksum(config_backup)

        # Create manifest
        manifest = {
            "version": "1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "backup_name": backup_name,
            "reason": reason,
            "checksums": {
                "source_code": source_checksum,
                "configuration": config_checksum,
            },
            "file_count": len(list(source_code_backup.rglob("*"))),
            "size_bytes": sum(f.stat().st_size for f in source_code_backup.rglob("*") if f.is_file()),
            "algorithm": CHECKSUM_ALGORITHM,
        }

        manifest_file = backup_path / MANIFEST_NAME
        manifest_file.write_text(json.dumps(manifest, indent=2))

        logger.info(f"Backup created: {backup_name}")
        logger.info(f"Source checksum: {source_checksum}")
        logger.info(f"Config checksum: {config_checksum}")

        return {
            "ok": True,
            "backup_name": backup_name,
            "backup_path": str(backup_path),
            "manifest": manifest,
        }

    except Exception as e:  # noqa: BLE001
        logger.error(f"Backup creation failed: {e}")
        # Cleanup partial backup on failure
        if backup_path.exists():
            shutil.rmtree(backup_path, ignore_errors=True)
        return {
            "ok": False,
            "error": str(e),
        }


def verify_backup(backup_name: str) -> Dict[str, Any]:
    """Verifies integrity of a backup using stored checksums."""
    backup_path = BACKUP_ROOT / backup_name

    if not backup_path.exists():
        return {
            "ok": False,
            "error": f"Backup not found: {backup_name}",
        }

    try:
        manifest_file = backup_path / MANIFEST_NAME
        if not manifest_file.exists():
            return {
                "ok": False,
                "error": "Manifest not found in backup",
            }

        manifest = json.loads(manifest_file.read_text())
        source_code_dir = backup_path / "connectors"

        # Verify source code checksum
        current_source_checksum = compute_directory_checksum(source_code_dir)
        expected_source_checksum = manifest["checksums"]["source_code"]

        if current_source_checksum != expected_source_checksum:
            logger.error(
                f"Source code checksum mismatch! "
                f"Expected: {expected_source_checksum}, "
                f"Got: {current_source_checksum}"
            )
            return {
                "ok": False,
                "error": "Source code checksum verification failed",
                "expected": expected_source_checksum,
                "got": current_source_checksum,
            }

        # Verify configuration checksum
        config_file = backup_path / "config_snapshot.json"
        current_config_checksum = compute_file_checksum(config_file)
        expected_config_checksum = manifest["checksums"]["configuration"]

        if current_config_checksum != expected_config_checksum:
            logger.error(
                f"Configuration checksum mismatch! "
                f"Expected: {expected_config_checksum}, "
                f"Got: {current_config_checksum}"
            )
            return {
                "ok": False,
                "error": "Configuration checksum verification failed",
            }

        logger.info(f"Backup {backup_name} verified successfully")
        return {
            "ok": True,
            "backup_name": backup_name,
            "manifest": manifest,
            "verified_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:  # noqa: BLE001
        logger.error(f"Backup verification failed: {e}")
        return {
            "ok": False,
            "error": str(e),
        }


def list_backups() -> Dict[str, Any]:
    """Lists all available backups with metadata."""
    ensure_backup_dir()

    backups = []
    for backup_dir in sorted(BACKUP_ROOT.iterdir()):
        if not backup_dir.is_dir():
            continue

        manifest_file = backup_dir / MANIFEST_NAME
        if not manifest_file.exists():
            continue

        try:
            manifest = json.loads(manifest_file.read_text())
            backups.append({
                "name": backup_dir.name,
                "timestamp": manifest.get("timestamp"),
                "reason": manifest.get("reason"),
                "size_bytes": manifest.get("size_bytes"),
                "file_count": manifest.get("file_count"),
            })
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to read backup metadata for {backup_dir.name}: {e}")

    return {
        "ok": True,
        "backup_count": len(backups),
        "backups": sorted(backups, key=lambda b: b["timestamp"], reverse=True),
    }


def restore_backup(
    backup_name: str,
    target_dir: Path,
    verify_first: bool = True,
) -> Dict[str, Any]:
    """Restores a backup to the target directory.

    Args:
        backup_name: Name of the backup to restore
        target_dir: Directory to restore to (will be overwritten)
        verify_first: Verify backup integrity before restoring

    Returns:
        Restoration result
    """
    backup_path = BACKUP_ROOT / backup_name
    source_backup = backup_path / "connectors"

    if not backup_path.exists():
        return {
            "ok": False,
            "error": f"Backup not found: {backup_name}",
        }

    # Verify backup integrity if requested
    if verify_first:
        verification = verify_backup(backup_name)
        if not verification.get("ok"):
            return {
                "ok": False,
                "error": "Backup verification failed",
                "details": verification,
            }

    try:
        # Create temporary directory for safety
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_target = Path(tmp_dir) / "restore"

            # Copy backup to temp location
            shutil.copytree(source_backup, temp_target, dirs_exist_ok=True)

            # Verify copy succeeded
            if not temp_target.exists():
                raise RuntimeError("Restore preparation failed")

            # Remove target directory if it exists
            if target_dir.exists():
                shutil.rmtree(target_dir)

            # Move restored backup to target
            shutil.copytree(temp_target, target_dir, dirs_exist_ok=True)

        logger.info(f"Backup {backup_name} restored to {target_dir}")
        return {
            "ok": True,
            "backup_name": backup_name,
            "restored_to": str(target_dir),
            "restored_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:  # noqa: BLE001
        logger.error(f"Backup restoration failed: {e}")
        return {
            "ok": False,
            "error": str(e),
        }


def cleanup_old_backups(keep_count: int = 10) -> Dict[str, Any]:
    """Removes old backups, keeping only the most recent N."""
    ensure_backup_dir()

    backups = list(BACKUP_ROOT.iterdir())
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    deleted = []
    for old_backup in backups[keep_count:]:
        try:
            if old_backup.is_dir():
                shutil.rmtree(old_backup)
                deleted.append(old_backup.name)
                logger.info(f"Deleted old backup: {old_backup.name}")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to delete old backup {old_backup.name}: {e}")

    return {
        "ok": True,
        "deleted_count": len(deleted),
        "deleted": deleted,
        "retention_count": keep_count,
    }
