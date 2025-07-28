import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CommandLineIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  PlayIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClipboardDocumentIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { ServiceSummary } from '../../types/service'
import { ApiTestingPanel } from './ApiTestingPanel'

interface ServiceOperationsProps {
  service: ServiceSummary
}

interface OperationGroup {
  title: string
  description: string
  count: number
  color: string
  operations: MockOperation[]
}

interface MockOperation {
  id: string
  method: string
  path: string
  summary: string
  description?: string
  tags: string[]
  tier: 1 | 2
}

// Mock operation data - in real implementation, this would come from API
const generateMockOperations = (service: ServiceSummary): MockOperation[] => {
  const operations: MockOperation[] = []
  const serviceName = service.service_name
  
  // Generate Tier 1 operations (CRUD)
  const tier1Ops = [
    { method: 'GET', path: `/${serviceName}`, summary: `List all ${serviceName} records`, tier: 1 as const },
    { method: 'GET', path: `/${serviceName}/{id}`, summary: `Get ${serviceName} by ID`, tier: 1 as const },
    { method: 'POST', path: `/${serviceName}`, summary: `Create new ${serviceName}`, tier: 1 as const },
    { method: 'PUT', path: `/${serviceName}/{id}`, summary: `Update ${serviceName}`, tier: 1 as const },
    { method: 'DELETE', path: `/${serviceName}/{id}`, summary: `Delete ${serviceName}`, tier: 1 as const },
  ]
  
  tier1Ops.slice(0, service.tier1_operations).forEach((op, index) => {
    operations.push({
      id: `tier1-${index}`,
      ...op,
      description: `${op.summary} with full validation and error handling`,
      tags: ['CRUD', serviceName]
    })
  })
  
  // Generate Tier 2 operations (specialized)
  const tier2Examples = [
    { method: 'POST', path: `/${serviceName}/bulk`, summary: `Bulk create ${serviceName} records` },
    { method: 'GET', path: `/${serviceName}/search`, summary: `Advanced search ${serviceName}` },
    { method: 'POST', path: `/${serviceName}/export`, summary: `Export ${serviceName} data` },
    { method: 'POST', path: `/${serviceName}/import`, summary: `Import ${serviceName} data` },
    { method: 'GET', path: `/${serviceName}/stats`, summary: `Get ${serviceName} statistics` },
    { method: 'POST', path: `/${serviceName}/{id}/clone`, summary: `Clone ${serviceName}` },
    { method: 'PATCH', path: `/${serviceName}/{id}/status`, summary: `Update ${serviceName} status` },
    { method: 'GET', path: `/${serviceName}/{id}/history`, summary: `Get ${serviceName} history` },
  ]
  
  tier2Examples.slice(0, service.tier2_operations).forEach((op, index) => {
    operations.push({
      id: `tier2-${index}`,
      ...op,
      tier: 2 as const,
      description: `${op.summary} with advanced features and analytics`,
      tags: ['Advanced', serviceName]
    })
  })
  
  return operations
}

