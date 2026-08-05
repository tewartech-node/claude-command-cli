# Implementation Plan

Prioritized guide for implementing CLI commands and Worker endpoints.

## Phase 1: Core Commands (Week 1-2)

These commands establish the foundation for all future features.

### 1.1 `warnet ping`
**Priority**: 🔴 CRITICAL (do first)
**Purpose**: Verify connectivity between CLI and Worker

**CLI Implementation**:
```bash
warnet ping
```

**Expected Output**:
```
✓ Ping: Connected
  Worker: https://your-worker.workers.dev
  Latency: 125ms
```

**Worker Endpoint**: `POST /cli`
```json
Request:
{
  "command": "ping"
}

Response:
{
  "ok": true,
  "command": "ping",
  "message": "pong",
  "timestamp": "2026-08-05T10:15:00Z"
}
```

**Why First**: 
- Simplest command (no external APIs)
- Tests basic CLI ↔ Worker communication
- Validates encryption/decryption
- Unblocks all other commands

---

### 1.2 `warnet gh-open "<repo>"`
**Priority**: 🔴 CRITICAL (do second)
**Purpose**: Get Claude link for a GitHub repository

**CLI Implementation**:
```bash
warnet gh-open "tewartech-node/claude-command-cli"
```

**Expected Output**:
```
✓ Repository: tewartech-node/claude-command-cli
✓ URL: https://github.com/tewartech-node/claude-command-cli
✓ Claude: https://claude.ai/new?repo=https://github.com/tewartech-node/claude-command-cli

Open in Claude? (y/n)
```

**Worker Endpoint**: `POST /cli`
```json
Request:
{
  "command": "gh-open",
  "args": ["tewartech-node/claude-command-cli"]
}

Response:
{
  "ok": true,
  "command": "gh-open",
  "data": {
    "repo": "tewartech-node/claude-command-cli",
    "url": "https://github.com/tewartech-node/claude-command-cli",
    "claude_url": "https://claude.ai/new?repo=https://github.com/tewartech-node/claude-command-cli"
  }
}
```

**Why Second**:
- No external API calls
- Simple URL construction
- Tests Worker command routing
- Enables Claude integration

---

### 1.3 `warnet ai "<prompt>"`
**Priority**: 🟠 HIGH (do third)
**Purpose**: Get AI assistance via NVIDIA Nemotron

**CLI Implementation**:
```bash
warnet ai "explain this code"
```

**Expected Output**:
```
✓ Prompt sent
> Processing...
[AI Response from Nemotron]
```

**Worker Endpoint**: `POST /cli`
```json
Request:
{
  "command": "ai",
  "args": ["explain this code"]
}

Response:
{
  "ok": true,
  "command": "ai",
  "data": {
    "response": "AI response text...",
    "tokens": {
      "input": 15,
      "output": 250,
      "total": 265
    },
    "model": "nemotron-3-ultra"
  }
}
```

**Subtasks**:
- [ ] Implement nemotron.js client
- [ ] Test with NVIDIA API
- [ ] Add streaming support (optional for phase 1)
- [ ] Add error handling for API failures
- [ ] Add token counting

**Why Third**:
- Requires external API integration
- Critical for AI features
- Tests error handling
- Foundation for fix/explain commands

---

### 1.4 `warnet gh-push "<message>"`
**Priority**: 🟠 HIGH (do fourth)
**Purpose**: Commit and push changes to GitHub

**CLI Implementation**:
```bash
warnet gh-push "feat: add new command"
```

**Expected Output**:
```
✓ Checking changes...
✓ Staging files...
✓ Committing...
✓ Pushing...
✓ Success: Pushed to origin/main
```

**Worker Endpoint**: `POST /cli`
```json
Request:
{
  "command": "gh-push",
  "args": ["feat: add new command"]
}

Response:
{
  "ok": true,
  "command": "gh-push",
  "data": {
    "message": "feat: add new command",
    "pushed": true,
    "branch": "main"
  }
}
```

**Note**: GitHub automation may be limited in Worker environment
- Consider delegating to CLI itself (using git CLI)
- Or require GitHub token in config

