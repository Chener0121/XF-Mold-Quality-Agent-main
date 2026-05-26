<template>
  <div class="chat-page">
    <!-- 左侧会话列表 -->
    <div class="chat-sidebar">
      <div class="chat-sidebar__header">
        <span>智能问答</span>
        <button class="chat-sidebar__btn" @click="chatStore.createConversation()">
          <Plus :size="16" />
        </button>
      </div>
      <div class="chat-sidebar__list">
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          class="chat-sidebar__item"
          :class="{ active: conv.id === chatStore.activeId }"
          @click="chatStore.switchConversation(conv.id)"
        >
          <MessageSquare :size="14" />
          <span class="chat-sidebar__title">{{ conv.title }}</span>
          <Trash2 :size="12" class="chat-sidebar__delete" @click.stop="chatStore.deleteConversation(conv.id)" />
        </div>
        <div v-if="chatStore.conversations.length === 0" class="chat-sidebar__empty">
          暂无对话
        </div>
      </div>
    </div>

    <!-- 右侧聊天区域 -->
    <div class="chat-main">
      <!-- 欢迎界面 -->
      <div v-if="!chatStore.activeConversation" class="chat-welcome">
        <Bot :size="40" />
        <h2>XF 质量助手</h2>
        <p>上传 FMEA/VDA6.4 文档，开始智能问答</p>
        <button class="chat-welcome__btn" @click="chatStore.createConversation()">开始新对话</button>
      </div>

      <!-- 对话界面 -->
      <template v-else>
        <!-- 消息列表 -->
        <div ref="messageListRef" class="chat-messages">
          <div v-if="chatStore.activeConversation.messages.length === 0" class="chat-messages__empty">
            输入问题，开始对话
          </div>
          <div
            v-for="(msg, idx) in chatStore.activeConversation.messages"
            :key="idx"
            class="msg"
            :class="'msg--' + msg.role"
          >
            <div class="msg__avatar" :style="msg.role === 'assistant' ? 'background: var(--color-primary-50); color: var(--color-primary-500)' : 'background: var(--gray-100); color: var(--gray-600)'">
              <Bot v-if="msg.role === 'assistant'" :size="16" />
              <User v-else :size="16" />
            </div>
            <div class="msg__body">
              <div class="msg__content" v-html="renderMessage(msg)"></div>
              <div v-if="msg.retrievals?.length" class="msg__retrievals">
                <div class="retrieval-header">
                  <FileSearch :size="12" />
                  <span>引用来源（{{ msg.retrievals.length }} 条检索）</span>
                </div>
                <div v-for="(r, ri) in msg.retrievals" :key="ri" class="retrieval-item">
                  <span class="retrieval-name">{{ r.tool_name }}</span>
                  <span class="retrieval-preview">{{ r.content_preview.slice(0, 120) }}{{ r.content_preview.length > 120 ? '...' : '' }}</span>
                </div>
              </div>
            </div>
          </div>
          <!-- 加载动画 -->
          <div v-if="chatStore.loading" class="msg msg--assistant">
            <div class="msg__avatar" style="background: var(--color-primary-50); color: var(--color-primary-500)">
              <Bot :size="16" />
            </div>
            <div class="msg__body">
              <div class="msg__dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <div class="chat-input__wrapper">
            <textarea
              ref="inputRef"
              v-model="inputText"
              placeholder="输入你的问题..."
              rows="1"
              @input="autoResize"
              @keydown="handleKeydown"
            ></textarea>
            <button class="chat-input__send" :disabled="!inputText.trim() || chatStore.loading" @click="sendMessage">
              <ArrowUp :size="18" />
            </button>
          </div>
          <p class="chat-input__disclaimer">内容由 AI 生成，请仔细甄别</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch } from 'vue'
import katex from 'katex'
import { marked } from 'marked'
import 'katex/dist/katex.min.css'
import { Plus, MessageSquare, Trash2, Bot, User, ArrowUp, FileSearch } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { askQuestion } from '@/apis/rag'

const chatStore = useChatStore()
const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement>()
const messageListRef = ref<HTMLElement>()

function renderMessage(msg: any): string {
  const text = msg.content as string
  if (msg.role === 'user') {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
  }

  // Assistant: 渲染 LaTeX + Markdown
  const holders: string[] = []

  // 提取块级公式 $$...$$
  let processed = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    const i = holders.length
    try {
      holders.push(katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false }))
    } catch {
      holders.push(`<code>$$${tex}$$</code>`)
    }
    return `%%K${i}%%`
  })

  // 提取行内公式 $...$
  processed = processed.replace(/\$([^\$\n]+?)\$/g, (_, tex) => {
    const i = holders.length
    try {
      holders.push(katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false }))
    } catch {
      holders.push(`<code>$${tex}$</code>`)
    }
    return `%%K${i}%%`
  })

  // Markdown 渲染
  let html = marked.parse(processed) as string

  // 还原公式占位符
  holders.forEach((rendered, i) => {
    html = html.replace(`<p>%%K${i}%%</p>`, rendered)
    html = html.replace(`%%K${i}%%`, rendered)
  })

  return html
}

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chatStore.loading) return

  chatStore.addUserMessage(text)
  inputText.value = ''
  if (inputRef.value) inputRef.value.style.height = 'auto'
  scrollToBottom()

  chatStore.loading = true
  try {
    const result = await askQuestion(text)
    chatStore.addAssistantMessage(result.answer, result.retrievals)
  } catch (e: any) {
    chatStore.addAssistantMessage('抱歉，出了点问题，请稍后重试。')
  } finally {
    chatStore.loading = false
    scrollToBottom()
  }
}