export const ServiceOperations: React.FC<ServiceOperationsProps> = ({ service }) => {
  const [expandedGroup, setExpandedGroup] = useState<string | null>('Core CRUD Operations')
  const [selectedOperation, setSelectedOperation] = useState<MockOperation | null>(null)
  const [isTestingMode, setIsTestingMode] = useState(false)
  
  const operations = generateMockOperations(service)
  
  const operationGroups: OperationGroup[] = [
    {
      title: 'Core CRUD Operations',
      description: 'Essential create, read, update, and delete operations',
      count: service.tier1_operations,
      color: 'green',
      operations: operations.filter(op => op.tier === 1)
    },
    {
      title: 'Advanced Operations',
      description: 'Specialized functionality and business logic',
      count: service.tier2_operations,
      color: 'purple',
      operations: operations.filter(op => op.tier === 2)
    }
  ]

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400'
      case 'POST': return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400'
      case 'PUT': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'PATCH': return 'text-orange-600 bg-orange-100 dark:bg-orange-900/30 dark:text-orange-400'
      case 'DELETE': return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30 dark:text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">API Operations</h2>
        <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
          <CommandLineIcon className="h-4 w-4" />
          <span>{operations.length} total endpoints</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Operations List */}
        <div className="lg:col-span-2 space-y-4">
          {operationGroups.map((group) => (
            <div key={group.title} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              <button
                onClick={() => setExpandedGroup(expandedGroup === group.title ? null : group.title)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  {expandedGroup === group.title ? (
                    <ChevronDownIcon className="h-5 w-5 text-gray-500" />
                  ) : (
                    <ChevronRightIcon className="h-5 w-5 text-gray-500" />
                  )}
                  <div className="text-left">
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {group.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {group.description}
                    </p>
                  </div>
                </div>
                <div className={`
                  px-3 py-1 rounded-full text-sm font-medium
                  ${group.color === 'green' 
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                    : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                  }
                `}>
                  {group.count} ops
                </div>
              </button>

              <AnimatePresence>
                {expandedGroup === group.title && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3 }}
                    className="border-t border-gray-200 dark:border-gray-700"
                  >
                    <div className="p-4 space-y-2">
                      {group.operations.map((operation) => (
                        <motion.button
                          key={operation.id}
                          onClick={() => setSelectedOperation(operation)}
                          className={`
                            w-full p-4 rounded-lg border transition-all duration-200 text-left
                            ${selectedOperation?.id === operation.id
                              ? 'border-blue-300 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-600'
                              : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700'
                            }
                          `}
                          whileHover={{ scale: 1.01 }}
                          whileTap={{ scale: 0.99 }}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                              <span className={`px-2 py-1 rounded text-xs font-mono font-bold ${getMethodColor(operation.method)}`}>
                                {operation.method}
                              </span>
                              <code className="text-sm font-mono text-gray-900 dark:text-gray-100">
                                {operation.path}
                              </code>
                            </div>
                            <PlayIcon className="h-4 w-4 text-gray-400" />
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 ml-2">
                            {operation.summary}
                          </p>
                          <div className="flex items-center space-x-2 mt-2 ml-2">
                            {operation.tags.map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs"
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </motion.button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>

        {/* Operation Details / Testing Panel */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden sticky top-6">
            {selectedOperation ? (
              <>
                {/* Header */}
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <span className={`px-3 py-1 rounded font-mono font-bold ${getMethodColor(selectedOperation.method)}`}>
                        {selectedOperation.method}
                      </span>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {isTestingMode ? 'API Testing' : 'Operation Details'}
                      </h3>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setIsTestingMode(!isTestingMode)}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                          isTestingMode
                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                            : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                        }`}
                      >
                        {isTestingMode ? (
                          <>
                            <DocumentTextIcon className="h-4 w-4 inline mr-1" />
                            Details
                          </>
                        ) : (
                          <>
                            <PlayIcon className="h-4 w-4 inline mr-1" />
                            Test
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white mb-2">Endpoint</h4>
                    <div className="flex items-center space-x-2">
                      <code className="flex-1 p-3 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm font-mono text-gray-900 dark:text-gray-100">
                        {selectedOperation.path}
                      </code>
                      <button 
                        onClick={() => navigator.clipboard.writeText(selectedOperation.path)}
                        className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                        title="Copy endpoint"
                      >
                        <ClipboardDocumentIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6">
                  {isTestingMode ? (
                    <ApiTestingPanel operation={selectedOperation} serviceName={service.service_name} />
                  ) : (
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Summary</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {selectedOperation.summary}
                        </p>
                      </div>

                      {selectedOperation.description && (
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-white mb-2">Description</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {selectedOperation.description}
                          </p>
                        </div>
                      )}

                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white mb-2">Tags</h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedOperation.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                        <button 
                          onClick={() => setIsTestingMode(true)}
                          className="w-full flex items-center justify-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          <PlayIcon className="h-4 w-4" />
                          <span>Test Operation</span>
                        </button>
                        <button className="w-full flex items-center justify-center space-x-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                          <SparklesIcon className="h-4 w-4" />
                          <span>Ask AI Assistant</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-12 p-6">
                <CodeBracketIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  Select an Operation
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Click on any operation to view details and test it
                </p>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <div className="flex items-center space-x-2 text-blue-700 dark:text-blue-300">
                    <SparklesIcon className="h-5 w-5" />
                    <span className="font-medium">AI-Powered Testing</span>
                  </div>
                  <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                    Get intelligent test data generation and guidance
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}