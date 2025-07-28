import React from 'react'
import { motion } from 'framer-motion'
import { 
  LightBulbIcon,
  CommandLineIcon,
  DocumentTextIcon,
  CogIcon
} from '@heroicons/react/24/outline'
import { ServiceContext } from '../../types/chat'

interface ContextualSuggestionsProps {
  serviceContext?: ServiceContext
  onSuggestionClick: (suggestion: string) => void
  disabled?: boolean
}

export const ContextualSuggestions: React.FC<ContextualSuggestionsProps> = ({
  serviceContext,
  onSuggestionClick,
  disabled = false
}) => {
  const getServiceSuggestions = (serviceName: string) => {
    const suggestions = [
      {
        text: `What does the ${serviceName} service do?`,
        icon: DocumentTextIcon,
        category: 'General'
      },
      {
        text: `How do I create a new ${serviceName} record?`,
        icon: CommandLineIcon,
        category: 'API Usage'
      },
      {
        text: `What are the main operations for ${serviceName}?`,
        icon: CogIcon,
        category: 'Operations'
      },
      {
        text: `Show me the ${serviceName} API documentation`,
        icon: DocumentTextIcon,
        category: 'Documentation'
      },
      {
        text: `What parameters does ${serviceName} need?`,
        icon: CommandLineIcon,
        category: 'API Usage'
      },
      {
        text: `How do I troubleshoot ${serviceName} errors?`,
        icon: LightBulbIcon,
        category: 'Troubleshooting'
      }
    ]
    return suggestions.slice(0, 4) // Show 4 most relevant
  }

  const getGeneralSuggestions = () => [
    {
      text: "What's the most commonly used service?",
      icon: DocumentTextIcon,
      category: 'Discovery'
    },
    {
      text: "How do I create an incident ticket?",
      icon: CommandLineIcon,
      category: 'Common Tasks'
    },
    {
      text: "Show me user management APIs",
      icon: CogIcon,
      category: 'User Management'
    },
    {
      text: "What's the authentication process?",
      icon: LightBulbIcon,
      category: 'Security'
    }
  ]

  const suggestions = serviceContext?.service_name 
    ? getServiceSuggestions(serviceContext.service_name)
    : getGeneralSuggestions()

  if (disabled) return null

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
        <LightBulbIcon className="h-4 w-4" />
        <span>Suggestions</span>
        {serviceContext?.service_name && (
          <span className="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded text-xs">
            {serviceContext.service_name}
          </span>
        )}
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {suggestions.map((suggestion, index) => (
          <motion.button
            key={suggestion.text}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => onSuggestionClick(suggestion.text)}
            className="flex items-start space-x-3 p-3 text-left rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all duration-200 group"
          >
            <div className="flex-shrink-0 mt-0.5">
              <suggestion.icon className="h-4 w-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 group-hover:text-blue-900 dark:group-hover:text-blue-100 transition-colors">
                {suggestion.text}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {suggestion.category}
              </p>
            </div>
          </motion.button>
        ))}
      </div>
    </div>
  )
}