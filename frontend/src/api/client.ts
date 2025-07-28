const API_BASE_URL = '/api/v1/manoman'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public response?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  const config: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      )
    }

    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }
    
    return response.text() as unknown as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    
    // Network or other errors
    throw new ApiError(
      error instanceof Error ? error.message : 'Network error',
      0
    )
  }
}

export const api = {
  // Upload endpoints
  uploadFile: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return fetchApi('/upload', {
      method: 'POST',
      headers: {}, // Let browser set content-type for FormData
      body: formData,
    })
  },

  // Classification endpoints
  getClassificationServices: (uploadId: string) =>
    fetchApi(`/classification/${uploadId}/services`),

  getUploadStatus: (uploadId: string) =>
    fetchApi(`/upload/${uploadId}/status`),

  // Service endpoints
  getServiceDetail: (uploadId: string, serviceName: string) =>
    fetchApi(`/definition/service/${uploadId}/${serviceName}`),

  // Validation endpoints
  startValidation: (data: any) =>
    fetchApi('/start-procedural-testing', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getValidationProgress: (sessionId: string) =>
    fetchApi(`/testing-progress/${sessionId}`),

  getValidationResults: (sessionId: string) =>
    fetchApi(`/testing-results/${sessionId}`),

  // Utility endpoints
  getHealth: () => fetchApi('/health'),
}

export default api