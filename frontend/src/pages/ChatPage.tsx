import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import ConversationList from '../components/ConversationList'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import AuthModal from '../components/AuthModal'
import UserProfileModal from '../components/UserProfileModal'
import { getConversations } from '../services/conversation'
import { getModelConfigs } from '../services/modelConfig'
import { useConversationStore } from '../stores/conversationStore'
import { useModelConfigStore } from '../stores/modelConfigStore'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'

/**
 * Main chat page component
 * Manages chat interface layout and state
 */
export default function ChatPage() {
  const { setConversations, setIsNewConversation, setCurrentConversationId, conversations, currentConversationId, isNewConversation } = useConversationStore()
  const { configs, setSelectedConfigId, setConfigs: setModelConfigs } = useModelConfigStore()
  const { accessToken } = useAuthStore()
  const previousAccessToken = useRef('')
  const location = useLocation()
  const hasCheckedConversation = useRef(false)

  // Modal display states
  const [showProfile, setShowProfile] = useState(false)
  const [showLogin, setShowLogin] = useState(false)

  /**
   * Handle returning from ModelConfigPage using global event
   */
  useEffect(() => {
    const handleRestoreConversation = (event: Event) => {
      const customEvent = event as CustomEvent<number>
      setCurrentConversationId(customEvent.detail)
      setIsNewConversation(false)
    }

    window.addEventListener('restoreConversation', handleRestoreConversation)

    // Check URL search params for restore
    const searchParams = new URLSearchParams(location.search)
    const restoreId = searchParams.get('restore')
    if (restoreId) {
      const conversationId = parseInt(restoreId, 10)
      setCurrentConversationId(conversationId)
      setIsNewConversation(false)
      window.history.replaceState({}, '', '/')
    }

    return () => {
      window.removeEventListener('restoreConversation', handleRestoreConversation)
    }
  }, [])

  /**
   * Load conversations and model configs when accessToken changes
   * Only loads when accessToken changes from empty to valid, avoiding duplicate requests
   */
  useEffect(() => {
    if (accessToken && !previousAccessToken.current) {
      previousAccessToken.current = accessToken
      loadConversations()
      loadModelConfigs()
    }
    // Reset previousAccessToken when accessToken is cleared (logout)
    if (!accessToken) {
      previousAccessToken.current = ''
    }
  }, [accessToken])

  /**
   * Auto-select first config when model configs are loaded
   */
  useEffect(() => {
    if (configs.length > 0 && !useModelConfigStore.getState().selectedConfigId) {
      setSelectedConfigId(configs[0].config_id)
    }
  }, [configs])

  /**
   * Set model config when conversation changes
   * Also validate restored conversationId on page load
   */
  useEffect(() => {
    const { clearMessages } = useChatStore.getState()

    if (currentConversationId) {
      const conversation = conversations.find(c => c.conversation_id === currentConversationId)
      if (conversation) {
        if (conversation.model_config_id) {
          setSelectedConfigId(conversation.model_config_id)
        }
      } else if (!hasCheckedConversation.current && conversations.length > 0) {
        // Conversation not found on first load with populated list (may have been deleted), clear currentConversationId
        // 但也要检查是否是新创建的对话（可能在重新加载列表时还没返回）
        // 只有在多次检查后才清除，避免误判
        setCurrentConversationId(null)
        clearMessages()
        hasCheckedConversation.current = true
      }
    } else if (!isNewConversation) {
      // Clear messages only when no conversation is selected AND it's not a new conversation
      clearMessages()
    }
  }, [currentConversationId, conversations, setSelectedConfigId, isNewConversation])

  /**
   * Load conversation list
   */
  const loadConversations = async () => {
    try {
      const data = await getConversations()
      setConversations(data)
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }

  /**
   * Load model config list
   */
  const loadModelConfigs = async () => {
    try {
      const data = await getModelConfigs()
      setModelConfigs(data)
      if (data.length > 0 && !useModelConfigStore.getState().selectedConfigId) {
        setSelectedConfigId(data[0].config_id)
      }
    } catch (err) {
      console.error('Failed to load model configs:', err)
    }
  }

  /**
   * Create new conversation
   */
  const handleNewConversation = () => {
    if (!accessToken) {
      setShowLogin(true)
      return
    }
    setCurrentConversationId(null)
    setIsNewConversation(true)
    useChatStore.getState().clearMessages()
  }

  /**
   * Handle user avatar click
   * Show user profile if logged in, otherwise show login modal
   */
  const handleProfileClick = () => {
    if (!accessToken) {
      setShowLogin(true)
      return
    }
    setShowProfile(true)
  }

  /**
   * Close user profile modal
   */
  const handleProfileClose = () => {
    setShowProfile(false)
  }

  return (
    <div className="min-h-screen">
      <div className="flex h-screen">
        {/* Left side: conversation list */}
        <ConversationList
          onNewConversation={handleNewConversation}
          onProfileClick={handleProfileClick}
          onShowLogin={() => setShowLogin(true)}
        />

        {/* Right side: message list and input */}
        <div className="flex-1 flex flex-col">
          <MessageList />
          <ChatInput onShowLogin={() => setShowLogin(true)} />
        </div>
      </div>

      {/* Login/Register modal */}
      <AuthModal isOpen={showLogin} onClose={() => setShowLogin(false)} />

      {/* User profile modal */}
      <UserProfileModal isOpen={showProfile} onClose={handleProfileClose} />
    </div>
  )
}