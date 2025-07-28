import { create } from 'zustand'

export interface ConnectionStatus {
  status: 'disconnected' | 'connecting' | 'connected' | 'error'
  lastChecked?: Date
  errorMessage?: string
  responseTime?: number
}

export type AuthorizationType = 'bearer' | 'infraonDNS' | 'custom'

export interface ApplicationSettings {
  // API Configuration
  apiRootUrl: string
  authorizationKey: string
  authorizationType: AuthorizationType
  customAuthPrefix: string
  testEndpoint: string
  csrfToken: string
  
  // Proxy Configuration
  useProxy: boolean
  proxyUrl: string
  
  // Testing Configuration
  defaultTimeout: number
  autoRetryEnabled: boolean
  maxRetries: number
  
  // UI Preferences
  defaultRequestFormat: 'json' | 'form' | 'raw'
  showResponseHeaders: boolean
  enableSyntaxHighlighting: boolean
  
  // AI Features
  aiAssistanceEnabled: boolean
  autoGenerateTestData: boolean
  aiSuggestionsEnabled: boolean
  
  // Advanced
  enableRequestLogging: boolean
  preserveHistory: boolean
  workspaceMode: 'single' | 'tabs'
}

interface SettingsStore {
  settings: ApplicationSettings
  connectionStatus: ConnectionStatus
  
  // Settings Actions
  updateSettings: (settings: Partial<ApplicationSettings>) => void
  resetToDefaults: () => void
  exportSettings: () => string
  importSettings: (settingsJson: string) => Promise<boolean>
  
  // Connection Actions
  testConnection: () => Promise<void>
  updateConnectionStatus: (status: Partial<ConnectionStatus>) => void
  
  // Persistence
  saveSettings: () => void
  loadSettings: () => void
}

const defaultSettings: ApplicationSettings = {
  // API Configuration
  apiRootUrl: 'http://localhost:8000',
  authorizationKey: '',
  authorizationType: 'bearer',
  customAuthPrefix: '',
  testEndpoint: '/api/v1/services',
  csrfToken: '',
  
  // Proxy Configuration
  useProxy: false,
  proxyUrl: 'http://localhost:8000',
  
  // Testing Configuration
  defaultTimeout: 30000, // 30 seconds
  autoRetryEnabled: true,
  maxRetries: 3,
  
  // UI Preferences
  defaultRequestFormat: 'json',
  showResponseHeaders: true,
  enableSyntaxHighlighting: true,
  
  // AI Features
  aiAssistanceEnabled: true,
  autoGenerateTestData: true,
  aiSuggestionsEnabled: true,
  
  // Advanced
  enableRequestLogging: false,
  preserveHistory: true,
  workspaceMode: 'single',
}

const defaultConnectionStatus: ConnectionStatus = {
  status: 'disconnected',
}

