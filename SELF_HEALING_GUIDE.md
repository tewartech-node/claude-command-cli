# Self-Healing Code Module Guide
## Autonomous AI Training & Development Strategy

The Brain now includes a comprehensive **self-healing system** that continuously monitors, diagnoses, repairs, and improves its own code during runtime. This enables the system to achieve expert-level AI training readiness.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    Self-Healing System                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. DIAGNOSTIC ENGINE                                            │
│     ├─ Routine health scans (every 5 minutes)                    │
│     ├─ Performance monitoring (CPU, memory, disk)                │
│     ├─ Database integrity checks                                │
│     ├─ Decision quality analysis                                 │
│     ├─ Learning health monitoring                               │
│     └─ Network connectivity checks                               │
│                        ↓                                          │
│  2. CODE ANALYZER (AST-based)                                    │
│     ├─ Detects dead code                                         │
│     ├─ Finds bare except clauses                                 │
│     ├─ Identifies unused imports                                 │
│     ├─ Checks code complexity (McCabe)                           │
│     ├─ Finds security issues                                     │
│     └─ Extracts dependency graph                                 │
│                        ↓                                          │
│  3. SELF-REPAIR ENGINE                                           │
│     ├─ Analyzes issues from diagnostics                          │
│     ├─ Generates targeted fixes                                  │
│     ├─ Applies code patches safely                               │
│     ├─ Tests repairs before deployment                           │
│     ├─ Logs all repairs with rollback info                       │
│     └─ Auto-repair enabled by default                            │
│                        ↓                                          │
│  4. BEHAVIOR MONITOR (Real-time)                                 │
│     ├─ Tracks success rates                                      │
│     ├─ Monitors confidence levels                                │
│     ├─ Detects anomalies in metrics                              │
│     ├─ Triggers alerts on deviations                             │
│     └─ Calculates health score                                   │
│                        ↓                                          │
│  5. CONSTRAINT SYSTEM                                            │
│     ├─ Defines acceptable system states                          │
│     ├─ Validates behavior against constraints                    │
│     ├─ Auto-fixes violations                                     │
│     ├─ Generates compliance reports                              │
│     └─ Supports custom constraints                               │
│                        ↓                                          │
│  6. VERSION MANAGER (Git-based)                                  │
│     ├─ Creates checkpoints of good states                        │
│     ├─ Enables rollback to known good versions                   │
│     ├─ Tracks code changes over time                             │
│     ├─ Tags stable releases                                      │
│     └─ Provides blame/diff analysis                              │
│                        ↓                                          │
│  7. HEALTH DASHBOARD                                             │
│     ├─ Real-time visualization                                   │
│     ├─ Comprehensive health scoring                              │
│     ├─ Alert management                                          │
│     └─ Web-based monitoring                                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Key Features

### 1. Automatic Diagnostics
Runs every 5 minutes:
- **Performance**: CPU, memory, disk usage
- **Database**: Integrity checks, fragmentation, size monitoring
- **Code Quality**: Static analysis, security issues
- **Learning**: Pattern extraction rate, confidence levels
- **Decisions**: Success rate, quality metrics
- **Network**: Connectivity and API health

### 2. Code Analysis (AST-based)
- Parses Python AST to understand code structure
- Detects 8+ types of code issues
- Extracts function signatures and dependencies
- Identifies security vulnerabilities
- Tracks code complexity (McCabe cyclomatic)

### 3. Automatic Self-Repair
Fixes issues including:
- **Database fragmentation** → Auto-vacuum
- **Bare except clauses** → Proper exception handling
- **Large database** → Archive old data
- **Memory leaks** → GC optimization
- **Performance issues** → Task throttling
- **Code issues** → Automatic patching

### 4. Real-Time Behavior Monitoring
Tracks:
- Success rate (24h, 7d, 30d trends)
- Decision confidence progression
- Decision velocity (decisions/hour)
- Email processing rate
- Pattern extraction rate
- Memory trends
- Response latency
- Error rates

### 5. Constraint Validation
Built-in constraints:
- Success rate ≥ 60% (critical)
- Average confidence ≥ 0.5 (high)
- Database < 1GB (medium)
- Memory < 500MB (high)
- CPU < 80% (medium)
- Decisions ≥ 1/hour (low)
- Patterns ≥ 1/day (low)
- Error rate < 5% (high)
- No critical code issues (critical)
- Database integrity = ok (critical)

### 6. Git-Based Version Control
- **Checkpoints**: Create snapshots before risky changes
- **Rollback**: Revert to known good states
- **Tags**: Mark stable versions (stable-v1, stable-v2)
- **Blame**: Track origin of issues
- **Diff**: Compare code changes
- **Recovery Snapshots**: Full system state capture

### 7. Health Dashboard
Web UI showing:
- Overall health score (0-100)
- Diagnostics summary
- Auto-repair statistics
- Active alerts
- Performance metrics
- Constraint compliance
- Critical issues list
- Auto-refresh every 30 seconds

---

## How It Works: Self-Repair Cycle

