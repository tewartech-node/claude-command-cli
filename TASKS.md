# Tasks for Claude

This is Claude's working to-do list for the claude-command-cli project. Tasks are organized by priority and dependency.

## Core Tasks

These are the primary development goals.

### 1. Improve the Termux CLI Script
**Status**: 🔄 In Progress (Scaffolding Complete)

**What**: Enhance termux-cli/warnet with full functionality

**Subtasks**:
- [ ] Implement command parser (Commander.js)
- [ ] Add config file loading (~/.claude-cli/config.json)
- [ ] Implement request encryption (AES-256-GCM)
- [ ] Implement response decryption
- [ ] Add error handling & helpful messages
- [ ] Add progress indicators & formatting
- [ ] Test with actual Worker
- [ ] Add bash completions
- [ ] Package as standalone binary

**Related Docs**: 
- [05_CLI_COMMANDS.md](docs/05_CLI_COMMANDS.md) - Command reference
- [04_CODE_STANDARDS.md](docs/04_CODE_STANDARDS.md) - Coding guidelines

---

### 2. Improve the Cloudflare Worker Code
**Status**: 🔄 In Progress (Scaffolding Complete)

**What**: Build production-ready Worker with all handlers

**Subtasks**:
- [ ] Implement full request validation (validateRequest)
- [ ] Implement AES-256-GCM encryption/decryption
- [ ] Implement ChaCha20-Poly1305 fallback
- [ ] Implement Argon2id key derivation
- [ ] Implement HMAC-SHA256 signature verification
- [ ] Add anti-tamper checks
- [ ] Add data tier enforcement
- [ ] Implement rate limiting (Cloudflare KV)
- [ ] Add comprehensive error handling
- [ ] Add request/response logging (WORM storage)
- [ ] Test all endpoints
- [ ] Deploy to Cloudflare

**Related Docs**:
- [06_WORKER_SPEC.md](docs/06_WORKER_SPEC.md) - Worker specification
- [04_CODE_STANDARDS.md](docs/04_CODE_STANDARDS.md) - Code standards

---

### 3. Add New CLI Commands
**Status**: 🔄 In Progress (Framework Ready)

**Commands to Implement**:

#### Essential Commands
- [ ] `warnet ai "<prompt>"` - NVIDIA Nemotron integration
  - [ ] Basic prompt sending
  - [ ] Streaming support for reasoning tokens
  - [ ] Timeout handling
  - [ ] Error explanation via AI
  
- [ ] `warnet fix "<file>"` - Code fixing
  - [ ] Read file content
  - [ ] Send to AI with diagnostic prompt
  - [ ] Display suggestions
  - [ ] Option to apply fixes
  
- [ ] `warnet explain "<file>"` - Code explanation
  - [ ] Read file content
  - [ ] Generate explanation prompt
  - [ ] Display formatted explanation
  
- [ ] `warnet gh-open "<repo>"` - GitHub integration
  - [ ] Validate repo URL
  - [ ] Generate Claude link
  - [ ] Display link & open if possible
  
- [ ] `warnet gh-push "<message>"` - Git automation
  - [ ] Git add changes
  - [ ] Git commit with message
  - [ ] Git push to remote
  - [ ] Handle merge conflicts
  
- [ ] `warnet gh-pull` - Pull changes
  - [ ] Git fetch origin
  - [ ] Git pull with rebase option
  - [ ] Handle conflicts
  
- [ ] `warnet status` - System status
  - [ ] Check Worker connectivity
  - [ ] Show quota usage
  - [ ] Display version info
  - [ ] Show config status
  
- [ ] `warnet sync` - Sync remote state
  - [ ] Fetch baselines
  - [ ] Update signatures
  - [ ] Sync quotas
  - [ ] Check for updates
  
- [ ] `warnet update` - Update CLI
  - [ ] Check latest version
  - [ ] Download new version
  - [ ] Verify signature
  - [ ] Atomic replacement
  - [ ] Verify functionality
  
