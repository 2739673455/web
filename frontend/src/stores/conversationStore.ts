import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { Conversation } from '../services/conversation'

interface ConversationState {
  conversations: Conversation[]
  currentConversationId: number | null
  isNewConversation: boolean
  setConversations: (conversations: Conversation[]) => void
  addConversation: (conversation: Conversation) => void
  updateConversation: (conversation: Conversation) => void
  removeConversations: (ids: number[]) => void
  setCurrentConversationId: (id: number | null) => void
  setIsNewConversation: (isNew: boolean) => void
  getCurrentConversation: () => Conversation | null
}

export const useConversationStore = create<ConversationState>()(
  persist(
    (set, get) => ({
  conversations: [],
  currentConversationId: null,
  isNewConversation: false,
  setConversations: (conversations) => set({ conversations }),
  addConversation: (conversation) =>
    set((state) => ({
      conversations: [...state.conversations, conversation],
      currentConversationId: conversation.conversation_id,
      isNewConversation: false,
    })),
  updateConversation: (conversation) =>
    set((state) => ({
      conversations: state.conversations.map((c) =>
        c.conversation_id === conversation.conversation_id ? conversation : c,
      ),
    })),
  removeConversations: (ids) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => !ids.includes(c.conversation_id)),
      currentConversationId: ids.includes(state.currentConversationId || 0)
        ? null
        : state.currentConversationId,
    })),
  setCurrentConversationId: (id) => set({ currentConversationId: id }),
  setIsNewConversation: (isNew) => set({ isNewConversation: isNew }),
  getCurrentConversation: () => {
    const state = get()
    return (
      state.conversations.find((c) => c.conversation_id === state.currentConversationId) || null
    )
  },
}),
    {
      name: 'conversation-storage',
      partialize: (state) => ({
        currentConversationId: state.currentConversationId,
        isNewConversation: state.isNewConversation,
      }),
    },
  ),
)