"""Tests for warnetech_cli.doctor.

Every check is a small, injection-friendly function -- these tests
monkeypatch exactly the stdlib entry point each check reads (sys.version_info,
os.environ, shutil.which, Path.home) rather than faking a whole environment,
so a single test failure points at exactly one check.
"""

from __future__ import annotations

import json


from warnetech_cli import doctor


# -- individual checks -----------------------------------------------------------


def test_python_version_ok_on_a_supported_version(monkeypatch):
    monkeypatch.setattr(doctor.sys, "version_info", (3, 11, 0, "final", 0))
    result = doctor.check_python_version()
    assert result.status == doctor.OK


def test_python_version_fails_below_the_floor(monkeypatch):
    monkeypatch.setattr(doctor.sys, "version_info", (3, 9, 0, "final", 0))
    result = doctor.check_python_version()
    assert result.status == doctor.FAIL
    assert "3.10" in result.hint


def test_required_dependency_ok_when_importable(monkeypatch):
    monkeypatch.setattr(doctor, "_can_import", lambda name: True)
    assert doctor.check_required_dependency().status == doctor.OK


def test_required_dependency_fails_with_a_termux_specific_hint(monkeypatch):
    monkeypatch.setattr(doctor, "_can_import", lambda name: False)
    result = doctor.check_required_dependency()
    assert result.status == doctor.FAIL
    assert "rust" in result.hint  # the actual Termux build pitfall, named


def test_optional_dependencies_are_warn_free_when_absent(monkeypatch):
    """Missing an optional extra is normal, not a problem -- must be `skip`,
    never `warn` or `fail`."""
    monkeypatch.setattr(doctor, "_can_import", lambda name: False)
    results = doctor.check_optional_dependencies()
    assert len(results) == len(doctor._OPTIONAL_EXTRAS)
    assert all(r.status == doctor.SKIP for r in results)


def test_optional_dependencies_report_ok_when_present(monkeypatch):
    monkeypatch.setattr(doctor, "_can_import", lambda name: True)
    results = doctor.check_optional_dependencies()
    assert all(r.status == doctor.OK for r in results)


def test_git_ok_when_on_path(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: "/usr/bin/git")
    assert doctor.check_git().status == doctor.OK


def test_git_fails_and_hints_pkg_install_on_termux(monkeypatch):
    monkeypatch.setattr(doctor.shutil, "which", lambda name: None)
    monkeypatch.setattr(doctor, "_is_termux", lambda: True)
    result = doctor.check_git()
    assert result.status == doctor.FAIL
    assert "pkg install" in result.hint


def test_envelope_round_trip_skips_without_cryptography(monkeypatch):
    monkeypatch.setattr(doctor, "_can_import", lambda name: False)
    assert doctor.check_envelope_round_trip().status == doctor.SKIP


def test_envelope_round_trip_ok_with_real_crypto():
    """No monkeypatching -- exercises the real warnetech_envelope round trip,
    same as bootstrap_termux.sh's own inline check."""
    result = doctor.check_envelope_round_trip()
    assert result.status == doctor.OK


def test_envelope_round_trip_reports_failure_without_crashing(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("simulated backend failure")

    monkeypatch.setattr(doctor, "_can_import", lambda name: True)
    monkeypatch.setitem(
        __import__("sys").modules, "warnetech_envelope",
        type("FakeModule", (), {"encrypt_data": boom, "decrypt_data": boom})(),
    )
    result = doctor.check_envelope_round_trip()
    assert result.status == doctor.FAIL
    assert "simulated backend failure" in result.message


def test_runtime_directory_warns_when_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor.Path, "home", lambda: tmp_path / "nonexistent-home")
    result = doctor.check_runtime_directory()
    assert result.status == doctor.WARN


def test_runtime_directory_ok_when_writable(tmp_path, monkeypatch):
    (tmp_path / ".warnetech").mkdir()
    monkeypatch.setattr(doctor.Path, "home", lambda: tmp_path)
    assert doctor.check_runtime_directory().status == doctor.OK


def test_runtime_directory_fails_when_unwritable(tmp_path, monkeypatch):
    """Permission bits alone are not a reliable way to simulate this (root,
    which this suite may run as, bypasses them) -- inject the failure
    directly at the write call instead, so the test holds regardless of
    which user is running it."""
    runtime = tmp_path / ".warnetech"
    runtime.mkdir()
    monkeypatch.setattr(doctor.Path, "home", lambda: tmp_path)

    real_write_text = doctor.Path.write_text

    def failing_write_text(self, *args, **kwargs):
        if self.name == ".doctor-write-probe":
            raise PermissionError("simulated: read-only filesystem")
        return real_write_text(self, *args, **kwargs)

    monkeypatch.setattr(doctor.Path, "write_text", failing_write_text)
    result = doctor.check_runtime_directory()
    assert result.status == doctor.FAIL


