export interface StreamCallbacks {
  onMeta: (meta: { conversation_id: string; domain: string; rewritten_query?: string | null }) => void
  onToken: (token: string) => void
  onThinking: (token: string) => void
  onDone: (data: { tool_calls: { tool_name: string; content_preview: string }[] }) => void
  onError: (message: string) => void
}

export function askQuestionStream(
  query: string,
  conversationId: string | undefined,
  callbacks: StreamCallbacks,
  agent?: string,
  rules?: string,
): AbortController {
  const controller = new AbortController()

  fetch('/api/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      conversation_id: conversationId || null,
      agent: agent || 'general',
      rules: rules || null,
    }),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: '请求失败' }))
        callbacks.onError(err.detail || '请求失败')
        return
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ') && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6))
              switch (currentEvent) {
                case 'meta': callbacks.onMeta(data); break
                case 'token': callbacks.onToken(data.content); break
                case 'thinking': callbacks.onThinking(data.content); break
                case 'done': callbacks.onDone({ tool_calls: data.tool_calls }); break
                case 'error': callbacks.onError(data.message); break
              }
            } catch { /* 忽略解析错误 */ }
            currentEvent = ''
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError(err.message || '连接失败')
      }
    })

  return controller
}
