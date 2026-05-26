import api from './index'

export function listConversations() {
  return api.get('/conversations') as Promise<{
    items: { id: string; title: string; created_at: string }[]
    total: number
  }>
}

export function getConversation(id: string) {
  return api.get(`/conversations/${id}`) as Promise<{
    id: string
    title: string
    messages: {
      id: string
      role: string
      content: string
      retrievals: { tool_name: string; content_preview: string }[]
      created_at: string
    }[]
    created_at: string
  }>
}

export function deleteConversation(id: string) {
  return api.delete(`/conversations/${id}`)
}
