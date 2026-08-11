# Prometheus Metrics Guide

This package exposes Prometheus metrics for monitoring the Claude CLI and server operations.

## Available Metrics

### Command Metrics

**`claude_cli_commands_total`** (Counter)
- Total commands executed
- Labels: `command` (e.g., "ai", "gh"), `status` (e.g., "started", "success", "error")
- Example: `claude_cli_commands_total{command="ai",status="success"} 42`

**`claude_cli_command_duration_seconds`** (Histogram)
- Command execution duration
- Labels: `command`
- Buckets: 0.01s, 0.05s, 0.1s, 0.5s, 1s, 2s, 5s, 10s
- Example: `claude_cli_command_duration_seconds_bucket{command="ai",le="0.1"} 15`

### Encryption Metrics

**`claude_cli_encryption_duration_seconds`** (Histogram)
- Encryption/decryption operation duration
- Labels: `operation` (e.g., "encrypt", "decrypt")
- Buckets: 0.001s, 0.005s, 0.01s, 0.05s, 0.1s
- Example: `claude_cli_encryption_duration_seconds_bucket{operation="encrypt",le="0.01"} 8`

**`claude_cli_encryption_errors_total`** (Counter)
- Total encryption failures
- Labels: `reason` (e.g., "invalid_nonce", "tag_mismatch")
- Example: `claude_cli_encryption_errors_total{reason="tag_mismatch"} 1`

### Network Metrics

**`claude_cli_network_requests_total`** (Counter)
- Total network requests made
- Labels: `method` (e.g., "POST", "GET"), `status` (e.g., "200", "500")
- Example: `claude_cli_network_requests_total{method="POST",status="200"} 52`

**`claude_cli_network_duration_seconds`** (Histogram)
- Network request duration
- Labels: `method`
- Buckets: 0.01s, 0.05s, 0.1s, 0.5s, 1s, 2s, 5s, 10s
- Example: `claude_cli_network_duration_seconds_bucket{method="POST",le="0.5"} 48`

**`claude_cli_network_errors_total`** (Counter)
- Total network errors
- Labels: `method`, `reason` (e.g., "timeout", "connection_refused")
- Example: `claude_cli_network_errors_total{method="POST",reason="timeout"} 2`

### Retry Metrics

**`claude_cli_retry_attempts_total`** (Counter)
- Total retry attempts made
- Labels: `operation`, `reason` (e.g., "rate_limited", "network_error")
- Example: `claude_cli_retry_attempts_total{operation="execute",reason="rate_limited"} 5`

### Configuration Metrics

**`claude_cli_config_errors_total`** (Counter)
- Total configuration errors
- Labels: `reason` (e.g., "not_configured", "invalid_key")
- Example: `claude_cli_config_errors_total{reason="not_configured"} 1`

### Payload Metrics

**`claude_cli_payload_bytes`** (Histogram)
- Request/response payload size distribution
- Labels: `direction` (e.g., "request", "response")
- Buckets: 100B, 500B, 1KB, 5KB, 10KB, 50KB, 100KB, 500KB, 1MB
- Example: `claude_cli_payload_bytes_bucket{direction="request",le="1000"} 22`

## Querying Metrics

### Grafana Examples

**Total commands by status:**
```promql
sum(rate(claude_cli_commands_total[5m])) by (status)
```

**Command latency (p95):**
```promql
histogram_quantile(0.95, rate(claude_cli_command_duration_seconds_bucket[5m]))
```

**Encryption error rate:**
```promql
rate(claude_cli_encryption_errors_total[5m])
```

**Network error percentage:**
```promql
100 * (sum(rate(claude_cli_network_errors_total[5m])) / sum(rate(claude_cli_network_requests_total[5m])))
```

**Average command duration by type:**
```promql
sum(rate(claude_cli_command_duration_seconds_sum[5m])) by (command)
/
sum(rate(claude_cli_command_duration_seconds_count[5m])) by (command)
```

## Exposing Metrics

### Option 1: Standalone Metrics Server

```go
package main

import (
	"log"
	"github.com/tewartech-node/claude-cli/pkg/metrics"
)

func main() {
	if err := metrics.StartMetricsServer(":9090"); err != nil {
		log.Fatal(err)
	}
	select {} // Block forever
}
```

Then access metrics at `http://localhost:9090/metrics`

### Option 2: Integrate into Existing HTTP Server

```go
package main

import (
	"net/http"
	"github.com/tewartech-node/claude-cli/pkg/metrics"
)

func main() {
	http.Handle("/metrics", metrics.Handler())
	http.ListenAndServe(":8080", nil)
}
```

## Integration with Commands

Metrics are automatically recorded in command handlers:

```go
import (
	"time"
	"github.com/tewartech-node/claude-cli/pkg/metrics"
)

func handleCommand() error {
	start := time.Now()
	
	// Record command start
	metrics.CommandsTotal.WithLabelValues("mycommand", "started").Inc()
	
	// Do work...
	
	// Record completion
	duration := time.Since(start).Seconds()
	metrics.CommandDuration.WithLabelValues("mycommand").Observe(duration)
	metrics.CommandsTotal.WithLabelValues("mycommand", "success").Inc()
	
	return nil
}
```

## Best Practices

1. **Always use labels**: Labels make queries more powerful
2. **Record duration in seconds**: Prometheus convention
3. **Use appropriate metric types**:
   - Counter: Things that only increase (errors, requests)
   - Histogram: Request duration, payload sizes
   - Gauge: Current values (queue depth, active connections)
4. **Keep cardinality low**: Don't create infinite label combinations
5. **Add context**: Use structured logging alongside metrics

## Monitoring & Alerting

### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'claude-cli'
    static_configs:
      - targets: ['localhost:9090']
```

### Alert Rules

```yaml
groups:
  - name: claude-cli
    rules:
      - alert: HighEncryptionErrorRate
        expr: rate(claude_cli_encryption_errors_total[5m]) > 0.01
        for: 5m
        annotations:
          summary: "Encryption errors detected"
      
      - alert: HighNetworkErrorRate
        expr: |
          100 * (sum(rate(claude_cli_network_errors_total[5m])) / 
                  sum(rate(claude_cli_network_requests_total[5m]))) > 5
        for: 5m
        annotations:
          summary: "Network error rate > 5%"
      
      - alert: SlowCommands
        expr: histogram_quantile(0.95, claude_cli_command_duration_seconds_bucket) > 5
        for: 5m
        annotations:
          summary: "Commands taking > 5s at p95"
```

## Performance Impact

- Minimal overhead: ~0.1ms per metric recording
- Async publishing: Metrics buffered, not blocking
- No allocation: Pre-allocated metric objects
- Thread-safe: All metrics are concurrent-safe

## Related Documentation

- [Structured Logging Guide](../log/README.md)
- [Health Check Endpoints](../health/)
- [Prometheus Official Docs](https://prometheus.io/docs/)
