package commands

import (
	"fmt"
	"strings"

	"github.com/tewartech-node/claude-cli/pkg/client"
	"github.com/tewartech-node/claude-cli/pkg/config"
	"github.com/spf13/cobra"
)

// NewStatusCommand creates the 'status' command
func NewStatusCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "status",
		Short: "Check CLI and server status",
		Long:  `Check the status of the CLI configuration and server connectivity.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runStatus()
		},
	}
}

func runStatus() error {
	// Load config
	mgr, err := config.NewManager()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	fmt.Println("📊 Claude CLI Status")
	fmt.Println(strings.Repeat("─", 40))

	// Check configuration
	if !mgr.IsConfigured() {
		fmt.Println("❌ Not configured")
		fmt.Println("   Run: claude setup")
		return nil
	}

	cfg := mgr.GetConfig()
	fmt.Printf("✓ Configured\n")
	fmt.Printf("  Email: %s\n", cfg.User.Email)
	fmt.Printf("  Model: %s\n", cfg.User.PreferredModel)
	fmt.Printf("  Server: %s\n", cfg.Server.URL)

	// Check server connectivity
	key := deriveKey(mgr.GetAPIKey())
	c, err := client.NewClient(cfg, key)
	if err != nil {
		fmt.Printf("❌ Client error: %v\n", err)
		return nil
	}

	fmt.Print("Checking server... ")
	if err := c.HealthCheck(); err != nil {
		fmt.Printf("❌\n  %v\n", err)
		return nil
	}

	fmt.Printf("✓ Connected\n")
	fmt.Println()
	fmt.Println("✨ All systems operational")

	return nil
}
