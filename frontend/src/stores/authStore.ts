import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { UserInfo } from '../services/user'

interface AuthState {
  accessToken: string
  refreshToken: string
  userInfo: UserInfo | null
  isAuthenticated: boolean
  setTokens: (accessToken: string, refreshToken: string) => void
  setUserInfo: (userInfo: UserInfo) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: '',
      refreshToken: '',
      userInfo: null,
      isAuthenticated: false,
      setTokens: (accessToken, refreshToken) => {
        set({
          accessToken,
          refreshToken,
          isAuthenticated: !!accessToken,
        })
        // Clear conversation selection when logging in
        if (accessToken) {
          // Import dynamically to avoid circular dependency
          import('../stores/conversationStore').then(({ useConversationStore }) => {
            useConversationStore.getState().setCurrentConversationId(null)
            useConversationStore.getState().setIsNewConversation(false)
          })
        }
      },
      setUserInfo: (userInfo) => set({ userInfo }),
      logout: () => {
        set({
          accessToken: '',
          refreshToken: '',
          userInfo: null,
          isAuthenticated: false,
        })
        // Clear conversation state when logging out
        import('../stores/conversationStore').then(({ useConversationStore }) => {
          useConversationStore.getState().setCurrentConversationId(null)
          useConversationStore.getState().setIsNewConversation(false)
        })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        userInfo: state.userInfo,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
)