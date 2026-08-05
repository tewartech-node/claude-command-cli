// Handles GitHub operations (open, push, pull)

async function handleGh(args, env) {
  if (!args || args.length === 0) {
    throw new Error('GitHub action required: open|push|pull');
  }

  const subcommand = args[0];
  const subargs = args.slice(1);

  switch (subcommand) {
    case 'open':
      return handleGhOpen(subargs[0]);
    case 'push':
      return handleGhPush(subargs[0]);
    case 'pull':
      return handleGhPull();
    default:
      throw new Error(`Unknown action: ${subcommand}`);
  }
}

function handleGhOpen(repo) {
  if (!repo) throw new Error('Repository name required');

  // Validate repo format (owner/name)
  if (!repo.includes('/')) {
    throw new Error('Repository format should be: owner/name');
  }

  const repoUrl = `https://github.com/${repo}`;
  const claudeUrl = `https://claude.ai/new?repo=${encodeURIComponent(repoUrl)}`;

  return {
    repo,
    url: repoUrl,
    claude_url: claudeUrl,
  };
}

function handleGhPush(message) {
  if (!message) throw new Error('Commit message required');

  // Git operations should be performed by CLI using git CLI
  return {
    message,
    status: 'NOT_IMPLEMENTED',
    note: 'Git operations should be performed by CLI, not Worker',
  };
}

function handleGhPull() {
  // Git operations should be performed by CLI using git CLI
  return {
    status: 'NOT_IMPLEMENTED',
    note: 'Git operations should be performed by CLI, not Worker',
  };
}

export default handleGh;