- [ ] `warnet evolve` - Self-update with AI synthesis
  - [ ] Synthesis: Generate changes
  - [ ] Verification: Test in sandbox
  - [ ] Deployment: Atomic update
  - [ ] Rollback: Restore if needed
  
- [ ] `warnet help [cmd]` - Help system
  - [ ] Show general help
  - [ ] Show command-specific help
  - [ ] AI-powered error explanation (`--error`)

#### Secondary Commands
- [ ] `warnet init` - Initialize configuration
- [ ] `warnet quota` - Quota management
- [ ] `warnet detect-anomalies` - Security monitoring
- [ ] `warnet sync-signatures` - Sync baselines
- [ ] `warnet request-score` - AI reinforcement scoring

**Related Docs**:
- [05_CLI_COMMANDS.md](docs/05_CLI_COMMANDS.md) - Full command reference

---

### 4. Add New Worker Endpoints
**Status**: 🔄 In Progress (Foundation Ready)

**Endpoints to Implement**:

#### Command Endpoints
- [ ] `POST /api/command` (Main)
  - [ ] Route to ai.js handler
  - [ ] Route to gh.js handler
  - [ ] Route to sys.js handler
  
#### Health & Status
- [ ] `GET /health` - Health check
  - [ ] Return status info
  - [ ] Check dependencies
  
- [ ] `GET /health/detailed` - Detailed health
  - [ ] D1 connection status
  - [ ] R2 bucket status
  - [ ] KV namespace status
  - [ ] Supabase connection status
  - [ ] NVIDIA API quota

#### Authentication
- [ ] `POST /api/authenticate` - Key negotiation
  - [ ] Validate public key
  - [ ] Return session token
  - [ ] Implement ML-KEM handshake

#### Hot Reload (Evolution)
- [ ] `POST /api/hotload` - Deploy patches
  - [ ] Validate patch code
  - [ ] Apply changes in-memory
  - [ ] Run smoke tests
  - [ ] Log deployment

#### Monitoring
- [ ] `GET /api/metrics` - Performance metrics
  - [ ] Request counts
  - [ ] Latency stats
  - [ ] Error rates
  
- [ ] `GET /api/logs` - Audit logs
  - [ ] Require authentication
  - [ ] RLS enforcement
  - [ ] WORM validation

**Related Docs**:
- [06_WORKER_SPEC.md](docs/06_WORKER_SPEC.md) - Worker specification

---

### 5. Add GitHub Automation Features
**Status**: 🔄 In Progress (Foundation Ready)

**Features to Implement**:

#### GitHub Commands
- [ ] `gh-open` - Open repo in Claude
  - [ ] Verify repo URL
  - [ ] Generate Claude link
  - [ ] Open if browser available
  
- [ ] `gh-push` - Commit & push
  - [ ] Git add files
  - [ ] Commit with message
  - [ ] Push to remote
  - [ ] Handle authentication
  
- [ ] `gh-pull` - Pull changes
  - [ ] Fetch latest
  - [ ] Merge or rebase
  - [ ] Resolve conflicts
  - [ ] Push if needed

#### GitHub Actions Workflow
- [ ] Create linting workflow
  - [ ] ESLint
  - [ ] Prettier
  - [ ] Fail on issues
  
- [ ] Create testing workflow
  - [ ] Unit tests
  - [ ] Integration tests
  - [ ] Coverage reporting
  
- [ ] Create deployment workflow
  - [ ] Worker deployment (staging)
  - [ ] CLI release build
  - [ ] Publish artifacts
  - [ ] Deploy to production (main branch)

#### Claude Integration
- [ ] Worker endpoint for Claude redirect
  - [ ] GET /api/claude-link
  - [ ] Returns: `https://claude.ai/new?repo=...`
  
- [ ] Termux command to open Claude
  - [ ] `warnet gh-open <repo>` opens Claude
  - [ ] Pre-fills repo context

**Related Docs**:
- [05_CLI_COMMANDS.md](docs/05_CLI_COMMANDS.md) - GitHub commands

---

