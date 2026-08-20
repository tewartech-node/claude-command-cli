"""Tests for the S3 offsite tier bolted onto operator backup/recall:
push_to_s3, pull_from_s3, the passphrase prompt, and the tar-extraction
path-traversal guard.

The real warnetech_connectors.s3_backup is replaced with an in-memory fake
throughout -- this suite is about the orchestration in
warnetech_backup_recall.py (archiving, extraction safety, state, exit
codes), not about S3 itself, which tests/connectors/test_s3_backup.py
already covers on its own.
"""

from __future__ import annotations

import io
import json
import tarfile

import pytest

from warnetech_operator import warnetech_backup_recall as br


class _FakeS3Backup:
    """Records what it was asked to do and returns canned/queued results,
    standing in for warnetech_connectors.s3_backup."""

    def __init__(self):
        self.ensure_calls: list[tuple] = []
        self.upload_calls: list[tuple] = []
        self.download_calls: list[tuple] = []
        self.ensure_result = {"ok": True, "bucket": "vault"}
        self.upload_result_ok = True
        self.download_payload: bytes | None = None
        self.download_result_ok = True

    def ensure_bucket(self, bucket, region=None):
        self.ensure_calls.append((bucket, region))
        return dict(self.ensure_result)

    def upload_backup(self, bucket, key, data, passphrase, region=None):
        self.upload_calls.append((bucket, key, data, passphrase, region))
        if not self.upload_result_ok:
            return {"ok": False, "error": "simulated upload failure"}
        return {"ok": True, "bucket": bucket, "key": key, "bytes_sealed": len(data)}

    def download_backup(self, bucket, key, passphrase, region=None):
        self.download_calls.append((bucket, key, passphrase, region))
        if not self.download_result_ok:
            return {"ok": False, "error": "simulated download failure"}
        return {"ok": True, "bucket": bucket, "key": key, "data": self.download_payload}


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    rt = tmp_path / ".warnetech"
    repo = tmp_path / "claude-command-cli"
    (rt / "logs").mkdir(parents=True)
    (rt / "backups").mkdir(parents=True)
    (repo / "warnetech_server").mkdir(parents=True)
    (repo / "warnetech_server" / "app.py").write_text("real source")

    monkeypatch.setattr(br, "RUNTIME", rt)
    monkeypatch.setattr(br, "BACKUP_DIR", rt / "backups")
    monkeypatch.setattr(br, "STATE_FILE", rt / "state.json")
    monkeypatch.setattr(br, "LOG_FILE", rt / "logs" / "backup_recall.log")
    monkeypatch.setattr(br, "_repo_root", lambda: repo)

    (rt / "state.json").write_text(json.dumps(dict(br.DEFAULT_STATE)))
    return {"rt": rt, "repo": repo, "targets": [repo / "warnetech_server", rt / "state.json"]}


@pytest.fixture
def fake_s3(monkeypatch):
    fake = _FakeS3Backup()
    monkeypatch.setattr(br, "_s3_backup_module", lambda: fake)
    return fake


PASSPHRASE = "a genuinely long passphrase"


# -- push_to_s3 ---------------------------------------------------------------


def test_push_seals_and_uploads_a_real_backup(runtime, fake_s3):
    backup_path = br.create_backup(runtime["targets"])
    result = br.push_to_s3(backup_path.name, "vault", PASSPHRASE)

    assert result["ok"] is True
    assert fake_s3.ensure_calls == [("vault", None)]
    assert len(fake_s3.upload_calls) == 1
    bucket, key, data, passphrase, region = fake_s3.upload_calls[0]
    assert (bucket, key, passphrase) == ("vault", f"{backup_path.name}.tar", PASSPHRASE)
    assert data  # the tar archive bytes, not empty


def test_push_of_unknown_backup_raises(runtime, fake_s3):
    with pytest.raises(ValueError, match="not found"):
        br.push_to_s3("does-not-exist", "vault", PASSPHRASE)
    assert fake_s3.ensure_calls == []


def test_push_records_state_on_success(runtime, fake_s3):
    backup_path = br.create_backup(runtime["targets"])
    br.push_to_s3(backup_path.name, "vault", PASSPHRASE)
    state = br.load_state()
    assert state["last_s3_push"]["backup"] == backup_path.name
    assert state["last_s3_push"]["bucket"] == "vault"


def test_push_does_not_record_state_on_upload_failure(runtime, fake_s3):
    fake_s3.upload_result_ok = False
    backup_path = br.create_backup(runtime["targets"])
    result = br.push_to_s3(backup_path.name, "vault", PASSPHRASE)
    assert result["ok"] is False
    assert "last_s3_push" not in br.load_state()


def test_push_stops_before_uploading_if_bucket_setup_fails(runtime, fake_s3):
    fake_s3.ensure_result = {"ok": False, "error": "bucket name taken"}
    backup_path = br.create_backup(runtime["targets"])
    result = br.push_to_s3(backup_path.name, "vault", PASSPHRASE)
    assert result["ok"] is False
    assert fake_s3.upload_calls == []


# -- pull_from_s3 ---------------------------------------------------------------


