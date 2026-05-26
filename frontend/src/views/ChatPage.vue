<template>
  <div class="chat-page">
    <!-- 欢迎页 -->
    <div v-if="!chatStore.activeConversation" class="chat-welcome">
      <div class="chat-welcome__inner">
        <h2 class="chat-welcome__title">Ask Away</h2>
        <p class="chat-welcome__desc">基于 FMEA 和 VDA6.4 质量手册的智能问答</p>

        <div class="chat-input__inner chat-input__inner--welcome">
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

    <!-- 对话界面 -->
    <template v-else>
      <!-- 消息列表 -->
      <div ref="messageListRef" class="chat-messages">
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
            <div class="msg__avatar">
              <Bot v-if="msg.role === 'assistant'" :size="16" />
              <User v-else :size="16" />
            </div>
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
          <!-- 加载动画 -->
          <div v-if="chatStore.loading" class="msg msg--assistant">
            <div class="msg__avatar">
              <Bot :size="16" />
            </div>
            <div class="msg__body">
              <div class="msg__dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input">
        <div class="chat-input__inner">
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
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted, watch } from 'vue'
import katex from 'katex'
import { marked } from 'marked'
import 'katex/dist/katex.min.css'
import { Bot, User, ArrowUp, FileSearch, ChevronDown } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { askQuestion } from '@/apis/rag'

const chatStore = useChatStore()
const inputText = ref('')
const inputRef = ref<HTMLTextAreaElement>()
const messageListRef = ref<HTMLElement>()
const showRetrievals = reactive<Record<number, boolean>>({})

function toggleRetrievals(idx: number) {
  showRetrievals[idx] = !showRetrievals[idx]
}

function renderMessage(msg: any): string {
  const text = msg.content as string
  if (msg.role === 'user') {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')
  }

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

  if (!chatStore.activeConversation) {
    chatStore.createConversation()
    await nextTick()
  }

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
  flex-direction: column;
  height: 100vh;
  background: var(--main-0);
}

/* ===== 欢迎页 ===== */
.chat-welcome {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-welcome__inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 680px;
  width: 100%;
  padding: 0 24px;
}

.chat-welcome__title {
  font-size: 32px;
  font-weight: 600;
  color: var(--main-900);
  margin: 0 0 8px;
}

.chat-welcome__desc {
  font-size: 15px;
  color: var(--gray-500);
  margin: 0 0 40px;
}

/* 欢迎页输入框 */
.chat-input__inner--welcome {
  width: 100%;
  border-radius: 28px;
  padding: 8px 8px 8px 20px;

  textarea {
    font-size: 16px;
    padding: 12px 0;
  }
}

.chat-welcome .chat-input__disclaimer {
  margin-top: 12px;
}

/* ===== 消息区域 ===== */
.chat-messages {
  flex: 1;
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
  gap: 12px;
  margin-bottom: 24px;
}

.msg__avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--gray-100);
  color: var(--gray-500);
}

.msg--assistant .msg__avatar {
  background: var(--color-primary-50);
  color: var(--color-primary-500);
}

.msg__body {
  max-width: 640px;
  min-width: 0;
}

.msg__content {
  font-size: 14px;
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
  background: var(--gray-50);
  padding: 10px 14px;
  border-radius: 16px 16px 4px 16px;
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

/* ===== 输入区域 ===== */
.chat-input {
  border-top: 1px solid var(--gray-200);
  padding: 12px 24px 12px;
  background: var(--main-0);
}

.chat-input__inner {
  max-width: 760px;
  margin: 0 auto;
  position: relative;
  display: flex;
  align-items: flex-end;
  border: 1px solid var(--gray-300);
  border-radius: 24px;
  padding: 4px 4px 4px 16px;
  transition: border-color 0.2s;

  &:focus-within {
    border-color: var(--color-primary-500);
  }

  textarea {
    flex: 1;
    border: none;
    outline: none;
    resize: none;
    font-size: 14px;
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
</style>
