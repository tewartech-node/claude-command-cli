package commands

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"

	"github.com/tewartech-node/claude-cli/pkg/client"
	"github.com/tewartech-node/claude-cli/pkg/config"
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
	// Load config
	mgr, err := config.NewManager()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	if !mgr.IsConfigured() {
		return fmt.Errorf("CLI not configured. Run: claude setup")
	}

	// Create encryption key from API key
	key := deriveKey(mgr.GetAPIKey())

	// Create client
	c, err := client.NewClient(mgr.GetConfig(), key)
	if err != nil {
		return fmt.Errorf("failed to create client: %w", err)
	}

	// Execute command
	fmt.Print("⏳ Processing... ")

	resp, err := c.Execute("ai", map[string]interface{}{
		"prompt": prompt,
		"model":  mgr.GetConfig().User.PreferredModel,
	})
	if err != nil {
		fmt.Printf("✗\n")
		return err
	}

	fmt.Printf("✓\n\n")

	// Display response
	if data, ok := resp.Data.(map[string]interface{}); ok {
		if content, ok := data["content"].(string); ok {
			fmt.Println(content)
			return nil
		}
	}

	// Fallback: display raw data
	fmt.Printf("%v\n", resp.Data)
	return nil
}

// deriveKey creates a 32-byte key from an API key string using SHA-256
func deriveKey(apiKey string) []byte {
	hash := sha256.Sum256([]byte(apiKey))
	return hash[:]
}
