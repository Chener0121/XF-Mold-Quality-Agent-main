<template>
  <div class="chat-page">
    <!-- 标题：淡出 -->
    <Transition name="welcome-fade" appear>
      <h2 v-if="!chatStore.activeConversation" class="chat-welcome__title">{{ welcomeText }}</h2>
    </Transition>

    <!-- 消息列表 -->
    <Transition name="messages-fade">
      <div v-if="chatStore.activeConversation" ref="messageListRef" class="chat-messages">
        <div class="chat-messages__inner">
          <div v-if="chatStore.activeConversation.messages.length === 0" class="chat-empty">
            <div class="chat-empty__inner">
              <Bot :size="28" />
              <p>输入问题，开始对话</p>
            </div>
          </div>
          <div
            v-for="(msg, idx) in chatStore.activeConversation.messages"
            :key="idx"
            class="msg"
            :class="'msg--' + msg.role"
          >
            <div class="msg__body">
              <div class="msg__content" v-html="renderMessage(msg)"></div>
              <div v-if="msg.retrievals?.length" class="msg__retrievals">
                <button class="retrievals-toggle" @click="toggleRetrievals(idx)">
                  <FileSearch :size="12" />
                  <span>{{ showRetrievals[idx] ? '收起' : '展开' }}引用来源（{{ msg.retrievals.length }} 条）</span>
                  <ChevronDown :size="12" :class="{ 'retrievals-toggle__icon--open': showRetrievals[idx] }" />
                </button>
                <div v-if="showRetrievals[idx]" class="retrievals-list">
                  <div v-for="(r, ri) in msg.retrievals" :key="ri" class="retrieval-item">
                    <span class="retrieval-preview">{{ r.content_preview.slice(0, 200) }}{{ r.content_preview.length > 200 ? '...' : '' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- 加载动画：pipeline 前置处理阶段 -->
          <div v-if="chatStore.loading && !chatStore.streaming" class="msg msg--assistant">
            <div class="msg__body">
              <div class="msg__dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 唯一的输入框：始终渲染，通过 class 切换位置 -->
    <div class="chat-input-container"
         :class="{ 'chat-input-container--docked': !!chatStore.activeConversation }">
      <div class="chat-input__inner chat-input__inner--welcome"
           :class="{ 'chat-input__inner--multiline': lineCount > 1 }"
           :style="{ height: welcomeInputHeight + 'px' }">
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, watch, onBeforeUnmount } from 'vue'
import katex from 'katex'
import { marked } from 'marked'
import 'katex/dist/katex.min.css'
import { Bot, ArrowUp, FileSearch, ChevronDown } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { askQuestionStream } from '@/apis/rag'

// ── 流式 token 批量合并 ──
let tokenBuffer = ''
let rafId: number | null = null

const chatStore = useChatStore()

const welcomeTexts = ['Ask Away', 'Ready when you are', 'Any new ideas to explore?', 'Ask Me Anything', "what's on your mind?"]
const welcomeText = welcomeTexts[Math.floor(Math.random() * welcomeTexts.length)]
const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement>()
const messageListRef = ref<HTMLElement>()
const showRetrievals = reactive<Record<number, boolean>>({})
const lineCount = ref(1)
const welcomeInputHeight = computed(() => lineCount.value <= 1 ? 64 : Math.min(lineCount.value, 7) * 24 + 78)

function toggleRetrievals(idx: number) {
  showRetrievals[idx] = !showRetrievals[idx]
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function renderMarkdown(text: string): string {
  const holders: string[] = []

  let processed = text.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
    const i = holders.length
    try {
      holders.push(katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false }))
    } catch {
      holders.push(`<code>$$${tex}$$</code>`)
    }
    return `%%K${i}%%`
  })

  processed = processed.replace(/\$([^\$\n]+?)\$/g, (_, tex) => {
    const i = holders.length
    try {
      holders.push(katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false }))
    } catch {
      holders.push(`<code>$${tex}$</code>`)
    }
    return `%%K${i}%%`
  })

  let html = marked.parse(processed) as string
  holders.forEach((rendered, i) => {
    html = html.replace(`<p>%%K${i}%%</p>`, rendered)
    html = html.replace(`%%K${i}%%`, rendered)
  })

  return html
}

function renderMessage(msg: any): string {
  const text = msg.content as string
  if (msg.role === 'user') {
    return escapeHtml(text).replace(/\n/g, '<br>')
  }

  return renderMarkdown(text)
}

let resizeObserver: ResizeObserver | null = null

