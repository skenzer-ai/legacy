import { create } from 'zustand'

type Theme = 'light' | 'dark' | 'system'

interface ThemeStore {
  theme: Theme
  resolvedTheme: 'light' | 'dark'
  setTheme: (theme: Theme) => void
  initializeTheme: () => void
}

export const useThemeStore = create<ThemeStore>((set, get) => ({
  theme: 'system',
  resolvedTheme: 'light',
  
  setTheme: (theme: Theme) => {
    set({ theme })
    // Store in localStorage manually
    localStorage.setItem('theme', theme)
    get().initializeTheme()
  },
  
  initializeTheme: () => {
    // Load from localStorage
    const storedTheme = localStorage.getItem('theme') as Theme || 'system'
    const { theme } = get()
    const currentTheme = theme === 'system' ? storedTheme : theme
    
    let resolvedTheme: 'light' | 'dark' = 'light'
    
    if (currentTheme === 'system') {
      resolvedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches 
        ? 'dark' 
        : 'light'
    } else {
      resolvedTheme = currentTheme
    }
    
    set({ theme: storedTheme, resolvedTheme })
  },
}))

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const store = useThemeStore.getState()
    if (store.theme === 'system') {
      store.initializeTheme()
    }
  })
}