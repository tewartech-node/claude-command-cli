package commands

import (
	"fmt"

	"github.com/tewartech-node/claude-cli/pkg/config"
	"github.com/spf13/cobra"
)

// NewConfigCommand creates the 'config' command
func NewConfigCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "Manage CLI configuration",
		Long:  `View and modify CLI configuration settings.`,
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "get <key>",
		Short: "Get a config value",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runConfigGet(args[0])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "set <key> <value>",
		Short: "Set a config value",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runConfigSet(args[0], args[1])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List all config values",
		RunE: func(cmd *cobra.Command, args []string) error {
			return runConfigList()
		},
	})

	return cmd
}

func runConfigGet(key string) error {
	mgr, err := config.NewManager()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	value, err := mgr.Get(key)
	if err != nil {
		return err
	}

	fmt.Printf("%s = %v\n", key, value)
	return nil
}

func runConfigSet(key, value string) error {
	mgr, err := config.NewManager()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	if err := mgr.Set(key, value); err != nil {
		return err
	}

	fmt.Printf("✓ %s = %s\n", key, value)
	return nil
}

func runConfigList() error {
	mgr, err := config.NewManager()
	if err != nil {
		return fmt.Errorf("failed to load config: %w", err)
	}

	cfg := mgr.GetConfig()
	fmt.Println("📋 Claude CLI Configuration")
	fmt.Println()
	fmt.Printf("Server URL: %s\n", cfg.Server.URL)
	fmt.Printf("Server Timeout: %ds\n", cfg.Server.TimeoutSeconds)
	fmt.Printf("Max Retries: %d\n", cfg.Server.RetryMax)
	fmt.Printf("User Email: %s\n", cfg.User.Email)
	fmt.Printf("Preferred Model: %s\n", cfg.User.PreferredModel)
	fmt.Printf("Cache Enabled: %v\n", cfg.Cache.Enabled)
	fmt.Printf("Offline Mode: %v\n", cfg.Offline.Enabled)

	return nil
}
