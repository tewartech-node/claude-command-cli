"""Tests for warnetech_connectors.s3_backup.

No real AWS access, and boto3 need not even be installed (it is optional,
mirroring lz4/zstandard/pyarrow's guarded-import pattern) -- a fake client
stands in for it, so what is under test is this module's own logic:
sealing before upload, unsealing after download, AAD binding to the
object's location, and idempotent bucket setup.
"""

from __future__ import annotations

import pytest

from warnetech_connectors import s3_backup


class _ClientError(Exception):
    def __init__(self, code: str, message: str = "boom"):
        self.response = {"Error": {"Code": code, "Message": message}}
        super().__init__(message)


class _FakeBody:
    def __init__(self, data: bytes):
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakeS3Client:
    """In-memory stand-in for boto3's S3 client, keyed by (bucket, key)."""

    def __init__(self):
        self.buckets: set[str] = set()
        self.objects: dict[tuple[str, str], bytes] = {}
        self.public_access_blocked: set[str] = set()
        self.encryption_configured: set[str] = set()
        self.versioning: dict[str, str] = {}

    def create_bucket(self, Bucket: str, **_kwargs):
        if Bucket in self.buckets:
            raise _ClientError("BucketAlreadyOwnedByYou")
        self.buckets.add(Bucket)

    def put_public_access_block(self, Bucket: str, **_kwargs):
        self.public_access_blocked.add(Bucket)

    def put_bucket_encryption(self, Bucket: str, **_kwargs):
        self.encryption_configured.add(Bucket)

    def put_bucket_versioning(self, Bucket: str, VersioningConfiguration: dict):
        self.versioning[Bucket] = VersioningConfiguration["Status"]

    def put_object(self, Bucket: str, Key: str, Body: bytes, **_kwargs):
        self.objects[(Bucket, Key)] = Body
        return {"VersionId": f"v-{len(self.objects)}"}

    def get_object(self, Bucket: str, Key: str):
        if (Bucket, Key) not in self.objects:
            raise _ClientError("NoSuchKey", "not found")
        return {"Body": _FakeBody(self.objects[(Bucket, Key)])}


@pytest.fixture(autouse=True)
def fake_boto3(monkeypatch):
    """Makes the module behave as if boto3 were installed, backed by the
    fake client above instead of the network."""
    client = _FakeS3Client()
    monkeypatch.setattr(s3_backup, "_BOTO3_AVAILABLE", True)
    monkeypatch.setattr(s3_backup, "ClientError", _ClientError)
    monkeypatch.setattr(s3_backup, "_client", lambda region=None: client)
    return client


PASSPHRASE = "a genuinely long passphrase"


def test_ensure_bucket_creates_and_hardens(fake_boto3):
    result = s3_backup.ensure_bucket("my-bucket")
    assert result["ok"] is True
    assert "my-bucket" in fake_boto3.buckets
    assert "my-bucket" in fake_boto3.public_access_blocked
    assert "my-bucket" in fake_boto3.encryption_configured
    assert fake_boto3.versioning["my-bucket"] == "Enabled"


def test_ensure_bucket_is_idempotent(fake_boto3):
    """The pasted script's CreateBucketCommand threw on a second run;
    this must not."""
    first = s3_backup.ensure_bucket("my-bucket")
    second = s3_backup.ensure_bucket("my-bucket")
    assert first["ok"] is True
    assert second["ok"] is True


def test_ensure_bucket_refuses_a_name_owned_by_someone_else(fake_boto3, monkeypatch):
    def create_bucket(Bucket, **_kwargs):
        raise _ClientError("BucketAlreadyExists")

    monkeypatch.setattr(fake_boto3, "create_bucket", create_bucket)
    result = s3_backup.ensure_bucket("taken-name")
    assert result["ok"] is False
    assert "already taken" in result["error"]


