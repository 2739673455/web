import { useEffect, useRef } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useConversationStore } from '../stores/conversationStore'
import { useAuthStore } from '../stores/authStore'
import { getMessages } from '../services/chat'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 配置 marked.js，禁用段落标签
marked.setOptions({
  breaks: true,
  gfm: true,
})

// 自定义渲染器，禁用段落标签
const renderer = new marked.Renderer()
renderer.paragraph = (text) => text

marked.setOptions({ renderer })

export default function MessageList() {
  const { messages, currentAssistantMessage, hasError } = useChatStore()
  const { currentConversationId, isNewConversation } = useConversationStore()
  const { isAuthenticated } = useAuthStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const previousConversationId = useRef<number | null>(null)

  useEffect(() => {
    // 检测对话是否切换
    const conversationChanged = currentConversationId !== previousConversationId.current

    // 从 null 变为某个 ID 也算作变化
    const fromNullToValue = previousConversationId.current === null && currentConversationId !== null

    // 消息为空说明还没加载过
    const needsLoading = Array.isArray(messages) && messages.length === 0

    // 在以下情况加载消息：
    // 1. 有选中的对话ID
    // 2. 不是新对话状态
    // 3. 用户已登录
    // 4. 对话ID发生变化，或者消息为空（还没加载过）
    if (currentConversationId && !isNewConversation && isAuthenticated &&
        (conversationChanged || fromNullToValue || needsLoading)) {
      loadMessages()
      previousConversationId.current = currentConversationId
    }
  }, [currentConversationId, isNewConversation, isAuthenticated, Array.isArray(messages) ? messages.length : 0])

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentAssistantMessage])

  const loadMessages = async () => {
    try {
      const data = await getMessages(currentConversationId!)
      // 确保 data 是数组
      useChatStore.getState().setMessages(Array.isArray(data) ? data : [])
      // 延迟滚动，确保图片和其他资源已加载
      setTimeout(() => {
        scrollToBottom()
      }, 100)
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const renderImages = (content: string | Record<string, unknown>[]) => {
    if (!Array.isArray(content)) return null
    return content.map((item, index) => {
      if (item.type === 'image_url') {
        const imageUrl = typeof item.image_url === 'string'
          ? item.image_url
          : (item.image_url as { url: string }).url
        return (
          <img
            key={index}
            src={imageUrl}
            alt="Uploaded image"
            className="max-w-full max-h-48 h-auto rounded mb-2"
            onError={(e) => {
              // 图片加载失败，显示占位符
              e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="192" height="192"%3E%3Crect width="192" height="192" fill="%23e5e5e5"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23999"%3EImage%3C/text%3E%3C/svg%3E'
            }}
          />
        )
      }
      return null
    })
  }

  const renderText = (content: string | Record<string, unknown>[]) => {
    if (!Array.isArray(content)) {
      // 检查是否包含 markdown 语法
      const hasMarkdown = content && (
        content.includes('**') ||
        content.includes('*') ||
        content.includes('`') ||
        content.includes('[') ||
        content.includes('#') ||
        content.includes('\n')
      )
      
      if (!hasMarkdown) {
        // 纯文本，直接显示
        return <span>{content}</span>
      }
      
      // 包含 markdown，使用 marked.parse
      const html = marked.parse(content || '') as string
      return (
        <div
          className="markdown-content"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
        />
      )
    }
    return content.map((item, index) => {
      if (item.type === 'text') {
        const text = item.text as string || ''
        const hasMarkdown = text && (
          text.includes('**') ||
          text.includes('*') ||
          text.includes('`') ||
          text.includes('[') ||
          text.includes('#') ||
          text.includes('\n')
        )
        
        if (!hasMarkdown) {
          // 纯文本，直接显示
          return <span key={index}>{text}</span>
        }
        
        // 包含 markdown，使用 marked.parse
        const html = marked.parse(text) as string
        return (
          <div
            key={index}
            className="markdown-content"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
          />
        )
      }
      return null
    })
  }

  return (
    <div
      ref={messagesContainerRef}
      className="flex-1 overflow-y-auto p-6 space-y-6 relative"
    >
      {!currentConversationId && !isNewConversation && Array.isArray(messages) && messages.length === 0 && !currentAssistantMessage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">Chat</h2>
            <p className="opacity-60">Select a conversation or start a new one</p>
          </div>
        </div>
      )}

      {isNewConversation && Array.isArray(messages) && messages.length === 0 && !currentAssistantMessage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">New Chat</h2>
            <p className="opacity-60">Send a message to start</p>
          </div>
        </div>
      )}

      {Array.isArray(messages) && messages.map((message, index) => {
        const hasImage = Array.isArray(message.content) && message.content.some(item => item.type === 'image_url')
        const isLastUserMessage = message.role === 'user' && index === messages.length - 1
        const showRetryButton = isLastUserMessage && hasError

        return (
          <div
            key={index}
            className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} mb-4`}
          >
            {hasImage && (
              <div className="mb-2">
                {renderImages(message.content)}
              </div>
            )}
            <div className="flex items-end gap-2">
              {showRetryButton && (
                <button
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('retryMessage'))
                  }}
                  className="w-6 h-6 flex items-center justify-center text-red-700 cursor-pointer no-hover"
                  title="重试"
                  style={{ flexShrink: 0 }}
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                </button>
              )}
              <div
                className={`${
                  message.role === 'user'
                    ? 'bg-mono-800 rounded-lg px-2 py-1'
                    : ''
                }`}
                style={{ lineHeight: '1.5', margin: '0', color: message.role === 'user' ? 'var(--color-bg)' : undefined, display: 'inline-block' }}
              >
                {renderText(message.content)}
              </div>
            </div>
          </div>
        )
      })}

      {currentAssistantMessage && (
        <div className="flex flex-col items-start">
          <div
            className="markdown-content"
            style={{ lineHeight: '1.5', margin: '0', display: 'inline-block' }}
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(marked.parse(currentAssistantMessage) as string) }}
          />
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}