export const useSettingsStore = create<SettingsStore>((set, get) => ({
  settings: defaultSettings,
  connectionStatus: defaultConnectionStatus,
  
  updateSettings: (newSettings: Partial<ApplicationSettings>) => {
    const currentSettings = get().settings
    const updatedSettings = { ...currentSettings, ...newSettings }
    
    set({ settings: updatedSettings })
    get().saveSettings()
    
    // If API URL, auth key, auth type, test endpoint, or proxy settings changed, test connection
    if (newSettings.apiRootUrl || 
        newSettings.authorizationKey !== undefined || 
        newSettings.authorizationType || 
        newSettings.testEndpoint ||
        newSettings.useProxy !== undefined ||
        newSettings.proxyUrl) {
      get().testConnection()
    }
  },
  
  resetToDefaults: () => {
    set({ 
      settings: defaultSettings,
      connectionStatus: defaultConnectionStatus 
    })
    get().saveSettings()
  },
  
  exportSettings: () => {
    const { settings } = get()
    return JSON.stringify(settings, null, 2)
  },
  
  importSettings: async (settingsJson: string): Promise<boolean> => {
    try {
      const parsedSettings = JSON.parse(settingsJson)
      
      // Validate required fields
      if (!parsedSettings.apiRootUrl) {
        throw new Error('Missing required field: apiRootUrl')
      }
      
      // Merge with defaults to ensure all fields exist
      const validatedSettings = { ...defaultSettings, ...parsedSettings }
      
      set({ settings: validatedSettings })
      get().saveSettings()
      await get().testConnection()
      
      return true
    } catch (error) {
      console.error('Failed to import settings:', error)
      return false
    }
  },
  
  testConnection: async () => {
    const { settings } = get()
    
    set({ 
      connectionStatus: { 
        status: 'connecting', 
        lastChecked: new Date() 
      } 
    })
    
    try {
      const startTime = Date.now()
      let url: string
      let headers: Record<string, string>
      
      if (settings.useProxy) {
        // Use proxy mode - send request to our backend proxy
        const proxyBase = settings.proxyUrl.replace(/\/$/, '')
        const testPath = settings.testEndpoint.replace(/^\//, '') // Remove leading slash for proxy
        url = `${proxyBase}/api/v1/proxy/infraon/${testPath}`
        
        headers = {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-Infraon-Base-URL': settings.apiRootUrl,
          'X-Infraon-Auth-Type': settings.authorizationType,
          'X-Infraon-Auth-Token': settings.authorizationKey,
        }
        
        if (settings.csrfToken) {
          headers['X-Infraon-CSRF-Token'] = settings.csrfToken
        }
      } else {
        // Direct mode (original behavior)
        const baseUrl = settings.apiRootUrl.replace(/\/$/, '')
        const testPath = settings.testEndpoint.startsWith('/') ? settings.testEndpoint : `/${settings.testEndpoint}`
        url = `${baseUrl}${testPath}`
        
        headers = {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        }
        
        // Add authorization header based on type
        if (settings.authorizationKey) {
          switch (settings.authorizationType) {
            case 'bearer':
              headers['Authorization'] = `Bearer ${settings.authorizationKey}`
              break
            case 'infraonDNS':
              headers['Authorization'] = `infraonDNS ${settings.authorizationKey}`
              break
            case 'custom':
              const prefix = settings.customAuthPrefix || 'Bearer'
              headers['Authorization'] = `${prefix} ${settings.authorizationKey}`
              break
          }
        }
        
        // Add CSRF token if provided
        if (settings.csrfToken) {
          headers['X-CSRFToken'] = settings.csrfToken
        }
      }
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
        signal: AbortSignal.timeout(10000), // 10 second timeout
      })
      
      const responseTime = Date.now() - startTime
      
      // Consider 2xx responses as successful
      if (response.ok) {
        set({
          connectionStatus: {
            status: 'connected',
            lastChecked: new Date(),
            responseTime,
          }
        })
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    } catch (error) {
      let errorMessage = 'Unknown error'
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Connection timeout (10s)'
        } else if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
          if (settings.useProxy) {
            errorMessage = 'Proxy connection failed - check if the backend proxy server is running'
          } else {
            // This is typically a CORS error when testing external APIs from localhost
            errorMessage = 'CORS Error: Cannot connect to external API from localhost. Enable proxy mode to bypass this restriction.'
          }
        } else if (error.message.includes('CORS')) {
          errorMessage = 'CORS error - enable proxy mode to bypass cross-origin restrictions'
        } else {
          errorMessage = error.message
        }
      }
      
      set({
        connectionStatus: {
          status: 'error',
          lastChecked: new Date(),
          errorMessage,
        }
      })
    }
  },
  
  updateConnectionStatus: (status: Partial<ConnectionStatus>) => {
    const currentStatus = get().connectionStatus
    set({ connectionStatus: { ...currentStatus, ...status } })
  },
  
  saveSettings: () => {
    try {
      const { settings } = get()
      localStorage.setItem('man-o-man-settings', JSON.stringify(settings))
    } catch (error) {
      console.error('Failed to save settings to localStorage:', error)
    }
  },
  
  loadSettings: () => {
    try {
      const storedSettings = localStorage.getItem('man-o-man-settings')
      if (storedSettings) {
        const parsedSettings = JSON.parse(storedSettings)
        const validatedSettings = { ...defaultSettings, ...parsedSettings }
        set({ settings: validatedSettings })
        
        // Test connection on load if URL is configured
        if (validatedSettings.apiRootUrl && validatedSettings.apiRootUrl !== 'http://localhost:8000') {
          get().testConnection()
        }
      }
    } catch (error) {
      console.error('Failed to load settings from localStorage:', error)
      // Reset to defaults on error
      set({ settings: defaultSettings })
    }
  },
}))

// Initialize settings on store creation
if (typeof window !== 'undefined') {
  useSettingsStore.getState().loadSettings()
}