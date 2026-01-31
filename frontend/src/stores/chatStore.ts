import { create } from 'zustand'
import { Message } from '../services/chat'

interface ChatState {
  messages: Message[]
  isSending: boolean
  isAborting: boolean
  currentAssistantMessage: string
  hasError: boolean
  errorMessage: string
  setMessages: (messages: Message[] | ((prev: Message[]) => Message[])) => void
  addMessage: (message: Message) => void
  appendToAssistantMessage: (content: string) => void
  completeCurrentAssistantMessage: () => void
  setIsSending: (isSending: boolean) => void
  setIsAborting: (isAborting: boolean) => void
  setHasError: (hasError: boolean) => void
  setErrorMessage: (errorMessage: string) => void
  resetCurrentAssistantMessage: () => void
  clearMessages: () => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isSending: false,
  isAborting: false,
  currentAssistantMessage: '',
  hasError: false,
  errorMessage: '',
  setMessages: (messages) => set((state) => ({
    messages: typeof messages === 'function' ? messages(state.messages) : (Array.isArray(messages) ? messages : []),
  })),
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  appendToAssistantMessage: (content) =>
    set((state) => ({
      currentAssistantMessage: state.currentAssistantMessage + content,
      hasError: false,
      errorMessage: '',
    })),
  completeCurrentAssistantMessage: () =>
    set((state) => {
      if (state.currentAssistantMessage) {
        const newMessage: Message = {
          role: 'assistant',
          content: state.currentAssistantMessage,
          timestamp: new Date().toISOString(),
        }
        return {
          messages: [...state.messages, newMessage],
          currentAssistantMessage: '',
          hasError: false,
          errorMessage: '',
        }
      }
      return state
    }),
  setIsSending: (isSending) => set({ isSending }),
  setIsAborting: (isAborting) => set({ isAborting }),
  setHasError: (hasError) => set({ hasError }),
  setErrorMessage: (errorMessage) => set({ errorMessage }),
  resetCurrentAssistantMessage: () => set({ currentAssistantMessage: '', hasError: false, errorMessage: '' }),
  clearMessages: () => set({ messages: [], currentAssistantMessage: '', hasError: false, errorMessage: '' }),
}))