def _archive_bytes(source_dir_name: str, files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for relpath, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=f"{source_dir_name}/{relpath}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def test_pull_extracts_and_reverifies_checksums(runtime, fake_s3):
    """Pulls the SAME backup name it was (conceptually) pushed under -- the
    S3 key is derived from that name, so push and pull always agree on it.
    Uses push_to_s3's own archiving helper against a renamed copy of a real
    backup, so the fake S3 payload is exactly what a real push would have
    produced -- rather than hand-rolling a tar that might silently diverge
    from what _archive_backup_to_bytes() actually emits (which is what
    happened here originally: hand-rolling it skipped directory items and
    passed against a manifest it could not actually satisfy)."""
    original = br.create_backup(runtime["targets"])

    pulled_name = "backup_from_offsite"
    renamed = br.BACKUP_DIR / pulled_name
    import shutil
    shutil.copytree(original, renamed)
    fake_s3.download_payload = br._archive_backup_to_bytes(renamed)
    shutil.rmtree(renamed)  # pull_from_s3 refuses to overwrite an existing local copy

    result = br.pull_from_s3(pulled_name, "vault", PASSPHRASE)

    assert fake_s3.download_calls == [("vault", f"{pulled_name}.tar", PASSPHRASE, None)]
    assert (br.BACKUP_DIR / pulled_name).exists()
    assert result["ok"] is True
    assert result["verification"]["all_ok"] is True


def test_pull_refuses_to_overwrite_an_existing_local_backup(runtime, fake_s3):
    br.create_backup(runtime["targets"])
    existing_name = br.list_backups()[0]
    with pytest.raises(ValueError, match="already exists"):
        br.pull_from_s3(existing_name, "vault", PASSPHRASE)
    assert fake_s3.download_calls == [(  # still attempted the download itself
        "vault", f"{existing_name}.tar", PASSPHRASE, None
    )]


def test_pull_propagates_a_download_failure_without_touching_disk(runtime, fake_s3):
    fake_s3.download_result_ok = False
    result = br.pull_from_s3("some-backup", "vault", PASSPHRASE)
    assert result["ok"] is False
    assert not (br.BACKUP_DIR / "some-backup").exists()


def test_pull_records_state_on_success(runtime, fake_s3):
    backup_path = br.create_backup(runtime["targets"])
    manifest = json.loads((backup_path / br.MANIFEST_NAME).read_text())
    fake_s3.download_payload = _archive_bytes("restored", {br.MANIFEST_NAME: json.dumps(manifest)})
    br.pull_from_s3("restored", "vault", PASSPHRASE)
    state = br.load_state()
    assert state["last_s3_pull"]["backup"] == "restored"


# -- extraction safety ----------------------------------------------------------


def test_safe_extract_refuses_path_traversal(tmp_path):
    """A crafted archive with a `../` member must not write outside the
    destination directory -- tarfile.extractall() does not guarantee this
    on every Python version this project supports."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        payload = b"malicious"
        info = tarfile.TarInfo(name="../../escaped.txt")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    destination = tmp_path / "safe_dir"
    destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(buffer.getvalue()), mode="r") as archive:
        with pytest.raises(ValueError, match="outside the target directory"):
            br._safe_extract(archive, destination)

    assert not (tmp_path / "escaped.txt").exists()


def test_safe_extract_refuses_symlink_members(tmp_path):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo(name="link")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        archive.addfile(info)

    destination = tmp_path / "safe_dir"
    destination.mkdir()
    with tarfile.open(fileobj=io.BytesIO(buffer.getvalue()), mode="r") as archive:
        with pytest.raises(ValueError, match="link member"):
            br._safe_extract(archive, destination)


def test_safe_extract_allows_a_well_formed_archive(tmp_path):
    destination = tmp_path / "safe_dir"
    destination.mkdir()
    payload = _archive_bytes("backup_1", {"manifest.json": "{}"})
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r") as archive:
        br._safe_extract(archive, destination)
    assert (destination / "backup_1" / "manifest.json").read_text() == "{}"


# -- passphrase prompting --------------------------------------------------------


def test_prompt_confirms_on_write_and_matches(monkeypatch):
    answers = iter(["same-passphrase-value", "same-passphrase-value"])
    monkeypatch.setattr(br.getpass, "getpass", lambda *_a, **_k: next(answers))
    assert br._prompt_passphrase(confirm=True) == "same-passphrase-value"


def test_prompt_rejects_a_mismatched_confirmation(monkeypatch):
    """The exact bug verified in the pasted script: no confirmation meant a
    typo could silently seal a backup under a passphrase nobody knows."""
    answers = iter(["first-value", "different-value"])
    monkeypatch.setattr(br.getpass, "getpass", lambda *_a, **_k: next(answers))
    with pytest.raises(ValueError, match="did not match"):
        br._prompt_passphrase(confirm=True)


def test_prompt_does_not_confirm_on_read(monkeypatch):
    calls = []
    monkeypatch.setattr(br.getpass, "getpass", lambda *_a, **_k: (calls.append(1), "value")[1])
    assert br._prompt_passphrase(confirm=False) == "value"
    assert len(calls) == 1


# -- CLI exit codes ---------------------------------------------------------------


def test_cli_push_s3_exits_nonzero_on_failure(runtime, fake_s3, monkeypatch, capsys):
    """Mirrors the bug found in the pasted standalone script: its catch
    block logged the error and exited 0 regardless."""
    fake_s3.upload_result_ok = False
    monkeypatch.setattr(br, "_prompt_passphrase", lambda confirm: PASSPHRASE)
    backup_path = br.create_backup(runtime["targets"])
    code = br.main(["push-s3", backup_path.name, "--bucket", "vault"])
    assert code == 1


def test_cli_push_s3_exits_zero_on_success(runtime, fake_s3, monkeypatch):
    monkeypatch.setattr(br, "_prompt_passphrase", lambda confirm: PASSPHRASE)
    backup_path = br.create_backup(runtime["targets"])
    code = br.main(["push-s3", backup_path.name, "--bucket", "vault"])
    assert code == 0


def test_cli_pull_s3_exits_nonzero_on_failure(runtime, fake_s3, monkeypatch):
    fake_s3.download_result_ok = False
    monkeypatch.setattr(br, "_prompt_passphrase", lambda confirm: PASSPHRASE)
    code = br.main(["pull-s3", "whatever", "--bucket", "vault"])
    assert code == 1
