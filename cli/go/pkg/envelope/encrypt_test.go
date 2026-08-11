package envelope

import (
	"testing"
)

func TestEncryption(t *testing.T) {
	// Create a 32-byte key
	key := make([]byte, 32)
	for i := 0; i < 32; i++ {
		key[i] = byte(i)
	}

	encryptor, err := NewEncryptor(key)
	if err != nil {
		t.Fatalf("Failed to create encryptor: %v", err)
	}

	// Test plaintext
	plaintext := []byte("Hello, World!")

	// Encrypt
	env, err := encryptor.Encrypt(plaintext)
	if err != nil {
		t.Fatalf("Encryption failed: %v", err)
	}

	// Verify envelope structure
	if env.SealedEnvelope == "" {
		t.Error("SealedEnvelope is empty")
	}
	if env.Nonce == "" {
		t.Error("Nonce is empty")
	}
	if env.Tag == "" {
		t.Error("Tag is empty")
	}

	// Decrypt
	decrypted, err := encryptor.Decrypt(env)
	if err != nil {
		t.Fatalf("Decryption failed: %v", err)
	}

	// Verify
	if string(decrypted) != string(plaintext) {
		t.Errorf("Decrypted data mismatch. Expected %s, got %s", plaintext, decrypted)
	}
}

func TestJSONEncryption(t *testing.T) {
	key := make([]byte, 32)
	for i := 0; i < 32; i++ {
		key[i] = byte(i)
	}

	encryptor, err := NewEncryptor(key)
	if err != nil {
		t.Fatalf("Failed to create encryptor: %v", err)
	}

	// Test data
	testData := map[string]interface{}{
		"command": "ai",
		"prompt":  "Hello Claude",
	}

	// Encrypt JSON
	env, err := encryptor.EncryptJSON(testData)
	if err != nil {
		t.Fatalf("JSON encryption failed: %v", err)
	}

	// Decrypt JSON
	var decrypted map[string]interface{}
	err = encryptor.DecryptJSON(env, &decrypted)
	if err != nil {
		t.Fatalf("JSON decryption failed: %v", err)
	}

	// Verify
	if decrypted["command"] != testData["command"] {
		t.Errorf("Command mismatch. Expected %v, got %v", testData["command"], decrypted["command"])
	}
	if decrypted["prompt"] != testData["prompt"] {
		t.Errorf("Prompt mismatch. Expected %v, got %v", testData["prompt"], decrypted["prompt"])
	}
}

func TestMultipleEncryptions(t *testing.T) {
	key := make([]byte, 32)
	for i := 0; i < 32; i++ {
		key[i] = byte(i)
	}

	encryptor, err := NewEncryptor(key)
	if err != nil {
		t.Fatalf("Failed to create encryptor: %v", err)
	}

	plaintext1 := []byte("Message 1")
	plaintext2 := []byte("Message 2")

	// Encrypt two messages
	env1, err := encryptor.Encrypt(plaintext1)
	if err != nil {
		t.Fatalf("First encryption failed: %v", err)
	}

	env2, err := encryptor.Encrypt(plaintext2)
	if err != nil {
		t.Fatalf("Second encryption failed: %v", err)
	}

	// Verify nonces are different
	if env1.Nonce == env2.Nonce {
		t.Error("Nonces should be different for different encryptions")
	}

	// Decrypt and verify
	dec1, _ := encryptor.Decrypt(env1)
	dec2, _ := encryptor.Decrypt(env2)

	if string(dec1) != string(plaintext1) {
		t.Error("First decryption failed")
	}
	if string(dec2) != string(plaintext2) {
		t.Error("Second decryption failed")
	}
}

func TestInvalidTag(t *testing.T) {
	key := make([]byte, 32)
	for i := 0; i < 32; i++ {
		key[i] = byte(i)
	}

	encryptor, err := NewEncryptor(key)
	if err != nil {
		t.Fatalf("Failed to create encryptor: %v", err)
	}

	plaintext := []byte("Hello, World!")

	// Encrypt
	env, err := encryptor.Encrypt(plaintext)
	if err != nil {
		t.Fatalf("Encryption failed: %v", err)
	}

	// Tamper with tag
	env.Tag = "AAAAAAAAAA" // Invalid base64

	// Try to decrypt - should fail
	_, err = encryptor.Decrypt(env)
	if err == nil {
		t.Error("Expected decryption to fail with tampered tag")
	}
}
