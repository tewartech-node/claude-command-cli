"""Canonical Warnetech AES-256-GCM request/response envelope.

Single source of truth for the wire format, shared by the Python CLI
(warnetech_cli.server_client) and the server (warnetech_server.middleware).
Neither owns it: it is the protocol between them.

WIRE FORMAT
    base64( iv(12) || ciphertext || tag(16) )

  * 96-bit IV per NIST SP 800-38D.
  * The tag trails the ciphertext because WebCrypto's subtle.encrypt does not
    expose it separately, so this is the only layout every runtime can emit.

KEY DERIVATION
    PBKDF2-HMAC-SHA256(api_key, salt=b"claude-command-cli", 100_000) -> 32 bytes

These parameters are byte-compatible with worker/utils/crypto.js and
warnetech_cli_legacy/crypto.js. Changing any of them breaks every client, so
they are pinned here and asserted by the cross-language tests in
tests/security/test_envelope_interop.py.

NOTE ON THE ITERATION COUNT: 100_000 is deliberately NOT the 480_000 used by
warnetech_cli.security.SecurityManager. That module is a separate, unwired
local-storage path (see its docstring); this one must match the JavaScript
implementations byte for byte, and raising it here would break them.

ARCHIVE FORMAT (seal_archive / unseal_archive)
    version(1) || salt(16) || iv(12) || tag(16) || ciphertext

A second, deliberately different sealing mode, for a different threat model:
long-term storage (e.g. an offsite backup) protected by a human-chosen
passphrase rather than a per-session API key. It is *not* a second crypto
implementation — see CLAUDE.md's "never add a second implementation" rule —
it is this module's existing AES-256-GCM primitive (`aes_gcm_encrypt`), used
with parameters that fit its own threat model instead of the CLI/Worker
channel's:

  * RANDOM per-object salt, not the fixed PBKDF2_SALT above. The channel's
    fixed salt is safe there because the derived key is single-purpose and
    the "password" is a high-entropy API key; reusing one salt across many
    objects protected by the same *human* passphrase would mean a single
    cracked salt/passphrase pair unlocks every object ever sealed with it.
  * A VERSION byte prefixes the blob. The channel envelope has no such byte
    because both ends are always running matched code from this repository;
    an archive can outlive the code that wrote it, so unseal_archive() can
    refuse a blob from a future format instead of misreading it.
  * ARCHIVE_PBKDF2_ITERATIONS (600_000) is higher than the channel's 100_000:
    OWASP's current PBKDF2-HMAC-SHA256 guidance, appropriate for a
    passphrase an attacker can attempt offline indefinitely against a stolen
    blob, as opposed to a live, rate-limitable network channel.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

__all__ = [
    "IV_LENGTH",
    "TAG_LENGTH",
    "PBKDF2_ITERATIONS",
    "PBKDF2_SALT",
    "EnvelopeError",
    "aes_gcm_encrypt",
    "aes_gcm_decrypt",
    "derive_key",
    "encrypt_data",
    "decrypt_data",
    "generate_hmac_signature",
    "verify_hmac_signature",
    "seal",
    "unseal",
    "is_envelope",
    "ARCHIVE_VERSION",
    "ARCHIVE_SALT_LENGTH",
    "ARCHIVE_PBKDF2_ITERATIONS",
    "ARCHIVE_MIN_PASSPHRASE_LENGTH",
    "derive_archive_key",
    "seal_archive",
    "unseal_archive",
]

IV_LENGTH = 12
TAG_LENGTH = 16
KEY_LENGTH = 32
PBKDF2_ITERATIONS = 100_000
PBKDF2_SALT = b"claude-command-cli"

# -- archive sealing (passphrase-protected, long-term storage) --------------

ARCHIVE_VERSION = 1
ARCHIVE_SALT_LENGTH = 16
ARCHIVE_PBKDF2_ITERATIONS = 600_000
ARCHIVE_MIN_PASSPHRASE_LENGTH = 12
_ARCHIVE_HEADER_LENGTH = 1 + ARCHIVE_SALT_LENGTH + IV_LENGTH + TAG_LENGTH


class EnvelopeError(RuntimeError):
    """Raised when an envelope cannot be produced or opened."""


def _aesgcm(key: bytes):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise EnvelopeError(
            "the 'cryptography' package is required: pip install cryptography"
        ) from exc
    return AESGCM(key)


def aes_gcm_encrypt(
    key: bytes, plaintext: bytes, associated_data: bytes | None = None
) -> tuple[bytes, bytes]:
    """Low-level primitive: returns (nonce, ciphertext_with_tag).

    Used for at-rest encryption (see warnetech_control_plane.slice_engine),
    where the nonce is stored alongside the ciphertext rather than prefixed
    to it. The channel envelope uses :func:`encrypt_data` instead.
    """
    nonce = os.urandom(IV_LENGTH)
    return nonce, _aesgcm(key).encrypt(nonce, plaintext, associated_data)


def aes_gcm_decrypt(
    key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes | None = None
) -> bytes:
    """Inverse of :func:`aes_gcm_encrypt`."""
    return _aesgcm(key).decrypt(nonce, ciphertext, associated_data)


def derive_key(api_key: str) -> bytes:
    """Derive the 256-bit channel key from the API key."""
    return hashlib.pbkdf2_hmac(
        "sha256", api_key.encode("utf-8"), PBKDF2_SALT, PBKDF2_ITERATIONS, dklen=KEY_LENGTH
    )


def encrypt_data(plaintext: str, api_key: str) -> str:
    """Encrypt a UTF-8 string, returning base64 of iv || ciphertext+tag."""
    iv = os.urandom(IV_LENGTH)
    ct_with_tag = _aesgcm(derive_key(api_key)).encrypt(iv, plaintext.encode("utf-8"), None)
    return base64.b64encode(iv + ct_with_tag).decode("ascii")


def decrypt_data(payload: str, api_key: str) -> str:
    """Reverse of :func:`encrypt_data`. Raises EnvelopeError on any failure."""
    try:
        combined = base64.b64decode(payload, validate=True)
    except Exception as exc:
        raise EnvelopeError(f"Decryption failed: malformed base64: {exc}") from exc

    if len(combined) <= IV_LENGTH + TAG_LENGTH:
        raise EnvelopeError("Decryption failed: packet too short")

    iv, ct_with_tag = combined[:IV_LENGTH], combined[IV_LENGTH:]
    try:
        return _aesgcm(derive_key(api_key)).decrypt(iv, ct_with_tag, None).decode("utf-8")
    except EnvelopeError:
        raise
    except Exception as exc:
        raise EnvelopeError(f"Decryption failed: {exc}") from exc


def _canonical_json(payload: Any) -> str:
    """Serialise the way JSON.stringify does.

    Python's json.dumps defaults to ', ' and ': ' separators; JavaScript emits
    none. The HMAC is taken over these bytes, so a mismatch here silently
    invalidates every signature crossing the language boundary.
    """
    return json.dumps(payload, separators=(",", ":"))


def generate_hmac_signature(payload: Any, secret: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), _canonical_json(payload).encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_hmac_signature(payload: Any, signature: str, secret: str) -> bool:
    return hmac.compare_digest(generate_hmac_signature(payload, secret), signature)


def seal(body: Any, api_key: str) -> dict:
    """Wrap a JSON-serialisable body into a signed encrypted envelope."""
    encrypted = encrypt_data(_canonical_json(body), api_key)
    return {
        "encrypted_data": encrypted,
        "signature": generate_hmac_signature({"encrypted_data": encrypted}, api_key),
    }


def unseal(envelope: dict, api_key: str) -> Any:
    """Verify and open an envelope produced by :func:`seal`."""
    if not is_envelope(envelope):
        raise EnvelopeError("not an envelope: missing 'encrypted_data'")

    encrypted = envelope["encrypted_data"]
    signature = envelope.get("signature")
    if signature is not None and not verify_hmac_signature(
        {"encrypted_data": encrypted}, signature, api_key
    ):
        raise EnvelopeError("Decryption failed: signature mismatch")

    return json.loads(decrypt_data(encrypted, api_key))


def is_envelope(body: Any) -> bool:
    return isinstance(body, dict) and isinstance(body.get("encrypted_data"), str)


def derive_archive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key for archive sealing. See the ARCHIVE FORMAT note
    at the top of this module for why the salt is random per call rather
    than the channel envelope's fixed PBKDF2_SALT."""
    return hashlib.pbkdf2_hmac(
        "sha256", passphrase.encode("utf-8"), salt, ARCHIVE_PBKDF2_ITERATIONS, dklen=KEY_LENGTH
    )


