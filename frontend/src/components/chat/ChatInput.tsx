import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  PaperAirplaneIcon,
  MicrophoneIcon,
  StopIcon
} from '@heroicons/react/24/outline'

import { ServiceContext } from '../../types/chat'

interface ChatInputProps {
  onSendMessage: (message: string) => void
  isLoading?: boolean
  placeholder?: string
  disabled?: boolean
  serviceContext?: ServiceContext
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  isLoading = false, 
  placeholder = "Ask about services, APIs, or anything else...",
  disabled = false,
  serviceContext
}) => {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message.trim())
      setMessage('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])

  const toggleRecording = () => {
    if (isRecording) {
      // Stop recording
      setIsRecording(false)
      // In a real implementation, you'd stop the recording and process the audio
    } else {
      // Start recording
      setIsRecording(true)
      // In a real implementation, you'd start recording audio
    }
  }

  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="relative flex items-end space-x-3">
          {/* Voice Recording Button */}
          <button
            type="button"
            onClick={toggleRecording}
            disabled={disabled}
            className={`
              flex-shrink-0 p-3 rounded-full transition-all duration-200
              ${isRecording 
                ? 'bg-red-500 text-white animate-pulse' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }
              ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
            `}
          >
            {isRecording ? (
              <StopIcon className="h-5 w-5" />
            ) : (
              <MicrophoneIcon className="h-5 w-5" />
            )}
          </button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={disabled || isLoading}
              rows={1}
              className={`
                w-full resize-none rounded-2xl border border-gray-300 dark:border-gray-600 
                bg-white dark:bg-gray-700 px-4 py-3 pr-12 
                text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400
                focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-opacity-20
                max-h-32 overflow-y-auto
                ${disabled || isLoading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              style={{ minHeight: '48px' }}
            />
            
            {/* Character Counter */}
            {message.length > 500 && (
              <div className="absolute -top-6 right-0 text-xs text-gray-500">
                {message.length}/1000
              </div>
            )}
          </div>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!message.trim() || isLoading || disabled}
            className={`
              flex-shrink-0 p-3 rounded-full transition-all duration-200
              ${message.trim() && !isLoading && !disabled
                ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl transform hover:scale-105' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            {isLoading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="h-5 w-5 border-2 border-current border-t-transparent rounded-full"
              />
            ) : (
              <PaperAirplaneIcon className="h-5 w-5" />
            )}
          </button>
        </div>
        
        {/* Quick Suggestions */}
        {!message && (
          <div className="mt-3 flex flex-wrap gap-2">
            {(serviceContext?.service_name ? [
              `How do I use ${serviceContext.service_name}?`,
              `Show ${serviceContext.service_name} endpoints`,
              `What are common errors?`,
              "Get API documentation"
            ] : [
              "How do I create an incident ticket?",
              "What's the user management API?",
              "Show me CMDB services",
              "Explain authentication flow"
            ]).map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => setMessage(suggestion)}
                disabled={disabled || isLoading}
                className="text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
      </form>
    </div>
  )
}