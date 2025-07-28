import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClipboardDocumentIcon,
  SparklesIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CodeBracketIcon,
} from '@heroicons/react/24/outline'

interface MockOperation {
  id: string
  method: string
  path: string
  summary: string
  description?: string
  tags: string[]
  tier: 1 | 2
}

interface ApiTestingPanelProps {
  operation: MockOperation
  serviceName: string
}

interface TestResult {
  status: 'success' | 'error' | 'loading'
  statusCode?: number
  response?: any
  error?: string
  duration?: number
}

// Mock parameter generation based on operation type
const generateMockParameters = (operation: MockOperation) => {
  const baseUrl = 'https://api.infraon.io/v1'
  const isCreate = operation.method === 'POST' && !operation.path.includes('{id}')
  const isUpdate = operation.method === 'PUT' || operation.method === 'PATCH'
  const isDelete = operation.method === 'DELETE'
  const isGetById = operation.method === 'GET' && operation.path.includes('{id}')

  const params: any = {}

  // Path parameters
  if (operation.path.includes('{id}')) {
    params.id = '12345'
  }

  // Query parameters for GET requests
  if (operation.method === 'GET' && !operation.path.includes('{id}')) {
    params.limit = 10
    params.offset = 0
    if (operation.path.includes('search')) {
      params.q = 'test query'
    }
  }

  // Request body for POST/PUT/PATCH
  if (isCreate || isUpdate) {
    params.body = {
      name: `Test ${operation.id}`,
      description: `Generated test data for ${operation.summary.toLowerCase()}`,
      status: 'active',
      created_by: 'test_user',
      tags: ['test', 'automation']
    }
  }

  return {
    url: `${baseUrl}${operation.path.replace('{id}', params.id || '')}`,
    method: operation.method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer <your-api-token>',
      'X-API-Version': '1.0'
    },
    queryParams: operation.method === 'GET' ? {
      limit: params.limit,
      offset: params.offset,
      ...(params.q && { q: params.q })
    } : {},
    body: params.body ? JSON.stringify(params.body, null, 2) : ''
  }
}

// Mock API response generator
const generateMockResponse = (operation: MockOperation): TestResult => {
  const isCreate = operation.method === 'POST' && !operation.path.includes('{id}')
  const isGetList = operation.method === 'GET' && !operation.path.includes('{id}')
  const isGetById = operation.method === 'GET' && operation.path.includes('{id}')
  const isUpdate = operation.method === 'PUT' || operation.method === 'PATCH'
  const isDelete = operation.method === 'DELETE'

  if (isCreate) {
    return {
      status: 'success',
      statusCode: 201,
      duration: Math.floor(Math.random() * 500) + 100,
      response: {
        id: '12345',
        name: `Test ${operation.id}`,
        description: `Generated test data for ${operation.summary.toLowerCase()}`,
        status: 'active',
        created_at: new Date().toISOString(),
        created_by: 'test_user'
      }
    }
  }

  if (isGetList) {
    return {
      status: 'success',
      statusCode: 200,
      duration: Math.floor(Math.random() * 300) + 50,
      response: {
        data: Array.from({ length: 3 }, (_, i) => ({
          id: `${12345 + i}`,
          name: `${operation.id} Item ${i + 1}`,
          description: `Sample ${operation.id} record`,
          status: i === 0 ? 'active' : 'inactive',
          created_at: new Date(Date.now() - i * 86400000).toISOString()
        })),
        total: 25,
        limit: 10,
        offset: 0
      }
    }
  }

  if (isGetById) {
    return {
      status: 'success',
      statusCode: 200,
      duration: Math.floor(Math.random() * 200) + 30,
      response: {
        id: '12345',
        name: `Test ${operation.id}`,
        description: `Sample ${operation.id} record`,
        status: 'active',
        created_at: '2024-01-15T10:30:00Z',
        updated_at: new Date().toISOString(),
        metadata: {
          version: 1,
          tags: ['test', 'sample']
        }
      }
    }
  }

  if (isUpdate) {
    return {
      status: 'success',
      statusCode: 200,
      duration: Math.floor(Math.random() * 400) + 80,
      response: {
        id: '12345',
        name: `Updated Test ${operation.id}`,
        description: `Updated test data for ${operation.summary.toLowerCase()}`,
        status: 'active',
        updated_at: new Date().toISOString(),
        updated_by: 'test_user'
      }
    }
  }

  if (isDelete) {
    return {
      status: 'success',
      statusCode: 204,
      duration: Math.floor(Math.random() * 200) + 50,
      response: null
    }
  }

  return {
    status: 'success',
    statusCode: 200,
    duration: Math.floor(Math.random() * 300) + 100,
    response: { message: 'Operation completed successfully' }
  }
}

