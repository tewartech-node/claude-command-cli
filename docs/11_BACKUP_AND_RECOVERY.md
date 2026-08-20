# Backup and Recovery

`warnetech_operator/warnetech_backup_recall.py` implements steps 1-4 of the
recovery protocol in `docs/AI-FIREWALL-COMPLETE-REFERENCE.txt`: export,
store, rehydrate, validate checksums. It has two tiers.

## Local tier

Copies runtime state (`~/.warnetech/state.json`, `logs/`, `tmp/`) into a
timestamped, checksummed backup under `~/.warnetech/backups/`. Source code
is deliberately excluded — git already versions it, and restoring a backup
over the working tree would silently revert committed work.

```bash
warnetech-backup-recall backup              # create
warnetech-backup-recall list                # list
warnetech-backup-recall verify <name>       # re-checksum without restoring
warnetech-backup-recall recall <name>       # restore (prompts unless --yes)
```

`recall` refuses to run if any checksum fails, so a corrupted backup cannot
overwrite good state.

## Offsite tier (S3, client-side encrypted)

Local backups protect against losing state on this machine; they do nothing
if the machine itself is lost, stolen, or its disk fails. The offsite tier
uploads one local backup to S3, sealed under a passphrase before it ever
leaves this process.

```bash
warnetech-backup-recall push-s3 <name> --bucket my-bucket [--region ...]
warnetech-backup-recall pull-s3 <name> --bucket my-bucket [--region ...]
```

Both prompt for the passphrase interactively (`push-s3` asks twice and
refuses on a mismatch, so a typo cannot silently seal a backup under a key
nobody knows; `pull-s3` asks once). Install the `s3` extra first:

```bash
pip install -e ".[s3]"
```

### What is protected, and by what

**Confidentiality of the content** is the passphrase, full stop.
`warnetech_envelope.seal_archive()` — AES-256-GCM, PBKDF2-HMAC-SHA256 at
600,000 iterations, a random salt per object, a version byte, and the
S3 bucket+key bound in as authenticated associated data — seals the backup
before `warnetech_connectors/s3_backup.py` sends a single byte over the
network. AWS, anyone with bucket access, and anyone who intercepts the
upload see only that ciphertext. See `warnetech_envelope/__init__.py`'s
module docstring (the "ARCHIVE FORMAT" section) for exactly how this differs
from the CLI↔server channel envelope and why.

Losing the passphrase means losing the backup — there is no recovery path,
by design. Write it down somewhere that is not this repository.

**What this does *not* hide**: bucket existence, object size, and access
timestamps are visible to AWS regardless of encryption, and are recorded in
any CloudTrail/S3 access logging you have enabled. Encryption is for
confidentiality of *content* against an untrusted or compromised store; it
is not anonymity, and it does not change what a party with lawful authority
over your AWS account, or a valid legal process directed at AWS, can obtain.
Server-side encryption (`SSEAlgorithm: AES256`) is also enabled on the
bucket for defense in depth, but that is AWS encrypting-at-rest for its own
infrastructure, not a substitute for the client-side sealing above.

### Bucket setup

`push-s3` calls `ensure_bucket()` first, which is idempotent (safe to
re-run) and applies, every time:

- **Block Public Access** (all four settings) — the bucket cannot become
  publicly readable through a future misconfigured ACL or policy.
- **Server-side encryption** (`AES256`).
- **Versioning** — an overwrite cannot destroy the prior object outright,
  which matters specifically for a backup store.

### Object-substitution resistance

Two objects sealed under the same passphrase cannot be swapped by an
attacker with S3 write access and still decrypt as if nothing happened:
each seal is bound to its own `bucket/key` as authenticated associated
data, so reading key A's ciphertext back under key B's identity fails
authentication rather than silently returning the wrong plaintext. This is
exercised directly in `tests/connectors/test_s3_backup.py::
test_object_substitution_across_keys_is_rejected` and
`tests/security/test_envelope_archive.py::
test_associated_data_mismatch_is_rejected`.

### Extraction safety

A downloaded backup is a tar archive from the network. `pull_from_s3()`
extracts it through `_safe_extract()`, which rejects any member whose path
would land outside the destination directory and any symlink/hardlink
member, before calling `extractall()`. `tarfile.extractall()` does not
guard against this on every Python version this project supports (the
protective `filter` argument is 3.12+), so a crafted archive is not trusted
just because it round-tripped through this module's own upload path once.
