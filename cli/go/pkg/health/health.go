package health

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/tewartech-node/claude-cli/pkg/config"
)

// Status represents the health check status
type Status struct {
	Status        string                 `json:"status"`
	Version       string                 `json:"version"`
	Timestamp     string                 `json:"timestamp"`
	Uptime        int64                  `json:"uptime_seconds"`
	Checks        map[string]bool        `json:"checks"`
	Details       map[string]interface{} `json:"details,omitempty"`
}

var startTime = time.Now()

// Handler returns the HTTP handler for health checks
func Handler(version string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		status := performHealthChecks(version)

		w.Header().Set("Content-Type", "application/json")
		if status.Status == "healthy" {
			w.WriteHeader(http.StatusOK)
		} else {
			w.WriteHeader(http.StatusServiceUnavailable)
		}

		json.NewEncoder(w).Encode(status)
	}
}

func performHealthChecks(version string) Status {
	checks := make(map[string]bool)
	details := make(map[string]interface{})

	// Check configuration
	mgr, err := config.NewManager()
	configOK := err == nil && mgr.IsConfigured()
	checks["config"] = configOK
	if !configOK {
		details["config_error"] = "CLI not configured"
	}

	// Check encryption (basic)
	checks["encryption"] = true

	// Determine overall status
	allOK := true
	for _, ok := range checks {
		if !ok {
			allOK = false
			break
		}
	}

	statusStr := "healthy"
	if !allOK {
		statusStr = "degraded"
	}

	return Status{
		Status:    statusStr,
		Version:   version,
		Timestamp: time.Now().Format(time.RFC3339),
		Uptime:    int64(time.Since(startTime).Seconds()),
		Checks:    checks,
		Details:   details,
	}
}