```
┌─────────────────────────────────────┐
│  1. DIAGNOSTIC SCAN (5-min cycle)   │
│     ├─ Health checks                │
│     ├─ Performance monitoring       │
│     ├─ Code analysis                │
│     └─ Issue identification         │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  2. ISSUE CLASSIFICATION            │
│     ├─ Categorize (database,        │
│     │   performance, code, etc)     │
│     ├─ Assess severity              │
│     └─ Determine fix strategy       │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  3. REPAIR ENGINE                   │
│     ├─ Generate fix                 │
│     ├─ Create checkpoint first      │
│     ├─ Apply patch                  │
│     ├─ Verify with tests            │
│     └─ Log repair action            │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  4. BEHAVIOR MONITORING             │
│     ├─ Collect metrics              │
│     ├─ Detect anomalies             │
│     ├─ Compare to baseline          │
│     └─ Generate alerts              │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  5. CONSTRAINT VALIDATION           │
│     ├─ Check all constraints        │
│     ├─ Assess compliance            │
│     ├─ Auto-fix violations          │
│     └─ Generate compliance report   │
└────────────┬────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│  6. LEARNING & ADAPTATION           │
│     ├─ Update baseline metrics      │
│     ├─ Adjust thresholds            │
│     ├─ Learn from repairs           │
│     └─ Improve future diagnoses     │
└─────────────────────────────────────┘
```

---

## Usage Examples

### Start Self-Healing System

```python
from agent.self_healing import (
    DiagnosticEngine,
    SelfRepairEngine,
    BehaviorMonitor,
    ConstraintSystem,
    HealthDashboard
)

# Initialize system
diagnostic = DiagnosticEngine()
repair = SelfRepairEngine()
monitor = BehaviorMonitor()
constraints = ConstraintSystem()
dashboard = HealthDashboard()

# Run full diagnostic and repair cycle
cycle_result = repair.full_repair_cycle()
print(f"Repairs attempted: {cycle_result['repairs_attempted']}")
print(f"Repairs successful: {cycle_result['repairs_successful']}")

# Start continuous monitoring
monitor.start_monitoring()

# Check constraint compliance
metrics = monitor.collect_metrics()
compliance = constraints.check_all_constraints(metrics)
print(f"Compliance score: {compliance['passed']}/{compliance['total_constraints']}")
```

### Monitor System Health

```python
# Get real-time health report
report = dashboard.get_comprehensive_health_report()

print(f"Health Score: {report['metrics']['success_rate_24h']}%")
print(f"Critical Issues: {report['diagnostics']['unresolved_critical']}")
print(f"Auto-Repairs (24h): {report['repairs']['successful']}")
print(f"Active Alerts: {report['alerts']['total_active']}")
```

### Rollback to Known Good State

```python
from agent.self_healing import VersionManager

version = VersionManager()

# Get recent commits
commits = version.get_recent_commits(10)
print("Recent versions:")
for commit in commits:
    print(f"  {commit['hash'][:7]} - {commit['message']}")

# Rollback to specific commit
result = version.rollback_to_commit(
    commit_hash="abc1234",
    create_backup=True  # Backs up current state first
)
print(f"Rollback: {result['success']}")
```

### View Health Dashboard

```python
# Generate HTML dashboard
html = dashboard.get_dashboard_html()

# Save to file
with open("dashboard.html", "w") as f:
    f.write(html)

# Open in browser or use Flask to serve
```

### Define Custom Constraints

```python
# Define custom constraint at runtime
constraints.define_custom_constraint(
    name="peak_accuracy",
    description="Peak accuracy must stay above 90%",
    validator_func=lambda val: val >= 90,
    severity="critical"
)

# Check custom constraint
result = constraints.check_constraint("peak_accuracy", 92.5)
print(f"Peak accuracy constraint: {result['satisfied']}")
```

---

## Configuration

### Environment Variables

```bash
# Enable/disable auto-repair (default: true)
export AUTO_REPAIR=true

# Database path
export DB_PATH=./agent/storage/memory.db

# Diagnostic scan interval (seconds)
export DIAGNOSTIC_INTERVAL=300

# Monitoring interval (seconds)
export MONITOR_INTERVAL=60

# Alert threshold (deviation from baseline)
export ALERT_THRESHOLD=0.7
```

### Customize Repair Strategies

Edit `agent/self_healing/self_repair.py`:

```python
def _repair_custom_issue(self) -> bool:
    """Add custom repair logic"""
    # Your diagnostic and repair logic here
    self._log_repair("custom", "issue_type", "Repair description")
    return True
```

---

## Metrics Tracked

### System Metrics
- CPU usage (%)
- Memory usage (MB)
- Disk usage (%)
- Database size (MB)

### Learning Metrics
- Success rate (24h, 7d, 30d)
- Average confidence (0-1)
- Patterns learned (total, daily)
- Decision velocity (decisions/hour)

### Quality Metrics
- Error rate (%)
- Alert count (active)
- Constraint violations
- Code quality issues