def seal_archive(plaintext: bytes, passphrase: str, associated_data: bytes | None = None) -> bytes:
    """Seal raw bytes for long-term, passphrase-protected storage.

    `associated_data` should bind the ciphertext to where it will live (e.g.
    b"bucket/key") when the caller can supply one. AES-GCM authenticates but
    does not otherwise "know" where a blob is stored, so without this an
    attacker with write access to the store can swap two ciphertexts sealed
    under the same passphrase and both will still decrypt -- just as the
    wrong object. Binding the location closes that.
    """
    if len(passphrase) < ARCHIVE_MIN_PASSPHRASE_LENGTH:
        raise EnvelopeError(
            f"passphrase must be at least {ARCHIVE_MIN_PASSPHRASE_LENGTH} characters"
        )
    salt = os.urandom(ARCHIVE_SALT_LENGTH)
    key = derive_archive_key(passphrase, salt)
    nonce, ct_with_tag = aes_gcm_encrypt(key, plaintext, associated_data)
    # cryptography's AESGCM appends the tag to the ciphertext; split it out
    # so the on-disk layout documented above (tag before ciphertext) holds.
    ciphertext, tag = ct_with_tag[:-TAG_LENGTH], ct_with_tag[-TAG_LENGTH:]
    return bytes([ARCHIVE_VERSION]) + salt + nonce + tag + ciphertext


def unseal_archive(blob: bytes, passphrase: str, associated_data: bytes | None = None) -> bytes:
    """Reverse of :func:`seal_archive`. Raises EnvelopeError on any failure,
    including a bad passphrase, a truncated blob, or an unrecognised version
    byte -- an archive is expected to outlive the code that wrote it, so a
    future format is reported rather than misread."""
    if len(blob) < _ARCHIVE_HEADER_LENGTH:
        raise EnvelopeError("archive too short to contain a header")

    version = blob[0]
    if version != ARCHIVE_VERSION:
        raise EnvelopeError(
            f"unsupported archive version {version}; this build understands version {ARCHIVE_VERSION}"
        )

    offset = 1
    salt = blob[offset:offset + ARCHIVE_SALT_LENGTH]
    offset += ARCHIVE_SALT_LENGTH
    nonce = blob[offset:offset + IV_LENGTH]
    offset += IV_LENGTH
    tag = blob[offset:offset + TAG_LENGTH]
    offset += TAG_LENGTH
    ciphertext = blob[offset:]

    key = derive_archive_key(passphrase, salt)
    try:
        return aes_gcm_decrypt(key, nonce, ciphertext + tag, associated_data)
    except Exception as exc:
        raise EnvelopeError(f"archive decryption failed: {exc}") from exc
