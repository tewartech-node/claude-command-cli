import handleGh from '../../worker/commands/gh.js';

describe('gh command', () => {
  describe('gh-open', () => {
    it('returns github and claude URLs', async () => {
      const result = await handleGh(['open', 'tewartech-node/claude-command-cli'], {});
      expect(result.repo).toBe('tewartech-node/claude-command-cli');
      expect(result.url).toBe('https://github.com/tewartech-node/claude-command-cli');
      expect(result.claude_url).toContain('https://claude.ai/new?repo=');
    });

    it('encodes repository URL in claude link', async () => {
      const result = await handleGh(['open', 'owner/repo-name'], {});
      expect(result.claude_url).toContain(encodeURIComponent('https://github.com/owner/repo-name'));
    });

    it('throws error when repo argument missing', async () => {
      await expect(handleGh(['open'], {})).rejects.toThrow('Repository name required');
    });

    it('throws error when repo format invalid', async () => {
      await expect(handleGh(['open', 'invalid-repo'], {})).rejects.toThrow('owner/name');
    });
  });

  describe('gh-push', () => {
    it('returns placeholder message for push', async () => {
      const result = await handleGh(['push', 'feat: test'], {});
      expect(result.message).toBe('feat: test');
      expect(result.status).toBe('NOT_IMPLEMENTED');
    });
  });

  describe('gh-pull', () => {
    it('returns placeholder message for pull', async () => {
      const result = await handleGh(['pull'], {});
      expect(result.status).toBe('NOT_IMPLEMENTED');
    });
  });
});
