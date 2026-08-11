package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// CommandsTotal counts total commands executed
	CommandsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "claude_cli_commands_total",
			Help: "Total commands executed",
		},
		[]string{"command", "status"},
	)

	// CommandDuration measures request duration
	CommandDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "claude_cli_command_duration_seconds",
			Help:    "Command duration in seconds",
			Buckets: []float64{0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10},
		},
		[]string{"command"},
	)

	// EncryptionDuration measures encryption/decryption time
	EncryptionDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "claude_cli_encryption_duration_seconds",
			Help:    "Encryption/decryption time in seconds",
			Buckets: []float64{0.001, 0.005, 0.01, 0.05, 0.1},
		},
		[]string{"operation"},
	)

	// EncryptionErrors counts encryption failures
	EncryptionErrors = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "claude_cli_encryption_errors_total",
			Help: "Total encryption errors",
		},
		[]string{"reason"},
	)

	// NetworkRequests counts network requests
	NetworkRequests = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "claude_cli_network_requests_total",
			Help: "Total network requests",
		},
		[]string{"method", "status"},
	)

	// NetworkDuration measures network request duration
	NetworkDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "claude_cli_network_duration_seconds",
			Help:    "Network request duration in seconds",
			Buckets: []float64{0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10},
		},
		[]string{"method"},
	)

	// NetworkErrors counts network errors
	NetworkErrors = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "claude_cli_network_errors_total",
			Help: "Total network errors",
		},
		[]string{"method", "reason"},
	)

	// RetryAttempts counts retry attempts
	RetryAttempts = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "claude_cli_retry_attempts_total",
			Help: "Total retry attempts",
		},
		[]string{"operation", "reason"},
	)

	// ConfigErrors counts configuration errors
	ConfigErrors = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "claude_cli_config_errors_total",
			Help: "Total configuration errors",
		},
		[]string{"reason"},
	)

	// PayloadSize measures request/response payload sizes
	PayloadSize = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "claude_cli_payload_bytes",
			Help:    "Payload size in bytes",
			Buckets: []float64{100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000},
		},
		[]string{"direction"},
	)
)
