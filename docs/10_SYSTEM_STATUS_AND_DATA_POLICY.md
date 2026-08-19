# Warnetech / claude-command-cli — System Status, Scope & Data Policy

**Document date:** 2026-08-19
**Branch described:** `claude/repo-diagnostics-437eix`
**Test status at time of writing:** 284 Python tests passing, 92 JavaScript tests passing, 0 lint errors

> **How to read this document.** Everything below is marked either
> **[LIVE]** (implemented, tested, in the repository today) or
> **[PLANNED]** (designed and agreed, not yet built). Nothing is described
> as a capability unless the code for it exists. Section 9 lists what is
> explicitly *not* implemented, including several items that appear as
> goals elsewhere in the project's own documentation.

---

## 1. Status summary

| Area | State |
| --- | --- |
| Encrypted CLI↔server channel (AES-256-GCM) | **[LIVE]** |
| CLI command set (14 commands) | **[LIVE]** |
| Server route table (17 routes) | **[LIVE]** |
| Three-tier data retention (hot/warm/ghost) | **[LIVE]** |
| Backup, checksum verification, restore | **[LIVE]** |
| Backup-before-mutate guard | **[LIVE]** |
| Takeover safety envelope (classifier, budget, assumptions) | **[LIVE]** |
| Termux + Ubuntu/Debian bootstrap | **[LIVE]** |
| Background daemon / multi-session | **[PLANNED]** |
| Terminal observation (failed commands) | **[PLANNED]** |
| GitHub auto-reconnect | **[PLANNED]** |
| AI "assist" on failure | **[PLANNED]** |

**Today the system observes nothing on your device automatically.** It acts
only when you run a command. The observation layer described in section 7.2
is designed and agreed but not written.

---

## 2. What the system does as a whole

Three layers, per the project architecture:

**Layer 1 — CLI (local, on your device).** A Python command-line tool. Reads
local configuration, seals requests, talks to the server, manages local data
slices, compression, retention and backups.

**Layer 2 — warnetech-server (canonical).** Receives sealed commands,
authenticates them, routes to handlers, coordinates the control-plane, the
AI controller, Supabase and external intelligence connectors, returns sealed
responses.

**Layer 3 — GitHub repository.** Source, documentation and history.

A legacy Cloudflare Worker (`worker/`) exists as a **test harness only**. It
is retained for wire-format regression coverage and is not part of the
canonical path. No new functionality goes there.

### 2.1 Purpose

The system is a security/data-defense toolchain: it slices and compresses
data, tiers it by age, keeps recoverable "ghost" copies, scores and learns
from threat signatures, and coordinates recovery. The CLI is the operator's
interface to that.

---

## 3. What the command-line tool can do

### 3.1 Commands **[LIVE]**

| Command | What it does |
| --- | --- |
| `status` | System status from the server |
| `metrics` | Retrieve system metrics |
| `signatures` | List attack signatures |
| `learn` | Report a true/false-positive outcome to the adaptive model |
| `recover` | Trigger the recovery protocol for an incident |
| `slice` | Create data slices from a file |
| `compress` | Compress data (lz4 / zstd) |
| `ai-query` | Query the AI controller |
| `export` / `import` | Move data in and out |
| `config` | Read and write local configuration |
| `server-ping` | Round-trip latency to the server |
| `db-check` / `db-sync` | Database health and partition/rollup sync |
| `ai-diagnose` | Full 8-check system self-test |

### 3.2 The self-test (`ai-diagnose`) **[LIVE]**

Eight checks: envelope round-trip, server reachability, retention tier
boundaries, ghost reconstruction pipeline, Supabase RPC dry-run parse,
operator backup + checksum, plaintext-rejection probe, configuration
sanity. Checks that cannot run (no server reachable) are reported as
*skipped*, not as failures.

### 3.3 Server routes reachable from the CLI **[LIVE]**

`/status` · `/metrics` · `/signatures` · `/learn` · `/recover` · `/slice` ·
`/compress` · `/ai/query` · `/ai/recall` · `/ghost/create` · `/ghost/recall` ·
`/retention/apply` · `/retention/policy` · `/db/health` · `/db/sync` ·
`/tests/run` · `/tests/results`

