// Request validation, security checks, and decryption

async function validateRequest(body, headers, env) {
  try {
    // Validate API key hash (not the actual key)
    const apiKeyHash = headers.get('x-api-key-hash');
    if (!apiKeyHash) {
      return { ok: false, error: 'API key validation required' };
    }

    // Validate request ID (prevent replay)
    const requestId = headers.get('x-request-id');
    if (!requestId) {
      return { ok: false, error: 'Request ID required' };
    }

    // TODO: Check if request ID already seen
    // const seen = await env.KV.get(`request_id:${requestId}`);
    // if (seen) {
    //   return { ok: false, error: 'Duplicate request ID' };
    // }

    // Validate timestamp
    const timestamp = headers.get('x-timestamp');
    if (!timestamp) {
      return { ok: false, error: 'Timestamp required' };
    }

    const requestTime = new Date(timestamp).getTime();
    const now = Date.now();
    if (Math.abs(now - requestTime) > 300000) { // 5 minutes
      return { ok: false, error: 'Request timestamp too old' };
    }

    // For unencrypted requests (backwards compatibility)
    if (body.command) {
      const validCommands = ['ping', 'ai', 'gh', 'sys'];
      if (!validCommands.includes(body.command)) {
        return {
          ok: false,
          error: `Unknown command: ${body.command}. Valid commands: ${validCommands.join(', ')}`,
        };
      }

      return {
        ok: true,
        command: body.command,
        args: body.args || [],
      };
    }

    // For encrypted requests
    if (body.encrypted_data) {
      return {
        ok: true,
        encrypted: true,
        encrypted_data: body.encrypted_data,
        signature: body.signature,
      };
    }

    return { ok: false, error: 'Command or encrypted_data required' };
  } catch (error) {
    return { ok: false, error: error.message };
  }
}

async function decryptRequest(encryptedData, headers, env) {
  // Note: In production, use env.API_KEY retrieved from secure storage
  // For now, we'll implement basic decryption framework
  try {
    // This would normally use WebCrypto in Cloudflare Workers
    // For Node.js testing, we'll add decryption logic
    throw new Error('Decryption not yet implemented in Worker (requires WebCrypto)');
  } catch (error) {
    throw new Error(`Failed to decrypt request: ${error.message}`);
  }
}

// Anti-tamper checks - verify request hasn't been modified
async function antiTamperCheck(request, env) {
  // Verify signature
  if (request.signature) {
    const verified = await verifySignature(
      request,
      request.signature,
      env.SIGNING_KEY
    );
    if (!verified) {
      throw new Error('Signature verification failed');
    }
  }

  // Check data tier compliance
  if (request.data_tier) {
    validateDataTier(request.data_tier);
  }

  return true;
}

function validateDataTier(tier) {
  const valid = ['TIER_1', 'TIER_2', 'TIER_3'];
  if (!valid.includes(tier)) {
    throw new Error(`Invalid data tier: ${tier}`);
  }
}

async function verifySignature(payload, signature, secret) {
  // HMAC-SHA256 verification
  // This is a placeholder - full implementation requires crypto access
  return true;
}

export {
  validateRequest,
  decryptRequest,
  antiTamperCheck,
  validateDataTier,
  verifySignature,
};
