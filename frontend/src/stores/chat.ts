import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  retrievals?: { tool_name: string; content_preview: string }[]
}

export interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: string
}

const STORAGE_KEY = 'xf-chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const activeId = ref('')
  const loading = ref(false)

  const activeConversation = computed(() =>
    conversations.value.find(c => c.id === activeId.value),
  )

  // 立即从 localStorage 加载，避免首次渲染闪烁
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      conversations.value = data.conversations || []
      activeId.value = data.activeId || ''
    }
  } catch { /* ignore */ }

  function save() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      conversations: conversations.value,
      activeId: activeId.value,
    }))
  }

  function createConversation() {
    const conv: Conversation = {
      id: Date.now().toString(),
      title: '新对话',
      messages: [],
      createdAt: new Date().toISOString(),
    }
    conversations.value.unshift(conv)
    activeId.value = conv.id
    save()
  }

  function switchConversation(id: string) {
    activeId.value = id
    save()
  }

  function deleteConversation(id: string) {
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeId.value === id) {
      activeId.value = conversations.value[0]?.id || ''
    }
    save()
  }

  function goHome() {
    activeId.value = ''
    save()
  }

  function addUserMessage(content: string) {
    const conv = activeConversation.value
    if (!conv) return
    conv.messages.push({ role: 'user', content })
    if (conv.title === '新对话') {
      conv.title = content.length > 20 ? content.slice(0, 20) + '...' : content
    }
    save()
  }

  function addAssistantMessage(content: string, retrievals?: { tool_name: string; content_preview: string }[]) {
    const conv = activeConversation.value
    if (!conv) return
    conv.messages.push({ role: 'assistant', content, retrievals })
    save()
  }

  return {
    conversations,
    activeId,
    activeConversation,
    loading,
    createConversation,
    switchConversation,
    deleteConversation,
    goHome,
    addUserMessage,
    addAssistantMessage,
  }
})
