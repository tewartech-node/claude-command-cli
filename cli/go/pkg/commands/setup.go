package commands

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/tewartech-node/claude-cli/pkg/config"
	"golang.org/x/term"
	"github.com/spf13/cobra"
)

// NewSetupCommand creates the 'setup' command
func NewSetupCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "setup",
		Short: "Initialize CLI configuration",
		Long:  `Interactive setup to configure the CLI with your credentials and preferences.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runSetup()
		},
	}
}

func runSetup() error {
	fmt.Println("🚀 Claude CLI Setup")
	fmt.Println(strings.Repeat("─", 40))
	fmt.Println()

	reader := bufio.NewReader(os.Stdin)

	// Email
	fmt.Print("Email (for account identification): ")
	email, err := reader.ReadString('\n')
	if err != nil {
		return err
	}
	email = strings.TrimSpace(email)

	// API Key (hidden input)
	fmt.Print("API Key (hidden): ")
	apiKeyBytes, err := term.ReadPassword(int(os.Stdin.Fd()))
	if err != nil {
		return fmt.Errorf("failed to read API key: %w", err)
	}
	apiKey := string(apiKeyBytes)
	fmt.Println()

	// Server URL (optional)
	fmt.Print("Server URL (default: https://warnetech-server.example.com): ")
	serverURL, err := reader.ReadString('\n')
	if err != nil {
		return err
	}
	serverURL = strings.TrimSpace(serverURL)
	if serverURL == "" {
		serverURL = "https://warnetech-server.example.com"
	}

	// Preferred model
	fmt.Print("Preferred model (default: claude-3-5-sonnet): ")
	model, err := reader.ReadString('\n')
	if err != nil {
		return err
	}
	model = strings.TrimSpace(model)
	if model == "" {
		model = "claude-3-5-sonnet"
	}

	// Save configuration
	fmt.Println()
	fmt.Print("Saving configuration... ")

	mgr, err := config.NewManager()
	if err != nil {
		fmt.Println("✗")
		return fmt.Errorf("failed to load config manager: %w", err)
	}

	cfg := mgr.GetConfig()
	cfg.Auth.APIKey = apiKey
	cfg.User.Email = email
	cfg.Server.URL = serverURL
	cfg.User.PreferredModel = model

	if err := mgr.Save(); err != nil {
		fmt.Println("✗")
		return fmt.Errorf("failed to save config: %w", err)
	}

	fmt.Println("✓")
	fmt.Println()
	fmt.Println("✨ Setup complete!")
	fmt.Println()
	fmt.Println("Try:")
	fmt.Println("  claude ai \"Hello, Claude!\"")
	fmt.Println("  claude status")

	return nil
}
