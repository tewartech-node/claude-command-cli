# Claude Command CLI

A modular Termux CLI that integrates Cloudflare Workers, NVIDIA Nemotron AI, GitHub automation, and ASAEAI hierarchical architecture.

## Features

### AI-Powered Commands
- `warnet ai "<prompt>"` - Ask Claude anything
- `warnet fix "<file>"` - Fix code issues
- `warnet explain "<file>"` - Understand code
- `warnet help --error "<message>"` - Explain errors

### GitHub Integration
- `warnet gh-open "<repo>"` - Open repo in Claude
- `warnet gh-push "<message>"` - Commit & push
- `warnet gh-pull` - Pull latest changes

### System Operations
- `warnet status` - Show system status
- `warnet sync` - Sync quotas & baselines
- `warnet update` - Update to latest version
- `warnet evolve` - Self-update with AI synthesis

### Security First
- AES-256-GCM encryption
- ChaCha20-Poly1305 fallback
- Argon2id key derivation
- ML-KEM post-quantum handshake
- Anti-tamper heuristics
- WORM audit logging

## Architecture

```
Termux CLI
    ↓ (HTTPS + AES-256-GCM)
Cloudflare Worker
    ↓
NVIDIA Nemotron / GitHub / Warnetwork APIs
    ↓
Responses
```

## Quick Start

### Installation
```bash
git clone https://github.com/tewartech-node/claude-command-cli
cd claude-command-cli
npm install
```

### Configuration
```bash
warnet init
# Creates ~/.claude-cli/config.json
```

### First Command
```bash
warnet ai "explain quantum computing"
```

## Development

### Setup
```bash
npm install
npm run lint     # Check code style
npm run format   # Format code
npm test         # Run tests
```

### Running Locally
```bash
# Development server
npm run dev

# In another terminal, test CLI
./termux-cli/warnet status
```

### Deployment
```bash
# Deploy Worker to Cloudflare
npm run deploy

# Deploy CLI (if building standalone binary)
npm run build
```

## Documentation

- **[01_PROJECT_GOALS.md](docs/01_PROJECT_GOALS.md)** - Vision & objectives
- **[02_ARCHITECTURE_MAP.md](docs/02_ARCHITECTURE_MAP.md)** - System design
- **[03_TASKS_FOR_CLAUDE.md](docs/03_TASKS_FOR_CLAUDE.md)** - Implementation phases
- **[04_CODE_STANDARDS.md](docs/04_CODE_STANDARDS.md)** - Coding guidelines
- **[05_CLI_COMMANDS.md](docs/05_CLI_COMMANDS.md)** - Command reference
- **[06_WORKER_SPEC.md](docs/06_WORKER_SPEC.md)** - Worker specification
- **[07_AI_INTEGRATION.md](docs/07_AI_INTEGRATION.md)** - NVIDIA Nemotron integration
- **[08_GIT_WORKFLOW.md](docs/08_GIT_WORKFLOW.md)** - Git & deployment workflow
- **[09_AUTOMATION_PLAN.md](docs/09_AUTOMATION_PLAN.md)** - Self-update mechanism

## Project Structure

```
claude-command-cli/
├── docs/                       # Documentation
│   ├── 01_PROJECT_GOALS.md
│   ├── 02_ARCHITECTURE_MAP.md
│   ├── 03_TASKS_FOR_CLAUDE.md
│   ├── 04_CODE_STANDARDS.md
│   ├── 05_CLI_COMMANDS.md
│   ├── 06_WORKER_SPEC.md
│   ├── 07_AI_INTEGRATION.md
│   ├── 08_GIT_WORKFLOW.md
│   └── 09_AUTOMATION_PLAN.md
│
├── termux-cli/
│   ├── warnet                  # Main CLI entrypoint
│   └── config.json             # Runtime config
│
├── worker/
│   ├── index.js                # Cloudflare Worker
│   ├── commands/
│   │   ├── ai.js               # NVIDIA Nemotron
│   │   ├── gh.js               # GitHub operations
│   │   └── sys.js              # System operations
│   └── utils/
│       ├── validate.js         # Security validation
│       ├── respond.js          # Response formatting
│       └── nemotron.js         # NVIDIA client
│
├── scripts/
│   ├── claude-open.sh          # Open Claude
│   ├── gh-push.sh              # Git automation
│   └── gh-pull.sh
│
├── package.json
└── README.md
```

## Configuration

### ~/.claude-cli/config.json
```json
{
  "api_key": "your-api-key",
  "worker_url": "https://your-worker.workers.dev",
  "nemotron_api_key": "your-nemotron-key",
  "github_token": "your-github-token",
  "tier": 2,
  "cache_dir": "~/.claude-cli/cache"
}
```

## Security

- All network communication encrypted (AES-256-GCM)
- API keys never logged
- Input validation on all boundaries
- Rate limiting via Cloudflare KV
- Audit logging with WORM storage
- Data tier classification & enforcement

## Contributing

1. Create feature branch from `claude/termux-cli-cloudflare-nemotron-pve6ca`
2. Make changes & add tests
3. Run `npm run lint && npm run test`
4. Commit with descriptive message
5. Push and create PR

See [08_GIT_WORKFLOW.md](docs/08_GIT_WORKFLOW.md) for details.

## License

MIT - See LICENSE file

## Support

- Issues: https://github.com/tewartech-node/claude-command-cli/issues
- Discussions: https://github.com/tewartech-node/claude-command-cli/discussions

## Status

🚀 Active Development - v0.1.0

Current Phase: Foundation & Scaffolding
Next: Core CLI & Worker Implementation
