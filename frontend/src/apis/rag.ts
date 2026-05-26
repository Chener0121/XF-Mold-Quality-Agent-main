import api from './index'

export function askQuestion(query: string, conversationId?: string) {
  return api.post('/rag/query', {
    query,
    conversation_id: conversationId || null,
  }) as Promise<{
    answer: string
    conversation_id: string
    domain: string
    retrievals: { tool_name: string; content_preview: string }[]
    context_preview: string
    context_length: number
    rewritten_query?: string
  }>
}
