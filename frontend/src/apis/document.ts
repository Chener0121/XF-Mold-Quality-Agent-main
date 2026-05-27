import api from './index'

export function uploadDocument(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }) as Promise<{ id: string; filename: string; status: string }>
}

export function getTaskStatus(taskId: string) {
  return api.get(`/documents/${taskId}`) as Promise<{
    task_id: string
    filename: string
    stage: string
    progress: Record<string, any>
    status: string
  }>
}

export function listDocuments() {
  return api.get('/documents') as Promise<{ id: string; filename: string }[]>
}

export function getAgentDocuments(agent: string) {
  return api.get(`/documents/agents/${agent}/documents`) as Promise<string[]>
}

export function setAgentDocuments(agent: string, documentIds: string[]) {
  return api.put(`/documents/agents/${agent}/documents`, { document_ids: documentIds }) as Promise<{ ok: boolean }>
}
