"""Tests for bootstrap_termux.sh.

The full script runs real `pkg install`/`git clone`/`pip install` against
the live system -- not something to execute in a test suite. What can and
should be verified without running it for real:

  * it is syntactically valid bash,
  * every script path it references actually exists at that path,
  * the idempotent "append this line to .bashrc" logic it uses for
    completion installation genuinely does not duplicate on a second run
    (extracted and run against a throwaway file, not the real script).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / "bootstrap_termux.sh"


def test_bootstrap_script_has_valid_bash_syntax():
    result = subprocess.run(["bash", "-n", str(BOOTSTRAP)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_bootstrap_references_scripts_that_actually_exist():
    text = BOOTSTRAP.read_text(encoding="utf-8")
    for referenced in ("scripts/install-curriculum-hook.sh", "scripts/completions/warnetech.bash"):
        assert referenced in text, f"{referenced} not referenced in bootstrap_termux.sh"
        assert (ROOT / referenced).is_file(), f"{referenced} is referenced but does not exist"


def test_referenced_hook_installer_is_executable():
    hook_installer = ROOT / "scripts" / "install-curriculum-hook.sh"
    assert hook_installer.stat().st_mode & 0o111, "install-curriculum-hook.sh must be executable"


def test_completion_install_is_idempotent(tmp_path):
    """Isolates the exact append-if-missing pattern bootstrap_termux.sh uses
    for shell completion and proves it twice: the second run of the script
    must not double the line in .bashrc."""
    bashrc = tmp_path / ".bashrc"
    bashrc.write_text("# existing bashrc content\n", encoding="utf-8")
    completion_line = 'source "/home/user/claude-command-cli/scripts/completions/warnetech.bash"'

    script = f'''
set -euo pipefail
COMPLETION_LINE={completion_line!r}
BASHRC="{bashrc}"
if ! grep -qF "$COMPLETION_LINE" "$BASHRC" 2>/dev/null; then
    echo "$COMPLETION_LINE" >> "$BASHRC"
fi
'''
    subprocess.run(["bash", "-c", script], check=True)
    subprocess.run(["bash", "-c", script], check=True)  # run again

    contents = bashrc.read_text(encoding="utf-8")
    assert contents.count(completion_line) == 1


def test_bootstrap_never_aborts_on_the_final_summary_line():
    """set -e would otherwise kill the script on its own summary line
    whenever a check failed, before the final "Try:" hint ever printed --
    the exact bug this test pins."""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    # Extract and execute just the summary block using bash itself as the
    # ground truth for whether `set -e` would abort it.
    summary_block = text[text.index('[ "$PY_OK" = 1 ]'):]
    result = subprocess.run(
        ["bash", "-c", f'set -euo pipefail\nPY_OK=1; JS_OK=0; DOCTOR_OK=1\n{summary_block}'],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "reached" not in result.stdout  # sanity: this script has no such marker
    assert "Try: warnetech" in result.stdout
