# The Warnetech Curriculum

A system that learns from its own failures, and cannot quietly forget them.

The curriculum exists because of a specific, recurring failure in this
repository: code written against an API that was **imagined rather than
read**. `warnetech_ai_controller/diagnostics.py` imported `open` from
`warnetech_envelope` (the export is `unseal`), read `RetentionEngine().slices`
and called `GhostEngine().reconstruct()` (neither exists), and imported
`supabase_schema.database` (no such module). Every one of those is provable
in milliseconds by parsing the source. None of them was parsed. The module
shipped, reported success, and was broken in every single check.

That is the class of mistake this package makes impossible to repeat.

---

## Three principles

**1. Decisions are verified, not guessed.**
Before an action, the rules prove — by parsing the tree with `ast` — that the
modules, symbols and attributes it depends on genuinely exist. Where proof is
unavailable (a star-import, an unresolved base class, a `__getattr__`), the
surface is marked *opaque* and the checker stays silent rather than guessing.
A checker that cries wolf gets switched off, and a switched-off checker
protects nothing.

**2. Nothing is ever deleted.**
Failures are appended to a hash-chained ledger. There is no delete method, no
update method, no compaction. A correction is a *new* entry pointing at the
old one; both stay readable forever. Removing or editing an entry breaks the
chain, and `verify` reports the exact sequence number where it parts.

**3. Every rule traces to a real failure.**
Each rule carries an `origin` — a commit hash or a `file:line` you can go and
read — and a `lesson` explaining what it cost. A rule with no origin has not
been learned, only assumed.

---

## Parameter-free by construction

No model weights. No API key. No network. No clock-dependence. Standard
library only.

This is a deliberate downgrade, and it buys three things:

- **It runs on Termux**, offline, on a phone, with no build toolchain.
- **It is reproducible.** The same tree yields the same verdict everywhere,
  so a finding is an argument you can check, not an opinion you must trust.
- **It cannot be wrong in an interesting way.** `from x import y` either
  resolves or it does not. There is no threshold to tune and no confidence
  score to misread.

It also **never imports the code it judges**. `importlib` would execute
module-level code as a side effect of asking a question about it, and a
checker that runs the code it is checking is not safe to run *before* an
action — which is exactly when it needs to run.

---

## Commands

```bash
warnetech-curriculum curriculum   # what has been learned, enforced and open
warnetech-curriculum check        # verify the whole tree
warnetech-curriculum preflight    # gate: only what changed against HEAD
warnetech-curriculum learn "..."  # record a new failure, permanently
warnetech-curriculum resolve ID   # supersede an entry (original is kept)
warnetech-curriculum log -v       # read the ledger
warnetech-curriculum verify       # prove nothing was removed
warnetech-curriculum seed         # install the pre-installed base curriculum
```

Exit codes: `0` clean, `1` blocking findings, `2` usage error or a broken chain.

`python -m warnetech_curriculum <command>` works identically, for a Termux
install without the console script on `PATH`.

---

## The enforced rules

| Rule | Severity | Learned from |
|------|----------|--------------|
| **R001** imports must resolve | critical | `f0b7781`, `c0bf30c`, `1b1477c` |
| **R002** attributes must exist on the class | critical | `f0b7781` |
| **R003** failures must stay visible | high | `f0b7781` |
| **R004** a guard must be able to fail | critical | `worker/utils/validate.js:146` |
| **R005** declared surface must be reachable | medium | repo scan, 2026-08-20 |

**R003** deserves a note. Every check in the broken diagnostics module caught
its own exception and returned the error as a *string*, so the command
reported success while everything inside it was failing. Swallowing an
exception does not remove the failure; it removes your ability to see it.
The rule accepts an honest failure report (`return {"error": ...}`), a
re-raise, a log call, or an explicit `# noqa: BLE001 - <reason>` — this
codebase already writes exactly that, with a stated reason, and a checker
that cannot be told "yes, deliberately" trains people to disable it wholesale.

**R004** is the one still open in the tree: `verifySignature()` in the Worker
returns `true` unconditionally and `antiTamperCheck()` calls it, so the
anti-tamper path passes forged requests. Its sibling `decryptRequest()` had
the mirror-image bug — it always *threw* — and was fixed. A stub that fails
closed is found in minutes; one that fails open sits for months.

---

## Open lessons

Failures that are recorded and understood but that **no rule catches yet**.
They are kept visible on purpose — an honest backlog beats a clean board.

| ID | Lesson |
|----|--------|
| `WL-OPEN-001` | Documented crypto that was never implemented (ChaCha20-Poly1305, Argon2id) |
| `WL-OPEN-002` | Two crypto implementations silently disagreed on the wire |
| `WL-OPEN-003` | A CLI flag that silently did nothing (`options["dry-run"]` vs `options.dryRun`) |
| `WL-OPEN-004` | The test suite was not protected by CI |
| `WL-OPEN-005` | CLI commands that bypass the server layer entirely |

`warnetech-curriculum curriculum` prints these next to the enforced rules, so
the gap between "we know" and "we check" is always visible.

---

## The ledger

Plain JSON Lines at `~/.warnetech/curriculum/ledger.jsonl` — readable with
`cat`, which matters on a phone. Override with `WARNETECH_CURRICULUM_HOME`.
It sits beside the operator runtime that `warnetech backup` already targets,
so preserving it is one path, not two.

Each entry carries `prev_hash`. The chain is what makes deletion *detectable*
rather than merely disallowed:

```
$ warnetech-curriculum verify
  BROKEN  at entry 3: sequence gap: expected 2, found 3 (an entry was removed)
```

Four kinds of entry: `failure` (something broke), `lesson` (what it teaches),
`resolution` (it is understood now), `note` (bookkeeping). `log --id WL-0001`
reassembles the whole arc of one failure, which is what turns a mistake into
a curriculum entry rather than an embarrassment to be swept away.

---

## How it is wired in

**Pre-commit** — `./scripts/install-curriculum-hook.sh` installs a hook that
runs `preflight` over the files a commit is about to take. Remove it with
`--remove`; bypass once with `git commit --no-verify`. If the curriculum is
not installed the hook gets out of the way rather than blocking your work.

**CI** — `.github/workflows/checks.yml` applies it as a **ratchet**:

- `preflight --since <base>` judges a pull request on the files it actually
  changes, and **blocks**. New work is held to the full curriculum.
- `check` scans the whole tree for the record, and does **not** block.

So the existing debt is visible without taxing every contributor, and it
cannot grow.

---

## Adding a rule

Deliberately two steps, in this order:

```bash
warnetech-curriculum learn "what broke" --detail "why, and what it teaches"
```

Then write the check in `warnetech_curriculum/rules.py` with an `origin`
pointing at that evidence, and give it **two** tests: one proving it fires on
the failure that taught it, and one proving it stays silent on correct code.
The second matters more. When R002 first ran against this repository it
produced 112 findings, of which 99 were false — it was treating every
function's return value as if it were a class instance. The fix was to make
it refuse to answer where it could not know.

The ordering — evidence first, enforcement second — is the point. It keeps
the curriculum honest: every rule traces back to something that actually
happened.