export const ApiTestingPanel: React.FC<ApiTestingPanelProps> = ({ operation, serviceName }) => {
  const [testParams, setTestParams] = useState(() => generateMockParameters(operation))
  const [testResult, setTestResult] = useState<TestResult | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)

  const executeTest = async () => {
    setIsExecuting(true)
    setTestResult({ status: 'loading' })

    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000))

    // Simulate occasional errors
    if (Math.random() < 0.15) {
      setTestResult({
        status: 'error',
        statusCode: Math.random() < 0.5 ? 404 : 500,
        error: Math.random() < 0.5 ? 'Resource not found' : 'Internal server error',
        duration: Math.floor(Math.random() * 200) + 100
      })
    } else {
      setTestResult(generateMockResponse(operation))
    }

    setIsExecuting(false)
  }

  const generateTestData = () => {
    setTestParams(generateMockParameters(operation))
    setTestResult(null)
  }

  const copyResponse = () => {
    if (testResult?.response) {
      navigator.clipboard.writeText(JSON.stringify(testResult.response, null, 2))
    }
  }

  return (
    <div className="space-y-6">
      {/* Test Configuration */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="font-medium text-gray-900 dark:text-white">Test Configuration</h4>
          <button
            onClick={generateTestData}
            className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            <SparklesIcon className="h-3 w-3" />
            <span>Generate Test Data</span>
          </button>
        </div>

        <div className="space-y-3">
          {/* URL */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              URL
            </label>
            <input
              type="text"
              value={testParams.url}
              onChange={(e) => setTestParams(prev => ({ ...prev, url: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-mono bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          {/* Headers */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Headers
            </label>
            <textarea
              value={JSON.stringify(testParams.headers, null, 2)}
              onChange={(e) => {
                try {
                  setTestParams(prev => ({ ...prev, headers: JSON.parse(e.target.value) }))
                } catch {}
              }}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-xs font-mono bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          {/* Request Body */}
          {(operation.method === 'POST' || operation.method === 'PUT' || operation.method === 'PATCH') && (
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Request Body
              </label>
              <textarea
                value={testParams.body}
                onChange={(e) => setTestParams(prev => ({ ...prev, body: e.target.value }))}
                rows={6}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-xs font-mono bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
          )}

          {/* Query Parameters */}
          {Object.keys(testParams.queryParams).length > 0 && (
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Query Parameters
              </label>
              <textarea
                value={JSON.stringify(testParams.queryParams, null, 2)}
                onChange={(e) => {
                  try {
                    setTestParams(prev => ({ ...prev, queryParams: JSON.parse(e.target.value) }))
                  } catch {}
                }}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-xs font-mono bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
            </div>
          )}
        </div>
      </div>

      {/* Execute Button */}
      <div>
        <button
          onClick={executeTest}
          disabled={isExecuting}
          className={`w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg font-medium transition-colors ${
            isExecuting
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
        >
          {isExecuting ? (
            <>
              <StopIcon className="h-4 w-4 animate-spin" />
              <span>Executing...</span>
            </>
          ) : (
            <>
              <PlayIcon className="h-4 w-4" />
              <span>Execute Test</span>
            </>
          )}
        </button>
      </div>

      {/* Test Results */}
      <AnimatePresence>
        {testResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900 dark:text-white">Test Results</h4>
              {testResult.response && (
                <button
                  onClick={copyResponse}
                  className="flex items-center space-x-1 text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                >
                  <ClipboardDocumentIcon className="h-3 w-3" />
                  <span>Copy</span>
                </button>
              )}
            </div>

            {/* Status */}
            <div className="flex items-center space-x-3">
              <div className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-sm font-medium ${
                testResult.status === 'success'
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                  : testResult.status === 'error'
                  ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
              }`}>
                {testResult.status === 'success' && <CheckCircleIcon className="h-4 w-4" />}
                {testResult.status === 'error' && <XCircleIcon className="h-4 w-4" />}
                {testResult.status === 'loading' && <div className="h-4 w-4 border-2 border-current border-t-transparent rounded-full animate-spin" />}
                <span>
                  {testResult.status === 'loading' ? 'Loading...' : `${testResult.statusCode} ${testResult.status}`}
                </span>
              </div>
              {testResult.duration && (
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {testResult.duration}ms
                </span>
              )}
            </div>

            {/* Response */}
            {testResult.response && (
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Response Body
                </label>
                <pre className="w-full p-3 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs font-mono text-gray-900 dark:text-gray-100 overflow-x-auto">
                  {JSON.stringify(testResult.response, null, 2)}
                </pre>
              </div>
            )}

            {/* Error */}
            {testResult.error && (
              <div className="flex items-start space-x-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-red-700 dark:text-red-300">Error</p>
                  <p className="text-sm text-red-600 dark:text-red-400">{testResult.error}</p>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Assistant Suggestion */}
      <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
        <div className="flex items-center space-x-2 mb-2">
          <SparklesIcon className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          <span className="text-sm font-medium text-purple-700 dark:text-purple-300">AI Testing Assistant</span>
        </div>
        <p className="text-xs text-purple-600 dark:text-purple-400 mb-3">
          Need help with this API? I can generate realistic test data, explain error responses, or suggest test scenarios.
        </p>
        <button className="flex items-center space-x-1 text-xs text-purple-600 hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300 font-medium">
          <span>Ask AI for Testing Help</span>
          <CodeBracketIcon className="h-3 w-3" />
        </button>
      </div>
    </div>
  )
}