---

## 4. Devices it can be installed on

Support is defined by the bootstrap scripts that actually exist in the
repository. Anything not listed here has no install path.

| Target | Script | Architectures |
| --- | --- | --- |
| **Termux on Android** | `bootstrap_termux.sh` | arm64 (aarch64), 32-bit armhf (armv7), x86_64, i686 |
| **Ubuntu / Debian** (native) | `bootstrap_linux.sh` | x86_64, arm64, 32-bit armhf, i386 |
| **Debian/Ubuntu proot-distro inside Termux** | `bootstrap_linux.sh` | same as above |

**Both 32-bit and 64-bit are supported.** On 64-bit (x86_64, arm64) PyPI
ships a prebuilt `cryptography` wheel. On 32-bit (armhf, i386) it does not,
so both scripts install a Rust toolchain unconditionally and `cryptography`
is compiled from source. This is why a first install on a 32-bit device is
substantially slower.

### 4.1 Not supported

iOS, Windows, macOS, and non-apt Linux distributions (Fedora, Arch, Alpine)
have **no bootstrap script**. The Python packages may work on them, but
nothing in this repository installs or tests that, and it should not be
represented as supported.

### 4.2 Requirements

- Python ≥ 3.10 (hard requirement, declared in `pyproject.toml`)
- `cryptography` ≥ 42.0 — **mandatory**, not optional; the encrypted channel
  raises without it
- Node.js — only needed to run the JavaScript test suite
- Optional extras: `lz4` + `zstandard` (compression), `pyarrow` (parquet).
  Absent, the code degrades rather than crashing.

### 4.3 Capability by device

Capability does **not** vary by device or architecture. The same Python
package runs everywhere with the same features. What varies is:

| Factor | Effect |
| --- | --- |
| 32-bit vs 64-bit | Install time only (source build vs wheel) |
| Available RAM | Practical ceiling on slice/compression sizes |
| Available disk | Backup retention depth (see §8) |
| Network reachability | Server-dependent commands skip rather than fail |

---

## 5. Parameters and limits

| Parameter | Default | Where set |
| --- | --- | --- |
| Hot tier age | 3 days | `RetentionPolicy.TIER_CONFIG` |
| Warm tier age | 30 days | `RetentionPolicy.TIER_CONFIG` |
| Ghost tier age / expiry | 365 days | `TIER_CONFIG`, `GhostStore.GHOST_EXPIRATION_DAYS` |
| Hot compression | `lz4` | config `compression_hot` |
| Warm compression | `zstd-medium` | config `compression_warm` |
| Ghost compression | `zstd-max` | config `compression_ghost` |
| Envelope cipher | AES-256-GCM | `warnetech_envelope` |
| Key derivation | PBKDF2-HMAC-SHA256, 100,000 iterations | `warnetech_envelope` |
| IV length | 96 bits (12 bytes), per NIST SP 800-38D | `warnetech_envelope` |
| Max backup size per guarded step | 256 MB | `safeguard.MAX_BACKUP_BYTES` |
| Takeover step budget cap | 5 steps | `takeover.DEFAULT_BUDGET_CAP` |
| Config file permissions | `0600` (owner read/write only) | `Config.save()` |

### 5.1 Local paths

```
~/.warnetech/config.json     configuration, chmod 600
~/.warnetech/backups/        timestamped backups + SHA-256 manifests
~/.warnetech/logs/           operator logs
~/.warnetech/tmp/            scratch
~/.warnetech/state.json      operator state
```

---

## 6. Data retention policy **[LIVE]**

Three tiers, promoted automatically by age:

| Tier | Age | Compression | Purpose |
| --- | --- | --- | --- |
| **Hot** | 0–3 days | lz4 (fast) | Active working data |
| **Warm** | 3–30 days | zstd-medium | Recent history |
| **Ghost** | 30–365 days | zstd-max | Minimal reconstructable archive |

Beyond 365 days data is marked expired. Tier transitions are one-directional
(hot → warm → ghost); data is never demoted back.

