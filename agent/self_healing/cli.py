"""
Self-Healing System CLI
Command-line interface for monitoring and controlling the self-healing system
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .diagnostic_engine import DiagnosticEngine
from .code_analyzer import CodeAnalyzer
from .self_repair import SelfRepairEngine
from .behavior_monitor import BehaviorMonitor
from .constraint_system import ConstraintSystem
from .version_manager import VersionManager
from .health_dashboard import HealthDashboard


class SelfHealingCLI:
    """Command-line interface for self-healing system"""

    def __init__(self):
        self.diagnostic = DiagnosticEngine()
        self.analyzer = CodeAnalyzer()
        self.repair = SelfRepairEngine()
        self.monitor = BehaviorMonitor()
        self.constraints = ConstraintSystem()
        self.version = VersionManager()
        self.dashboard = HealthDashboard()

    def run(self, args=None):
        """Run CLI with arguments"""
        parser = self._build_parser()
        parsed_args = parser.parse_args(args)

        if not hasattr(parsed_args, 'func'):
            parser.print_help()
            return

        parsed_args.func(parsed_args)

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build argument parser"""
        parser = argparse.ArgumentParser(
            description="Self-Healing Code System CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        subparsers = parser.add_subparsers(title="commands")

        # Diagnostics
        diag_parser = subparsers.add_parser("diagnose", help="Run diagnostic scan")
        diag_parser.add_argument("--full", action="store_true", help="Full scan (slower)")
        diag_parser.add_argument("--recent", type=int, default=24, help="Recent hours to check")
        diag_parser.set_defaults(func=self._cmd_diagnose)

        # Repair
        repair_parser = subparsers.add_parser("repair", help="Run repair cycle")
        repair_parser.add_argument("--auto", action="store_true", help="Enable auto-repair")
        repair_parser.add_argument("--dry-run", action="store_true", help="Simulate repairs")
        repair_parser.set_defaults(func=self._cmd_repair)

        # Monitor
        monitor_parser = subparsers.add_parser("monitor", help="Start monitoring")
        monitor_parser.add_argument("--duration", type=int, default=300, help="Monitor duration (seconds)")
        monitor_parser.add_argument("--status", action="store_true", help="Show current status")
        monitor_parser.set_defaults(func=self._cmd_monitor)

        # Constraints
        const_parser = subparsers.add_parser("constraints", help="Check constraints")
        const_parser.add_argument("--check-all", action="store_true", help="Check all constraints")
        const_parser.add_argument("--report", action="store_true", help="Generate report")
        const_parser.add_argument("--fix", action="store_true", help="Auto-fix violations")
        const_parser.set_defaults(func=self._cmd_constraints)

        # Code Analysis
        code_parser = subparsers.add_parser("analyze", help="Analyze code")
        code_parser.add_argument("--file", type=str, help="Analyze specific file")
        code_parser.add_argument("--full", action="store_true", help="Full codebase analysis")
        code_parser.add_argument("--report", action="store_true", help="Generate report")
        code_parser.set_defaults(func=self._cmd_analyze)

        # Version/Rollback
        version_parser = subparsers.add_parser("version", help="Version management")
        version_parser.add_argument("--checkpoint", action="store_true", help="Create checkpoint")
        version_parser.add_argument("--history", action="store_true", help="Show commit history")
        version_parser.add_argument("--rollback", type=str, help="Rollback to commit")
        version_parser.add_argument("--tag", type=str, help="Tag current version")
        version_parser.add_argument("--list-tags", action="store_true", help="List all tags")
        version_parser.set_defaults(func=self._cmd_version)

        # Dashboard
        dash_parser = subparsers.add_parser("dashboard", help="Show health dashboard")
        dash_parser.add_argument("--health", action="store_true", help="Show health score")
        dash_parser.add_argument("--metrics", action="store_true", help="Show metrics")
        dash_parser.add_argument("--html", type=str, help="Generate HTML dashboard")
        dash_parser.set_defaults(func=self._cmd_dashboard)

        # Status
        status_parser = subparsers.add_parser("status", help="System status")
        status_parser.add_argument("--full", action="store_true", help="Full status report")
        status_parser.set_defaults(func=self._cmd_status)

        return parser

    def _cmd_diagnose(self, args):
        """Run diagnostic scan"""
        print("🔍 Running diagnostic scan...")

        result = self.diagnostic.full_diagnostic_scan()

        print(f"\n📊 Diagnostic Results")
        print(f"├─ Timestamp: {result['scan_timestamp']}")
        print(f"├─ Total Issues: {result['total_issues']}")
        print(f"├─ Critical: {result['critical']}")
        print(f"├─ Warnings: {result['warning']}")
        print(f"└─ Info: {result['info']}")

        if args.full:
            print("\n📋 Detailed Issues:")
            for issue in result["issues"]:
                print(f"  ├─ [{issue['severity']}] {issue['issue']}")
                print(f"  │  Category: {issue['category']}")
                print(f"  └─  Details: {issue['details']}")

    def _cmd_repair(self, args):
        """Run repair cycle"""
        print("🔧 Starting repair cycle...")

        if args.dry_run:
            print("   [DRY RUN MODE - No repairs will be applied]")

        result = self.repair.full_repair_cycle()

        print(f"\n✅ Repair Cycle Complete")
        print(f"├─ Diagnostics Found: {result['diagnostics_found']}")
        print(f"├─ Repairs Attempted: {result['repairs_attempted']}")
        print(f"├─ Successful: {result['repairs_successful']}")
        print(f"└─ Failed: {result['repairs_attempted'] - result['repairs_successful']}")

        if result["repairs"]:
            print("\n🔨 Repairs Applied:")
            for repair in result["repairs"][:5]:  # Show first 5
                status = "✓" if repair["status"] == "successful" else "✗"
                print(f"  {status} {repair['type']}")

    def _cmd_monitor(self, args):
        """Start monitoring or show status"""
        if args.status:
            print("📈 System Status")
            report = self.monitor.get_status_report()

            print(f"├─ Health Score: {report['health_score']:.1f}/100")
            print(f"├─ Monitoring: {'Active' if report['is_monitoring'] else 'Inactive'}")
            print(f"├─ Active Alerts: {report['active_alerts']}")
            print(f"├─ Anomalies: {len(report['anomalies_detected'])}")
            print(f"└─ Timestamp: {report['timestamp']}")

            if report["metrics"]:
                print("\n📊 Metrics:")
                for metric, value in report["metrics"].items():
                    print(f"  ├─ {metric}: {value}")

        else:
            print("📍 Starting continuous monitoring...")
            self.monitor.start_monitoring()
            print(f"   Monitoring for {args.duration} seconds...")
            print("   Press Ctrl+C to stop")

            try:
                import time
                time.sleep(args.duration)
            except KeyboardInterrupt:
                print("\n   Stopped by user")
            finally:
                self.monitor.stop_monitoring()

    def _cmd_constraints(self, args):
        """Check and manage constraints"""
        if args.check_all:
            print("✅ Checking all constraints...")
            metrics = self.monitor.collect_metrics()
            result = self.constraints.check_all_constraints(metrics)

            print(f"\n📋 Constraint Status")
            print(f"├─ Total: {result['total_constraints']}")
            print(f"├─ Passed: {result['passed']}")
            print(f"├─ Failed: {result['failed']}")
            print(f"└─ Violations: {len(result['violations'])}")

            if result["violations"]:
                print("\n⚠️  Violations:")
                for v in result["violations"]:
                    print(f"  ├─ [{v['severity'].upper()}] {v['constraint']}")
                    print(f"  │  {v['description']}")
                    print(f"  └─  Value: {v['value']}")

        elif args.fix:
            print("🔧 Auto-fixing constraint violations...")
            metrics = self.monitor.collect_metrics()
            result = self.constraints.check_all_constraints(metrics)

            if result["violations"]:
                fixes = self.constraints.auto_fix_violations()
                print(f"\n✅ Fixes Attempted: {fixes['fixes_attempted']}")
                print(f"   Successful: {fixes['fixes_successful']}")
            else:
                print("   No violations to fix")

        elif args.report:
            print("📊 Constraint Compliance Report")
            report = self.constraints.get_constraint_report()

            print(f"├─ Compliance Score: {report['compliance_score']:.1f}%")
            print(f"├─ Total Constraints: {report['total_constraints']}")
            print(f"├─ Critical Violations: {report['violations_critical']}")
            print(f"└─ Total Violations: {report['violations_total']}")

    def _cmd_analyze(self, args):
        """Analyze code"""
        print("🔍 Analyzing code...")

        if args.file:
            signatures = self.analyzer.get_function_signatures(Path(args.file))
            print(f"\n📝 Functions in {args.file}:")
            for func_name, sig in signatures.items():
                if func_name != "_error":
                    print(f"  ├─ {func_name}({', '.join(sig['args'])})")
                    print(f"  │  Line: {sig['line']}")
                    if sig.get("docstring"):
                        print(f"  │  Doc: {sig['docstring'][:50]}...")

        elif args.full:
            analysis = self.analyzer.analyze_codebase()
            print(f"\n📊 Code Analysis Results")
            print(f"├─ Files Analyzed: {analysis['files_analyzed']}")
            print(f"├─ Total Issues: {analysis['total_issues']}")
            print(f"└─ Issues by Type:")
            for issue_type, count in analysis["issues_by_type"].items():
                print(f"   ├─ {issue_type}: {count}")

        elif args.report:
            report = self.analyzer.get_issue_report()
            print(f"\n📋 Code Quality Report")
            print(f"├─ Files: {report['summary']['files_analyzed']}")
            print(f"├─ Total Issues: {report['summary']['total_issues']}")
            print(f"├─ Critical: {report['summary']['critical']}")
            print(f"└─ Warnings: {report['summary']['warnings']}")

    def _cmd_version(self, args):
        """Manage versions and rollback"""
        if args.checkpoint:
            print("📸 Creating checkpoint...")
            result = self.version.create_checkpoint("Manual checkpoint")

            if "success" in result and result["success"]:
                print(f"✅ Checkpoint created")
                print(f"   Hash: {result['commit_hash'][:7]}")
                print(f"   Message: {result['message']}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")

        elif args.history:
            print("📜 Recent Commits")
            commits = self.version.get_recent_commits(10)

            for commit in commits:
                print(f"  ├─ {commit['hash'][:7]} - {commit['message']}")
                print(f"  │  {commit['timestamp']}")

        elif args.rollback:
            print(f"↩️  Rolling back to {args.rollback}...")
            result = self.version.rollback_to_commit(args.rollback)

            if "success" in result and result["success"]:
                print(f"✅ Rollback successful")
                print(f"   Backup: {result.get('backup_commit', 'N/A')[:7]}")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")

        elif args.tag:
            print(f"🏷️  Tagging as {args.tag}...")
            result = self.version.tag_stable_version(args.tag)

            if "success" in result and result["success"]:
                print(f"✅ Tagged successfully")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")

        elif args.list_tags:
            print("🏷️  Stable Versions")
            tags = self.version.get_all_tags()

            for tag in tags:
                print(f"  ├─ {tag['tag']}")
                print(f"  │  {tag['created']}")

    def _cmd_dashboard(self, args):
        """Show dashboard"""
        if args.health:
            report = self.dashboard.get_comprehensive_health_report()
            score = report["metrics"].get("success_rate_24h", 0)

            emoji = "🟢" if score >= 85 else "🟡" if score >= 70 else "🔴"
            print(f"{emoji} System Health: {score:.1f}%")

        elif args.metrics:
            report = self.dashboard.get_comprehensive_health_report()
            print("📊 Performance Metrics")
            for key, value in report["metrics"].items():
                print(f"  ├─ {key}: {value}")

        elif args.html:
            print("Generating HTML dashboard...")
            html = self.dashboard.get_dashboard_html()

            with open(args.html, "w") as f:
                f.write(html)

            print(f"✅ Dashboard saved to {args.html}")

    def _cmd_status(self, args):
        """Show system status"""
        print("📊 System Status Report\n")

        # Health
        report = self.dashboard.get_comprehensive_health_report()
        health_score = report["metrics"].get("success_rate_24h", 0)
        emoji = "🟢" if health_score >= 85 else "🟡" if health_score >= 70 else "🔴"

        print(f"Health: {emoji} {health_score:.1f}%")

        # Diagnostics
        print(f"\nDiagnostics (24h):")
        print(f"  ├─ Total Issues: {report['diagnostics']['total_24h']}")
        print(f"  ├─ Critical: {report['diagnostics']['critical']}")
        print(f"  └─ Unresolved: {report['diagnostics']['unresolved_critical']}")

        # Repairs
        print(f"\nRepairs (24h):")
        print(f"  ├─ Successful: {report['repairs']['successful']}")
        print(f"  ├─ Failed: {report['repairs']['failed']}")
        print(f"  └─ Recommended: {report['repairs']['recommended']}")

        # Alerts
        print(f"\nAlerts:")
        print(f"  ├─ Active: {report['alerts']['total_active']}")
        print(f"  ├─ High: {report['alerts']['high_severity']}")
        print(f"  └─ Medium: {report['alerts']['medium_severity']}")

        # Metrics
        print(f"\nMetrics:")
        print(f"  ├─ Success Rate: {report['metrics'].get('success_rate_24h', 0):.1f}%")
        print(f"  ├─ Avg Confidence: {report['metrics'].get('avg_confidence', 0):.2f}")
        print(f"  ├─ Decisions: {report['metrics'].get('decisions_24h', 0)}")
        print(f"  └─ Patterns: {report['metrics'].get('total_patterns_learned', 0)}")


def main():
    """Main entry point"""
    cli = SelfHealingCLI()
    cli.run()


if __name__ == "__main__":
    main()