// ResizeObserver: 内容高度变化时自动滚动（流式 + 非流式通用）
watch(messageListRef, (el, _, onCleanup) => {
  resizeObserver?.disconnect()
  if (!el) return
  const inner = el.querySelector('.chat-messages__inner') as HTMLElement
  if (!inner) return
  resizeObserver = new ResizeObserver(() => {
    const dist = el.scrollHeight - el.scrollTop - el.clientHeight
    if (dist < 120) el.scrollTop = el.scrollHeight
  })
  resizeObserver.observe(inner)
  onCleanup(() => {
    resizeObserver?.disconnect()
    resizeObserver = null
  })
}, { immediate: true })

function scrollToBottom(smooth = false) {
  nextTick(() => {
    const el = messageListRef.value
    if (!el) return
    el.scrollTo({ top: el.scrollHeight, behavior: smooth ? 'smooth' : 'instant' })
  })
}

function autoResize() {
  const el = inputRef.value
  if (!el) return

  el.style.height = '0'
  el.style.paddingTop = '0'
  el.style.paddingBottom = '0'

  const lineHeight = parseFloat(getComputedStyle(el).lineHeight) || 24
  const lines = Math.max(1, Math.round(el.scrollHeight / lineHeight))

  el.style.height = ''
  el.style.paddingTop = ''
  el.style.paddingBottom = ''

  lineCount.value = lines
  el.style.overflowY = lines > 7 ? 'auto' : ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function flushTokenBuffer() {
  if (tokenBuffer) {
    chatStore.appendStreamingToken(tokenBuffer)
    tokenBuffer = ''
  }
  rafId = null
}

let streamAbortController: AbortController | null = null

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chatStore.loading) return

  if (!chatStore.activeConversation) {
    chatStore.createConversation()
    await nextTick()
  }

  chatStore.addUserMessage(text)
  inputText.value = ''
  lineCount.value = 1
  if (inputRef.value) {
    inputRef.value.style.height = ''
    inputRef.value.style.overflowY = ''
  }
  scrollToBottom()

  chatStore.loading = true
  chatStore.streaming = false

  const convId = chatStore.activeId || undefined

  streamAbortController = askQuestionStream(text, convId, {
    onMeta(meta) {
      if (!chatStore.activeId) {
        chatStore.confirmConversationId(meta.conversation_id)
      }
      // 创建空 assistant 消息，切换到 streaming 模式
      chatStore.addAssistantMessage('')
      chatStore.streaming = true
      scrollToBottom()
    },
    onToken(token) {
      // 批量合并 token，每帧只 flush 一次
      tokenBuffer += token
      if (!rafId) {
        rafId = requestAnimationFrame(flushTokenBuffer)
      }
    },
    onDone(data) {
      // 立即刷出剩余 token
      if (rafId) {
        cancelAnimationFrame(rafId)
        rafId = null
      }
      if (tokenBuffer) {
        chatStore.appendStreamingToken(tokenBuffer)
        tokenBuffer = ''
      }
      chatStore.updateRetrievals(
        data.tool_calls.map(tc => ({
          tool_name: tc.tool_name,
          content_preview: tc.content_preview,
        })),
      )
      chatStore.streaming = false
      chatStore.loading = false
      scrollToBottom()
    },
    onError(_message) {
      if (!chatStore.streaming) {
        chatStore.addAssistantMessage('抱歉，出了点问题，请稍后重试。')
      } else {
        chatStore.updateLastAssistantMessage(
          chatStore.activeConversation?.messages.slice(-1)[0]?.content || '抱歉，出了点问题，请稍后重试。',
        )
      }
      chatStore.streaming = false
      chatStore.loading = false
      scrollToBottom()
    },
  })
}

watch(() => chatStore.activeId, () => {
  scrollToBottom()
})

onBeforeUnmount(() => {
  streamAbortController?.abort()
  if (rafId) cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
})
</script>

<style scoped lang="less">
.chat-page {
  position: relative;
  height: 100vh;
  background: var(--main-0);
  overflow: hidden;
}

/* ===== 标题 ===== */
.chat-welcome__title {
  position: absolute;
  top: 38%;
  left: 50%;
  transform: translateX(-50%);
  font-size: 32px;
  font-weight: 600;
  color: var(--main-900);
  margin: 0;
  white-space: nowrap;
}

/* ===== 输入框容器：位置过渡 ===== */
.chat-input-container {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  width: 660px;
  max-width: calc(100% - 48px);
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: top 1.2s cubic-bezier(0.4, 0, 0.2, 1), 
              width 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              padding 0.5s ease,
              border-color 0.3s ease;

  /* 欢迎模式：居中偏下 */
  &:not(.chat-input-container--docked) {
    top: 50%;
  }

  /* 聊天模式：底部，保持同样的宽度 */
  &.chat-input-container--docked {
    top: calc(100% - 100px);
  }
}

