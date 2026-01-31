import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark'

interface ThemeStore {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
  isDark: boolean
}

export const useThemeStore = create<ThemeStore>()(
  persist(
    (set, get) => ({
      theme: 'light',
      isDark: false,
      toggleTheme: () => {
        const currentTheme = get().theme
        const newTheme: Theme = currentTheme === 'light' ? 'dark' : 'light'
        set({ theme: newTheme, isDark: newTheme === 'dark' })

        // Apply theme to document
        if (newTheme === 'dark') {
          document.documentElement.setAttribute('data-theme', 'dark')
        } else {
          document.documentElement.removeAttribute('data-theme')
        }
      },
      setTheme: (theme: Theme) => {
        set({ theme, isDark: theme === 'dark' })

        // Apply theme to document
        if (theme === 'dark') {
          document.documentElement.setAttribute('data-theme', 'dark')
        } else {
          document.documentElement.removeAttribute('data-theme')
        }
      },
    }),
    {
      name: 'theme-storage',
    }
  )
)

// Initialize theme on app load
const initializeTheme = () => {
  const stored = localStorage.getItem('theme-storage')
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      const theme = parsed.state?.theme || 'light'
      if (theme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark')
      }
    } catch (error) {
      console.error('Failed to parse theme storage:', error)
    }
  }
}

// Call immediately to set theme on load
initializeTheme()