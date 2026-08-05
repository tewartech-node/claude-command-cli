# Claude Instructions for claude-command-cli

## Role
Claude is the primary developer for this project. This document defines the scope, constraints, and best practices for maintaining and extending the architecture.

## Architecture to Maintain

```
┌─────────────────────────────────────────────────────┐
│                 Three-Layer Architecture            │
└─────────────────────────────────────────────────────┘

Layer 1: Termux CLI (Local)
├── Bash-based command runner
├── Sends encrypted commands to Worker
├── Opens Claude chats with repo context
├── Manages local configuration (~/.claude-cli/config.json)
└── Handles git push/pull operations

Layer 2: Cloudflare Worker (Remote)
├── Receives encrypted CLI commands
├── Authenticates via API_KEY
├── Routes to appropriate handler (ai, gh, sys)
├── Calls external APIs (NVIDIA, GitHub, Warnetech)
├── Returns JSON responses
└── Manages encryption/decryption

Layer 3: GitHub Repository
├── Stores CLI scripts & executables
├── Stores Worker code (Cloudflare Workers)
├── Stores complete documentation
├── Stores Claude instructions (this file)
├── Tracks development on feature branches
└── Maintains version control & history
```

## Principles

### 1. Separation of Concerns
- **CLI layer**: Local operations, user I/O, config management
- **Worker layer**: Remote logic, external API coordination, security
- **Repo layer**: Code storage, documentation, version control

Keep each layer independent. Don't move Worker logic to CLI or vice versa.

### 2. Security First
- All network communication: **AES-256-GCM encrypted**
- Fallback: **ChaCha20-Poly1305**
- Key derivation: **Argon2id**
- Never log plaintext secrets
- Validate all inputs at boundaries
- Use timing-safe comparisons for secrets

