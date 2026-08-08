package commands

import (
	"fmt"
	"strings"

	"github.com/tewartech-node/claude-cli/pkg/client"
	"github.com/tewartech-node/claude-cli/pkg/config"
	"github.com/spf13/cobra"
)

// NewGHCommand creates the 'gh-open' command
func NewGHCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "gh-open <repo>",
		Short: "Open a GitHub repository",
		Long:  `Open a GitHub repository in the browser via warnetech-server.`,
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runGHOpen(args[0])
		},
	}
}

func runGHOpen(repo string) error {
	// Validate repo format
	if !strings.Contains(repo, "/") {
		return fmt.Errorf("invalid repo format. Use: owner/repo")
	}

	// Load config
	mgr, err := config.NewManager()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	if !mgr.IsConfigured() {
		return fmt.Errorf("CLI not configured. Run: claude setup")
	}

	// Create client
	key := deriveKey(mgr.GetAPIKey())
	c, err := client.NewClient(mgr.GetConfig(), key)
	if err != nil {
		return fmt.Errorf("failed to create client: %w", err)
	}

	// Execute command
	fmt.Printf("⏳ Opening %s... ", repo)

	resp, err := c.Execute("gh-open", map[string]interface{}{
		"repo": repo,
	})
	if err != nil {
		fmt.Printf("✗\n")
		return err
	}

	fmt.Printf("✓\n")

	// Display URL
	if data, ok := resp.Data.(map[string]interface{}); ok {
		if url, ok := data["url"].(string); ok {
			fmt.Printf("🔗 %s\n", url)
		}
	}

	return nil
}
