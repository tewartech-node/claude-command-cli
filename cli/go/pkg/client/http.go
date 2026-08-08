package client

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/tewartech-node/claude-cli/pkg/config"
	"github.com/tewartech-node/claude-cli/pkg/envelope"
)

// Client handles communication with warnetech-server
type Client struct {
	config      *config.Config
	httpClient  *http.Client
	encryptor   *envelope.Encryptor
	retryPolicy RetryPolicy
}

// RetryPolicy defines retry behavior
type RetryPolicy struct {
	MaxRetries int
	InitialBackoff time.Duration
	MaxBackoff time.Duration
}

// Request represents a command request
type Request struct {
	Command string                 `json:"command"`
	Args    map[string]interface{} `json:"args,omitempty"`
}

// Response represents a command response
type Response struct {
	Status  string      `json:"status"`  // "success" or "error"
	Data    interface{} `json:"data,omitempty"`
	Error   string      `json:"error,omitempty"`
	Message string      `json:"message,omitempty"`
}

// NewClient creates a new server client
func NewClient(cfg *config.Config, key []byte) (*Client, error) {
	encryptor, err := envelope.NewEncryptor(key)
	if err != nil {
		return nil, err
	}

	return &Client{
		config: cfg,
		httpClient: &http.Client{
			Timeout: time.Duration(cfg.Server.TimeoutSeconds) * time.Second,
		},
		encryptor: encryptor,
		retryPolicy: RetryPolicy{
			MaxRetries:     cfg.Server.RetryMax,
			InitialBackoff: 1 * time.Second,
			MaxBackoff:     10 * time.Second,
		},
	}, nil
}

// Execute sends a command to the server and returns the response
func (c *Client) Execute(command string, args map[string]interface{}) (*Response, error) {
	req := &Request{
		Command: command,
		Args:    args,
	}

	// Encrypt request
	env, err := c.encryptor.EncryptJSON(req)
	if err != nil {
		return nil, fmt.Errorf("failed to encrypt request: %w", err)
	}

	// Make HTTP request with retries
	var lastErr error
	backoff := c.retryPolicy.InitialBackoff

	for attempt := 0; attempt <= c.retryPolicy.MaxRetries; attempt++ {
		resp, err := c.makeRequest(env)
		if err == nil {
			return resp, nil
		}

		lastErr = err

		if attempt < c.retryPolicy.MaxRetries {
			time.Sleep(backoff)
			backoff *= 2
			if backoff > c.retryPolicy.MaxBackoff {
				backoff = c.retryPolicy.MaxBackoff
			}
		}
	}

	return nil, fmt.Errorf("request failed after %d retries: %w", c.retryPolicy.MaxRetries, lastErr)
}

// makeRequest sends the HTTP request
func (c *Client) makeRequest(env *envelope.Envelope) (*Response, error) {
	body, err := json.Marshal(env)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal envelope: %w", err)
	}

	httpReq, err := http.NewRequest("POST", c.config.Server.URL+"/api/v1/command", bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+c.config.Auth.APIKey)
	httpReq.Header.Set("User-Agent", "claude-cli/0.1.0")

	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(httpResp.Body)
		return nil, fmt.Errorf("server returned status %d: %s", httpResp.StatusCode, string(bodyBytes))
	}

	// Decode response envelope
	var respEnv envelope.Envelope
	if err := json.NewDecoder(httpResp.Body).Decode(&respEnv); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Decrypt response
	var respData Response
	if err := c.encryptor.DecryptJSON(&respEnv, &respData); err != nil {
		return nil, fmt.Errorf("failed to decrypt response: %w", err)
	}

	if respData.Status == "error" {
		return nil, fmt.Errorf("server error: %s", respData.Error)
	}

	return &respData, nil
}

// HealthCheck verifies server connectivity
func (c *Client) HealthCheck() error {
	httpReq, err := http.NewRequest("GET", c.config.Server.URL+"/health", nil)
	if err != nil {
		return fmt.Errorf("failed to create health check request: %w", err)
	}

	httpResp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("health check failed: %w", err)
	}
	defer httpResp.Body.Close()

	if httpResp.StatusCode != http.StatusOK {
		return fmt.Errorf("server unhealthy: status %d", httpResp.StatusCode)
	}

	return nil
}
