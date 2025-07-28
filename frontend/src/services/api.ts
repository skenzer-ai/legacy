import { useSettingsStore } from '../stores/settings'

interface Service {
  service_name: string
  endpoint_count: number
  suggested_description: string
  tier1_operations: number
  tier2_operations: number
  confidence_score: number
  needs_review: boolean
  keywords: string[]
  synonyms: string[]
}

// Alias for compatibility with existing components
interface ServiceSummary extends Service {}

interface ApiResponse<T> {
  data: T
  status: string
  message?: string
}

class ApiService {
  // Method to make requests to external APIs through proxy
  async makeInfraonRequest(endpoint: string, options: RequestInit = {}): Promise<any> {
    const settingsStore = useSettingsStore.getState()
    
    if (!settingsStore.settings.useProxy) {
      throw new Error('Proxy mode is not enabled. Enable proxy mode in settings to make Infraon API requests.')
    }
    
    const proxyBase = this.getBaseUrl()
    const cleanEndpoint = endpoint.replace(/^\//, '') // Remove leading slash
    const url = `${proxyBase}/api/v1/proxy/infraon/${cleanEndpoint}`
    
    const config: RequestInit = {
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
      timeout: settingsStore.settings.defaultTimeout,
      ...options,
    }

    // Log request if enabled
    if (settingsStore.settings.enableRequestLogging) {
      console.log(`[Infraon API Request] ${options.method || 'GET'} ${endpoint}`, {
        proxyUrl: url,
        headers: config.headers,
        body: options.body,
      })
    }

    try {
      const response = await fetch(url, config)
      
      // Log response if enabled
      if (settingsStore.settings.enableRequestLogging) {
        console.log(`[Infraon API Response] ${response.status} ${response.statusText}`, {
          endpoint,
          headers: Object.fromEntries(response.headers.entries()),
        })
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error(`Infraon API request failed for ${endpoint}:`, error)
      throw error
    }
  }

  private getBaseUrl(): string {
    const settingsStore = useSettingsStore.getState()
    
    // If proxy mode is enabled, use proxy URL for our backend
    if (settingsStore.settings.useProxy) {
      return settingsStore.settings.proxyUrl.replace(/\/$/, '')
    }
    
    // Direct mode: use configured API URL
    const configuredUrl = settingsStore.settings.apiRootUrl
    
    if (configuredUrl && configuredUrl !== 'http://localhost:8000') {
      return configuredUrl.replace(/\/$/, '') // Remove trailing slash
    }
    
    // Fallback to environment variable or derive from current location
    if (import.meta.env.VITE_API_BASE_URL) {
      return import.meta.env.VITE_API_BASE_URL
    }
    
    // If accessing via ssh.skenzer.com, use same host for API
    const currentHost = window.location.host
    if (currentHost.includes('ssh.skenzer.com')) {
      return `${window.location.protocol}//ssh.skenzer.com:8000`
    }
    
    return 'http://localhost:8000'
  }
  
  private getHeaders(): Record<string, string> {
    const settingsStore = useSettingsStore.getState()
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    }
    
    // In proxy mode, send Infraon config as headers to proxy
    if (settingsStore.settings.useProxy) {
      headers['X-Infraon-Base-URL'] = settingsStore.settings.apiRootUrl
      headers['X-Infraon-Auth-Type'] = settingsStore.settings.authorizationType
      
      if (settingsStore.settings.authorizationKey) {
        headers['X-Infraon-Auth-Token'] = settingsStore.settings.authorizationKey
      }
      
      if (settingsStore.settings.csrfToken) {
        headers['X-Infraon-CSRF-Token'] = settingsStore.settings.csrfToken
      }
    } else {
      // Direct mode: add authorization header based on configured type
      if (settingsStore.settings.authorizationKey) {
        switch (settingsStore.settings.authorizationType) {
          case 'bearer':
            headers['Authorization'] = `Bearer ${settingsStore.settings.authorizationKey}`
            break
          case 'infraonDNS':
            headers['Authorization'] = `infraonDNS ${settingsStore.settings.authorizationKey}`
            break
          case 'custom':
            const prefix = settingsStore.settings.customAuthPrefix || 'Bearer'
            headers['Authorization'] = `${prefix} ${settingsStore.settings.authorizationKey}`
            break
        }
      }
      
      // Add CSRF token if configured
      if (settingsStore.settings.csrfToken) {
        headers['X-CSRFToken'] = settingsStore.settings.csrfToken
      }
    }
    
    return headers
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const baseUrl = this.getBaseUrl()
    const url = `${baseUrl}${endpoint}`
    const settingsStore = useSettingsStore.getState()
    
    const config: RequestInit = {
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
      timeout: settingsStore.settings.defaultTimeout,
      ...options,
    }

    // Log request if enabled
    if (settingsStore.settings.enableRequestLogging) {
      console.log(`[API Request] ${options.method || 'GET'} ${url}`, {
        headers: config.headers,
        body: options.body,
      })
    }

    let retries = settingsStore.settings.autoRetryEnabled ? settingsStore.settings.maxRetries : 0
    let lastError: Error

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetch(url, config)
        
        // Log response if enabled
        if (settingsStore.settings.enableRequestLogging) {
          console.log(`[API Response] ${response.status} ${response.statusText}`, {
            url,
            attempt: attempt + 1,
            headers: Object.fromEntries(response.headers.entries()),
          })
        }
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status} ${response.statusText}`)
        }

        const data = await response.json()
        return data
      } catch (error) {
        lastError = error instanceof Error ? error : new Error('Unknown error')
        
        if (settingsStore.settings.enableRequestLogging) {
          console.error(`[API Error] Attempt ${attempt + 1}/${retries + 1} failed for ${endpoint}:`, lastError)
        }
        
        // Don't retry on final attempt
        if (attempt === retries) {
          break
        }
        
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000))
      }
    }

    console.error(`API request failed for ${endpoint} after ${retries + 1} attempts:`, lastError)
    throw lastError
  }

  async getServices(): Promise<Service[]> {
    try {
      const response = await this.request<{
        services: Service[]
        total_services: number
        upload_id: string | null
        upload_filename: string | null
        last_updated: string | null
      }>('/api/v1/manoman/services')
      return response.services
    } catch (error) {
      console.warn('Failed to fetch services from API, using fallback data:', error)
      // Return mock data as fallback
      return [
        {
          service_name: 'announcement',
          endpoint_count: 7,
          suggested_description: 'Service for announcement management with CRUD operations',
          tier1_operations: 5,
          tier2_operations: 2,
          confidence_score: 0.9,
          needs_review: false,
          keywords: ['announcement', 'notifications', 'alerts'],
          synonyms: ['notice', 'bulletin'],
        },
        {
          service_name: 'user_profile',
          endpoint_count: 27,
          suggested_description: 'Manages user operations including CRUD and specialized workflows',
          tier1_operations: 5,
          tier2_operations: 22,
          confidence_score: 0.9,
          needs_review: false,
          keywords: ['user', 'profile', 'account'],
          synonyms: ['person', 'account'],
        },
        {
          service_name: 'cmdb',
          endpoint_count: 45,
          suggested_description: 'Configuration Management Database operations',
          tier1_operations: 5,
          tier2_operations: 40,
          confidence_score: 0.85,
          needs_review: true,
          keywords: ['cmdb', 'configuration', 'assets'],
          synonyms: ['assets', 'ci'],
        },
      ]
    }
  }

  // Method to test Infraon API connectivity
  async testInfraonConnectivity(): Promise<any> {
    const settingsStore = useSettingsStore.getState()
    
    if (settingsStore.settings.useProxy) {
      // Use proxy for testing
      return this.makeInfraonRequest(settingsStore.settings.testEndpoint)
    } else {
      // Direct mode - this will likely fail due to CORS but shows the attempt
      const baseUrl = settingsStore.settings.apiRootUrl.replace(/\/$/, '')
      const testPath = settingsStore.settings.testEndpoint
      const url = `${baseUrl}${testPath}`
      
      const headers = this.getHeaders()
      
      const response = await fetch(url, {
        method: 'GET',
        headers,
      })
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      
      return await response.json()
    }
  }

  async getService(serviceName: string): Promise<Service | null> {
    try {
      const response = await this.request<Service>(`/api/v1/manoman/services/${serviceName}`)
      return response
    } catch (error) {
      console.error(`Failed to fetch service ${serviceName}:`, error)
      return null
    }
  }

  async uploadApiSpec(file: File): Promise<{ upload_id: string }> {
    const baseUrl = this.getBaseUrl()
    const headers = this.getHeaders()
    
    // Remove Content-Type for FormData (browser will set it with boundary)
    const uploadHeaders = { ...headers }
    delete uploadHeaders['Content-Type']
    
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${baseUrl}/api/v1/manoman/upload`, {
      method: 'POST',
      headers: uploadHeaders,
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status} ${response.statusText}`)
    }

    return await response.json()
  }

  async getUploadStatus(uploadId: string): Promise<{ status: string; progress?: number; error?: string }> {
    try {
      const response = await this.request<{ status: string; progress?: number; error?: string }>(`/api/v1/manoman/upload/${uploadId}/status`)
      return response
    } catch (error) {
      console.error(`Failed to get upload status for ${uploadId}:`, error)
      throw error
    }
  }
}

export const apiService = new ApiService()
export type { Service, ServiceSummary, ApiResponse }