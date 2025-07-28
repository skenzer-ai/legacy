export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  reasoning?: ReasoningStep[]
  sources?: Source[]
  context?: ServiceContext
}

export interface ReasoningStep {
  step: number
  thought: string
  action: string
  observation?: string
}

export interface Source {
  type: 'document' | 'api' | 'service'
  title: string
  content: string
  url?: string
  confidence?: number
}

export interface ServiceContext {
  service_name?: string
  endpoint?: string
  operation?: string
}

export interface ChatSession {
  id: string
  title: string
  messages: Message[]
  created_at: Date
  updated_at: Date
  service_context?: ServiceContext
}

export interface AgentResponse {
  response: string
  reasoning_chain?: ReasoningStep[]
  sources?: Source[]
  confidence?: number
  session_id?: string
}

export interface AgentRequest {
  query: string
  context?: {
    user_role?: string
    department?: string
    service_context?: ServiceContext
    conversation_history?: Message[]
  }
  strategy?: 'direct' | 'react'
  max_reasoning_loops?: number
}