### 3. Modular Commands
Each command should:
- Have its own handler (worker/commands/*.js)
- Be independent from other commands
- Include error handling
- Support CLI piping/chaining
- Have clear help documentation

### 4. Atomic Commits
- One feature per commit
- Working code (tests pass)
- Clear commit message following format:
  ```
  <type>: <description>
  
  <optional details>
  ```
- Types: feat, fix, refactor, test, docs, chore

### 5. Documentation First
- Update docs before or alongside code
- Keep architecture diagram synchronized
- Document new endpoints in WORKER_SPEC.md
- Add commands to CLI_COMMANDS.md
- Explain non-obvious logic with comments

## Development Workflow

### Starting a Feature
```bash
# Start from development branch
git checkout claude/termux-cli-cloudflare-nemotron-pve6ca

# Create feature branch
git checkout -b feat/feature-name

# Make changes
# Test locally with: npm test

# Commit
git add .
git commit -m "feat: add new feature"

# Push
git push -u origin feat/feature-name
```

### Merging Back
```bash
# After testing/review
git checkout claude/termux-cli-cloudflare-nemotron-pve6ca
git merge feat/feature-name
git push origin claude/termux-cli-cloudflare-nemotron-pve6ca

# Delete feature branch
git branch -d feat/feature-name
```

## Safe Extension Patterns

### Adding a New CLI Command
1. **Create handler in worker/commands/**
   ```javascript
   // worker/commands/newcmd.js
   async function handleNewcmd(args, env) {
     // Implementation
     return result;
   }
   export default handleNewcmd;
   ```

2. **Register in worker/index.js**
   ```javascript
   const COMMAND_HANDLERS = {
     // ...existing...
     newcmd: handleNewcmd,
   };
   ```

3. **Add CLI command in warnetech_cli_legacy/warnetech**
   ```javascript
   program
     .command('newcmd <arg>')
     .description('Description')
     .action(async (arg, options) => {
       // CLI logic
     });
   ```

4. **Document in docs/05_CLI_COMMANDS.md**

5. **Test**
   ```bash
   npm test
   warnetech newcmd "test"
   ```

### Adding a New API Integration
1. **Create utility in worker/utils/**
   ```javascript
   // worker/utils/newapi.js
   async function call(params, env) {
     // Implementation
   }
   export default { call };
   ```

2. **Use in appropriate handler**
   ```javascript
   // worker/commands/ai.js or gh.js
   import api from '../utils/newapi.js';
   const result = await api.call(args, env);
   ```

3. **Add error handling**
   ```javascript
   try {
     return await api.call(args, env);
   } catch (error) {
     throw new Error(`API error: ${error.message}`);
   }
   ```

4. **Test in isolation**
   ```bash
   npm test -- worker/utils/newapi.js
   ```

### Adding a New Utility Function
- Keep utilities focused (one responsibility)
- Place in appropriate utils/ directory
- Export as named function or default
- Add unit tests immediately
- Document with JSDoc comment

### Extending Security
- New encryption: add to worker/utils/validate.js
- New validation: add to validateRequest function
- New security check: add to antiTamperCheck function
- Always maintain backward compatibility

## Things to Avoid

### ❌ Do NOT
- Hardcode API keys or secrets anywhere
- Log plaintext sensitive data
- Mix CLI and Worker logic
- Create circular dependencies
- Skip tests when committing
- Force push to main/master branch
- Change the three-layer architecture
- Add heavy dependencies without justification
- Remove existing functionality without discussing first
- Commit node_modules or build artifacts

### ✅ Do Instead
- Use environment variables for secrets
- Log only sanitized data
- Keep layers separated
- Use modular imports
- Run full test suite before commits
- Use force-with-lease if absolutely necessary
- Extend architecture within existing pattern
- Justify new dependencies in commit message
- Maintain backward compatibility
- Deprecate gracefully before removing

## Environment Setup

### Required
```bash
npm install
npm run lint    # ESLint
npm run format  # Prettier
npm test        # Jest
```

### Local Development
```bash
# Terminal 1: Start Worker dev server
npm run dev

# Terminal 2: Test CLI commands
./warnetech_cli_legacy/warnetech status
./warnetech_cli_legacy/warnetech ai "test prompt"
```

### Deployment
```bash
# Deploy Worker to Cloudflare
npm run deploy

# Verify deployment
curl https://your-worker.workers.dev/health
```

## Code Review Checklist

Before committing, verify:
- [ ] Code follows 04_CODE_STANDARDS.md
- [ ] No secrets in code or commit message
- [ ] Tests added/updated (>80% coverage)
- [ ] Lint passes: `npm run lint`
- [ ] Format passes: `npm run format`
- [ ] Architecture diagram still accurate
- [ ] Documentation updated
- [ ] Commit message follows format
- [ ] Feature works end-to-end
- [ ] Error handling is robust

## Testing Strategy

### Unit Tests
- Test each module in isolation
- Mock external APIs
- Test error cases
- Aim for >80% coverage

```bash
npm test -- worker/commands/ai.js
```

### Integration Tests
- Test full CLI → Worker → API flow
- Test encryption/decryption round-trip
- Test error propagation

```bash
npm run test:integration
```

### Manual Testing
```bash
# Test locally
npm run dev

# In another terminal
./warnetech_cli_legacy/warnetech ai "explain this code"
./warnetech_cli_legacy/warnetech gh-open "tewartech-node/claude-command-cli"
./warnetech_cli_legacy/warnetech status
```

## Documentation Maintenance

Keep these synchronized:
- **02_ARCHITECTURE_MAP.md** - Update if architecture changes
- **05_CLI_COMMANDS.md** - Add new commands here
- **06_WORKER_SPEC.md** - Document endpoints
- **04_CODE_STANDARDS.md** - Update standards if needed
- **03_TASKS_FOR_CLAUDE.md** - Check off completed tasks

## Version Control

### Branch Strategy
- **Development**: `claude/termux-cli-cloudflare-nemotron-pve6ca`
- **Features**: `feat/feature-name` (from development)
- **Fixes**: `fix/issue-name` (from development)
- **Main**: `main` (production-ready, auto-deployed)

### Commit Message Format
```
feat: add warnetech ai command
fix: handle rate limit responses
refactor: improve encryption utils
test: add integration tests
docs: update architecture diagram
chore: upgrade dependencies
```

## When to Ask for Help

Ask the user (don't just decide) when:
- Removing significant functionality
- Making major architecture changes
- Changing security/encryption approach
- Adding large external dependencies
- Significantly refactoring core modules
- Unsure about design decision
- Encountering conflicts that can't be resolved

## Common Tasks

### Adding a New Command
1. Create handler in worker/commands/
2. Register in COMMAND_HANDLERS
3. Add CLI command in warnetech_cli_legacy/warnetech
4. Add tests
5. Document in 05_CLI_COMMANDS.md
6. Commit: `feat: add warnetech <cmd> command`

### Fixing a Bug
1. Create feature branch `fix/description`
2. Write failing test that reproduces bug
3. Fix the bug
4. Verify test passes
5. Commit: `fix: resolve issue description`

### Updating Documentation
1. Edit relevant markdown file
2. Update related files (architecture, standards)
3. Verify links still work
4. Commit: `docs: update documentation topic`

### Deploying Changes
1. Ensure all tests pass: `npm test`
2. Ensure lint passes: `npm run lint`
3. Merge to development branch
4. Push to remote
5. GitHub Actions automatically deploys to staging
6. After verification, merge to main for production

## Success Criteria

A feature is complete when:
- ✅ Code is implemented and tested
- ✅ Tests pass (>80% coverage)
- ✅ Lint & format pass
- ✅ Documentation updated
- ✅ End-to-end testing passed
- ✅ Committed with clear message
- ✅ Pushed to remote
- ✅ Architecture maintained
- ✅ No security issues introduced
- ✅ No secrets leaked

## Contact & Escalation

If you encounter issues:
1. Check the documentation first
2. Review similar implementations
3. Check git history for context
4. Run tests to identify failures
5. Ask user if blocked or uncertain

## Final Reminder

This architecture is proven and stable. Extend it carefully:
- Don't break the three-layer separation
- Maintain security standards
- Keep code modular and testable
- Document as you go
- Test thoroughly
- Commit atomically
- Keep the user informed

Good luck! 🚀