**Ghost copies** are heavily compressed partial representations intended to
let a dataset be reconstructed from a small fraction of its original size,
rather than full copies.

> **Known inconsistency (tracked, not silently ignored):** the ghost objects
> produced by the CLI's `GhostStore.create_ghost_copy()` do not carry the
> `system` / `type` / `time_range` fields the reconstruction planner expects,
> so a real ghost copy cannot currently be fed directly into reconstruction.
> `ai-diagnose` reports this as a finding on every run, and a regression test
> keeps it visible.

---

## 7. Privacy, confidentiality and authorization

### 7.1 What is transmitted **[LIVE]**

Every request body leaving the CLI is sealed in the `warnetech_envelope`:

- **AES-256-GCM**, 96-bit random IV per message
- Key derived from your API key by **PBKDF2-HMAC-SHA256, 100,000 iterations**
- **HMAC-SHA256** signature over the sealed payload
- The CLI **refuses to send at all** if no API key is configured — there is
  no plaintext fallback path

The API key itself travels as a `Bearer` header. Because that header is *not*
inside the envelope, the CLI **enforces `https://` for any non-loopback
server** and rejects plain HTTP, which would expose the key in transit.
`http://localhost` is exempt so local development works.

### 7.2 What the tool sees on your device

**Today [LIVE]: nothing automatically.** There is no background process, no
shell hook, no logging of your activity. The tool sees only the arguments of
commands you explicitly run.

**Planned [PLANNED]**, to the scope agreed for this project:

- Captured: **the text of a failed command and its exit code**, nothing more
- **Not** captured: command *output*, successful commands, environment
  variable values, file contents, keystrokes, screen contents
- Stored locally at `~/.warnetech/events.jsonl`
- Transmitted only when you explicitly answer "yes" to an offer of help

This is the narrowest of the options considered, and it was chosen
deliberately: full session transcripts were rejected because they would
capture everything displayed on screen, including secrets.

### 7.3 Secrets

- Secrets live in `~/.warnetech/config.json`, written `chmod 600`
- `Config.to_dict()` **strips every key whose name contains "key"** before
  returning configuration for display or logging
- Secrets are never written to logs by design; logging helpers take
  sanitized structures
- No secret is committed to the repository; all are environment- or
  config-sourced

### 7.4 Authorization

- The server authenticates by API key; the same key derives the channel
  encryption key, so an unauthenticated request cannot even be decrypted
- Signature verification uses **timing-safe comparison** (`hmac.compare_digest`)
- The server rejects unsealed request bodies with `400 envelope_required`;
  `ai-diagnose` actively probes for this and reports a failure if a server
  ever accepts plaintext

### 7.5 Third parties

The CLI transmits to **your own warnetech-server only**. Connectors for
external intelligence services exist server-side and are invoked by the
server, not the CLI. No telemetry or analytics is sent anywhere.

---

## 8. Change safety: backup before delete **[LIVE]**

The governing rule: **if a step is going to delete or overwrite something, a
verified backup of that something exists first, or the step does not run.**

1. **Before** a mutating step, every path it names is copied into a
   timestamped backup with a per-item SHA-256 manifest.
2. The backup is **verified by re-checksum**. If it cannot be made, or fails
   verification, the operation **raises and refuses to proceed** — backup
   failure is never a warning, because the next action would be a delete.
3. **After** the step, before/after checksums are compared, so the record
   reports precisely what was `removed`, `modified`, `created`, or left
   `unchanged`.
4. **Restore** replays the backup to each item's recorded origin path.
   Restore itself refuses on checksum mismatch, so a corrupt backup can never
   overwrite good files.

Recovery uses the existing operator tooling:

```bash
warnetech-backup-recall list
warnetech-backup-recall verify  <backup-name>
warnetech-backup-recall recall  <backup-name> --dry-run
warnetech-backup-recall recall  <backup-name>
```

### 8.1 Limits of the guarantee — stated plainly

- Paths are found by **static parsing of the command**. A command that
  computes its targets at runtime — a shell script, an unexpected glob
  expansion, `find -delete` — can touch files that were never backed up.
  Such commands are classified as requiring approval precisely because the
  guard cannot see into them.
