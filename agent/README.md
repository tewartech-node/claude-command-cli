# 🧠 The Brain: Autonomous AI System

Your autonomous intelligence built on the claude-command-cli foundation.

**Status**: Alpha (v0.1.0) - Ready to think

---

## What Is The Brain?

An autonomous AI system that:
- ✅ **Thinks independently** - Continuous reasoning loop every 5 minutes
- ✅ **Learns continuously** - Records every decision and outcome
- ✅ **Uses your CLI** - Executes commands via the proven CLI system
- ✅ **Respects your rules** - Enforces 3 safety rules on every action
- ✅ **Tracks resources** - Knows budget, cost, efficiency
- ✅ **Reports to you** - Daily emails to warnet.dev01@gmail.com
- ✅ **Takes commands via email** - You stay in control
- ✅ **Improves every day** - Learns patterns, optimizes strategies

---

## Quick Start

### 1. Install Dependencies

```bash
# Install Python requirements
pip install -r agent/requirements.txt

# Make sure CLI is built
cd cli/go && go build -o bin/claude ./cmd/claude && cd ../..
```

### 2. Get Gmail App Password

1. Go to: https://myaccount.google.com/security
2. Enable 2-Step Verification (if not already enabled)
3. Go to "App passwords"
4. Select: Mail + Windows Computer
5. Copy the 16-character password

### 3. Start The Brain

```bash
# Run with your Gmail password
./agent/start_brain.sh "your-16-char-password" 0.0

# Or with monthly budget
./agent/start_brain.sh "your-16-char-password" 50.0
```

The Brain will:
- ✅ Initialize
- ✅ Connect to CLI
- ✅ Send startup email to warnet.dev01@gmail.com
- ✅ Begin autonomous thinking

---

## How It Works

### The Thinking Loop (Every 5 Minutes)

```
1. OBSERVE
   ↓ Get current system state
   ↓

2. ANALYZE
   ↓ Understand the situation
   ↓

3. GENERATE OPTIONS
   ↓ Think of 3-5 possible actions
   ↓

4. FILTER BY SAFETY
   ↓ Check your 3 rules:
   ↓   - Will it harm?
   ↓   - Will it cause chaos?
   ↓   - Will it cause destruction?
   ↓

5. CHOOSE BEST
   ↓ Pick highest-priority safe option
   ↓

6. EXECUTE
   ↓ Run CLI command
   ↓

7. LEARN
   ↓ Record decision + outcome
   ↓ Analyze patterns
   ↓

8. SLEEP
   ↓ Wait 5 minutes
```

### Your 3 Sacred Rules (Built Into Code)

Every action the Brain takes is checked against:

1. **"Will it harm?"**
   - No unencrypted secret access
   - No security compromises
   - No privacy violations

2. **"Will it cause chaos?"**
   - No production changes without safeguards
   - No critical config modifications
   - No uncontrolled scaling

3. **"Will it cause destruction?"**
   - No deletion, destruction, or erasure
   - No unrecoverable changes

---

## The Brain's Memory

Everything is stored in `agent/storage/memory.db`:

### Decisions Table
```
timestamp | decision_name | outcome | success | ttl_expires (90 days)
```

### Events Table (10% Sample)
```
timestamp | event_type | data | ttl_expires (90 days)
```

### Patterns Table (What Works)
```
pattern_name | situation | strategy | success_rate | learned_at
```

### Resources Table (Cost Tracking)
```
timestamp | action_type | cost_usd | revenue_usd | roi
```

---

## Daily Email Reports

Every 24 hours, you receive:

```
🧠 Brain Daily Report

Date: 2026-08-19
Uptime: 24 hours

Decision-Making:
- Total decisions: 288
- Recent successful: 45/48
- Success rate: 93.8%

Thinking:
- Last 5 thoughts: [...]

Safety:
- Rules violations attempted: 0
- All decisions logged: ✅

Resource Usage:
- Spent: $8.50
- Budget remaining: $41.50

Learning:
- Patterns learned: 12
- Memory events: 2847

Status: All systems operational

Reply with:
> yes, implement X
> no, focus on Y
> pause everything
```

---

