# The Termux / CLI Interface

Four console scripts, all installed by `pip install -e .`:

| Command | What it is |
|---|---|
| `warnetech` | The canonical CLI (`warnetech_cli/main.py`). Previously reachable only via `python -m warnetech_cli.main` — it had no console script of its own. |
| `warnetech-curriculum` | Preflight + failure ledger. See `docs/10_CURRICULUM.md`. |
| `warnetech-backup-recall` | Local backup/recall plus the S3 offsite tier. See `docs/11_BACKUP_AND_RECOVERY.md`. |
| `warnetech-doctor` | Environment self-check — run this first on a new machine. |

`warnetech_cli_legacy/warnetech` (the deprecated Node CLI) is unaffected:
it's invoked by its own path, not through PATH, so there is no collision
with the new `warnetech` console script — the unqualified name now
unambiguously means the canonical Python CLI, which is the correct
resolution per CLAUDE.md's "the canonical CLI is `warnetech_cli/`".

## `warnetech-doctor`

```bash
warnetech-doctor          # human-readable
warnetech-doctor --json   # machine-readable, same exit code
```

Ten checks, each answering one specific "is this actually going to work"
question, in place of finding out from a raw traceback three commands into
a session:

- Python version (`pyproject.toml` requires ≥ 3.10)
- Running on Termux (informational)
- Terminal: interactive TTY + UTF-8 locale
- `cryptography` installed — **the single most common Termux first-run
  failure**, because the wheel builds from source there and needs `rust` +
  `binutils` on PATH first (see `bootstrap_termux.sh`'s own comment on this
  exact problem). The hint names the fix directly.
- The four optional extras (`lz4`, `zstandard`, `pyarrow`, `boto3`) — each
  reported as `skip`, never `warn` or `fail`, when absent: not having an
  extra you don't use is not a problem.
- `git` on PATH
- Envelope round-trip: encrypts and decrypts a probe string through the
  real `warnetech_envelope`, catching a `cryptography` install that
  imports fine but has a broken backend — the same check
  `bootstrap_termux.sh` already ran inline, now available on demand.
- `~/.warnetech` exists and is writable
- The curriculum ledger, if one exists, has an intact hash chain
- Whether the curriculum's pre-commit hook is installed

Exit code `0` when nothing failed (warnings are fine — a warning is
something to know about, not something blocking); `1` if anything failed.
Every check is a small, independently testable function
(`warnetech_cli/doctor.py`); nothing in the check layer prints or exits —
only `main()` does, so `run_checks()` can be driven from Python directly
(a future `ai-diagnose`-style command, a CI gate, another script) without
shelling out.

## Shell completion

```bash
source scripts/completions/warnetech.bash
```

`bootstrap_termux.sh` installs this line into `~/.bashrc` automatically
(idempotently — it checks first, so re-running bootstrap never duplicates
it). Covers all four console scripts' subcommands.

zsh: `autoload -Uz bashcompinit && bashcompinit` in `~/.zshrc`, then source
the same file — one completion implementation, not two to keep in sync.

**The completion script cannot silently drift from the real CLIs.**
`tests/cli/test_completion.py` introspects each tool's actual argparse
parser and asserts every subcommand is present in the completion script's
corresponding variable; add a subcommand to a parser and forget the
completion file, and the test suite fails, not the tab key.

## `warnetech-curriculum check --fix`: auto-correct

```bash
warnetech-curriculum check --fix
```

Applies renames for R001 (unresolved import) and R002 (unknown attribute)
findings, but **only** when exactly one candidate is both a strong
edit-distance match and clearly beats the runner-up. See
`docs/10_CURRICULUM.md`'s `--fix` section for the full detail, including
why this is a typo-corrector and deliberately not a mind-reader: it
correctly declines to "fix" the actual API-shape bug that motivated the
whole curriculum package, because `open` isn't a typo of `unseal`.

Two independent safety nets before anything is written: the proposed edit
is re-verified against the live file (a stale offset is refused, not
forced), and the whole file is re-parsed after every edit lands, before the
write happens — an edit that would leave the file unparseable is never
written.

## Friendlier top-level errors

`warnetech`'s top-level exception handler (`warnetech_cli/main.py`) now
recognises a few specific, previously-seen failure shapes and prints an
actionable one-line hint alongside the real error — never instead of it:

- a missing module → points at `warnetech-doctor`
- a connection failure → points at `server-ping` and the config's `server_url`
- a missing file → names it

Anything not recognised gets no hint, only the error itself
(`warnetech_cli.main.error_hint` returns `None`) — a wrong guess at "what
to do" is worse than no guess, the same discipline the curriculum's
`_confident_nearest` applies to auto-fix.

## Bootstrap

`bootstrap_termux.sh` now additionally, after installing dependencies and
running the test suites:

1. Seeds the curriculum (`warnetech-curriculum seed`) and installs its
   pre-commit hook.
2. Installs shell completion into `~/.bashrc` (idempotently).
3. Runs `warnetech-doctor` as the final check, replacing the old inline
   envelope-only self-test with the full battery above.
