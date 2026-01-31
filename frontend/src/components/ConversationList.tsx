import { useConversationStore } from '../stores/conversationStore'
import { useAuthStore } from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import ThemeToggle from './ThemeToggle'
import { deleteConversations } from '../services/conversation'

interface ConversationListProps {
  onNewConversation: () => void
  onProfileClick: () => void
  onShowLogin: () => void
}

export default function ConversationList({
  onNewConversation,
  onProfileClick,
  onShowLogin,
}: ConversationListProps) {
  const { conversations, setCurrentConversationId, setIsNewConversation, removeConversations } = useConversationStore()
  const { accessToken, userInfo } = useAuthStore()
  const { isDark, toggleTheme } = useThemeStore()

  const handleSelectConversation = (conversationId: number) => {
    if (!accessToken) {
      onShowLogin()
      return
    }
    setCurrentConversationId(conversationId)
    setIsNewConversation(false)
  }

  const handleDeleteConversation = async (conversationId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!accessToken) {
      onShowLogin()
      return
    }
    try {
      await deleteConversations({ ids: [conversationId] })
      removeConversations([conversationId])
    } catch (err) {
      console.error('Failed to delete conversation:', err)
    }
  }

  return (
    <div className="w-64 flex-shrink-0 border-r border-mono flex flex-col h-screen">
      <div className="p-4 flex justify-center">
        <button
          onClick={onNewConversation}
          className="w-fit py-1 px-3 transition-colors text-center dot-shadow"
        >
          + New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {conversations.map((conversation) => (
          <div
            key={conversation.conversation_id}
            className="p-2 cursor-pointer flex items-center justify-between hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors group whitespace-nowrap"
            onClick={() => handleSelectConversation(conversation.conversation_id)}
          >
            <span 
              className="truncate flex-1 max-w-48" 
              title={conversation.title || 'New Chat'}
            >
              {conversation.title || 'New Chat'}
            </span>
            <button
              onClick={(e) => handleDeleteConversation(conversation.conversation_id, e)}
              className="p-1 text-red-700 hover:bg-red-700 hover:text-white transition-colors"
              title="Delete"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        ))}
      </div>

      <div className="flex flex-col items-center">
        <button
          onClick={onProfileClick}
          className="py-1 px-3 transition-colors flex items-center justify-center dot-shadow max-w-48"
          title={userInfo?.username || 'User'}
        >
          <span className="truncate" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block', maxWidth: '100%' }}>
            {userInfo?.username || 'User'}
          </span>
        </button>
        <div className="dot-shadow">
          <ThemeToggle isDark={isDark} onToggle={toggleTheme} />
        </div>
      </div>
    </div>
  )
}