**Subtasks**:
- [ ] Check if git available in Termux
- [ ] Implement local git operations in CLI
- [ ] Or: Implement GitHub API in Worker
- [ ] Add error handling for conflicts
- [ ] Test with actual repo

---

### 1.5 `warnet gh-pull`
**Priority**: 🟠 HIGH (do fifth)
**Purpose**: Pull latest changes from GitHub

**CLI Implementation**:
```bash
warnet gh-pull
```

**Expected Output**:
```
✓ Fetching...
✓ Pulling...
✓ Success: Updated from origin
  Files changed: 3
  Insertions: +45
```

**Worker Endpoint**: `POST /cli`
```json
Request:
{
  "command": "gh-pull"
}

Response:
{
  "ok": true,
  "command": "gh-pull",
  "data": {
    "pulled": true,
    "files_changed": 3,
    "insertions": 45,
    "deletions": 12
  }
}
```

**Note**: Like gh-push, consider CLI-side implementation

---

## Phase 2: Intermediate Commands (Week 3-4)

Once core commands work, add these features.

### 2.1 `warnet fix "<file>"`
**Priority**: 🟡 MEDIUM
**Purpose**: Analyze code and suggest fixes

**Implementation Plan**:
1. Read file in CLI
2. Send to Worker with diagnostic prompt
3. Call Nemotron for analysis
4. Display suggestions with option to apply

---

### 2.2 `warnet explain "<file>"`
**Priority**: 🟡 MEDIUM
**Purpose**: Generate explanation of code

**Implementation Plan**:
1. Read file in CLI
2. Send to Worker with explanation prompt
3. Call Nemotron for detailed explanation
4. Display formatted output

---

## Phase 3: System Commands (Week 5-6)

### 3.1 `warnet status`
**Priority**: 🟡 MEDIUM
**Purpose**: Show system status

**Expected Output**:
```
CLI Version: 1.0.0
✓ Worker: Connected
✓ Config: ~/.claude-cli/config.json
Quotas:
  API Calls: 45/100 (45%)
  Storage: 2.3GB/10GB
```

### 3.2 `warnet sync`
**Priority**: 🟡 MEDIUM
**Purpose**: Sync quotas, baselines, signatures

---

### 3.3 `warnet update`
**Priority**: 🟡 MEDIUM
**Purpose**: Update CLI to latest version

---

## Testing Strategy

### Phase 1 Testing
After implementing each Phase 1 command:
1. Test CLI command parsing
2. Test request encryption
3. Test Worker endpoint
4. Test response decryption
5. Test output formatting
6. Test error handling

### Example Test
```javascript
describe('warnet ping', () => {
  it('sends ping command to worker', async () => {
    const response = await sendCommand('ping');
    expect(response.ok).toBe(true);
    expect(response.command).toBe('ping');
  });
  
  it('formats output correctly', async () => {
    const output = formatPingResponse(response);
    expect(output).toContain('✓ Ping: Connected');
  });
});
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] **warnet ping**
  - [ ] CLI implementation
  - [ ] Worker endpoint
  - [ ] Request encryption
  - [ ] Response decryption
  - [ ] Tests
  
- [ ] **warnet gh-open**
  - [ ] CLI implementation
  - [ ] Worker endpoint
  - [ ] URL generation
  - [ ] Tests
  
- [ ] **warnet ai**
  - [ ] CLI implementation
  - [ ] Worker endpoint
  - [ ] Nemotron integration
  - [ ] Error handling
  - [ ] Tests
  
- [ ] **warnet gh-push**
  - [ ] CLI implementation
  - [ ] Git operations
  - [ ] Error handling
  - [ ] Tests
  
- [ ] **warnet gh-pull**
  - [ ] CLI implementation
  - [ ] Git operations
  - [ ] Error handling
  - [ ] Tests

### Verification
- [ ] All Phase 1 commands work end-to-end
- [ ] Tests pass (>80% coverage)
- [ ] Lint & format pass
- [ ] Documentation updated
- [ ] Committed to git

---

## Worker Endpoint: POST /cli

This single endpoint handles all commands.

### Request Format
```javascript
{
  "command": "ping" | "ai" | "gh-open" | "gh-push" | "gh-pull",
  "args": string[],
  "encrypted": boolean,
  "signature": string
}
```

### Response Format (Success)
```javascript
{
  "ok": true,
  "command": string,
  "data": any,
  "timestamp": string
}
```

### Response Format (Error)
```javascript
{
  "ok": false,
  "error": string,
  "code": string,
  "timestamp": string
}
```

### Handler Routing
```javascript
// worker/index.js
const COMMAND_HANDLERS = {
  ping: handlePing,
  ai: handleAi,
  'gh-open': handleGhOpen,
  'gh-push': handleGhPush,
  'gh-pull': handleGhPull
};
```

---

## CLI Command Structure

Each command follows this pattern:

```javascript
program
  .command('command-name [args...]')
  .description('What this command does')
  .option('--flag', 'Optional flag')
  .action(async (args, options) => {
    try {
      // Validate input
      // Send to Worker
      // Format output
    } catch (error) {
      // Error handling
    }
  });
