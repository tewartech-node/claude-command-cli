"""Tests for the curriculum's --fix: computing a confident rename (rules.py)
and applying it safely (autofix.py).

Two-tier design under test: a Finding only carries a `.fix` when exactly
one candidate clearly beats the field (rules._confident_nearest); applying
it is a second, independent safety net (verify-then-splice-then-reparse).
Each test earns its place by exercising one of those guards specifically,
not by re-testing "does it rename a symbol" over and over.
"""

from __future__ import annotations

import pytest

from warnetech_curriculum.autofix import apply_fixes
from warnetech_curriculum.inspector import Inspector
from warnetech_curriculum.rules import _confident_nearest, run_rules


@pytest.fixture
def repo(tmp_path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "engine.py").write_text(
        "class Engine:\n"
        "    def __init__(self):\n"
        "        self.items = []\n"
        "    def reconstruct(self):\n"
        "        return 1\n"
        "\n"
        "def helper(x):\n"
        "    return x\n",
        encoding="utf-8",
    )

    def write(name: str, source: str):
        target = pkg / name
        target.write_text(source, encoding="utf-8")
        return target

    def check(*names):
        inspector = Inspector(tmp_path)
        files = [pkg / n for n in names]
        return run_rules(inspector, files)

    return tmp_path, write, check


# -- _confident_nearest: the decision to auto-apply at all ----------------------


def test_confident_nearest_accepts_a_clear_single_winner():
    assert _confident_nearest("reconstrukt", {"reconstruct", "helper", "items"}) == "reconstruct"


def test_confident_nearest_refuses_a_weak_match():
    assert _confident_nearest("zzz", {"reconstruct", "helper"}) is None


def test_confident_nearest_refuses_a_near_tie():
    """Two candidates close enough in score that picking one is a guess."""
    assert _confident_nearest("cofnig", {"config", "confit"}) is None


def test_confident_nearest_refuses_an_empty_candidate_set():
    assert _confident_nearest("anything", set()) is None


# -- R001: import rename fix -----------------------------------------------------


def test_import_typo_gets_a_confident_fix(repo):
    tmp_path, write, check = repo
    write("bad.py", "from app.engine import Engine, helpr\n")
    findings = [f for f in check("bad.py") if f.rule == "R001"]
    assert len(findings) == 1
    fix = findings[0].fix
    assert fix is not None
    assert (fix.original, fix.replacement) == ("helpr", "helper")


def test_import_of_a_genuinely_absent_name_gets_no_fix(repo):
    """No first-party name is close enough to guess at -- must not fix."""
    tmp_path, write, check = repo
    write("bad.py", "from app.engine import totally_unrelated_nonexistent_thing\n")
    findings = [f for f in check("bad.py") if f.rule == "R001"]
    assert findings[0].fix is None


def test_import_fix_never_touches_an_as_alias(repo):
    """`from x import wrong as local` -- only `wrong` may be replaced; `local`
    is the caller's own name for it and edmust survive untouched."""
    tmp_path, write, check = repo
    write("bad.py", "from app.engine import helpr as h\n")
    findings = [f for f in check("bad.py") if f.rule == "R001"]
    fix = findings[0].fix
    assert fix.original == "helpr"

    summary = apply_fixes(findings, tmp_path)
    fixed_source = (tmp_path / "app" / "bad.py").read_text(encoding="utf-8")
    assert fixed_source == "from app.engine import helper as h\n"
    assert summary["edit_count"] == 1


def test_applying_the_import_fix_resolves_the_finding(repo):
    tmp_path, write, check = repo
    write("bad.py", "from app.engine import helpr\n")
    before = check("bad.py")
    apply_fixes(before, tmp_path)
    after = check("bad.py")
    assert after == []


# -- R002: attribute rename fix --------------------------------------------------


def test_attribute_typo_gets_a_confident_fix(repo):
    tmp_path, write, check = repo
    write("bad.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    e = Engine()\n"
          "    return e.reconstrukt()\n")
    findings = [f for f in check("bad.py") if f.rule == "R002"]
    fix = findings[0].fix
    assert (fix.original, fix.replacement) == ("reconstrukt", "reconstruct")


def test_applying_the_attribute_fix_resolves_the_finding(repo):
    tmp_path, write, check = repo
    write("bad.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    e = Engine()\n"
          "    return e.reconstrukt()\n")
    before = check("bad.py")
    summary = apply_fixes(before, tmp_path)
    assert summary["edit_count"] == 1
    assert check("bad.py") == []


def test_attribute_fix_only_replaces_the_name_after_the_dot(repo):
    tmp_path, write, check = repo
    write("bad.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    e = Engine()\n"
          "    return e.reconstrukt()\n")
    findings = check("bad.py")
    apply_fixes(findings, tmp_path)
    fixed = (tmp_path / "app" / "bad.py").read_text(encoding="utf-8")
    assert "e.reconstruct()" in fixed
    assert "reconstrukt" not in fixed