- Backups are **local**, in `~/.warnetech/backups`. They protect against a
  bad edit or a failed step. They do **not** protect against a lost, wiped,
  or stolen device. They are not off-device backups.
- Backups are **not encrypted at rest**. They inherit the file permissions
  of the runtime directory.
- A step whose targets exceed **256 MB** is refused rather than backed up
  silently, to avoid filling a phone's storage.

### 8.2 A real bug this found

Implementing the guard surfaced a latent data-loss bug in the existing
backup module: backup directories were named `backup_<unix_seconds>`, so
two backups taken within the same second landed in the *same* directory and
silently overwrote same-named items. Fixed by adding a collision suffix,
with regression tests in both the operator and CLI suites.

---

## 9. Takeover safety envelope **[LIVE]**

The rules governing any autonomous run. Implemented and tested; **the
executor that would consume these rules is not yet built**, so nothing runs
autonomously today.

- Every command is classified **SAFE** / **NEEDS_APPROVAL** / **BLOCKED**
- **SAFE**: reads, builds, tests, installs, local git bookkeeping
- **NEEDS_APPROVAL** (hard stop): `rm`, `mv`, `sudo`, `chmod`, `git push`,
  `git reset --hard`, raw `curl`/`wget`, `npm publish`, service control
- **BLOCKED** outright: `rm -rf`, `mkfs`, `dd of=/dev/…`, fork bombs
- **Fails closed**: an unrecognised, unparseable, or substitution-containing
  command is never SAFE
- **Stops at the first wall** — it runs the leading safe steps and halts;
  it does not skip a blocked step to reach safe work behind it
- **Budget**: it proposes a number of steps (max 5), you confirm or lower
- **Assumptions**: if the objective was inferred rather than stated, it
  lists its assumptions and **refuses to run until you choose one**

### 9.1 What this is not

**It is not a sandbox.** It reads command lines statically and cannot see
inside what those commands then execute. `make test`, `pytest` and
`python script.py` all classify as SAFE and run whatever their target file
contains. Static classification raises the cost of an accident and catches
the obvious footguns — an `ARG_TRAPS` table exists because `python -c`,
`node -e`, `find -delete`, `sed -i` and `npx` would otherwise ride in on the
safe list — but it does not contain a determined payload. Real containment
requires process isolation, which belongs at the executor.

---

## 10. Not implemented

Listed because other documents in this project describe some of them as
current. They are not.

| Item | Status |
| --- | --- |
| **Argon2id** key derivation | **Not implemented.** PBKDF2-HMAC-SHA256 (100k) is what runs. The project's own principles document names Argon2id as a goal. |
| **ChaCha20-Poly1305** fallback cipher | **Not implemented.** AES-256-GCM only. |
| Data-tier enforcement | Open |
| WORM (write-once) logging | Open |
| Real Cloudflare deployment | Open — `worker/` is a legacy test harness |
| Background daemon | Planned, not built |
| Terminal observation | Planned, not built |
| Multi-session task registry | Planned, not built |
| GitHub auto-reconnect (PAT → device flow) | Planned, not built |
| AI `assist` on failure | Planned, not built — also requires an `NVIDIA_API_KEY` to return real answers |
| Takeover **executor** | Not built — the safety rules exist, nothing consumes them yet |
| Off-device / encrypted backups | Not built |

### 10.1 Code health

- 284 Python tests, 92 JavaScript tests, all passing
- 0 lint errors; ~417 ruff *style* findings remain (type-annotation
  modernisation, import ordering, `datetime.utcnow()` deprecation). None are
  correctness bugs — `ruff --select F` (undefined names, unused imports)
  passes clean.
- No CI is configured on the repository; all verification is local.

---

## 11. Roadmap

1. Shell hook + failed-command event log
2. Daemon under `termux-services` + multi-session task registry
3. GitHub PAT → device-flow reconnect
4. `assist` connector and server route
5. Takeover executor — consuming §8 and §9, refusing anything the classifier
   has not cleared

---

*Generated from the state of the repository on the date above. Every
capability claim here is traceable to code and tests in the branch named at
the top; every gap is listed in section 10.*