### 6. Add AI-Powered Code Correction Tools
**Status**: 🔄 In Progress (Foundation Ready)

**Features to Implement**:

#### Code Analysis
- [ ] `warnet fix "<file>"` - Fix code issues
  - [ ] Read file
  - [ ] Send to Nemotron with diagnostic prompt
  - [ ] Parse response for fixes
  - [ ] Display issues & suggestions
  - [ ] Option to apply (with backup)
  
- [ ] `warnet explain "<file>"` - Explain code
  - [ ] Read file
  - [ ] Generate explanation prompt
  - [ ] Call Nemotron
  - [ ] Display formatted explanation
  
- [ ] `warnet help --error "<message>"` - Error explanation
  - [ ] Send error to Nemotron
  - [ ] Get explanation & solution
  - [ ] Display troubleshooting steps

#### NVIDIA Nemotron Integration
- [ ] Implement nemotron.js client
  - [ ] Chat endpoint
  - [ ] Streaming support
  - [ ] Reasoning tokens
  - [ ] Error handling
  - [ ] Token counting
  
- [ ] Prompt optimization
  - [ ] AST mutation for clarity
  - [ ] Add context automatically
  - [ ] Format examples
  - [ ] Enforce constraints
  
- [ ] Response handling
  - [ ] Parse AI responses
  - [ ] Format for CLI display
  - [ ] Highlight code blocks
  - [ ] Handle truncation

#### Specialized Prompts
- [ ] Code fixing prompt
  - [ ] Identify bugs
  - [ ] Explain issues
  - [ ] Suggest fixes
  - [ ] Rate severity
  
- [ ] Code explanation prompt
  - [ ] High-level overview
  - [ ] Function breakdown
  - [ ] Data flow
  - [ ] Dependencies
  
- [ ] Error diagnosis prompt
  - [ ] Explain root cause
  - [ ] Troubleshooting steps
  - [ ] Prevention tips
  - [ ] Related issues

**Related Docs**:
- [07_AI_INTEGRATION.md](docs/07_AI_INTEGRATION.md) - NVIDIA integration
- [05_CLI_COMMANDS.md](docs/05_CLI_COMMANDS.md) - Command reference

---

## Secondary Tasks

These tasks improve code quality and maintainability.

### Refactor Code for Clarity
**Status**: 🔄 In Progress

**Goals**:
- [ ] Extract common patterns to utils
- [ ] Simplify error handling
- [ ] Remove duplication
- [ ] Improve variable naming
- [ ] Add JSDoc comments (for non-obvious logic only)

**Related Docs**:
- [04_CODE_STANDARDS.md](docs/04_CODE_STANDARDS.md) - Code standards

---

### Add Documentation
**Status**: ✅ Mostly Complete

**What's Done**:
- ✅ Project goals & vision
- ✅ Architecture documentation
- ✅ Code standards & guidelines
- ✅ CLI commands reference
- ✅ Worker specification
- ✅ NVIDIA integration guide
- ✅ Git workflow guide
- ✅ Self-update automation plan
- ✅ Claude instructions

**What's Remaining**:
- [ ] API endpoint documentation
- [ ] Configuration guide
- [ ] Troubleshooting guide
- [ ] Security guide
- [ ] Deployment guide
- [ ] Contributing guide

---

### Add Examples
**Status**: 🔄 In Progress

**Examples to Create**:
- [ ] Example CLI usage
- [ ] Example API requests
- [ ] Example responses
- [ ] Example error handling
- [ ] Example custom commands
- [ ] Example Worker deployment

---

### Add Error Handling
**Status**: 🔄 In Progress

**Where to Add**:
- [ ] CLI command validation
- [ ] Worker request validation
- [ ] API error responses
- [ ] Network timeout handling
- [ ] Encryption/decryption errors
- [ ] File I/O errors
- [ ] Git operation errors
- [ ] NVIDIA API errors

**Pattern**:
```javascript
try {
  // operation
} catch (error) {
  // User-friendly error message
  // Suggest next steps
  // Log for debugging
}
```