# -- the real bug this session found, end to end ---------------------------------


def test_the_actual_diagnostics_bug_is_correctly_left_unfixed(repo):
    """warnetech_ai_controller/diagnostics.py imported `open` where the
    module exports `unseal` -- not a typo of it (edit-distance ratio ~0.2),
    but a wrong guess about the module's shape entirely. Auto-fix is a
    typo-correction mechanism, not a mind-reader: it must recognise this
    is NOT a confident rename and leave it for a human, exactly as it
    leaves the module's other three bugs (RetentionEngine.slices,
    GhostEngine.reconstruct, supabase_schema.database) -- none of them
    typos either. Reported, not silently guessed at -- the same standard
    the curriculum holds every other rule to."""
    tmp_path, write, check = repo
    envelope = tmp_path / "app" / "envelope.py"
    envelope.write_text(
        "def unseal(x):\n    return x\n\ndef seal(x):\n    return x\n",
        encoding="utf-8",
    )
    diagnostics = write("diagnostics.py", "from app.envelope import seal, open\n")

    before = check("diagnostics.py")
    r001 = [f for f in before if f.rule == "R001"]
    assert len(r001) == 1
    assert r001[0].fix is None

    summary = apply_fixes(before, tmp_path)
    assert summary["edit_count"] == 0
    assert diagnostics.read_text(encoding="utf-8") == "from app.envelope import seal, open\n"
    assert check("diagnostics.py") == r001  # unresolved, and still reported


# -- apply_fixes: the independent safety net -------------------------------------


def test_apply_fixes_is_a_noop_on_an_empty_finding_list(repo):
    tmp_path, _, _ = repo
    assert apply_fixes([], tmp_path) == {
        "files_changed": [], "edits_applied": [], "skipped": [], "edit_count": 0,
    }


def test_apply_fixes_refuses_a_stale_edit(repo):
    """If the file changed since the edit was computed, the original text
    at that span no longer matches -- the edit must be skipped, not forced
    onto whatever is there now."""
    tmp_path, write, check = repo
    write("bad.py", "from app.engine import helpr\n")
    findings = check("bad.py")

    (tmp_path / "app" / "bad.py").write_text(
        "from app.engine import something_else_entirely\n", encoding="utf-8"
    )

    summary = apply_fixes(findings, tmp_path)
    assert summary["edit_count"] == 0
    assert summary["skipped"]
    assert (tmp_path / "app" / "bad.py").read_text(encoding="utf-8") == (
        "from app.engine import something_else_entirely\n"
    )


def test_apply_fixes_never_writes_a_file_that_would_stop_parsing(repo, monkeypatch):
    """Defense in depth: even if a fix's own arithmetic were wrong, the
    post-edit reparse must catch it and refuse to write."""
    tmp_path, write, check = repo
    write("bad.py", "from app.engine import helpr\n")
    findings = check("bad.py")

    # Corrupt the computed edit to prove the reparse guard actually fires,
    # not merely that a correct edit happens to parse.
    bad_fix = findings[0].fix
    import dataclasses
    corrupted = dataclasses.replace(bad_fix, replacement="def broken(:")
    findings[0] = dataclasses.replace(findings[0], fix=corrupted)

    summary = apply_fixes(findings, tmp_path)
    assert summary["files_changed"] == []
    assert "unparseable" in summary["skipped"][0]["reason"]
    original = (tmp_path / "app" / "bad.py").read_text(encoding="utf-8")
    assert original == "from app.engine import helpr\n"


def test_apply_fixes_handles_two_edits_in_one_file_without_corrupting_offsets(repo):
    tmp_path, write, check = repo
    write("bad.py",
          "from app.engine import Engine\n"
          "def go():\n"
          "    e = Engine()\n"
          "    e.reconstrukt()\n"
          "    return e.reconstrukt()\n")
    findings = check("bad.py")
    r002 = [f for f in findings if f.rule == "R002"]
    assert len(r002) == 2

    summary = apply_fixes(findings, tmp_path)
    assert summary["edit_count"] == 2
    fixed = (tmp_path / "app" / "bad.py").read_text(encoding="utf-8")
    assert fixed.count("reconstruct()") == 2
    assert "reconstrukt" not in fixed


def test_apply_fixes_only_touches_findings_that_have_a_fix(repo):
    tmp_path, write, check = repo
    write("bad.py",
          "from app.engine import totally_unrelated_nonexistent_thing\n"
          "def verify_it():\n"
          "    return True\n")
    findings = check("bad.py")
    assert any(f.fix is None for f in findings)  # R001 (no close name) and R004 both unfixable
    summary = apply_fixes(findings, tmp_path)
    assert summary["edit_count"] == 0
    assert summary["files_changed"] == []
