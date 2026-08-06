// Cross-implementation check: the legacy Node CLI and the Cloudflare Worker
// must agree on the AES-GCM wire format, since they are the two ends of the
// same encrypted channel.
//
// STATUS: they do NOT agree. These tests pin the current incompatibility so it
// is visible in CI. Once a canonical format is chosen and both sides updated,
// flip each `expect(...).rejects/toThrow` to a successful round-trip assertion.
import * as legacy from '../../warnetech_cli_legacy/crypto.js';
import * as worker from '../../worker/utils/crypto.js';

const API_KEY = 'test-password';
const PLAINTEXT = 'warnetech-interop';

describe('Legacy CLI <-> Worker AES-GCM interop', () => {
  test('each side round-trips itself', async () => {
    expect(legacy.decryptData(legacy.encryptData(PLAINTEXT, API_KEY), API_KEY)).toBe(PLAINTEXT);
    const w = await worker.encryptData(PLAINTEXT, API_KEY);
    expect(await worker.decryptData(w, API_KEY)).toBe(PLAINTEXT);
  });

  test('both sides derive the same 256-bit key', async () => {
    const legacyKey = legacy.deriveKey(API_KEY);
    expect(legacyKey.length).toBe(32);
    await expect(worker.deriveKey(API_KEY)).resolves.toBeDefined();
  });

  test('KNOWN BUG: legacy encrypt -> worker decrypt fails', async () => {
    const packet = legacy.encryptData(PLAINTEXT, API_KEY);
    await expect(worker.decryptData(packet, API_KEY)).rejects.toThrow(/Decryption failed/);
  });

  test('KNOWN BUG: worker encrypt -> legacy decrypt fails', async () => {
    const packet = await worker.encryptData(PLAINTEXT, API_KEY);
    expect(() => legacy.decryptData(packet, API_KEY)).toThrow(/Decryption failed/);
  });

  test('KNOWN BUG: wire layouts differ (iv 16+tag-first vs iv 12+tag-last)', async () => {
    const l = Buffer.from(legacy.encryptData(PLAINTEXT, API_KEY), 'base64');
    const w = Buffer.from(await worker.encryptData(PLAINTEXT, API_KEY), 'base64');
    expect(l.length - w.length).toBe(4); // 16-byte IV vs 12-byte IV
  });
});
