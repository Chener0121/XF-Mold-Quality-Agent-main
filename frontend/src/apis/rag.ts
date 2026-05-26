import api from './index'

export function askQuestion(query: string, topK: number = 5) {
  return api.post('/rag/query', { query, top_k: topK }) as Promise<{
    answer: string
    retrievals: { tool_name: string; content_preview: string }[]
    context_preview: string
    context_length: number
  }>
}