def test_curriculum_hook_skips_outside_a_checkout(tmp_path, monkeypatch):
    """An explicit `root` always means 'assume this is the repo root, just
    check for a hook' -- SKIP only happens when no root is given and none
    can be found by walking up from cwd, so this drives that path via cwd
    instead of passing root directly."""
    monkeypatch.chdir(tmp_path)
    result = doctor.check_curriculum_hook()
    assert result.status == doctor.SKIP


def test_curriculum_hook_warns_when_absent(tmp_path):
    (tmp_path / ".git" / "hooks").mkdir(parents=True)
    result = doctor.check_curriculum_hook(tmp_path)
    assert result.status == doctor.WARN
    assert "install-curriculum-hook.sh" in result.hint


def test_curriculum_hook_warns_when_a_different_hook_is_installed(tmp_path):
    hooks = tmp_path / ".git" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "pre-commit").write_text("#!/bin/sh\necho unrelated\n", encoding="utf-8")
    result = doctor.check_curriculum_hook(tmp_path)
    assert result.status == doctor.WARN
    assert "not the curriculum's" in result.message


def test_curriculum_hook_ok_when_installed(tmp_path):
    hooks = tmp_path / ".git" / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "pre-commit").write_text("warnetech-curriculum preflight\n", encoding="utf-8")
    assert doctor.check_curriculum_hook(tmp_path).status == doctor.OK


def test_curriculum_ledger_warns_when_none_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("WARNETECH_CURRICULUM_HOME", str(tmp_path / "nope"))
    result = doctor.check_curriculum_ledger()
    assert result.status == doctor.WARN
    assert "seed" in result.hint


def test_curriculum_ledger_ok_when_intact(tmp_path, monkeypatch):
    monkeypatch.setenv("WARNETECH_CURRICULUM_HOME", str(tmp_path))
    from warnetech_curriculum import writable_ledger

    writable_ledger(tmp_path / "ledger.jsonl").record_failure("probe")
    result = doctor.check_curriculum_ledger()
    assert result.status == doctor.OK


def test_curriculum_ledger_fails_when_tampered(tmp_path, monkeypatch):
    monkeypatch.setenv("WARNETECH_CURRICULUM_HOME", str(tmp_path))
    from warnetech_curriculum import writable_ledger

    ledger_path = tmp_path / "ledger.jsonl"
    book = writable_ledger(ledger_path)
    book.record_failure("a")
    book.record_failure("b")
    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    del lines[0]
    ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = doctor.check_curriculum_ledger()
    assert result.status == doctor.FAIL


def test_terminal_skipped_when_not_a_tty(monkeypatch):
    monkeypatch.setattr(doctor.sys.stdout, "isatty", lambda: False)
    assert doctor.check_terminal().status == doctor.SKIP


def test_termux_detected_via_prefix_env(monkeypatch):
    monkeypatch.setenv("PREFIX", "/data/data/com.termux/files/usr")
    assert doctor.check_termux().status == doctor.OK


def test_termux_not_detected_on_a_normal_linux_env(monkeypatch):
    monkeypatch.delenv("PREFIX", raising=False)
    monkeypatch.setenv("HOME", "/root")
    assert doctor.check_termux().status == doctor.SKIP


# -- run_checks orchestration -----------------------------------------------------


def test_run_checks_returns_a_flat_list_including_each_optional_dependency():
    results = doctor.run_checks()
    names = [r.name for r in results]
    assert "python_version" in names
    assert all(f"optional:{m}" in names for m in doctor._OPTIONAL_EXTRAS)


def test_a_raising_check_is_reported_not_propagated(monkeypatch):
    def boom():
        raise RuntimeError("this check is broken")

    monkeypatch.setattr(doctor, "check_git", boom)
    results = doctor.run_checks()
    git_like = [r for r in results if "broken" in r.message]
    assert git_like and git_like[0].status == doctor.FAIL


# -- CLI --------------------------------------------------------------------------


def test_cli_exits_zero_when_nothing_fails(monkeypatch, capsys):
    monkeypatch.setattr(doctor, "run_checks", lambda root=None: [
        doctor.CheckResult("a", doctor.OK, "fine"),
        doctor.CheckResult("b", doctor.WARN, "minor", hint="do X"),
    ])
    assert doctor.main([]) == 0
    out = capsys.readouterr().out
    assert "warning(s), nothing failing" in out


def test_cli_exits_nonzero_when_something_fails(monkeypatch, capsys):
    monkeypatch.setattr(doctor, "run_checks", lambda root=None: [
        doctor.CheckResult("a", doctor.FAIL, "broken", hint="fix it"),
    ])
    assert doctor.main([]) == 1
    out = capsys.readouterr().out
    assert "fix it" in out


def test_cli_json_output_is_valid_and_matches_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(doctor, "run_checks", lambda root=None: [
        doctor.CheckResult("a", doctor.FAIL, "broken"),
    ])
    code = doctor.main(["--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload == [{"name": "a", "status": "fail", "message": "broken", "hint": ""}]
    assert code == 1
