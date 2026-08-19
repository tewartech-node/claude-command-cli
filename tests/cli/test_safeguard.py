"""Tests for warnetech_cli.safeguard -- backup before mutate.

The load-bearing property is the refusal: if a backup cannot be made or
cannot be verified, guard() must raise rather than return, because the
caller's next move is to delete something. A guard that fails open is
worse than no guard at all.

Every test redirects the operator backup module's globals into tmp_path,
so nothing here touches the real ~/.warnetech.
"""

import json

import pytest

from warnetech_cli import safeguard
from warnetech_operator import warnetech_backup_recall as operator_backup


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    """Point the operator backup module at a throwaway runtime."""
    root = tmp_path / "runtime"
    monkeypatch.setattr(operator_backup, "RUNTIME", root)
    monkeypatch.setattr(operator_backup, "BACKUP_DIR", root / "backups")
    monkeypatch.setattr(operator_backup, "STATE_FILE", root / "state.json")
    monkeypatch.setattr(operator_backup, "LOG_FILE", root / "logs" / "test.log")
    return root


@pytest.fixture
def workdir(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    return work


# -- path extraction ----------------------------------------------------------------


def test_extract_paths_finds_existing_arguments(workdir):
    target = workdir / "a.txt"
    target.write_text("hello")
    found = safeguard.extract_paths(f"rm {target}", cwd=workdir)
    assert found == [target]


def test_extract_paths_ignores_flags_and_the_command_name(workdir):
    target = workdir / "a.txt"
    target.write_text("x")
    found = safeguard.extract_paths(f"rm -rf --verbose {target}", cwd=workdir)
    assert found == [target]


def test_extract_paths_resolves_relative_to_cwd(workdir):
    (workdir / "b.txt").write_text("x")
    found = safeguard.extract_paths("rm b.txt", cwd=workdir)
    assert found == [workdir / "b.txt"]


def test_extract_paths_skips_nonexistent(workdir):
    assert safeguard.extract_paths("rm nope.txt", cwd=workdir) == []


def test_extract_paths_survives_unparseable_input(workdir):
    assert safeguard.extract_paths('rm "unbalanced', cwd=workdir) == []


# -- the core guarantee: backup happens first --------------------------------------------


def test_guard_backs_up_before_the_step_runs(runtime, workdir):
    target = workdir / "important.txt"
    target.write_text("original content")

    record = safeguard.guard(f"rm {target}", cwd=workdir)

    assert record.backups, "a backup must exist before the step runs"
    verification = operator_backup.verify_backup(record.backups[0])
    assert verification["all_ok"] is True

    # The backed-up copy holds the original bytes even after the real delete.
    target.unlink()
    stored = operator_backup.BACKUP_DIR / record.backups[0] / "important.txt"
    assert stored.read_text() == "original content"


def test_guard_refuses_when_backup_fails(runtime, workdir, monkeypatch):
    """Fail closed: no backup means no mutation."""
    target = workdir / "a.txt"
    target.write_text("x")

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(operator_backup, "create_backup", boom)
    with pytest.raises(safeguard.SafeguardError, match="refusing to proceed"):
        safeguard.guard(f"rm {target}", cwd=workdir)


def test_guard_refuses_when_verification_fails(runtime, workdir, monkeypatch):
    target = workdir / "a.txt"
    target.write_text("x")

    monkeypatch.setattr(
        operator_backup,
        "verify_backup",
        lambda name: {"backup": name, "all_ok": False, "items": [{"name": "a.txt", "ok": False}]},
    )
    with pytest.raises(safeguard.SafeguardError, match="verification failed"):
        safeguard.guard(f"rm {target}", cwd=workdir)


def test_guard_refuses_oversized_targets(runtime, workdir):
    target = workdir / "big.bin"
    target.write_bytes(b"0" * 2048)
    with pytest.raises(safeguard.SafeguardError, match="exceeds"):
        safeguard.guard(f"rm {target}", cwd=workdir, max_bytes=1024)


def test_guard_on_nothing_existing_is_not_an_error(runtime, workdir):
    """A step that creates rather than destroys still gets a record."""
    record = safeguard.guard("mkdir newdir", cwd=workdir)
    assert record.backups == []
    assert record.pre_state == {}


def test_same_basename_paths_do_not_overwrite_each_other(runtime, workdir):
    """Regression guard: create_backup() stores by basename, so two files
    called config.json must not land in one backup directory."""
    first = workdir / "a"
    second = workdir / "b"
    first.mkdir()
    second.mkdir()
    (first / "config.json").write_text("FIRST")
    (second / "config.json").write_text("SECOND")

    record = safeguard.guard(
        f"rm {first / 'config.json'} {second / 'config.json'}", cwd=workdir
    )

    assert len(record.backups) == 2, "collision must be split across backups"
    stored = [
        (operator_backup.BACKUP_DIR / name / "config.json").read_text()
        for name in record.backups
    ]
    assert sorted(stored) == ["FIRST", "SECOND"]


# -- before/after comparison ----------------------------------------------------------------


def test_compare_reports_removal(runtime, workdir):
    target = workdir / "gone.txt"
    target.write_text("bye")

    record = safeguard.guard(f"rm {target}", cwd=workdir)
    target.unlink()
    safeguard.finalize(record)

    assert record.compare()[str(target)] == "removed"
    assert "removed" in record.summary()


def test_compare_reports_modification(runtime, workdir):
    target = workdir / "edit.txt"
    target.write_text("before")

    record = safeguard.guard(f"sed -i s/x/y/ {target}", cwd=workdir)
    target.write_text("after")
    safeguard.finalize(record)

    assert record.compare()[str(target)] == "modified"


def test_compare_reports_unchanged(runtime, workdir):
    target = workdir / "same.txt"
    target.write_text("static")

    record = safeguard.guard(f"chmod +x {target}", cwd=workdir)
    safeguard.finalize(record)

    assert record.compare()[str(target)] == "unchanged"
    assert record.summary() == "no files changed"


def test_comparison_is_empty_until_finalized(runtime, workdir):
    target = workdir / "a.txt"
    target.write_text("x")
    record = safeguard.guard(f"rm {target}", cwd=workdir)
    assert record.compare() == {}
    assert "pending" in record.summary()


def test_summary_names_the_restore_command(runtime, workdir):
    target = workdir / "a.txt"
    target.write_text("x")
    record = safeguard.guard(f"rm {target}", cwd=workdir)
    target.unlink()
    safeguard.finalize(record)
    assert "warnetech-backup-recall recall" in record.summary()


# -- restore ------------------------------------------------------------------------------------


def test_restore_brings_a_deleted_file_back(runtime, workdir):
    target = workdir / "recovered.txt"
    target.write_text("precious")

    record = safeguard.guard(f"rm {target}", cwd=workdir)
    target.unlink()
    assert not target.exists()

    safeguard.restore(record)
    assert target.exists()
    assert target.read_text() == "precious"


def test_restore_undoes_a_corrupting_edit(runtime, workdir):
    """The stated purpose: a step that damaged its target is reversible."""
    target = workdir / "data.json"
    target.write_text(json.dumps({"good": True}))

    record = safeguard.guard(f"sed -i s/a/b/ {target}", cwd=workdir)
    target.write_text("{{{corrupt")

    safeguard.restore(record)
    assert json.loads(target.read_text()) == {"good": True}


def test_restore_without_a_backup_raises(runtime, workdir):
    record = safeguard.ChangeRecord(command="rm x", paths=[])
    with pytest.raises(safeguard.SafeguardError, match="no backups"):
        safeguard.restore(record)


def test_record_serialises(runtime, workdir):
    target = workdir / "a.txt"
    target.write_text("x")
    record = safeguard.guard(f"rm {target}", cwd=workdir)
    target.unlink()
    safeguard.finalize(record)

    data = record.to_dict()
    assert data["completed"] is True
    assert data["changes"][str(target)] == "removed"
    assert data["backups"]
