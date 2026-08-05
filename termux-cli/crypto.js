// CLI-side cryptographic utilities for request/response handling
import crypto from 'crypto';

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16; // 128 bits for consistency

function deriveKey(apiKey) {
  // Derive encryption key from API key using PBKDF2
  return crypto.pbkdf2Sync(
    apiKey,
    'claude-command-cli',
    100000,
    32, // 256 bits
    'sha256'
  );
}

function encryptData(plaintext, apiKey) {
  try {
    const key = deriveKey(apiKey);
    const iv = crypto.randomBytes(IV_LENGTH);

    const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    // Return IV + authTag + ciphertext in base64
    const combined = Buffer.concat([iv, authTag, Buffer.from(encrypted, 'hex')]);
    return combined.toString('base64');
  } catch (error) {
    throw new Error(`Encryption failed: ${error.message}`);
  }
}

function decryptData(ciphertext, apiKey) {
  try {
    const key = deriveKey(apiKey);
    const combined = Buffer.from(ciphertext, 'base64');

    // Extract IV, authTag, and encrypted data
    const iv = combined.slice(0, IV_LENGTH);
    const authTag = combined.slice(IV_LENGTH, IV_LENGTH + 16);
    const encrypted = combined.slice(IV_LENGTH + 16);

    const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted);
    decrypted = Buffer.concat([decrypted, decipher.final()]);

    return decrypted.toString('utf8');
  } catch (error) {
    throw new Error(`Decryption failed: ${error.message}`);
  }
}

function generateHmacSignature(payload, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(JSON.stringify(payload));
  return hmac.digest('hex');
}

function verifyHmacSignature(payload, signature, secret) {
  const expected = generateHmacSignature(payload, secret);
  // Timing-safe comparison
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

function generateRequestId() {
  return `req-${Date.now()}-${crypto.randomBytes(4).toString('hex')}`;
}

function hashApiKey(apiKey) {
  // Hash API key for storage/comparison
  return crypto.createHash('sha256').update(apiKey).digest('hex');
}

export {
  encryptData,
  decryptData,
  deriveKey,
  generateHmacSignature,
  verifyHmacSignature,
  generateRequestId,
  hashApiKey,
};
