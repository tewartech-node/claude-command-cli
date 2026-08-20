"""The gate, the seeding, and the terminal surface -- the parts a Termux user
actually touches."""

from __future__ import annotations

import json

import pytest

from warnetech_curriculum.cli import EXIT_BLOCKED, EXIT_ERROR, EXIT_OK, main
from warnetech_curriculum.ledger import Ledger
from warnetech_curriculum.preflight import fingerprint, preflight
from warnetech_curriculum.rules import Finding
from warnetech_curriculum.seed import OPEN_LESSONS, seed


@pytest.fixture
def repo(tmp_path):
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "engine.py").write_text(
        "class Engine:\n    def run(self):\n        return 1\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "ledger.jsonl")


# -- preflight ------------------------------------------------------------------


def test_clean_tree_passes(repo, ledger):
    verdict = preflight(repo, ledger=ledger)
    assert verdict["ok"] is True
    assert verdict["counts"]["critical"] == 0


def test_a_critical_finding_blocks(repo, ledger):
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    verdict = preflight(repo, ledger=ledger)
    assert verdict["ok"] is False
    assert verdict["blocking"]


def test_a_medium_finding_does_not_block(repo, ledger):
    """Only provable non-existence stops the line; wiring gaps inform."""
    server = repo / "warnetech_server"
    server.mkdir()
    (server / "__init__.py").write_text("", encoding="utf-8")
    (server / "routes.py").write_text(
        'def build():\n    router.register("POST", "/orphan", h)\n', encoding="utf-8"
    )
    verdict = preflight(repo, ledger=ledger)
    assert verdict["counts"]["total"] >= 1
    assert verdict["ok"] is True


def test_findings_are_recorded_into_the_ledger(repo, ledger):
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    preflight(repo, ledger=ledger)
    titles = [e.title for e in ledger if e.kind == "failure"]
    assert any("does not export" in t for t in titles)


def test_the_same_finding_is_not_recorded_twice(repo, ledger):
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    preflight(repo, ledger=ledger)
    first = len(ledger.entries())
    preflight(repo, ledger=ledger)
    assert len(ledger.entries()) == first


def test_recording_can_be_declined(repo, ledger):
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    preflight(repo, ledger=ledger, record=False)
    assert ledger.entries() == []


def test_recording_never_breaks_the_chain(repo, ledger):
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    preflight(repo, ledger=ledger)
    assert ledger.verify()["ok"] is True


def test_scoped_runs_skip_whole_repo_rules(repo, ledger):
    """R005 needs the whole tree; judging it from one file would invent
    orphans out of missing context."""
    target = repo / "app" / "engine.py"
    verdict = preflight(repo, paths=[target], ledger=ledger)
    assert verdict["scope"] == "changed"
    assert all(f["rule"] != "R005" for f in verdict["findings"])


def test_fingerprints_are_stable_and_distinct():
    one = Finding("R001", "critical", "a.py", 1, "message")
    same = Finding("R001", "critical", "a.py", 9, "message")
    other = Finding("R001", "critical", "b.py", 1, "message")
    assert fingerprint(one) == fingerprint(same)
    assert fingerprint(one) != fingerprint(other)


# -- seeding ---------------------------------------------------------------------


def test_seed_installs_the_base_curriculum(ledger):
    result = seed(ledger)
    assert len(result["added"]) == result["enforced"] + result["open"]
    assert ledger.verify()["ok"] is True


def test_seed_is_idempotent(ledger):
    seed(ledger)
    before = len(ledger.entries())
    assert seed(ledger)["added"] == []
    assert len(ledger.entries()) == before


def test_seeded_lessons_carry_their_origin(ledger):
    seed(ledger)
    enforced = [e for e in ledger if "enforced" in e.tags]
    assert enforced
    assert all(e.origin.get("commit") for e in enforced)


def test_open_lessons_are_kept_visible_not_hidden(ledger):
    seed(ledger)
    open_ids = {e.id for e in ledger if "open" in e.tags}
    assert open_ids == {lesson["id"] for lesson in OPEN_LESSONS}


# -- cli --------------------------------------------------------------------------


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("WARNETECH_CURRICULUM_HOME", str(tmp_path / "curriculum"))
    monkeypatch.setenv("NO_COLOR", "1")
    return tmp_path


def test_check_exits_zero_on_a_clean_tree(repo, home, capsys):
    code = main(["check", "--root", str(repo), "--no-record"])
    assert code == EXIT_OK
    assert "PASS" in capsys.readouterr().out


def test_check_exits_blocked_on_a_critical_finding(repo, home, capsys):
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    code = main(["check", "--root", str(repo), "--no-record"])
    assert code == EXIT_BLOCKED
    assert "BLOCKED" in capsys.readouterr().out


def test_check_emits_valid_json(repo, home, capsys):
    main(["--json", "check", "--root", str(repo), "--no-record"])
    payload = json.loads(capsys.readouterr().out)
    assert {"ok", "findings", "counts"} <= set(payload)


def test_learn_records_and_reports_permanence(home, capsys):
    assert main(["learn", "a new mistake", "--detail", "what it teaches"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "WL-0001" in out
    assert "never removed" in out


def test_resolve_keeps_the_original(home, capsys):
    main(["learn", "the mistake"])
    capsys.readouterr()
    assert main(["resolve", "WL-0001", "understood"]) == EXIT_OK
    capsys.readouterr()
    main(["--json", "log"])
    entries = json.loads(capsys.readouterr().out)
    assert [e["title"] for e in entries] == ["the mistake", "understood"]


def test_resolve_refuses_an_unknown_id(home, capsys):
    assert main(["resolve", "WL-9999", "x"]) == EXIT_ERROR
    assert "unknown entry" in capsys.readouterr().err


def test_verify_reports_an_intact_chain(home, capsys):
    main(["seed"])
    capsys.readouterr()
    assert main(["verify"]) == EXIT_OK
    assert "INTACT" in capsys.readouterr().out


def test_verify_detects_tampering(home, capsys):
    main(["seed"])
    capsys.readouterr()
    path = home / "curriculum" / "ledger.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    del lines[2]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert main(["verify"]) == EXIT_ERROR
    assert "BROKEN" in capsys.readouterr().out


def test_curriculum_shows_enforced_and_open(home, capsys):
    assert main(["curriculum"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "ENFORCED" in out and "OPEN" in out
    assert "R001" in out


def test_curriculum_json_lists_both_halves(home, capsys):
    main(["--json", "curriculum"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["enforced"] and payload["open"]


def test_log_on_an_empty_ledger_points_at_seed(home, capsys):
    assert main(["log"]) == EXIT_OK
    assert "seed" in capsys.readouterr().out


def test_log_filters_by_kind(home, capsys):
    main(["seed"])
    main(["learn", "a failure"])
    capsys.readouterr()
    main(["--json", "log", "--kind", "failure"])
    entries = json.loads(capsys.readouterr().out)
    assert [e["title"] for e in entries] == ["a failure"]


def test_seed_is_idempotent_through_the_cli(home, capsys):
    main(["seed"])
    capsys.readouterr()
    main(["seed"])
    assert "already installed" in capsys.readouterr().out


def test_packages_lists_first_party(repo, home, capsys):
    assert main(["packages", "--root", str(repo)]) == EXIT_OK
    assert "app" in capsys.readouterr().out


# -- the git-backed pre-commit gate -----------------------------------------------


@pytest.fixture
def git_repo(repo):
    """A real git checkout, so changed_files() is exercised rather than mocked."""
    import subprocess

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        )

    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "test")
    git("add", "-A")
    git("commit", "-qm", "initial")
    return repo, git


def test_changed_files_sees_an_edit_against_head(git_repo):
    from warnetech_curriculum.preflight import changed_files

    repo, _ = git_repo
    (repo / "app" / "new.py").write_text("x = 1\n", encoding="utf-8")
    assert [p.name for p in changed_files(repo)] == ["new.py"]


def test_changed_files_is_empty_on_a_clean_checkout(git_repo):
    from warnetech_curriculum.preflight import changed_files

    repo, _ = git_repo
    assert changed_files(repo) == []


def test_changed_files_degrades_outside_a_checkout(tmp_path):
    """Termux may not have git at all; the gate must not explode."""
    from warnetech_curriculum.preflight import changed_files

    assert changed_files(tmp_path / "not-a-repo") == []


def test_preflight_command_passes_on_a_clean_checkout(git_repo, home, capsys):
    repo, _ = git_repo
    assert main(["preflight", "--root", str(repo)]) == EXIT_OK
    assert "no changed Python files" in capsys.readouterr().out


def test_preflight_command_blocks_a_bad_edit(git_repo, home, capsys):
    repo, _ = git_repo
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    assert main(["preflight", "--root", str(repo)]) == EXIT_BLOCKED
    out = capsys.readouterr().out
    assert "BLOCKED" in out and "do not commit" in out


def test_preflight_command_passes_a_good_edit(git_repo, home, capsys):
    repo, _ = git_repo
    (repo / "app" / "good.py").write_text(
        "from app.engine import Engine\n\n\ndef go():\n    return Engine().run()\n",
        encoding="utf-8",
    )
    assert main(["preflight", "--root", str(repo)]) == EXIT_OK
    assert "PASS" in capsys.readouterr().out


def test_preflight_command_emits_json(git_repo, home, capsys):
    repo, _ = git_repo
    (repo / "app" / "bad.py").write_text("from app.engine import nope\n", encoding="utf-8")
    main(["--json", "preflight", "--root", str(repo)])
    payload = json.loads(capsys.readouterr().out)
    assert payload["scope"] == "changed" and payload["ok"] is False


def test_log_distinguishes_an_empty_ledger_from_an_empty_filter(home, capsys):
    """Telling someone to seed a ledger that already has entries sends them
    the wrong way entirely."""
    main(["seed"])
    capsys.readouterr()

    main(["log", "--id", "WL-DOES-NOT-EXIST"])
    out = capsys.readouterr().out
    assert "no entry WL-DOES-NOT-EXIST" in out
    assert "ledger is empty" not in out

    main(["log", "--kind", "resolution"])
    out = capsys.readouterr().out
    assert "no resolution entries" in out
    assert "ledger is empty" not in out


def test_log_timeline_shows_a_failure_and_its_resolution(home, capsys):
    main(["learn", "the mistake"])
    main(["resolve", "WL-0001", "understood"])
    capsys.readouterr()
    main(["log", "--id", "WL-0001"])
    out = capsys.readouterr().out
    assert "the mistake" in out and "understood" in out


# -- check --fix ---------------------------------------------------------------


def test_check_fix_rewrites_a_typo_and_reports_it(repo, home, capsys):
    (repo / "app" / "bad.py").write_text(
        "from app.engine import Enginee\n", encoding="utf-8"
    )
    code = main(["check", "--root", str(repo), "--no-record", "--fix"])
    out = capsys.readouterr().out
    assert "1 file(s) changed, 1 edit(s) applied" in out
    assert "fixed" in out
    assert code == EXIT_OK
    assert (repo / "app" / "bad.py").read_text(encoding="utf-8") == (
        "from app.engine import Engine\n"
    )


def test_check_without_fix_leaves_the_file_untouched(repo, home, capsys):
    (repo / "app" / "bad.py").write_text(
        "from app.engine import Enginee\n", encoding="utf-8"
    )
    main(["check", "--root", str(repo), "--no-record"])
    assert (repo / "app" / "bad.py").read_text(encoding="utf-8") == (
        "from app.engine import Enginee\n"
    )


def test_check_fix_reports_json_summary(repo, home, capsys):
    (repo / "app" / "bad.py").write_text(
        "from app.engine import Enginee\n", encoding="utf-8"
    )
    main(["--json", "check", "--root", str(repo), "--no-record", "--fix"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["fix"]["edit_count"] == 1
    assert payload["ok"] is True


def test_check_fix_on_an_unfixable_finding_still_reports_it(repo, home, capsys):
    (repo / "app" / "bad.py").write_text(
        "from app.engine import totally_unrelated_nonexistent_name\n", encoding="utf-8"
    )
    code = main(["check", "--root", str(repo), "--no-record", "--fix"])
    out = capsys.readouterr().out
    assert "0 edit(s) applied" in out
    assert code == EXIT_BLOCKED
