package commands

import (
	"crypto/sha256"
	"fmt"
	"strings"
	"time"

	"github.com/tewartech-node/claude-cli/pkg/client"
	"github.com/tewartech-node/claude-cli/pkg/config"
	"github.com/tewartech-node/claude-cli/pkg/log"
	"github.com/tewartech-node/claude-cli/pkg/metrics"
	"github.com/spf13/cobra"
)

// NewAICommand creates the 'ai' command
func NewAICommand() *cobra.Command {
	return &cobra.Command{
		Use:   "ai <prompt>",
		Short: "Send a prompt to Claude",
		Long:  `Send a prompt to Claude API via warnetech-server for processing.`,
		Args:  cobra.MinimumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runAI(strings.Join(args, " "))
		},
	}
}

func runAI(prompt string) error {
	requestID := log.GetRequestID()
	start := time.Now()

	log.Infof(requestID, "Starting AI command execution")

	// Load config
	mgr, err := config.NewManager()
	if err != nil {
		duration := time.Since(start).Seconds()
		metrics.CommandDuration.WithLabelValues("ai").Observe(duration)
		metrics.CommandsTotal.WithLabelValues("ai", "error").Inc()
		log.CommandFailed(requestID, "ai", int64(duration*1000), err)
		return fmt.Errorf("failed to load config: %w", err)
	}

	if !mgr.IsConfigured() {
		err := fmt.Errorf("CLI not configured. Run: claude setup")
		duration := time.Since(start).Seconds()
		metrics.CommandDuration.WithLabelValues("ai").Observe(duration)
		metrics.CommandsTotal.WithLabelValues("ai", "error").Inc()
		metrics.ConfigErrors.WithLabelValues("not_configured").Inc()
		log.CommandFailed(requestID, "ai", int64(duration*1000), err)
		return err
	}

	// Create encryption key from API key
	key := deriveKey(mgr.GetAPIKey())

	// Create client
	c, err := client.NewClient(mgr.GetConfig(), key)
	if err != nil {
		duration := time.Since(start).Seconds()
		metrics.CommandDuration.WithLabelValues("ai").Observe(duration)
		metrics.CommandsTotal.WithLabelValues("ai", "error").Inc()
		log.CommandFailed(requestID, "ai", int64(duration*1000), err)
		return fmt.Errorf("failed to create client: %w", err)
	}

	// Log command start with metrics
	metrics.CommandsTotal.WithLabelValues("ai", "started").Inc()
	log.CommandStarted(requestID, "ai", map[string]interface{}{
		"prompt_length": len(prompt),
		"model":         mgr.GetConfig().User.PreferredModel,
	})

	// Execute command
	fmt.Print("⏳ Processing... ")

	resp, err := c.Execute("ai", map[string]interface{}{
		"prompt": prompt,
		"model":  mgr.GetConfig().User.PreferredModel,
	})

	duration := time.Since(start).Seconds()
	durationMs := int64(duration * 1000)

	if err != nil {
		fmt.Printf("✗\n")
		metrics.CommandDuration.WithLabelValues("ai").Observe(duration)
		metrics.CommandsTotal.WithLabelValues("ai", "error").Inc()
		log.CommandFailed(requestID, "ai", durationMs, err)
		return err
	}

	fmt.Printf("✓\n\n")
	metrics.CommandDuration.WithLabelValues("ai").Observe(duration)
	metrics.CommandsTotal.WithLabelValues("ai", "success").Inc()

	// Display response
	if data, ok := resp.Data.(map[string]interface{}); ok {
		if content, ok := data["content"].(string); ok {
			log.CommandCompleted(requestID, "ai", durationMs)
			fmt.Println(content)
			return nil
		}
	}

	// Fallback: display raw data
	log.CommandCompleted(requestID, "ai", durationMs)
	fmt.Printf("%v\n", resp.Data)
	return nil
}

// deriveKey creates a 32-byte key from an API key string using SHA-256
func deriveKey(apiKey string) []byte {
	hash := sha256.Sum256([]byte(apiKey))
	return hash[:]
}
