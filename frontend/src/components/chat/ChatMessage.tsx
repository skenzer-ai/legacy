import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  ChevronDownIcon, 
  ChevronUpIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  CogIcon
} from '@heroicons/react/24/outline'
import { Message, ReasoningStep, Source } from '../../types/chat'

interface ChatMessageProps {
  message: Message
  isLoading?: boolean
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isLoading = false }) => {
  const [showReasoning, setShowReasoning] = useState(false)
  const [showSources, setShowSources] = useState(false)
  
  const isUser = message.role === 'user'

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'document':
        return <DocumentTextIcon className="h-4 w-4" />
      case 'api':
        return <CodeBracketIcon className="h-4 w-4" />
      case 'service':
        return <CogIcon className="h-4 w-4" />
      default:
        return <DocumentTextIcon className="h-4 w-4" />
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`max-w-3xl ${isUser ? 'order-2' : 'order-1'}`}>
        {/* Avatar */}
        <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
          <div className={`
            flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
            ${isUser 
              ? 'bg-blue-600 text-white' 
              : 'bg-gradient-to-br from-purple-500 to-blue-600 text-white'
            }
          `}>
            {isUser ? 'U' : 'AI'}
          </div>
          
          <div className={`flex-1 ${isUser ? 'text-right' : 'text-left'}`}>
            {/* Message Content */}
            <div className={`
              inline-block p-4 rounded-2xl max-w-full
              ${isUser 
                ? 'bg-blue-600 text-white rounded-br-sm' 
                : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700 rounded-bl-sm'
              }
            `}>
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-sm text-gray-500">Thinking...</span>
                </div>
              ) : (
                <div className="prose prose-sm max-w-none">
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              )}
            </div>
            
            {/* Timestamp */}
            <div className={`text-xs text-gray-500 mt-1 ${isUser ? 'text-right' : 'text-left'}`}>
              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
            
            {/* Reasoning Chain (Assistant only) */}
            {!isUser && message.reasoning && message.reasoning.length > 0 && (
              <div className="mt-3">
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="flex items-center space-x-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                >
                  {showReasoning ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
                  <span>View reasoning ({message.reasoning.length} steps)</span>
                </button>
                
                {showReasoning && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                  >
                    <div className="space-y-2">
                      {message.reasoning.map((step: ReasoningStep, index: number) => (
                        <div key={index} className="text-sm">
                          <div className="font-medium text-gray-700 dark:text-gray-300">
                            Step {step.step}: {step.thought}
                          </div>
                          <div className="text-gray-600 dark:text-gray-400">
                            Action: {step.action}
                          </div>
                          {step.observation && (
                            <div className="text-gray-500 dark:text-gray-500 text-xs">
                              Observation: {step.observation}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            )}
            
            {/* Sources (Assistant only) */}
            {!isUser && message.sources && message.sources.length > 0 && (
              <div className="mt-3">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="flex items-center space-x-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
                >
                  {showSources ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />}
                  <span>Sources ({message.sources.length})</span>
                </button>
                
                {showSources && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mt-2 space-y-2"
                  >
                    {message.sources.map((source: Source, index: number) => (
                      <div
                        key={index}
                        className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700"
                      >
                        <div className="flex items-center space-x-2 mb-2">
                          {getSourceIcon(source.type)}
                          <span className="font-medium text-sm text-gray-700 dark:text-gray-300">
                            {source.title}
                          </span>
                          {source.confidence && (
                            <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded">
                              {Math.round(source.confidence * 100)}%
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">
                          {source.content}
                        </p>
                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 dark:text-blue-400 hover:underline mt-1 inline-block"
                          >
                            View source →
                          </a>
                        )}
                      </div>
                    ))}
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}