onMounted(() => {
  chatStore.load()
})

watch(() => chatStore.activeId, () => {
  scrollToBottom()
})
</script>

<style scoped lang="less">
.chat-page {
  display: flex;
  height: calc(100vh - 64px);
  margin: -20px;
}

/* ===== 左侧会话列表 ===== */
.chat-sidebar {
  width: 260px;
  border-right: 1px solid var(--gray-200);
  background: var(--main-0);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.chat-sidebar__header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--gray-200);
  font-size: 15px;
  font-weight: 600;
  color: var(--main-800);
}

.chat-sidebar__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary-500);
  color: var(--main-0);
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: var(--color-primary-700);
  }
}

.chat-sidebar__list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.chat-sidebar__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--gray-600);
  transition: background 0.15s;

  &:hover {
    background: var(--gray-50);
  }

  &.active {
    background: var(--color-primary-50);
    color: var(--color-primary-500);
  }

  &:hover .chat-sidebar__delete {
    opacity: 1;
  }
}

.chat-sidebar__title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-sidebar__delete {
  opacity: 0;
  color: var(--gray-400);
  flex-shrink: 0;
  transition: opacity 0.15s;

  &:hover {
    color: var(--color-error-500);
  }
}

.chat-sidebar__empty {
  text-align: center;
  padding: 24px 0;
  color: var(--gray-400);
  font-size: 13px;
}

/* ===== 右侧聊天区域 ===== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--main-0);
  min-width: 0;
}

/* 欢迎界面 */
.chat-welcome {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--gray-400);

  h2 {
    font-size: 20px;
    color: var(--main-800);
    font-weight: 600;
  }

  p {
    font-size: 14px;
  }
}

.chat-welcome__btn {
  margin-top: 8px;
  padding: 8px 24px;
  border: none;
  border-radius: 8px;
  background: var(--color-primary-500);
  color: var(--main-0);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: var(--color-primary-700);
  }
}

/* 消息列表 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
}

.chat-messages__empty {
  text-align: center;
  padding-top: 40%;
  color: var(--gray-400);
  font-size: 14px;
}

/* 单条消息 */
.msg {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.msg--user {
  flex-direction: row-reverse;
}

.msg__avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.msg__body {
  max-width: 70%;
}

.msg--user .msg__body {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.msg__content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.msg--user .msg__content {
  background: var(--color-primary-500);
  color: var(--main-0);
  border-bottom-right-radius: 4px;
}

.msg--assistant .msg__content {
  background: var(--gray-50);
  color: var(--main-900);
  border-bottom-left-radius: 4px;
}

/* 引用来源 */
.msg__retrievals {
  margin-top: 8px;
  background: var(--gray-50);
  border-radius: 8px;
  padding: 10px 12px;
  border: 1px solid var(--gray-200);
}

.retrieval-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--gray-500);
  margin-bottom: 6px;
}

.retrieval-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 0;
  border-bottom: 1px solid var(--gray-100);

  &:last-child {
    border-bottom: none;
  }
}

.retrieval-name {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-primary-500);
}

.retrieval-preview {
  font-size: 11px;
  color: var(--gray-500);
  line-height: 1.4;
}

/* 加载动画 */
.msg__dots {
  display: flex;
  gap: 4px;
  padding: 12px 16px;

  span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--gray-400);
    animation: dot-bounce 1.2s infinite ease-in-out;

    &:nth-child(2) { animation-delay: 0.2s; }
    &:nth-child(3) { animation-delay: 0.4s; }
  }
}

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入区域 */
.chat-input {
  padding: 0 32px 0px;
}

.chat-input__disclaimer {
  text-align: center;
  font-size: 11px;
  color: var(--gray-400);
  margin-top: 6px;
}

.chat-input__wrapper {
  position: relative;
  display: flex;
  align-items: flex-end;

  textarea {
    width: 100%;
    padding: 10px 48px 10px 14px;
    border: 1px solid var(--gray-200);
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
    resize: none;
    outline: none;
    font-family: inherit;
    max-height: 200px;
    background: var(--gray-25);
    color: var(--main-900);
    transition: border-color 0.2s;

    &:focus {
      border-color: var(--color-primary-500);
    }

    &::placeholder {
      color: var(--gray-400);
    }
  }
}

.chat-input__send {
  position: absolute;
  right: 6px;
  bottom: 6px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--color-primary-500);
  color: var(--main-0);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.2s;

  &:hover:not(:disabled) {
    background: var(--color-primary-700);
  }

  &:disabled {
    background: var(--gray-300);
    cursor: not-allowed;
  }
}
</style>