### Performance Metrics
- Response latency (ms)
- Email processing rate (emails/hour)
- Pattern extraction rate (patterns/hour)
- Memory trend (stable/increasing/decreasing)

---

## Diagnostic Issues Found

### Performance Issues
- High CPU usage (>80%)
- Memory pressure (>85% used)
- Low disk space (<10% free)
- Memory leaks detected
- High memory consumption (>500MB)

### Database Issues
- Integrity check failures
- Large database (>500MB)
- Database fragmentation

### Code Issues
- Dead code (unused functions)
- Bare except clauses
- Unused imports
- High complexity functions
- Security vulnerabilities

### Learning Issues
- No patterns learned yet
- Low average confidence (<0.5)
- Low success rate (<50% or <70%)
- Many unrated decisions

### Network Issues
- Network connectivity lost
- API health check failures

---

## Repair Actions

### Automatic Repairs
1. **VACUUM** - Defragment database
2. **ARCHIVE** - Remove old data (>90 days)
3. **FIX_BARE_EXCEPT** - Replace bare excepts with proper handlers
4. **ADD_DOCSTRINGS** - Generate missing documentation
5. **OPTIMIZE_GC** - Increase garbage collection frequency
6. **THROTTLE_TASKS** - Reduce background task intensity
7. **REDUCE_BUFFERS** - Shrink memory buffer sizes

### Recommended Repairs
Flagged for user action:
- CPU optimization (manual)
- Memory optimization (manual)
- Code refactoring (manual)
- Architecture changes (manual)

---

## Alerts & Notifications

### Alert Types
- **Anomaly Detection**: Metrics deviate from baseline
- **Constraint Violation**: System violates defined constraints
- **Critical Issue**: Unresolved critical diagnostic issues
- **Performance Degradation**: Metrics dropping over time

### Alert Severity
- **CRITICAL**: Immediate action required
- **HIGH**: Action needed soon
- **MEDIUM**: Monitor closely
- **LOW**: Informational

### Managing Alerts

```python
# Get active alerts
alerts = monitor.get_active_alerts()

# Acknowledge alert
monitor.acknowledge_alert(alert_id=1)

# View alert history
recent = diagnostic.get_recent_diagnostics(hours=24)
```

---

## Integration with Training Pipeline

The self-healing system integrates with your AI training:

1. **Pre-Training**: System health check, constraints validation
2. **During Training**: Continuous monitoring, anomaly detection
3. **Post-Training**: Repair any issues, archive old data
4. **Between Iterations**: Learn from repairs, update baselines

This ensures your training infrastructure stays healthy, performant, and reproducible.

---

## Advanced Features

### Learning from Repairs
The system learns which repairs work best:
- Tracks successful repair patterns
- Adjusts future repair strategies
- Improves diagnosis accuracy over time

### Predictive Diagnostics
Based on historical patterns:
- Predicts potential issues before they occur
- Suggests preventive repairs
- Optimizes repair timing

### Multi-Device Coordination
When running on multiple devices:
- Syncs diagnostics across network
- Shares repair strategies
- Aggregates metrics for network health

### Reproducibility
- Every repair is logged with full details
- Checkpoints enable reproduction of issues
- Git blame helps identify root causes

---

## Troubleshooting

### System reports false positives
- Adjust alert threshold: `ALERT_THRESHOLD=0.8` (less sensitive)
- Update baseline: Delete old metrics from `behavior_metrics` table
- Add custom constraint for your use case

### Auto-repair failed
- Check repair logs: `agent/self_healing/repair_log` table
- Review error details in database
- Manually rollback: Use VersionManager to revert changes

### Repairs not being applied
- Check if AUTO_REPAIR is enabled: `os.getenv("AUTO_REPAIR")`
- Verify database permissions
- Check for rollback blocks

### Performance overhead from monitoring
- Increase MONITOR_INTERVAL (default 60s)
- Disable unnecessary metrics collection
- Use background monitoring thread

---

## Dashboard Access

View the self-healing dashboard:

```python
from agent.self_healing import HealthDashboard

dashboard = HealthDashboard()
html = dashboard.get_dashboard_html()

# Save and open in browser
with open("/tmp/health.html", "w") as f:
    f.write(html)

# Or serve with Flask
from flask import Flask
app = Flask(__name__)

@app.route("/health")
def health():
    return dashboard.get_dashboard_html()

app.run(port=3001)
```

Then visit: `http://localhost:3001/health`

---

## Success Criteria

Your system is ready for advanced AI training when:

✅ Health score stays ≥ 85%
✅ Success rate ≥ 85%
✅ Average confidence ≥ 0.75
✅ Unresolved critical issues = 0
✅ Auto-repair success rate ≥ 80%
✅ All constraints satisfied
✅ Error rate < 2%
✅ System uptime > 99%

---

## Next Steps

1. **Deploy** the self-healing system
2. **Monitor** for 24-48 hours to establish baselines
3. **Review** repair history and adjust strategies
4. **Enable** on production for autonomous operation
5. **Iterate** based on system feedback

This transforms your AI system into a self-improving, self-healing intelligent agent. 🚀
