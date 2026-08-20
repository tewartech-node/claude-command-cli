"""Tests for warnetech_envelope's archive sealing (seal_archive/unseal_archive)
-- the passphrase-protected mode added for long-term storage (S3 backups),
distinct from the API-key channel envelope tested in test_envelope.py.

Every case here corresponds to a bug verified present in the standalone
S3 CLI script this mode replaced: silent empty-passphrase acceptance, no
version byte (an algorithm change would make every prior object
undecryptable with no way to detect which scheme wrote it), and no binding
between a ciphertext and the object identity it was sealed under (an
object-substitution attack, demonstrated exploitable in the original).
"""

from __future__ import annotations

import pytest

from warnetech_envelope import (
    ARCHIVE_MIN_PASSPHRASE_LENGTH,
    ARCHIVE_PBKDF2_ITERATIONS,
    ARCHIVE_SALT_LENGTH,
    ARCHIVE_VERSION,
    IV_LENGTH,
    TAG_LENGTH,
    EnvelopeError,
    derive_archive_key,
    seal_archive,
    unseal_archive,
)

PASSPHRASE = "a genuinely long passphrase"
HEADER_LENGTH = 1 + ARCHIVE_SALT_LENGTH + IV_LENGTH + TAG_LENGTH


def test_round_trip():
    blob = seal_archive(b"hello world", PASSPHRASE)
    assert unseal_archive(blob, PASSPHRASE) == b"hello world"


def test_round_trip_with_associated_data():
    aad = b"my-bucket/repo-data.enc"
    blob = seal_archive(b"hello world", PASSPHRASE, associated_data=aad)
    assert unseal_archive(blob, PASSPHRASE, associated_data=aad) == b"hello world"


def test_empty_plaintext_round_trips():
    blob = seal_archive(b"", PASSPHRASE)
    assert unseal_archive(blob, PASSPHRASE) == b""


def test_wrong_passphrase_is_rejected():
    blob = seal_archive(b"hello world", PASSPHRASE)
    with pytest.raises(EnvelopeError):
        unseal_archive(blob, "a different long passphrase")


def test_associated_data_mismatch_is_rejected():
    """The object-substitution case: sealed for one location, read back
    claiming a different one. Verified exploitable in the pasted script
    that lacked this; must be closed here."""
    blob = seal_archive(b"hello world", PASSPHRASE, associated_data=b"bucket/key-a")
    with pytest.raises(EnvelopeError):
        unseal_archive(blob, PASSPHRASE, associated_data=b"bucket/key-b")


def test_missing_associated_data_is_rejected_if_it_was_sealed_with_some():
    blob = seal_archive(b"hello world", PASSPHRASE, associated_data=b"bucket/key")
    with pytest.raises(EnvelopeError):
        unseal_archive(blob, PASSPHRASE)


@pytest.mark.parametrize("length", [0, 1, 5, 10, 11])
def test_short_passphrases_are_rejected(length):
    assert ARCHIVE_MIN_PASSPHRASE_LENGTH == 12, "test assumes the documented minimum"
    with pytest.raises(EnvelopeError):
        seal_archive(b"data", "x" * length)


def test_minimum_length_passphrase_is_accepted():
    blob = seal_archive(b"data", "x" * ARCHIVE_MIN_PASSPHRASE_LENGTH)
    assert unseal_archive(blob, "x" * ARCHIVE_MIN_PASSPHRASE_LENGTH) == b"data"


def test_version_byte_is_present_and_checked():
    blob = seal_archive(b"data", PASSPHRASE)
    assert blob[0] == ARCHIVE_VERSION

    tampered = bytes([ARCHIVE_VERSION + 1]) + blob[1:]
    with pytest.raises(EnvelopeError, match="unsupported archive version"):
        unseal_archive(tampered, PASSPHRASE)


@pytest.mark.parametrize("length", [0, 1, HEADER_LENGTH - 1])
def test_truncated_blobs_are_rejected_not_crashed_on(length):
    with pytest.raises(EnvelopeError):
        unseal_archive(b"\x00" * length, PASSPHRASE)


def test_tampered_ciphertext_is_rejected():
    blob = bytearray(seal_archive(b"hello world", PASSPHRASE))
    blob[-1] ^= 0xFF
    with pytest.raises(EnvelopeError):
        unseal_archive(bytes(blob), PASSPHRASE)


def test_tampered_tag_is_rejected():
    blob = bytearray(seal_archive(b"hello world", PASSPHRASE))
    tag_start = 1 + ARCHIVE_SALT_LENGTH + IV_LENGTH
    blob[tag_start] ^= 0xFF
    with pytest.raises(EnvelopeError):
        unseal_archive(bytes(blob), PASSPHRASE)


def test_salt_is_random_per_call():
    """The channel envelope's fixed PBKDF2_SALT would be wrong here: many
    objects share one human passphrase, so a fixed salt would mean cracking
    one salt/passphrase pair unlocks every object ever sealed with it."""
    b1 = seal_archive(b"same plaintext", PASSPHRASE)
    b2 = seal_archive(b"same plaintext", PASSPHRASE)
    salt1 = b1[1:1 + ARCHIVE_SALT_LENGTH]
    salt2 = b2[1:1 + ARCHIVE_SALT_LENGTH]
    assert salt1 != salt2
    assert b1 != b2  # different salt -> different derived key -> different ciphertext too


def test_derive_archive_key_is_deterministic_for_a_given_salt():
    salt = b"\x01" * ARCHIVE_SALT_LENGTH
    assert derive_archive_key(PASSPHRASE, salt) == derive_archive_key(PASSPHRASE, salt)
    assert len(derive_archive_key(PASSPHRASE, salt)) == 32


def test_iteration_count_exceeds_the_channel_envelope():
    """Archive material can be attacked offline indefinitely; the channel
    envelope's 100_000 (tuned for a live, rate-limitable connection) is not
    the right number here."""
    from warnetech_envelope import PBKDF2_ITERATIONS

    assert ARCHIVE_PBKDF2_ITERATIONS > PBKDF2_ITERATIONS
    assert ARCHIVE_PBKDF2_ITERATIONS >= 600_000


def test_ciphertext_never_contains_the_plaintext():
    secret = b"the quick brown fox jumps over a very identifiable phrase"
    blob = seal_archive(secret, PASSPHRASE)
    assert secret not in blob
