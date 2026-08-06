"""
Security Module
Handles encryption, decryption, and key derivation using AES-256-GCM.

WIRE FORMAT WARNING — this module is NOT interoperable with the Cloudflare
Worker. It emits iv(16) || ciphertext+tag, while the canonical channel format
shared by worker/utils/crypto.js and warnetech_cli_legacy/crypto.js is
iv(12) || ciphertext+tag. Do not wire this to the Worker without converting.

Currently unused: the only importer is warnetech_cli/commands.py, which never
calls it, and warnetech_cli/server_client.py does not encrypt request bodies.
"""

import hashlib
import os
from typing import Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class SecurityManager:
    """Manages encryption, decryption, and key derivation."""

    # OWASP-recommended minimum for PBKDF2-HMAC-SHA256.
    PBKDF2_ITERATIONS = 480000
    SALT_LENGTH = 16
    IV_LENGTH = 16
    TAG_LENGTH = 16

    def __init__(self):
        """Initialize security manager."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library is required for security features")

    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.

        Args:
            password: Password string
            salt: Salt bytes (generated if not provided)

        Returns:
            Tuple of (key, salt)
        """
        if salt is None:
            salt = os.urandom(SecurityManager.SALT_LENGTH)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=SecurityManager.PBKDF2_ITERATIONS,
            backend=default_backend(),
        )

        key = kdf.derive(password.encode())
        return key, salt

    @staticmethod
    def encrypt_data(data: bytes, key: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        Args:
            data: Data to encrypt
            key: Encryption key (32 bytes)

        Returns:
            IV + ciphertext + tag (concatenated)
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes (256-bit)")

        iv = os.urandom(SecurityManager.IV_LENGTH)
        cipher = AESGCM(key)

        ciphertext = cipher.encrypt(iv, data, None)

        return iv + ciphertext

    @staticmethod
    def decrypt_data(encrypted: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Args:
            encrypted: IV + ciphertext + tag
            key: Encryption key (32 bytes)

        Returns:
            Decrypted data
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes (256-bit)")

        iv = encrypted[: SecurityManager.IV_LENGTH]
        ciphertext = encrypted[SecurityManager.IV_LENGTH :]

        cipher = AESGCM(key)

        try:
            plaintext = cipher.decrypt(iv, ciphertext, None)
            return plaintext
        except Exception as e:
            raise RuntimeError(f"Decryption failed: {e}")

    @staticmethod
    def hash_key(key: str) -> str:
        """
        Hash an API key using SHA-256.

        Args:
            key: API key string

        Returns:
            Hex-encoded SHA-256 hash
        """
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def generate_slice_key(slice_id: str, master_key: bytes) -> bytes:
        """
        Generate a unique key for a slice using HMAC.

        Args:
            slice_id: Slice identifier
            master_key: Master encryption key

        Returns:
            Slice-specific key (32 bytes)
        """
        import hmac

        h = hmac.new(master_key, slice_id.encode(), hashlib.sha256)
        return h.digest()
