import { validateRequest } from './utils/validate.js';
import { respondSuccess, respondError } from './utils/respond.js';
import handleAi from './commands/ai.js';
import handleGh from './commands/gh.js';
import handleSys from './commands/sys.js';

const COMMAND_HANDLERS = {
  ai: handleAi,
  gh: handleGh,
  sys: handleSys,
};

async function handleRequest(request, env, ctx) {
  const url = new URL(request.url);

  // Health check endpoint
  if (url.pathname === '/health' && request.method === 'GET') {
    return new Response(
      JSON.stringify({
        status: 'ok',
        version: '0.1.0',
        timestamp: new Date().toISOString(),
      }),
      {
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  // Main command endpoint
  if (url.pathname === '/api/command' && request.method === 'POST') {
    try {
      const body = await request.json();

      // Validate request
      const validation = await validateRequest(body, request.headers, env);
      if (!validation.ok) {
        return new Response(
          JSON.stringify(respondError(new Error(validation.error), 400)),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      const { command, args, decrypted } = validation;

      // Get handler
      const handler = COMMAND_HANDLERS[command];
      if (!handler) {
        return new Response(
          JSON.stringify(respondError(new Error(`Unknown command: ${command}`), 400)),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Execute command
      const result = await handler(args, env);

      // Return success response
      return new Response(
        JSON.stringify(respondSuccess(result, command)),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    } catch (error) {
      console.error('Command error:', error);
      return new Response(
        JSON.stringify(respondError(error, 500)),
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }
  }

  // 404
  return new Response(JSON.stringify({ error: 'Not found' }), {
    status: 404,
    headers: { 'Content-Type': 'application/json' },
  });
}

export default {
  fetch: handleRequest,
};
