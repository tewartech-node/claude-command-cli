package envelope

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
)

// Envelope represents an AES-256-GCM encrypted message
type Envelope struct {
	SealedEnvelope string `json:"sealed_envelope"` // base64(ciphertext)
	Nonce          string `json:"nonce"`           // base64(nonce)
	Tag            string `json:"tag"`             // base64(tag/auth)
}

// Encryptor handles AES-256-GCM encryption/decryption
type Encryptor struct {
	key []byte
}

// NewEncryptor creates a new encryptor with a 32-byte key (AES-256)
func NewEncryptor(key []byte) (*Encryptor, error) {
	if len(key) != 32 {
		return nil, fmt.Errorf("key must be 32 bytes for AES-256, got %d", len(key))
	}
	return &Encryptor{key: make([]byte, 32)}, nil
}

// Encrypt encrypts data and returns an Envelope
func (e *Encryptor) Encrypt(data []byte) (*Envelope, error) {
	// Create cipher block
	block, err := aes.NewCipher(e.key)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}

	// Create GCM wrapper
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}

	// Generate random nonce (96 bits = 12 bytes for GCM)
	nonce := make([]byte, gcm.NonceSize())
	if _, err := io.ReadFull(rand.Reader, nonce); err != nil {
		return nil, fmt.Errorf("failed to generate nonce: %w", err)
	}

	// Encrypt with GCM (includes authentication tag)
	ciphertext := gcm.Seal(nil, nonce, data, nil)

	// Extract tag (last 16 bytes of ciphertext)
	tag := ciphertext[len(ciphertext)-16:]
	sealed := ciphertext[:len(ciphertext)-16]

	return &Envelope{
		SealedEnvelope: base64.StdEncoding.EncodeToString(sealed),
		Nonce:          base64.StdEncoding.EncodeToString(nonce),
		Tag:            base64.StdEncoding.EncodeToString(tag),
	}, nil
}

// EncryptJSON encrypts a JSON-serializable object
func (e *Encryptor) EncryptJSON(obj interface{}) (*Envelope, error) {
	data, err := json.Marshal(obj)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal JSON: %w", err)
	}
	return e.Encrypt(data)
}

// Decrypt decrypts an Envelope and returns plaintext
func (e *Encryptor) Decrypt(env *Envelope) ([]byte, error) {
	// Decode base64 fields
	sealed, err := base64.StdEncoding.DecodeString(env.SealedEnvelope)
	if err != nil {
		return nil, fmt.Errorf("failed to decode sealed envelope: %w", err)
	}

	nonce, err := base64.StdEncoding.DecodeString(env.Nonce)
	if err != nil {
		return nil, fmt.Errorf("failed to decode nonce: %w", err)
	}

	tag, err := base64.StdEncoding.DecodeString(env.Tag)
	if err != nil {
		return nil, fmt.Errorf("failed to decode tag: %w", err)
	}

	// Recreate ciphertext (sealed + tag)
	ciphertext := append(sealed, tag...)

	// Create cipher block
	block, err := aes.NewCipher(e.key)
	if err != nil {
		return nil, fmt.Errorf("failed to create cipher: %w", err)
	}

	// Create GCM wrapper
	gcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, fmt.Errorf("failed to create GCM: %w", err)
	}

	// Decrypt (includes tag verification)
	plaintext, err := gcm.Open(nil, nonce, ciphertext, nil)
	if err != nil {
		return nil, fmt.Errorf("decryption failed (invalid tag or corrupted data): %w", err)
	}

	return plaintext, nil
}

// DecryptJSON decrypts an Envelope and unmarshals JSON
func (e *Encryptor) DecryptJSON(env *Envelope, obj interface{}) error {
	plaintext, err := e.Decrypt(env)
	if err != nil {
		return err
	}
	return json.Unmarshal(plaintext, obj)
}
