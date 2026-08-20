"""The ledger's core promise is that a failure cannot be removed. These tests
exist to prove that promise mechanically rather than trusting the docstring."""

from __future__ import annotations

import json

import pytest

from warnetech_curriculum.ledger import (
    GENESIS_HASH,
    Ledger,
    default_ledger_path,
    writable_ledger,
)


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "ledger.jsonl")


def test_empty_ledger_reads_as_empty_and_verifies(ledger):
    assert ledger.entries() == []
    assert ledger.verify() == {"ok": True, "entries": 0, "head": GENESIS_HASH}


def test_append_assigns_sequential_ids_and_chains(ledger):
    first = ledger.record_failure("first failure")
    second = ledger.record_failure("second failure")
    assert (first.seq, second.seq) == (1, 2)
    assert first.prev_hash == GENESIS_HASH
    assert second.prev_hash == first.hash
    assert ledger.verify()["ok"] is True


def test_entry_requires_a_title(ledger):
    with pytest.raises(ValueError, match="title"):
        ledger.record_failure("   ")


def test_unknown_kind_is_rejected(ledger):
    with pytest.raises(ValueError, match="unknown ledger kind"):
        ledger.append(kind="invented", title="x")


def test_ledger_exposes_no_mutation_api(ledger):
    """The absence of these methods is the enforcement mechanism, so assert
    on it -- a future refactor that adds one should fail here loudly."""
    for forbidden in ("delete", "remove", "update", "truncate", "compact", "purge", "edit"):
        assert not hasattr(ledger, forbidden), f"Ledger must never grow a {forbidden}() method"


def test_deleting_an_entry_breaks_the_chain(ledger):
    for i in range(4):
        ledger.record_failure(f"failure {i}")
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    del lines[1]
    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = ledger.verify()
    assert result["ok"] is False
    assert result["broken_at"] == 3
    assert "removed" in result["reason"]


def test_editing_an_entry_in_place_breaks_the_chain(ledger):
    ledger.record_failure("the original wording")
    ledger.record_failure("second")
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace("the original wording", "a quieter wording")
    ledger.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = ledger.verify()
    assert result["ok"] is False
    assert result["broken_at"] == 1
    assert "altered in place" in result["reason"]


def test_reordering_entries_breaks_the_chain(ledger):
    ledger.record_failure("a")
    ledger.record_failure("b")
    lines = ledger.path.read_text(encoding="utf-8").splitlines()
    ledger.path.write_text("\n".join(reversed(lines)) + "\n", encoding="utf-8")
    assert ledger.verify()["ok"] is False


def test_resolution_supersedes_without_removing_the_original(ledger):
    failure = ledger.record_failure("guessed an API", detail="from x import open")
    ledger.record_resolution(failure.id, "repointed at the real module")

    still_there = ledger.by_id(failure.id)
    assert still_there is not None
    assert still_there.title == "guessed an API"
    assert still_there.detail == "from x import open"
    assert ledger.verify()["ok"] is True


def test_timeline_reassembles_the_whole_story(ledger):
    failure = ledger.record_failure("the mistake")
    ledger.record_failure("an unrelated mistake")
    ledger.record_resolution(failure.id, "the fix")

    timeline = ledger.timeline(failure.id)
    assert [e.title for e in timeline] == ["the mistake", "the fix"]


def test_resolving_an_unknown_entry_is_refused(ledger):
    with pytest.raises(ValueError, match="unknown entry"):
        ledger.record_resolution("WL-9999", "fixing a thing that was never recorded")


def test_entries_survive_a_reopen(tmp_path):
    path = tmp_path / "ledger.jsonl"
    Ledger(path).record_failure("written by one handle")
    assert [e.title for e in Ledger(path)] == ["written by one handle"]


def test_blank_lines_are_tolerated(ledger):
    ledger.record_failure("a")
    with ledger.path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n")
    assert len(ledger.entries()) == 1


def test_stored_form_is_canonical_json(ledger):
    ledger.record_failure("a failure")
    payload = json.loads(ledger.path.read_text(encoding="utf-8").strip())
    assert list(payload) == sorted(payload), "keys must be sorted for a stable hash"


def test_default_path_honours_the_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("WARNETECH_CURRICULUM_HOME", str(tmp_path / "elsewhere"))
    assert default_ledger_path() == tmp_path / "elsewhere" / "ledger.jsonl"


def test_writable_ledger_falls_back_when_home_is_unwritable(tmp_path, monkeypatch):
    """A curriculum that crashes the tool it protects has failed at its job."""
    blocked = tmp_path / "blocked"
    blocked.mkdir(mode=0o500)
    monkeypatch.setenv("WARNETECH_CURRICULUM_HOME", str(blocked / "nested"))
    book = writable_ledger()
    book.record_failure("recorded despite a read-only home")
    assert book.verify()["ok"] is True
