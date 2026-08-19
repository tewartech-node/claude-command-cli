# claude-command-cli

A Termux-first command-line assistant powered by:

- Cloudflare Workers
- NVIDIA Nemotron 3 Ultra
- GitHub automation
- Claude Code Chats

## Setup

One bootstrap script per platform, each installing OS packages, cloning the
repo, installing Python + Node dependencies, and running the test suite:

| Platform | Script |
| --- | --- |
| Termux (Android) | `./bootstrap_termux.sh` |
| Ubuntu / Debian (native, or a Debian/Ubuntu proot-distro inside Termux) | `./bootstrap_linux.sh` |

Both scripts work on x86_64 and arm64, and on 32-bit armhf/i386 (common on
older Android devices under proot-distro) where PyPI has no prebuilt
`cryptography` wheel -- each installs a Rust toolchain so pip's source-build
fallback has what it needs.

```bash
# Termux
curl -fsSL https://raw.githubusercontent.com/tewartech-node/claude-command-cli/claude/termux-cli-cloudflare-nemotron-pve6ca/bootstrap_termux.sh | bash

# Ubuntu / Debian
curl -fsSL https://raw.githubusercontent.com/tewartech-node/claude-command-cli/claude/termux-cli-cloudflare-nemotron-pve6ca/bootstrap_linux.sh | bash
```

Or clone first and run the matching script locally -- both are idempotent
and safe to re-run.

## GitHub Automation Commands

### Open Claude with this repo

warnetech gh-open "claude-command-cli"

### Push changes

warnetech gh-push "message"

### Pull updates

warnetech gh-pull
