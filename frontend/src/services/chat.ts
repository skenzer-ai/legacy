import { AgentRequest, AgentResponse, Message, ChatSession, ServiceContext } from '../types/chat'
import { apiService } from './api'

class ChatService {
  private baseUrl: string
  private sessions: Map<string, ChatSession> = new Map()

  constructor() {
    // Use the same base URL logic as apiService
    if (import.meta.env.VITE_API_BASE_URL) {
      this.baseUrl = import.meta.env.VITE_API_BASE_URL
    } else {
      const currentHost = window.location.host
      if (currentHost.includes('ssh.skenzer.com')) {
        this.baseUrl = `${window.location.protocol}//ssh.skenzer.com:8000`
      } else {
        this.baseUrl = 'http://localhost:8000'
      }
    }
    
    // Load sessions from localStorage
    this.loadSessions()
  }

  async sendMessage(
    message: string, 
    sessionId: string,
    serviceContext?: ServiceContext,
    strategy: 'direct' | 'react' = 'direct'
  ): Promise<AgentResponse> {
    const session = this.sessions.get(sessionId)
    const conversationHistory = session?.messages.slice(-5) || [] // Last 5 messages for context

    const request: AgentRequest = {
      query: message,
      context: {
        user_role: 'admin',
        service_context: serviceContext,
        conversation_history: conversationHistory
      },
      strategy,
      max_reasoning_loops: 3
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/agents/augment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Chat service error:', error)
      throw error
    }
  }

  createSession(title?: string, serviceContext?: ServiceContext): ChatSession {
    const session: ChatSession = {
      id: this.generateId(),
      title: title || 'New Conversation',
      messages: [],
      created_at: new Date(),
      updated_at: new Date(),
      service_context: serviceContext
    }
    
    this.sessions.set(session.id, session)
    this.saveSessions()
    return session
  }

  getSession(sessionId: string): ChatSession | undefined {
    return this.sessions.get(sessionId)
  }

  addMessage(sessionId: string, message: Message): void {
    const session = this.sessions.get(sessionId)
    if (session) {
      session.messages.push(message)
      session.updated_at = new Date()
      this.saveSessions()
    }
  }

  updateSessionTitle(sessionId: string, title: string): void {
    const session = this.sessions.get(sessionId)
    if (session) {
      session.title = title
      session.updated_at = new Date()
      this.saveSessions()
    }
  }

  deleteSession(sessionId: string): void {
    this.sessions.delete(sessionId)
    this.saveSessions()
  }

  getAllSessions(): ChatSession[] {
    return Array.from(this.sessions.values())
      .sort((a, b) => b.updated_at.getTime() - a.updated_at.getTime())
  }

  clearMemory(): Promise<void> {
    return fetch(`${this.baseUrl}/api/v1/agents/augment/memory/clear`, {
      method: 'POST',
    }).then(() => {})
  }

  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }

  private saveSessions(): void {
    try {
      const sessionsData = Array.from(this.sessions.entries()).map(([id, session]) => [
        id,
        {
          ...session,
          created_at: session.created_at.toISOString(),
          updated_at: session.updated_at.toISOString(),
          messages: session.messages.map(msg => ({
            ...msg,
            timestamp: msg.timestamp.toISOString()
          }))
        }
      ])
      localStorage.setItem('chat_sessions', JSON.stringify(sessionsData))
    } catch (error) {
      console.warn('Failed to save chat sessions:', error)
    }
  }

  private loadSessions(): void {
    try {
      const stored = localStorage.getItem('chat_sessions')
      if (stored) {
        const sessionsData = JSON.parse(stored)
        sessionsData.forEach(([id, sessionData]: [string, any]) => {
          const session: ChatSession = {
            ...sessionData,
            created_at: new Date(sessionData.created_at),
            updated_at: new Date(sessionData.updated_at),
            messages: sessionData.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp)
            }))
          }
          this.sessions.set(id, session)
        })
      }
    } catch (error) {
      console.warn('Failed to load chat sessions:', error)
    }
  }
}

export const chatService = new ChatService()