def test_upload_then_download_round_trips(fake_boto3):
    s3_backup.ensure_bucket("vault")
    up = s3_backup.upload_backup("vault", "repo-data.enc", b"top secret bytes", PASSPHRASE)
    assert up["ok"] is True
    assert up["bytes_sealed"] > len(b"top secret bytes")  # header + tag overhead

    down = s3_backup.download_backup("vault", "repo-data.enc", PASSPHRASE)
    assert down["ok"] is True
    assert down["data"] == b"top secret bytes"


def test_object_stored_in_s3_is_ciphertext_not_plaintext(fake_boto3):
    """The point of client-side sealing: what AWS actually holds must not
    contain the plaintext."""
    s3_backup.ensure_bucket("vault")
    s3_backup.upload_backup("vault", "k", b"the secret value", PASSPHRASE)
    stored = fake_boto3.objects[("vault", "k")]
    assert b"the secret value" not in stored


def test_download_with_wrong_passphrase_fails_softly(fake_boto3):
    s3_backup.upload_backup("vault", "k", b"data", PASSPHRASE)
    result = s3_backup.download_backup("vault", "k", "a different long passphrase")
    assert result["ok"] is False
    assert "error" in result


def test_download_of_missing_key_fails_softly(fake_boto3):
    result = s3_backup.download_backup("vault", "does-not-exist", PASSPHRASE)
    assert result["ok"] is False


def test_object_substitution_across_keys_is_rejected(fake_boto3):
    """Two objects sealed under the same passphrase: swapping the S3 keys
    they are read back from must fail, not silently decrypt as the wrong
    object. This is the exact gap the pasted script had -- verified
    exploitable there; must not reproduce here."""
    s3_backup.upload_backup("vault", "key-a", b"prod credentials", PASSPHRASE)
    s3_backup.upload_backup("vault", "key-b", b"attacker chosen", PASSPHRASE)

    swapped_object = fake_boto3.objects[("vault", "key-b")]
    fake_boto3.objects[("vault", "key-a")] = swapped_object

    result = s3_backup.download_backup("vault", "key-a", PASSPHRASE)
    assert result["ok"] is False, "AAD binding should reject a swapped object, not decrypt it"


def test_short_passphrase_is_rejected_before_any_network_call(fake_boto3):
    result = s3_backup.upload_backup("vault", "k", b"data", "short")
    assert result["ok"] is False
    assert ("vault", "k") not in fake_boto3.objects


def test_upload_never_calls_the_network_with_plaintext(fake_boto3, monkeypatch):
    """put_object must only ever be called with sealed bytes."""
    seen = {}
    original = fake_boto3.put_object

    def spy(Bucket, Key, Body, **kwargs):
        seen["body"] = Body
        return original(Bucket, Key, Body, **kwargs)

    monkeypatch.setattr(fake_boto3, "put_object", spy)
    s3_backup.upload_backup("vault", "k", b"never send this raw", PASSPHRASE)
    assert b"never send this raw" not in seen["body"]


def test_functions_degrade_softly_without_boto3(monkeypatch):
    monkeypatch.setattr(s3_backup, "_BOTO3_AVAILABLE", False)
    assert s3_backup.ensure_bucket("x")["ok"] is False
    assert s3_backup.upload_backup("x", "y", b"z", PASSPHRASE)["ok"] is False
    assert s3_backup.download_backup("x", "y", PASSPHRASE)["ok"] is False


def test_two_uploads_of_the_same_plaintext_produce_different_ciphertext(fake_boto3):
    """Random per-object salt/nonce: no ciphertext reuse even for identical
    content, unlike the fixed-salt channel envelope (which is fine for its
    own, different threat model -- see the ARCHIVE FORMAT note)."""
    s3_backup.upload_backup("vault", "a", b"same content", PASSPHRASE)
    s3_backup.upload_backup("vault", "b", b"same content", PASSPHRASE)
    assert fake_boto3.objects[("vault", "a")] != fake_boto3.objects[("vault", "b")]
