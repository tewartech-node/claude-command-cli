async function handleGh(args, env) {
  if (!args || args.length === 0) {
    throw new Error('gh command requires a subcommand: open, push, or pull');
  }

  const [subcommand, ...subargs] = Array.isArray(args) ? args : [args];

  switch (subcommand) {
    case 'open': {
      const repo = subargs[0] || 'claude-command-cli';
      const url = `https://claude.ai/new?repo=https://github.com/tewartech-node/${repo}`;
      return {
        action: 'open_claude',
        url,
      };
    }

    case 'push': {
      const message = subargs[0] || 'update';
      return {
        action: 'push_instructions',
        instructions: [
          'Run the following in Termux:',
          'git add .',
          `git commit -m "${message}"`,
          'git push origin main',
        ],
      };
    }

    case 'pull': {
      return {
        action: 'pull_instructions',
        instructions: [
          'Run the following in Termux:',
          'git pull',
        ],
      };
    }

    default:
      throw new Error(`Unknown gh subcommand: ${subcommand}`);
  }
}

export default handleGh;
