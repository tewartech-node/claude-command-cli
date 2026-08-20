"""Encrypted, offsite object storage for Warnetech backups.

Client-side encryption only: every object is sealed with
warnetech_envelope.seal_archive() before it leaves this process, so AWS
holds ciphertext only. Server-side encryption (SSEAlgorithm=AES256) is also
enabled on the bucket, but that protects data at rest inside AWS -- it does
not change what AWS itself, or anyone else with bucket access, can read.
Only the passphrase does that, and this module never sends it anywhere.

boto3 is optional (see the `s3` extra in pyproject.toml), following the
same guarded-import, availability-flag pattern already used for `lz4`,
`zstandard`, and `pyarrow`. A missing dependency degrades every function
here to a soft {"error": ...} return, consistent with every other
connector in this package: a connector failing does not crash the caller.
"""

from __future__ import annotations

from typing import Any, Optional

from warnetech_envelope import EnvelopeError, seal_archive, unseal_archive

from .logging import get_logger, log_error, log_request, log_response
from .utils import now_iso

logger = get_logger(__name__)

try:
    import boto3
    from botocore.exceptions import ClientError

    _BOTO3_AVAILABLE = True
except ImportError:  # pragma: no cover - environment dependent
    boto3 = None  # type: ignore[assignment]
    ClientError = Exception  # type: ignore[assignment,misc]
    _BOTO3_AVAILABLE = False


def _aad(bucket: str, key: str) -> bytes:
    """Binds each sealed object to exactly where it will be stored, so a
    write-access attacker cannot swap two ciphertexts under one passphrase
    and have both still decrypt -- just as the wrong object."""
    return f"{bucket}/{key}".encode("utf-8")


def _client(region: Optional[str] = None):
    if not _BOTO3_AVAILABLE:
        raise RuntimeError("boto3 is required: pip install 'warnetech[s3]'")
    return boto3.client("s3", region_name=region) if region else boto3.client("s3")


def ensure_bucket(bucket: str, region: Optional[str] = None) -> dict[str, Any]:
    """Create a hardened bucket if it does not already exist. Idempotent:
    a bucket this account already owns is treated as success, not an error,
    so `init` can be re-run safely (the pasted script's version could not)."""
    if not _BOTO3_AVAILABLE:
        return {"ok": False, "error": "boto3 not installed; pip install 'warnetech[s3]'"}

    client = _client(region)
    log_request(logger, "s3_backup", "PUT", f"bucket:{bucket}")

    try:
        params: dict[str, Any] = {"Bucket": bucket}
        if region and region != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": region}
        client.create_bucket(**params)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            log_error(logger, "s3_backup", str(exc))
            return {"ok": False, "error": str(exc)}
        # BucketAlreadyExists can also mean someone ELSE owns the name; only
        # BucketAlreadyOwnedByYou is safe to treat as "already set up".
        if code == "BucketAlreadyExists":
            log_error(logger, "s3_backup", f"bucket name '{bucket}' is taken by another account")
            return {"ok": False, "error": f"bucket name '{bucket}' is already taken by another account"}

    try:
        client.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )
        client.put_bucket_encryption(
            Bucket=bucket,
            ServerSideEncryptionConfiguration={
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            },
        )
        # Versioning: an overwrite must not be able to destroy the prior
        # blob outright. This matters specifically for a backup store,
        # where the whole point is not losing a prior good copy.
        client.put_bucket_versioning(Bucket=bucket, VersioningConfiguration={"Status": "Enabled"})
    except ClientError as exc:
        log_error(logger, "s3_backup", str(exc))
        return {"ok": False, "error": str(exc)}

    log_response(logger, "s3_backup", True, 0.0)
    return {"ok": True, "bucket": bucket, "versioning": "Enabled"}


def upload_backup(
    bucket: str, key: str, data: bytes, passphrase: str, region: Optional[str] = None
) -> dict[str, Any]:
    """Seal `data` under `passphrase` and upload it. Never sends the
    passphrase or the plaintext anywhere -- sealing happens before this
    function touches the network."""
    if not _BOTO3_AVAILABLE:
        return {"ok": False, "error": "boto3 not installed; pip install 'warnetech[s3]'"}

    try:
        blob = seal_archive(data, passphrase, associated_data=_aad(bucket, key))
    except EnvelopeError as exc:
        return {"ok": False, "error": str(exc)}

    client = _client(region)
    log_request(logger, "s3_backup", "PUT", f"{bucket}/{key}")
    try:
        response = client.put_object(
            Bucket=bucket, Key=key, Body=blob, ContentType="application/octet-stream"
        )
    except ClientError as exc:
        log_error(logger, "s3_backup", str(exc))
        return {"ok": False, "error": str(exc)}

    log_response(logger, "s3_backup", True, 0.0)
    return {
        "ok": True,
        "bucket": bucket,
        "key": key,
        "bytes_sealed": len(blob),
        "version_id": response.get("VersionId"),
        "uploaded_at": now_iso(),
    }


def download_backup(
    bucket: str, key: str, passphrase: str, region: Optional[str] = None
) -> dict[str, Any]:
    """Download and unseal an object. A wrong passphrase, a tampered or
    substituted object, or a truncated download all come back as a soft
    {"ok": False, "error": ...} -- never a decrypted-looking garbage
    plaintext, because unseal_archive() authenticates before returning."""
    if not _BOTO3_AVAILABLE:
        return {"ok": False, "error": "boto3 not installed; pip install 'warnetech[s3]'"}

    client = _client(region)
    log_request(logger, "s3_backup", "GET", f"{bucket}/{key}")
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        blob = response["Body"].read()
    except ClientError as exc:
        log_error(logger, "s3_backup", str(exc))
        return {"ok": False, "error": str(exc)}

    try:
        data = unseal_archive(blob, passphrase, associated_data=_aad(bucket, key))
    except EnvelopeError as exc:
        log_error(logger, "s3_backup", str(exc))
        return {"ok": False, "error": str(exc)}

    log_response(logger, "s3_backup", True, 0.0)
    return {"ok": True, "bucket": bucket, "key": key, "data": data}
