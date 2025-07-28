import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
  ClockIcon
} from '@heroicons/react/24/outline'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { ContextualSuggestions } from './ContextualSuggestions'
import { ChatHistory } from './ChatHistory'
import { chatService } from '../../services/chat'
import { Message, ChatSession, ServiceContext, AgentResponse } from '../../types/chat'

interface ChatInterfaceProps {
  serviceContext?: ServiceContext
  onClose?: () => void
  isOpen?: boolean
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  serviceContext, 
  onClose,
  isOpen = true 
}) => {
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [strategy, setStrategy] = useState<'direct' | 'react'>('direct')
  const [showSettings, setShowSettings] = useState(false)
  const [showHistory, setShowHistory] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Initialize session
  useEffect(() => {
    if (isOpen && !currentSession) {
      const title = serviceContext 
        ? `Chat about ${serviceContext.service_name || 'Service'}`
        : 'New Conversation'
      const session = chatService.createSession(title, serviceContext)
      setCurrentSession(session)
      setMessages([])
      
      // Add welcome message
      const welcomeMessage: Message = {
        id: 'welcome',
        role: 'assistant',
        content: serviceContext
          ? `Hi! I'm your AI assistant. I can help you understand the ${serviceContext.service_name} service, explain its APIs, or answer any questions you have about the platform.`
          : `Hi! I'm your AI assistant for the Infraon platform. I can help you understand services, explain APIs, guide you through workflows, or answer any questions you have.`,
        timestamp: new Date()
      }
      setMessages([welcomeMessage])
    }
  }, [isOpen, serviceContext])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (content: string) => {
    if (!currentSession) return

    // Create user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
      context: serviceContext
    }

    // Add user message to state
    setMessages(prev => [...prev, userMessage])
    chatService.addMessage(currentSession.id, userMessage)
    setIsLoading(true)

    try {
      // Send to agent
      const response: AgentResponse = await chatService.sendMessage(
        content,
        currentSession.id,
        serviceContext,
        strategy
      )

      // Create assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        reasoning: response.reasoning_chain,
        sources: response.sources,
        context: serviceContext
      }

      // Add assistant message to state
      setMessages(prev => [...prev, assistantMessage])
      chatService.addMessage(currentSession.id, assistantMessage)

      // Update session title if it's the first exchange
      if (messages.length <= 1) {
        const shortTitle = content.length > 30 ? content.substring(0, 30) + '...' : content
        chatService.updateSessionTitle(currentSession.id, shortTitle)
      }

    } catch (error) {
      console.error('Failed to send message:', error)
      
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearMemory = async () => {
    try {
      await chatService.clearMemory()
      // Optionally show a success message
    } catch (error) {
      console.error('Failed to clear memory:', error)
    }
  }

  const handleNewConversation = () => {
    const title = serviceContext 
      ? `Chat about ${serviceContext.service_name || 'Service'}`
      : 'New Conversation'
    const session = chatService.createSession(title, serviceContext)
    setCurrentSession(session)
    setMessages([])
    
    // Add welcome message
    const welcomeMessage: Message = {
      id: 'welcome-' + Date.now(),
      role: 'assistant',
      content: 'Hi! How can I help you today?',
      timestamp: new Date()
    }
    setMessages([welcomeMessage])
  }

  const handleSessionSelect = (session: ChatSession) => {
    setCurrentSession(session)
    setMessages(session.messages)
    setShowHistory(false)
  }

  if (!isOpen) return null

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
    >
      <div className="w-full max-w-4xl h-full max-h-[90vh] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg">
              <ChatBubbleLeftRightIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                AI Assistant
              </h2>
              {serviceContext && (
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Context: {serviceContext.service_name}
                </p>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* History Button */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              title="Chat History"
            >
              <ClockIcon className="h-5 w-5" />
            </button>
            
            {/* Settings Button */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            >
              <Cog6ToothIcon className="h-5 w-5" />
            </button>
            
            {/* New Conversation Button */}
            <button
              onClick={handleNewConversation}
              className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              title="New Conversation"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>
            
            {/* Close Button */}
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>

        {/* Settings Panel */}
        <AnimatePresence>
          {showSettings && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 px-4 py-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Strategy:
                  </label>
                  <select
                    value={strategy}
                    onChange={(e) => setStrategy(e.target.value as 'direct' | 'react')}
                    className="text-sm border border-gray-300 dark:border-gray-600 rounded-md px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  >
                    <option value="direct">Direct</option>
                    <option value="react">ReAct (Reasoning)</option>
                  </select>
                </div>
                
                <button
                  onClick={handleClearMemory}
                  className="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 transition-colors"
                >
                  Clear Memory
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          {isLoading && (
            <ChatMessage
              message={{
                id: 'loading',
                role: 'assistant',
                content: '',
                timestamp: new Date()
              }}
              isLoading={true}
            />
          )}
          
          {/* Show suggestions when no messages or after welcome message */}
          {messages.length <= 1 && !isLoading && (
            <div className="mt-6">
              <ContextualSuggestions
                serviceContext={serviceContext}
                onSuggestionClick={handleSendMessage}
                disabled={isLoading}
              />
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <ChatInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          serviceContext={serviceContext}
          placeholder={
            serviceContext
              ? `Ask about ${serviceContext.service_name} service...`
              : "Ask about services, APIs, or anything else..."
          }
        />
      </div>

      {/* Chat History Sidebar */}
      <AnimatePresence>
        {showHistory && (
          <ChatHistory
            isOpen={showHistory}
            onClose={() => setShowHistory(false)}
            onSessionSelect={handleSessionSelect}
            currentSessionId={currentSession?.id}
          />
        )}
      </AnimatePresence>
    </motion.div>
  )
}