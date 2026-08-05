// NVIDIA Nemotron API client

const NVIDIA_API_URL = 'https://integrate.api.nvidia.com/v1/chat/completions';
const MODEL = 'nvidia/nemotron-3-ultra';

async function chat(prompt, apiKey, options = {}) {
  const { stream = false } = options;

  const request = {
    model: MODEL,
    messages: [
      {
        role: 'system',
        content: 'You are Claude, an AI assistant for the Warnet command-line system. Provide concise, actionable responses.',
      },
      {
        role: 'user',
        content: prompt,
      },
    ],
    temperature: 0.7,
    max_tokens: 2048,
    stream,
  };

  try {
    const response = await fetch(NVIDIA_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`NVIDIA API error: ${response.status} ${response.statusText}`);
    }

    if (stream) {
      return handleStreamingResponse(response);
    } else {
      return handleBufferedResponse(response);
    }
  } catch (error) {
    throw new Error(`Nemotron request failed: ${error.message}`);
  }
}

async function handleBufferedResponse(response) {
  const data = await response.json();

  if (data.error) {
    throw new Error(`Nemotron error: ${data.error.message}`);
  }

  const choice = data.choices[0];
  const text = choice.text || choice.message?.content || '';

  return {
    text,
    tokens: {
      input: data.usage?.prompt_tokens || 0,
      output: data.usage?.completion_tokens || 0,
      total: data.usage?.total_tokens || 0,
    },
  };
}

async function handleStreamingResponse(response) {
  // TODO: Implement streaming response handling
  // For now, buffer the entire response
  const reader = response.body.getReader();
  let text = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = new TextDecoder().decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.choices && data.choices[0].delta?.content) {
          text += data.choices[0].delta.content;
        }
      }
    }
  }

  return {
    text,
    tokens: { input: 0, output: 0, total: 0 }, // Placeholder
  };
}

async function optimizePrompt(userPrompt, context = {}) {
  let optimized = userPrompt;

  // Add context if available
  if (context.language) {
    optimized = `[${context.language}]\n${optimized}`;
  }

  // Add format constraint if applicable
  if (context.wantCode) {
    optimized += '\n\nProvide code only, no explanation.';
  }

  // Ensure completeness
  if (!optimized.includes('?') && !optimized.endsWith('.')) {
    optimized += '.';
  }

  return optimized;
}

export default { chat, optimizePrompt };
