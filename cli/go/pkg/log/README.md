# Structured Logging Guide

All logs in claude-cli are **structured JSON** for easy parsing, searching, and alerting.

## Initialization

```go
import "github.com/tewartech-node/claude-cli/pkg/log"

func main() {
    // Initialize logging (set to "debug", "info", "warn", "error")
    if err := log.Init("info"); err != nil {
        panic(err)
    }
    defer log.Sync()
}
```

## Request ID Pattern

Every operation gets a unique `request_id` that follows it through the system:

```
CLI:    [REQUEST_ID=abc123] Starting AI command
CLI:    [REQUEST_ID=abc123] Encrypting payload
SERVER: [REQUEST_ID=abc123] Received request
SERVER: [REQUEST_ID=abc123] Calling Claude API
CLI:    [REQUEST_ID=abc123] Response received
```

**Why**: Trace a single user request across CLI → Server → Claude API

```go
requestID := log.GetRequestID()  // Generate unique ID
log.Infof(requestID, "Starting command execution")
```

## Examples

### Simple Info Log
```go
log.Infof(requestID, "User executed command: %s", command)
// Output: {"timestamp":"2026-08-11T...", "level":"info", "message":"User executed command: ai", "request_id":"123-456"}
```

### Command Execution
```go
start := time.Now()
log.CommandStarted(requestID, "ai", map[string]interface{}{
    "prompt_length": 256,
    "model": "claude-3-5-sonnet",
})

// ... do work ...

duration := time.Since(start).Milliseconds()
if err != nil {
    log.CommandFailed(requestID, "ai", duration, err)
} else {
    log.CommandCompleted(requestID, "ai", duration)
}
```

### Encryption Operations
```go
log.EncryptionStarted(requestID, len(payload))

// ... encryption ...

log.EncryptionCompleted(requestID, durationMs)
// Or on error:
log.EncryptionFailed(requestID, err)  // Triggers alert!
```

### Network Operations
```go
log.NetworkRequest(requestID, "POST", "https://api.example.com/command")

// ... network call ...

if err != nil {
    log.NetworkError(requestID, err, retryCount)
} else {
    log.NetworkResponse(requestID, statusCode, durationMs)
}
```

### Structured Context (Complex Logging)
```go
log.InfoContext(requestID, "processing_complete", map[string]interface{}{
    "items_processed": 1024,
    "errors": 2,
    "success_rate": 99.8,
    "duration_ms": 245,
})

// Or errors:
log.ErrorContext(requestID, "validation_failed", map[string]interface{}{
    "field": "api_key",
    "reason": "invalid_format",
    "expected": "sk-*",
})
```

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed troubleshooting | Nonce size, encryption algorithm |
| **INFO** | User actions & results | Command started, command completed |
| **WARN** | Unexpected but recoverable | Retry after network error |
| **ERROR** | Operation failed | Encryption failure, API error |
| **FATAL** | System cannot continue | Config not found, fatal panic |

## Querying Logs

### Find by Request ID
```bash
# If logs go to stdout (during testing)
./claude ai "test" 2>&1 | jq '.request_id'

# In production (using ELK Stack):
# Kibana query: request_id:"abc123"
```

### Find Encryption Failures
```bash
# Production logs:
# { "event": "encryption_failed", "alert": true }
# This triggers automated alerts!
```

### Find Slow Requests
```bash
# Find requests over 1 second:
# duration_ms > 1000 AND level: "info"
```

## Log Schema

Every log includes:

```json
{
  "timestamp": "2026-08-11T18:51:30.123Z",  // ISO 8601
  "level": "info",                           // DEBUG, INFO, WARN, ERROR
  "logger": "claude.cli",
  "caller": "commands/ai.go:42",             // Where log was called
  "function": "runAI",                       // Function name
  "message": "Command completed",            // Main message
  "request_id": "1723398690-1",             // Trace ID
  
  // Plus any additional fields (command, duration_ms, etc.)
  "command": "ai",
  "duration_ms": 234
}
```

## Best Practices

### ✅ DO

```go
// Include request ID on everything
log.Infof(requestID, "action=%s status=%s", action, status)

// Log at start and end of operations
log.CommandStarted(requestID, "ai", args)
// ... work ...
log.CommandCompleted(requestID, "ai", durationMs)

// Use structured fields for complex data
log.InfoContext(requestID, "message", map[string]interface{}{
    "key1": value1,
    "key2": value2,
})

// Alert on critical failures
log.EncryptionFailed(requestID, err)  // Triggers PagerDuty
```

### ❌ DON'T

```go
// Don't use fmt.Printf or println
fmt.Println("Debug info")  // ❌ Not structured, hard to parse

// Don't log without request ID (loses traceability)
log.Infof("", "Something happened")  // ❌ request_id=""

// Don't log sensitive data
log.Infof(requestID, "API Key: %s", apiKey)  // ❌ Security issue!

// Don't create custom log levels
log.Fatal(...) // ✅ Only use: Info, Warn, Error
```

## Performance Notes

- **Minimal overhead**: ~1ms per log entry
- **Async writing**: Logs buffered for performance
- **No allocation**: Uses pre-allocated buffers (production-safe)
- **JSON encoding**: Fast native encoder (not reflection-based)

## Monitoring & Alerts

Logs with `"alert": true` automatically trigger:

| Condition | Alert | Example |
|-----------|-------|---------|
| `encryption_failed` | ⚠️ Page on-call | Nonce collision detected |
| `network_error` (>3 retries) | ⚠️ Alert | Server unreachable |
| `command_failed` (rate > 5%) | 🔴 Critical | High error rate |

---

## Integration with Observability Stack

### Prometheus Metrics
Each log event generates metrics:
- `claude_commands_total` - Counter
- `claude_command_duration_seconds` - Histogram
- `claude_encryption_errors_total` - Counter

### ELK Stack (Production)
Logs ship to Elasticsearch for:
- Full-text search
- Kibana dashboards
- Historical analysis
- Trend detection

### PagerDuty Alerts
Critical logs (alert: true) trigger:
- Immediate notification
- On-call escalation
- Auto-remediation workflows

---

## Testing Logs

```go
// In tests, logs still output to stdout as JSON
// Use `jq` to parse:
output, _ := runCLI("ai", "test")
json := parseJSON(output)
assert.Equal(t, json["status"], "success")
```

---

**Start using structured logging in every new function. It's not optional - it's the foundation for observability.**