/* ===== 输入框内框 ===== */
.chat-input__inner {
  width: 100%;
  position: relative;
  display: flex;
  align-items: flex-end;
  border: 1px solid var(--gray-300);
  border-radius: 24px;
  padding: 4px 4px 4px 16px;
  transition: border-color 0.2s, height 0.2s ease, border-radius 0.2s ease, padding 0.2s ease;

  &:focus-within {
    border-color: var(--color-primary-500);
  }

  textarea {
    flex: 1;
    border: none;
    outline: none;
    resize: none;
    font-size: 16px;
    line-height: 1.5;
    font-family: inherit;
    max-height: 200px;
    padding: 8px 0;
    color: var(--main-900);
    background: transparent;

    &::placeholder {
      color: var(--gray-400);
    }
  }
}

/* 欢迎模式 - 单行药丸 */
.chat-input__inner--welcome {
  height: 64px;
  border-radius: 32px;
  padding: 0 16px 0 24px;
  align-items: center;

  textarea {
    font-size: 16px;
    padding: 0;
  }

  .chat-input__send {
    width: 32px;
    height: 32px;
    flex-shrink: 0;
    position: relative;
    transition: all 0.25s ease;
  }
}

/* 欢迎模式 - 多行展开 */
.chat-input__inner--welcome.chat-input__inner--multiline {
  border-radius: 20px;
  padding: 0;

  textarea {
    width: 100%;
    height: 100%;
    max-height: none;
    box-sizing: border-box;
    padding: 26px 56px 52px 24px;
    overflow-y: hidden;
  }

  .chat-input__send {
    position: absolute;
    right: 16px;
    bottom: 16px;
  }
}

.chat-input__send {
  width: 36px;
  height: 36px;
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

.chat-input__disclaimer {
  text-align: center;
  font-size: 11px;
  color: var(--gray-400);
  margin: 6px 0 0;
}

/* ===== 消息区域 ===== */
.chat-messages {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 70px;
  overflow-y: auto;
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

.chat-messages__inner {
  max-width: 760px;
  margin: 0 auto;
  padding: 24px 24px 16px;
}

.chat-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
}

.chat-empty__inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: var(--gray-400);
  text-align: center;

  p {
    margin: 8px 0 0;
    font-size: 14px;
  }
}

/* 消息 */
.msg {
  display: flex;
  margin-bottom: 24px;
}

.msg--user {
  justify-content: flex-end;
}

.msg--assistant {
  justify-content: flex-start;
}

.msg__body {
  max-width: 640px;
  min-width: 0;
}

.msg__content {
  font-size: 16px;
  line-height: 1.7;
  color: var(--main-900);
  word-break: break-word;

  :deep(p) { margin: 0 0 8px; }
  :deep(p:last-child) { margin-bottom: 0; }
  :deep(ul), :deep(ol) { padding-left: 20px; margin: 4px 0; }
  :deep(code) {
    background: var(--gray-100);
    padding: 1px 5px;
    border-radius: 4px;
    font-size: 13px;
  }
  :deep(pre) {
    background: var(--gray-50);
    border: 1px solid var(--gray-200);
    border-radius: 8px;
    padding: 12px 16px;
    overflow-x: auto;
    font-size: 13px;
    margin: 8px 0;
  }
  :deep(blockquote) {
    border-left: 3px solid var(--gray-300);
    padding-left: 12px;
    color: var(--gray-600);
    margin: 8px 0;
  }
}

.msg--user .msg__content {
  background: var(--gray-100);
  padding: 12px 18px;
  border-radius: 24px 24px 4px 24px;
}

.msg--assistant .msg__content {
  padding: 0;
}

/* 引用来源 */
.msg__retrievals {
  margin-top: 8px;
}

.retrievals-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid var(--gray-200);
  border-radius: 16px;
  background: var(--main-0);
  font-size: 12px;
  color: var(--gray-500);
  cursor: pointer;
  transition: background 0.15s;

  &:hover {
    background: var(--gray-50);
  }
}

.retrievals-toggle__icon--open {
  transform: rotate(180deg);
}

.retrievals-list {
  margin-top: 8px;
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  overflow: hidden;
}

.retrieval-item {
  padding: 8px 12px;
  border-bottom: 1px solid var(--gray-100);
  &:last-child { border-bottom: none; }
}

.retrieval-preview {
  font-size: 12px;
  color: var(--gray-500);
  line-height: 1.5;
}

/* 加载动画 */
.msg__dots {
  display: flex;
  gap: 4px;
  padding: 4px 0;

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

/* ===== Vue Transition 动画 ===== */
.welcome-fade-enter-active {
  transition: opacity 1.2s ease, transform 1.2s ease;
}
.welcome-fade-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
.welcome-fade-leave-active {
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.welcome-fade-leave-from {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.welcome-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.messages-fade-enter-active {
  transition: opacity 0.5s ease 0.3s;
}
.messages-fade-enter-from {
  opacity: 0;
}
</style>
