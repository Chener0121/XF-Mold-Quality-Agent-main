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
  const streaming = ref(false)

  const activeConversation = computed(() =>
    conversations.value.find(c => c.id === activeId.value),
  )

  // 从 localStorage 加载
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

  function createConversation(): Conversation {
    const conv: Conversation = {
      id: '',  // placeholder，等后端返回真实 ID 后回填
      title: '新对话',
      messages: [],
      createdAt: new Date().toISOString(),
    }
    conversations.value.unshift(conv)
    activeId.value = ''  // 通过 placeholder 标识
    _pendingConv = conv
    save()
    return conv
  }

  // 跟踪待回填的 conversation
  let _pendingConv: Conversation | null = null

  function confirmConversationId(serverId: string) {
    if (_pendingConv) {
      _pendingConv.id = serverId
      activeId.value = serverId
      _pendingConv = null
      save()
    }
  }

  function switchConversation(id: string) {
    activeId.value = id
    save()
  }

  async function deleteConversation(id: string) {
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeId.value === id) {
      activeId.value = conversations.value[0]?.id || ''
    }
    save()

    // 同步后端
    try {
      const { deleteConversation: apiDelete } = await import('@/apis/conversation')
      await apiDelete(id)
    } catch { /* 忽略后端错误，本地已删除 */ }
  }

  function goHome() {
    activeId.value = ''
    save()
  }

  function addUserMessage(content: string) {
    const conv = activeConversation.value || _pendingConv
    if (!conv) return
    conv.messages.push({ role: 'user', content })
    if (conv.title === '新对话') {
      conv.title = content.length > 20 ? content.slice(0, 20) + '...' : content
    }
    save()
  }

  function addAssistantMessage(content: string, retrievals?: { tool_name: string; content_preview: string }[]) {
    const conv = activeConversation.value || _pendingConv
    if (!conv) return
    conv.messages.push({ role: 'assistant', content, retrievals })
    save()
  }

  // ── Streaming 方法 ──

  function appendStreamingToken(token: string) {
    const conv = activeConversation.value || _pendingConv
    if (!conv || conv.messages.length === 0) return
    const lastMsg = conv.messages[conv.messages.length - 1]
    if (lastMsg.role === 'assistant') {
      lastMsg.content += token
    }
    // 不调用 save()，避免频繁写入 localStorage
  }

  function updateRetrievals(retrievals: { tool_name: string; content_preview: string }[]) {
    const conv = activeConversation.value || _pendingConv
    if (!conv || conv.messages.length === 0) return
    const lastMsg = conv.messages[conv.messages.length - 1]
    if (lastMsg.role === 'assistant') {
      lastMsg.retrievals = retrievals
      save()
    }
  }

  function updateLastAssistantMessage(content: string) {
    const conv = activeConversation.value || _pendingConv
    if (!conv || conv.messages.length === 0) return
    const lastMsg = conv.messages[conv.messages.length - 1]
    if (lastMsg.role === 'assistant') {
      lastMsg.content = content
      save()
    }
  }

  return {
    conversations,
    activeId,
    activeConversation,
    loading,
    streaming,
    createConversation,
    confirmConversationId,
    switchConversation,
    deleteConversation,
    goHome,
    addUserMessage,
    addAssistantMessage,
    appendStreamingToken,
    updateRetrievals,
    updateLastAssistantMessage,
  }
})
