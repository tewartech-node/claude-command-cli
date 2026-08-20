"""Keeps scripts/completions/warnetech.bash honest against the real
argparse subcommands of each of the four console scripts.

The completion script cannot import the parsers itself (it's bash, meant
to be sourced into a user's shell with no Python running), so this is the
other direction: Python introspects each tool's real parser and asserts
every subcommand appears in the completion script's corresponding
variable. Add a subcommand to a parser and forget the completion script,
and this fails the suite -- rather than a completion list that quietly
drifts and stops suggesting the new command forever.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


COMPLETION_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "completions" / "warnetech.bash"


def _subcommands(parser: argparse.ArgumentParser) -> set[str]:
    subparsers_actions = [
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    ]
    assert subparsers_actions, "parser has no subcommands to introspect"
    return set(subparsers_actions[0].choices.keys())


def _completion_variable(name: str) -> set[str]:
    text = COMPLETION_SCRIPT.read_text(encoding="utf-8")
    match = re.search(rf'^{re.escape(name)}="([^"]*)"', text, re.MULTILINE)
    assert match, f"{name} not found in {COMPLETION_SCRIPT}"
    return set(match.group(1).split())


def test_completion_script_exists_and_has_valid_bash_syntax():
    assert COMPLETION_SCRIPT.is_file()
    result = subprocess.run(["bash", "-n", str(COMPLETION_SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_warnetech_cli_subcommands_match_the_real_parser():
    from warnetech_cli.main import create_parser

    assert _subcommands(create_parser()) == _completion_variable("_WARNETECH_CLI_SUBCOMMANDS")


def test_curriculum_subcommands_match_the_real_parser():
    from warnetech_curriculum.cli import build_parser

    assert _subcommands(build_parser()) == _completion_variable("_WARNETECH_CURRICULUM_SUBCOMMANDS")


def test_backup_recall_subcommands_match_the_real_parser():
    from warnetech_operator.warnetech_backup_recall import build_parser

    assert _subcommands(build_parser()) == _completion_variable("_WARNETECH_BACKUP_RECALL_SUBCOMMANDS")


def test_completion_registers_all_four_console_scripts():
    text = COMPLETION_SCRIPT.read_text(encoding="utf-8")
    for tool in ("warnetech", "warnetech-curriculum", "warnetech-backup-recall", "warnetech-doctor"):
        assert re.search(rf"^complete -F \S+ {re.escape(tool)}$", text, re.MULTILINE), tool


def test_completion_actually_completes_a_prefix_in_a_real_shell():
    """End to end: source the script in a real bash and drive its
    programmable-completion function the way bash itself would, rather
    than only checking the file's contents."""
    script = f'''
source "{COMPLETION_SCRIPT}"
COMP_WORDS=(warnetech ai)
COMP_CWORD=1
_warnetech_complete
echo "${{COMPREPLY[@]}}"
'''
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, check=True)
    words = set(result.stdout.split())
    assert words == {"ai-query", "ai-recall", "ai-diagnose"}
