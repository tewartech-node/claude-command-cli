# CLI Commands Reference

> **Legacy CLI.** This documents `warnetech_cli_legacy/warnet` (the
> original Node.js CLI, deprecated but kept for its GitHub, AI-chat, and
> self-evolution commands). The canonical CLI is now the Python
> `warnetech_cli` package, which talks to warnetech-server's real HTTP
> API — see `warnetech_cli/main.py` for its command surface
> (`status`, `metrics`, `signatures`, `learn`, `recover`, `slice`,
> `compress`, `ghost-create`/`ghost-recall`, `retention-apply`/`retention-policy`,
> `ai-query`/`ai-recall`, `export`/`import`, `server-ping`, `db-check`,
> `db-sync`). The `warnet <command>` examples below are accurate for the
> legacy binary's real invocation syntax and are left as-is rather than
> rewritten to a command name that binary doesn't have.

## Core Commands

### warnet ai
```bash
warnet ai "<prompt>"
```
Sends a prompt to NVIDIA Nemotron 3 Ultra for AI assistance.

**Options:**
- `--stream`: Stream reasoning tokens in real-time
- `--timeout 30`: Set timeout in seconds (default: 30)
- `--model nemotron-3-ultra`: Specify model (default: nemotron-3-ultra)

**Example:**
```bash
warnet ai "explain this code snippet"
warnet ai "generate a bash script to backup files" --stream
```

**Flow:**
1. CLI reads prompt & options
2. CLI encrypts request (AES-256-GCM)
3. CLI sends to Worker via HTTPS
4. Worker calls NVIDIA API
5. Worker streams or buffers response
6. CLI decrypts & displays output

---

### warnet fix
```bash
warnet fix "<file_path>"
```
Uses AI to analyze and suggest fixes for a file.

**Example:**
```bash
warnet fix "script.sh"
warnet fix "src/index.js"
```

**Flow:**
1. CLI reads file from disk
2. CLI sends to Worker with file content
3. Worker calls AI with diagnostic prompt
4. Returns suggested fixes
5. CLI displays fixes with option to apply

---

### warnet explain
```bash
warnet explain "<file_path>"
```
Generates explanation for code in a file.

**Example:**
```bash
warnet explain "src/utils/crypto.js"
warnet explain "worker/index.js"
```

---

### warnet update
```bash
warnet update
```
Updates the CLI to latest version from GitHub.

**Options:**
- `--check`: Only check for updates, don't install
- `--version <version>`: Install specific version

**Flow:**
1. Checks GitHub releases for new version
2. Downloads new version
3. Verifies signature
4. Backs up current version to R2
5. Atomically deploys new version
6. Verifies functionality

---

### warnet status
```bash
warnet status
```
Displays current system status and configuration.

**Output:**
```
CLI Version: 1.0.0
API Status: ✓ Connected
Config: ~/.claude-cli/config.json
Latest Sync: 2026-08-05 10:15:00
Quotas:
  - API Calls: 45/100 (daily)
  - Storage: 2.3GB/10GB
  - Rate Limit: 60/100 (per minute)
```

---

### warnet sync
```bash
warnet sync
```
Synchronizes local state with remote (quotas, baselines, signatures).

**Syncs:**
- Quota information from warnetwork
- Baseline signatures for anomaly detection
- Rate limit rules
- Configuration updates

---

### warnet help
```bash
warnet help [command]
```
Shows help for commands. Can query AI for complex errors.

**Examples:**
```bash
warnet help
warnet help ai
warnet help --error "connection timeout"
```

---

## GitHub Commands

### warnet gh-open
```bash
warnet gh-open "<repo>"
```
Opens GitHub repository in browser or opens Claude with repo context.

**Examples:**
```bash
warnet gh-open "tewartech-node/claude-command-cli"
warnet gh-open "."  # current directory repo
```

---

### warnet gh-push
```bash
warnet gh-push "<commit_message>"
```
Commits and pushes changes to GitHub.

**Options:**
- `--branch <branch>`: Push to specific branch (default: current)
- `--no-verify`: Skip pre-commit hooks
- `--force`: Force push (careful!)

**Example:**
```bash
warnet gh-push "feat: add warnet ai command"
```

**Flow:**
1. CLI validates changes
2. CLI commits with message
3. CLI pushes to remote
4. CLI displays result

---

### warnet gh-pull
```bash
warnet gh-pull
```
Pulls latest changes from remote repository.

**Options:**
- `--rebase`: Use rebase instead of merge
- `--branch <branch>`: Pull specific branch

---

## System Commands

### warnet evolve
```bash
warnet evolve
```
Self-updates the CLI with new features (ASAEAI synthesis pattern).

**Process:**
1. Downloads latest code from GitHub
2. Runs sandbox synthesis tests
3. Verifies changes with automated tests
4. Performs atomic deployment
5. Verifies functionality
6. Can rollback if needed

**Stages:**
- Synthesis: Generate/apply code changes
- Verification: Test in isolated environment
- Deployment: Atomic update
- Rollback: Revert if needed

---

### warnet request-score
```bash
warnet request-score "<description>"
```
Requests AI reinforcement scoring for a task or output.

**Example:**
```bash
warnet request-score "quality of generated code"
```

---

## Configuration Command

### warnet init
```bash
warnet init
```
Initializes ~/.claude-cli/config.json with defaults.

**Creates:**
```json
{
  "api_key": "your-key-here",
  "worker_url": "https://your-worker.workers.dev",
  "nemotron_api_key": "your-nemotron-key",
  "github_token": "your-github-token",
  "tier": 2,
  "cache_dir": "~/.claude-cli/cache"
}
```

---

## Advanced Commands

### warnet quota
```bash
warnet quota [check|rollup]
```
**check:** Show current quota usage
**rollup:** Trigger quota rollup operation

---

### warnet detect-anomalies
```bash
warnet detect-anomalies
```
Triggers anomaly detection against stored baselines.

---

### warnet sync-signatures
```bash
warnet sync-signatures
```
Syncs baseline signatures from warnetwork control plane.

---

## Output Format

### Success
```bash
$ warnet ai "hello"
✓ Prompt sent
> Processing...
[AI Response]
```

### Error with AI Explanation
```bash
$ warnet ai "bad prompt"
✗ Error: Invalid prompt format
> Would you like AI explanation? Run: warnet help --error "Invalid prompt format"
```

### Status Display
```bash
$ warnet status
✓ System Status
  Version: 1.0.0
  Config: ~./claude-cli/config.json
  Worker: Connected
  Cache: 256MB used
```

---

## Exit Codes
- 0: Success
- 1: General error
- 2: Invalid command
- 3: Authentication error
- 4: Connection error
- 5: Timeout

---

## Tips

### Piping
```bash
cat file.js | warnet explain -  # read from stdin
warnet ai "generate script" | tee output.sh
```

### Chaining
```bash
warnet fix "buggy.js" && warnet ai "test this" && warnet gh-push "fix: resolved"
```

### Background Jobs
```bash
warnet update &  # update in background
warnet evolve &  # self-update in background
```