```

---

## API Integration Points

### NVIDIA Nemotron
- Endpoint: `https://integrate.api.nvidia.com/v1/chat/completions`
- Auth: Bearer token
- Used by: `warnet ai`, `warnet fix`, `warnet explain`

### GitHub API
- Endpoint: `https://api.github.com`
- Auth: Personal access token
- Used by: `warnet gh-open`, `warnet gh-push`, `warnet gh-pull`

### Warnetwork Control Plane
- Used by: `warnet status`, `warnet sync`
- Endpoints: TBD

---

## Error Handling Guide

### Common Errors

**Connection Error**:
```
✗ Error: Failed to connect to Worker
  Check: warnet ping
  Retry: warnet ai "prompt" --timeout 60
```

**API Key Error**:
```
✗ Error: API_KEY not found in config
  Run: warnet init
  For help: warnet help --error "API_KEY not found"
```

**NVIDIA API Error**:
```
✗ Error: Nemotron API rate limited
  Wait: Try again in a few minutes
  Check: warnet quota
```

**Git Error**:
```
✗ Error: No changes to commit
  Check: git status
  Add: git add .
```

---

## Progressive Implementation

Follow this order:
1. ✅ **warnet ping** → Basic connectivity
2. ✅ **warnet gh-open** → URL generation
3. ✅ **warnet ai** → AI integration
4. ✅ **warnet gh-push** → Git push
5. ✅ **warnet gh-pull** → Git pull
6. ⏳ **warnet fix** → Code analysis
7. ⏳ **warnet explain** → Code explanation
8. ⏳ **warnet status** → System status
9. ⏳ **warnet sync** → Remote sync
10. ⏳ **warnet update** → Self-update

---

## Success Criteria

### Phase 1 Complete When:
- ✅ All 5 core commands implemented
- ✅ All commands tested end-to-end
- ✅ All tests passing
- ✅ All documentation updated
- ✅ All TASKS.md items checked off
- ✅ Code follows STANDARDS.md
- ✅ Committed to git

---

## Commands Reference

| Command | Purpose | Status | Priority |
|---------|---------|--------|----------|
| `warnet ping` | Check connectivity | Phase 1 | 🔴 |
| `warnet gh-open` | Get Claude URL | Phase 1 | 🔴 |
| `warnet ai` | AI assistance | Phase 1 | 🟠 |
| `warnet gh-push` | Push to GitHub | Phase 1 | 🟠 |
| `warnet gh-pull` | Pull from GitHub | Phase 1 | 🟠 |
| `warnet fix` | Fix code | Phase 2 | 🟡 |
| `warnet explain` | Explain code | Phase 2 | 🟡 |
| `warnet status` | System status | Phase 3 | 🟡 |
| `warnet sync` | Sync remote | Phase 3 | 🟡 |
| `warnet update` | Update CLI | Phase 3 | 🟡 |

---

**Start with `warnet ping` to establish CLI ↔ Worker communication!**
