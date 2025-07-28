import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeftIcon,
  CommandLineIcon,
  SparklesIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  DocumentTextIcon,
  CpuChipIcon,
  BeakerIcon,
  ClipboardDocumentIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import { useService } from '../../hooks/useServices'
import { ApiTestingPanel } from '../service/ApiTestingPanel'

interface ApiTestingWorkspaceProps {
  serviceName: string
  onBack: () => void
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

// Generate mock operations for testing
const generateMockOperations = (serviceName: string): MockOperation[] => {
  const operations: MockOperation[] = []
  
  // Tier 1 operations (CRUD)
  const tier1Ops = [
    { method: 'GET', path: `/${serviceName}`, summary: `List all ${serviceName} records`, tier: 1 as const },
    { method: 'GET', path: `/${serviceName}/{id}`, summary: `Get ${serviceName} by ID`, tier: 1 as const },
    { method: 'POST', path: `/${serviceName}`, summary: `Create new ${serviceName}`, tier: 1 as const },
    { method: 'PUT', path: `/${serviceName}/{id}`, summary: `Update ${serviceName}`, tier: 1 as const },
    { method: 'DELETE', path: `/${serviceName}/{id}`, summary: `Delete ${serviceName}`, tier: 1 as const },
  ]
  
  tier1Ops.forEach((op, index) => {
    operations.push({
      id: `tier1-${index}`,
      ...op,
      description: `${op.summary} with full validation and error handling`,
      tags: ['CRUD', serviceName]
    })
  })
  
  // Tier 2 operations (specialized)
  const tier2Examples = [
    { method: 'POST', path: `/${serviceName}/bulk`, summary: `Bulk create ${serviceName} records` },
    { method: 'GET', path: `/${serviceName}/search`, summary: `Advanced search ${serviceName}` },
    { method: 'POST', path: `/${serviceName}/export`, summary: `Export ${serviceName} data` },
    { method: 'POST', path: `/${serviceName}/import`, summary: `Import ${serviceName} data` },
    { method: 'GET', path: `/${serviceName}/stats`, summary: `Get ${serviceName} statistics` },
  ]
  
  tier2Examples.slice(0, 3).forEach((op, index) => {
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

export const ApiTestingWorkspace: React.FC<ApiTestingWorkspaceProps> = ({ serviceName, onBack }) => {
  const { data: service, isLoading } = useService(serviceName)
  const [selectedOperation, setSelectedOperation] = useState<MockOperation | null>(null)
  const [operations] = useState(() => generateMockOperations(serviceName))
  const [testHistory, setTestHistory] = useState<Array<{
    operation: MockOperation
    timestamp: Date
    result: 'success' | 'error'
  }>>([])

  useEffect(() => {
    // Auto-select first operation
    if (operations.length > 0 && !selectedOperation) {
      setSelectedOperation(operations[0])
    }
  }, [operations, selectedOperation])

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

  const onTestComplete = (result: 'success' | 'error') => {
    if (selectedOperation) {
      setTestHistory(prev => [{
        operation: selectedOperation,
        timestamp: new Date(),
        result
      }, ...prev.slice(0, 9)]) // Keep last 10 tests
    }
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
        <p className="mt-4 text-gray-600 dark:text-gray-400">Loading service details...</p>
      </div>
    )
  }

  if (!service) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Service Not Found
        </h3>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Could not load service "{serviceName}"
        </p>
        <button
          onClick={onBack}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Go Back
        </button>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={onBack}
            className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
              <CommandLineIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              <span>Testing: {service.service_name}</span>
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              {service.suggested_description}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className="text-sm text-gray-500 dark:text-gray-400">Operations</div>
            <div className="font-semibold text-gray-900 dark:text-white">
              {operations.length} endpoints
            </div>
          </div>
        </div>
      </div>

      {/* Service Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <CpuChipIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-700 dark:text-blue-300">Total Endpoints</span>
          </div>
          <div className="text-2xl font-bold text-blue-900 dark:text-blue-100 mt-1">
            {service.endpoint_count}
          </div>
        </div>
        <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <BeakerIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
            <span className="text-sm text-green-700 dark:text-green-300">CRUD Ops</span>
          </div>
          <div className="text-2xl font-bold text-green-900 dark:text-green-100 mt-1">
            {service.tier1_operations}
          </div>
        </div>
        <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <SparklesIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            <span className="text-sm text-purple-700 dark:text-purple-300">Advanced</span>
          </div>
          <div className="text-2xl font-bold text-purple-900 dark:text-purple-100 mt-1">
            {service.tier2_operations}
          </div>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <CheckCircleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            <span className="text-sm text-yellow-700 dark:text-yellow-300">Confidence</span>
          </div>
          <div className="text-2xl font-bold text-yellow-900 dark:text-yellow-100 mt-1">
            {(service.confidence_score * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Main Testing Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Operations List */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">API Operations</h3>
            <div className="space-y-2">
              {operations.map((operation) => (
                <button
                  key={operation.id}
                  onClick={() => setSelectedOperation(operation)}
                  className={`w-full p-3 rounded-lg border text-left transition-all duration-200 ${
                    selectedOperation?.id === operation.id
                      ? 'border-blue-300 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-600'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-mono font-bold ${getMethodColor(operation.method)}`}>
                      {operation.method}
                    </span>
                    {operation.tier === 1 && (
                      <span className="text-xs text-green-600 dark:text-green-400 font-medium">CRUD</span>
                    )}
                  </div>
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
                    {operation.path}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400">
                    {operation.summary}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Test History */}
          {testHistory.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 mt-4">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Recent Tests</h3>
              <div className="space-y-2">
                {testHistory.slice(0, 5).map((test, index) => (
                  <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                    {test.result === 'success' ? (
                      <CheckCircleIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
                    ) : (
                      <XCircleIcon className="h-4 w-4 text-red-500 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-mono text-gray-900 dark:text-gray-100 truncate">
                        {test.operation.method} {test.operation.path}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {test.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Testing Panel */}
        <div className="lg:col-span-3">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            {selectedOperation ? (
              <>
                <div className="border-b border-gray-200 dark:border-gray-700 p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className={`px-3 py-1 rounded font-mono font-bold ${getMethodColor(selectedOperation.method)}`}>
                        {selectedOperation.method}
                      </span>
                      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        {selectedOperation.summary}
                      </h2>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        selectedOperation.tier === 1 
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                          : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300'
                      }`}>
                        Tier {selectedOperation.tier}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 mt-2">
                    {selectedOperation.description}
                  </p>
                </div>
                <div className="p-6">
                  <ApiTestingPanel 
                    operation={selectedOperation} 
                    serviceName={serviceName}
                  />
                </div>
              </>
            ) : (
              <div className="text-center py-12 p-6">
                <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                  Select an Operation
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Choose an API operation from the list to start testing
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}