---

### Add Modular Command Files
**Status**: ✅ Complete

**Created**:
- ✅ worker/commands/ai.js
- ✅ worker/commands/gh.js
- ✅ worker/commands/sys.js
- ✅ worker/utils/validate.js
- ✅ worker/utils/respond.js
- ✅ worker/utils/nemotron.js

**Pattern for New Commands**:
```javascript
// worker/commands/newcmd.js
async function handleNewcmd(args, env) {
  // Implementation
  return result;
}

export default handleNewcmd;
```

---

## Rules to Follow

### Security
- ❌ **Never** store secrets in repo
- ✅ Use environment variables
- ✅ Use Cloudflare secrets
- ✅ Encrypt sensitive data
- ✅ Never log plaintext secrets
- ✅ Sanitize user input
- ✅ Use timing-safe comparisons

### Compatibility
- ✅ **Keep everything free-tier compatible**
  - Cloudflare free tier limits
  - NVIDIA free API tier
  - GitHub free tier
  
- ✅ **Maintain Termux compatibility**
  - Node.js available
  - Bash available
  - No special permissions needed
  
- ✅ **Maintain Cloudflare Workers compatibility**
  - No file system access
  - Max 50MB code size
  - 30 second timeout
  - Limited CPU
  
- ✅ **Maintain NVIDIA Nemotron compatibility**
  - Use correct endpoint
  - Follow API specifications
  - Track token usage
  - Handle rate limits

### Code Quality
- ✅ Follow [04_CODE_STANDARDS.md](docs/04_CODE_STANDARDS.md)
- ✅ Write tests for new features
- ✅ Keep >80% test coverage
- ✅ Run lint & format before commit
- ✅ One feature per commit
- ✅ Clear commit messages
- ✅ Update documentation

---

## Progress Tracking

### Completed Tasks
- ✅ Project architecture designed
- ✅ Repository scaffolding created
- ✅ Documentation written (9 files)
- ✅ CLAUDE.md instructions created
- ✅ ARCHITECTURE.md designed
- ✅ Core command handlers scaffolded
- ✅ Utility functions scaffolded
- ✅ package.json configured
- ✅ Branch created & pushed

### Current Phase
🔄 **Phase 1: Foundation & CLI Implementation**

**This Week**:
1. Implement CLI command parser
2. Add config file loading
3. Implement basic encryption
4. Create first working CLI command (`warnet status`)
5. Test with Worker health endpoint

**Next Week**:
6. Implement `warnet ai` command
7. Implement NVIDIA Nemotron integration
8. Add streaming support
9. Build out remaining commands
10. Add comprehensive error handling

### Timeline

**Week 1-2**: Foundation
- CLI scaffolding → production ready
- Worker foundations → core handlers
- Basic security → full encryption

**Week 3-4**: Core Features
- All CLI commands implemented
- All Worker handlers implemented
- GitHub integration working
- NVIDIA integration complete

**Week 5-6**: Infrastructure
- D1, R2, Supabase connected
- Rate limiting working
- Quota tracking functional
- Anomaly detection enabled

**Week 7-8**: Advanced Features
- Hot reload system
- AST mutation engine
- Self-update (warnet evolve)
- Rollback capability

**Week 9-10**: Testing & Deployment
- Unit tests complete
- Integration tests complete
- End-to-end testing
- Production deployment

---

## How to Use This File

1. **Check Current Tasks**: Look at "Core Tasks" section
2. **Start Working**: Pick next unchecked task
3. **Update Progress**: Check off as you complete
4. **Related Docs**: Follow links to documentation
5. **Follow Rules**: Keep security & compatibility rules in mind

## Questions & Blockers

If you encounter:
- **Architecture questions** → Read ARCHITECTURE.md
- **Code questions** → Read CODE_STANDARDS.md
- **Security questions** → Read CLAUDE.md security section
- **Getting blocked** → Ask user for clarification

---

**Last Updated**: 2026-08-05
**Status**: 🚀 Active Development (v0.1.0)
