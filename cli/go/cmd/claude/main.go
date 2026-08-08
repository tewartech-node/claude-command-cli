package main

import (
	"fmt"
	"os"

	"github.com/tewartech-node/claude-cli/pkg/commands"
	"github.com/spf13/cobra"
)

var (
	Version = "0.1.0-alpha"
	BuildDate = "dev"
)

var rootCmd = &cobra.Command{
	Use:   "claude",
	Short: "Claude CLI - lightweight universal client",
	Long: `Claude CLI is a thin cryptographic client that communicates with
warnetech-server to provide AI assistance, GitHub operations, and more.

All heavy processing happens on the server, making this tool suitable for
resource-constrained devices including 32-bit phones.`,
	Version: fmt.Sprintf("%s (built %s)", Version, BuildDate),
}

func init() {
	rootCmd.AddCommand(commands.NewAICommand())
	rootCmd.AddCommand(commands.NewGHCommand())
	rootCmd.AddCommand(commands.NewStatusCommand())
	rootCmd.AddCommand(commands.NewConfigCommand())
	rootCmd.AddCommand(commands.NewSetupCommand())
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
