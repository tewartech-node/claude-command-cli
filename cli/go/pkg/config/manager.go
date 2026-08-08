package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Config represents the CLI configuration
type Config struct {
	Version string `json:"version"`
	Server  struct {
		URL            string `json:"url"`
		TimeoutSeconds int    `json:"timeout_seconds"`
		RetryMax       int    `json:"retry_max"`
	} `json:"server"`
	Auth struct {
		APIKey   string `json:"api_key"`
		NonceSalt string `json:"nonce_salt"`
	} `json:"auth"`
	User struct {
		Email          string `json:"email"`
		PreferredModel string `json:"preferred_model"`
	} `json:"user"`
	Cache struct {
		Enabled   bool `json:"enabled"`
		TTLSeconds int `json:"ttl_seconds"`
	} `json:"cache"`
	Offline struct {
		Enabled        bool   `json:"enabled"`
		QueueDB        string `json:"queue_db"`
		SyncIntervalSec int   `json:"sync_interval_seconds"`
		MaxQueueSize   int    `json:"max_queue_size"`
	} `json:"offline"`
}

// Manager handles configuration file operations
type Manager struct {
	configPath string
	config     *Config
}

// NewManager creates a new config manager
func NewManager() (*Manager, error) {
	path, err := getConfigPath()
	if err != nil {
		return nil, err
	}

	m := &Manager{configPath: path}

	// Load existing config or create default
	if err := m.Load(); err != nil {
		// If load fails, use defaults
		m.config = getDefaults()
	}

	return m, nil
}

// getConfigPath returns platform-specific config directory
func getConfigPath() (string, error) {
	var configDir string

	// Use XDG Base Directory on Linux/macOS
	if xdgConfig := os.Getenv("XDG_CONFIG_HOME"); xdgConfig != "" {
		configDir = xdgConfig
	} else if home := os.Getenv("HOME"); home != "" {
		configDir = filepath.Join(home, ".config")
	} else if appData := os.Getenv("APPDATA"); appData != "" {
		// Windows
		configDir = appData
	} else {
		return "", fmt.Errorf("unable to determine config directory")
	}

	configPath := filepath.Join(configDir, "claude-cli", "config.json")
	return configPath, nil
}

// getDefaults returns default configuration
func getDefaults() *Config {
	cfg := &Config{}
	cfg.Version = "1.0"
	cfg.Server.URL = "https://warnetech-server.example.com"
	cfg.Server.TimeoutSeconds = 30
	cfg.Server.RetryMax = 3
	cfg.User.PreferredModel = "claude-3-5-sonnet"
	cfg.Cache.Enabled = true
	cfg.Cache.TTLSeconds = 3600
	cfg.Offline.Enabled = true
	cfg.Offline.SyncIntervalSec = 60
	cfg.Offline.MaxQueueSize = 100

	home, _ := os.UserHomeDir()
	cfg.Offline.QueueDB = filepath.Join(home, ".local", "share", "claude-cli", "queue.db")

	return cfg
}

// Load reads configuration from disk
func (m *Manager) Load() error {
	data, err := os.ReadFile(m.configPath)
	if err != nil {
		if os.IsNotExist(err) {
			// Create default config
			m.config = getDefaults()
			return m.Save()
		}
		return fmt.Errorf("failed to read config: %w", err)
	}

	cfg := &Config{}
	if err := json.Unmarshal(data, cfg); err != nil {
		return fmt.Errorf("failed to parse config: %w", err)
	}

	m.config = cfg
	return nil
}

// Save writes configuration to disk
func (m *Manager) Save() error {
	// Create directory if it doesn't exist
	dir := filepath.Dir(m.configPath)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	data, err := json.MarshalIndent(m.config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(m.configPath, data, 0600); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	return nil
}

// Get returns a configuration value by key path (e.g., "server.url")
func (m *Manager) Get(key string) (interface{}, error) {
	// Simple key lookup (can be extended with dot notation)
	switch key {
	case "server.url":
		return m.config.Server.URL, nil
	case "auth.api_key":
		return m.config.Auth.APIKey, nil
	case "user.email":
		return m.config.User.Email, nil
	case "user.preferred_model":
		return m.config.User.PreferredModel, nil
	default:
		return nil, fmt.Errorf("unknown config key: %s", key)
	}
}

// Set updates a configuration value by key
func (m *Manager) Set(key, value string) error {
	switch key {
	case "server.url":
		m.config.Server.URL = value
	case "auth.api_key":
		m.config.Auth.APIKey = value
	case "user.email":
		m.config.User.Email = value
	case "user.preferred_model":
		m.config.User.PreferredModel = value
	default:
		return fmt.Errorf("unknown config key: %s", key)
	}

	return m.Save()
}

// GetConfig returns the full config structure
func (m *Manager) GetConfig() *Config {
	return m.config
}

// GetAPIKey returns the API key
func (m *Manager) GetAPIKey() string {
	return m.config.Auth.APIKey
}

// IsConfigured checks if the CLI is properly configured
func (m *Manager) IsConfigured() bool {
	return m.config.Auth.APIKey != "" && m.config.User.Email != ""
}