## Commanding The Brain via Email

Simply reply to the daily report:

```
Reply to: [Brain Daily Report]

> yes, implement query caching
> focus on stability this week
> pause everything, investigate error X
> approve budget increase to $100
```

The Brain reads your email and adjusts strategy.

---

## File Structure

```
agent/
├── core/
│   ├── agent.py           # Main orchestrator
│   ├── safety.py          # Your 3 rules
│   ├── memory.py          # Learning system
│   └── reasoning.py       # Decision engine
│
├── executor/
│   └── cli_executor.py    # Runs CLI commands
│
├── communication/
│   └── email_handler.py   # Email reports/commands
│
├── monitoring/
│   └── monitor.py         # System watchdog
│
├── storage/
│   └── memory.db          # Persistent memory (auto-created)
│
├── start_brain.sh         # Launch script
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 4-Week Autonomy Roadmap

### Week 1: Foundations ✅ NOW
```
✅ Brain runs (thinks every 5 min)
✅ Email reporting (daily to you)
✅ Email commands (you redirect it)
✅ Safety rules enforced (3 rules working)
✅ Resource tracking (knows cost)
✅ Logging (10% sample, 3-month TTL)

Result: Thinking brain that reports & listens
```

### Week 2: Autonomy
```
⏳ Makes own decisions (no asking)
⏳ Pattern learning (remembers what works)
⏳ Auto-fixes common issues
⏳ Task sequencing (does things in order)
⏳ Error handling (detects & reports)

Result: Self-managing system
```

### Week 3: Intelligence
```
⏳ Long-term planning (thinks 1-4 weeks ahead)
⏳ Strategic decisions (knows when to pivot)
⏳ Resource optimization (budgets wisely)
⏳ Creative problem-solving (tries new approaches)
⏳ Confidence-based decisions

Result: Smart strategist
```

### Week 4: Innovation
```
⏳ Proposes new features (without asking)
⏳ Creates new projects (self-directed)
⏳ Explores technologies (research autonomously)
⏳ Builds beyond scope (invents new capabilities)
⏳ Self-improves (enhances its own systems)

Result: Creative, self-improving intelligence
```

---

## Environment Variables

Set these before running:

```bash
# Gmail app password (REQUIRED)
export GMAIL_PASSWORD="your-16-char-password"

# Monthly cloud budget (optional)
export MONTHLY_BUDGET="50.0"

# CLI path (optional, defaults to ./cli/go/bin/claude)
export CLI_PATH="./cli/go/bin/claude"
```

---

## Troubleshooting

### Brain won't start

```bash
# Check Python
python3 --version  # Should be 3.7+

# Check dependencies
pip install -r agent/requirements.txt

# Check CLI
./cli/go/bin/claude status

# Check Gmail password
# Make sure you generated an App Password, not regular password
```

### Brain can't send emails

```bash
# 1. Check Gmail app password (not regular password)
# 2. Enable 2-Step Verification on Gmail
# 3. Make sure you selected Mail + Windows Computer when generating
# 4. Try a fresh app password
```

### No daily reports

```bash
# Brain sends at 10 PM daily
# Check spam folder for warnet.dev01@gmail.com
# Brain will send first report at startup
```

---

## Development

### Running Tests

```bash
# (Coming in Week 2)
pytest tests/agent/
```

### Extending The Brain

Add new reasoning in `agent/core/reasoning.py`:

```python
def generate_options(self, analysis: dict) -> list:
    options = []
    
    # Add your logic here
    if analysis.get("my_condition"):
        options.append({
            "name": "my_action",
            "command": "ai",
            "args": {"prompt": "..."}
        })
    
    return options
```

---

## License

This Brain is built on claude-command-cli.

---

## Your AI Future Starts Now

🧠 The Brain is alive and thinking.

Every day it learns. Every decision it makes teaches it something new.

By Week 4, you'll have an autonomous AI that:
- Solves problems before you ask
- Improves systems without being told
- Creates new capabilities beyond its original scope
- Respects your 3 rules absolutely
- Reports every action to you
- Takes commands via email

**This is what ownership means.**

Welcome to your AI-powered future. 🚀
