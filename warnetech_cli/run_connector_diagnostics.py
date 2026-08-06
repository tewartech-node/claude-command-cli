"""Executable runner for comprehensive connector diagnostics with backup and AI security integration.

Usage:
    python -m warnetech_cli.run_connector_diagnostics [--backup] [--verify] [--ai-security]

This script:
1. Creates a backup failsafe
2. Runs comprehensive diagnostics
3. Optionally integrates AI security monitoring
4. Generates actionable reports
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from warnetech_cli.connector_ai_security import create_secure_environment
from warnetech_cli.connector_backup import (
    create_backup,
    list_backups,
    verify_backup,
)
from warnetech_cli.connector_diagnostics import run_full_diagnostics
from warnetech_connectors.logging import get_logger
from warnetech_connectors.config import DEFAULT_CONFIG

logger = get_logger(__name__)


def print_report(title: str, data: Any, indent: int = 0) -> None:
    """Pretty-prints diagnostic report data."""
    prefix = " " * indent
    if isinstance(data, dict):
        print(f"{prefix}{title}:")
        for key, value in data.items():
            if key.startswith("_"):
                continue
            print_report(key, value, indent + 2)
    elif isinstance(data, (list, tuple)):
        print(f"{prefix}{title}: ({len(data)} items)")
        for i, item in enumerate(data[:5]):  # Show first 5
            print_report(f"[{i}]", item, indent + 2)
        if len(data) > 5:
            print(f"{prefix}  ... and {len(data) - 5} more")
    elif isinstance(data, bool):
        symbol = "✓" if data else "✗"
        print(f"{prefix}{symbol} {title}: {data}")
    else:
        print(f"{prefix}{title}: {data}")


def main() -> int:
    """Main diagnostic runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive connector diagnostics with backup and AI security"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before diagnostics",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing backups",
    )
    parser.add_argument(
        "--ai-security",
        action="store_true",
        help="Enable AI security monitoring",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write report to file (JSON format)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("CONNECTOR DIAGNOSTIC SUITE")
    print("=" * 80)
    print()

    report: Dict[str, Any] = {}

    # Step 1: Create backup if requested
    if args.backup:
        print("📦 Creating backup failsafe...")
        print("-" * 80)
        connectors_dir = Path(__file__).parent.parent / "warnetech_connectors"
        backup_result = create_backup(
            connectors_dir,
            reason="pre-diagnostic-failsafe",
            config=DEFAULT_CONFIG,
        )
        print_report("Backup Result", backup_result)
        report["backup"] = backup_result
        print()

    # Step 2: List and verify existing backups
    if args.verify:
        print("🔍 Verifying existing backups...")
        print("-" * 80)
        backups = list_backups()
        print_report("Available Backups", backups)

        for backup in backups.get("backups", [])[:3]:  # Verify latest 3
            print(f"\nVerifying: {backup['name']}")
            verification = verify_backup(backup["name"])
            print_report("Verification Result", verification)

        print()

    # Step 3: Run diagnostics
    print("🔧 Running comprehensive diagnostics...")
    print("-" * 80)
    diagnostics = run_full_diagnostics(DEFAULT_CONFIG)
    print_report("Diagnostic Results", diagnostics)
    report["diagnostics"] = diagnostics
    print()

    # Step 4: AI Security Integration
    if args.ai_security:
        print("🤖 Initializing AI-integrated security environment...")
        print("-" * 80)
        secure_env = create_secure_environment(DEFAULT_CONFIG)
        print_report("Secure Environment", {
            k: v for k, v in secure_env.items() if k != "auditor"
        })
        report["ai_security"] = {
            k: v for k, v in secure_env.items() if k != "auditor"
        }
        print()

    # Step 5: Summary and recommendations
    print("=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print()

    if "diagnostics" in report:
        diag = report["diagnostics"]
        summary = diag.get("summary", {})
        print(f"Total Checks: {summary.get('total_checks', 'N/A')}")
        print(f"Passed: {summary.get('passed', 0)}")
        print(f"Failed: {summary.get('failed', 0)}")
        print(f"Skipped: {summary.get('skipped', 0)}")

        if summary.get("failed", 0) > 0:
            print(f"\nFailed Checks: {', '.join(summary.get('failed_checks', []))}")
            print("\n⚠️  Action Required:")
            print("  1. Review failed check details above")
            print("  2. Verify connector configuration")
            print("  3. Check network connectivity to endpoints")
            print("  4. Validate API credentials")
        else:
            print("\n✅ All checks passed!")

    # Step 6: Save report if requested
    if args.output:
        output_file = Path(args.output)
        output_file.write_text(json.dumps(report, indent=2))
        print(f"\n📄 Report saved to: {output_file}")

    print()
    print("=" * 80)

    # Determine exit code
    if "diagnostics" in report:
        return 0 if report["diagnostics"].get("overall_ok") else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
