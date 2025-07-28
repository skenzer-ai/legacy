import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Cog6ToothIcon,
  CloudIcon,
  BeakerIcon,
  SparklesIcon,
  WrenchScrewdriverIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ClockIcon,
  DocumentArrowDownIcon,
  DocumentArrowUpIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import { useSettingsStore, ApplicationSettings, ConnectionStatus, AuthorizationType } from '../stores/settings'

interface SettingsTabProps {
  id: string
  label: string
  icon: any
  description: string
}

const settingsTabs: SettingsTabProps[] = [
  {
    id: 'api',
    label: 'API Configuration',
    icon: CloudIcon,
    description: 'Configure API endpoint and authentication',
  },
  {
    id: 'testing',
    label: 'Testing Options',
    icon: BeakerIcon,
    description: 'Set testing preferences and defaults',
  },
  {
    id: 'ai',
    label: 'AI Features',
    icon: SparklesIcon,
    description: 'Enable and configure AI assistance',
  },
  {
    id: 'advanced',
    label: 'Advanced',
    icon: WrenchScrewdriverIcon,
    description: 'Advanced settings and preferences',
  },
]

function ConnectionStatusIndicator({ status }: { status: ConnectionStatus }) {
  const getStatusColor = () => {
    switch (status.status) {
      case 'connected': return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400'
      case 'connecting': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400'
      case 'error': return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30 dark:text-gray-400'
    }
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'connected': return CheckCircleIcon
      case 'connecting': return ClockIcon
      case 'error': return XCircleIcon
      default: return ExclamationTriangleIcon
    }
  }

  const StatusIcon = getStatusIcon()

  return (
    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}>
      <StatusIcon className="h-3 w-3 mr-1" />
      <span className="capitalize">{status.status}</span>
      {status.responseTime && (
        <span className="ml-1">({status.responseTime}ms)</span>
      )}
    </div>
  )
}

function ApiConfigurationTab() {
  const { settings, connectionStatus, updateSettings, testConnection } = useSettingsStore()
  const [localSettings, setLocalSettings] = useState({
    apiRootUrl: settings.apiRootUrl,
    authorizationKey: settings.authorizationKey,
    authorizationType: settings.authorizationType,
    customAuthPrefix: settings.customAuthPrefix,
    testEndpoint: settings.testEndpoint,
    csrfToken: settings.csrfToken,
    useProxy: settings.useProxy,
    proxyUrl: settings.proxyUrl,
  })
  const [isTestingConnection, setIsTestingConnection] = useState(false)

  const handleSave = () => {
    updateSettings(localSettings)
  }

  const handleTestConnection = async () => {
    setIsTestingConnection(true)
    await testConnection()
    setIsTestingConnection(false)
  }

  const hasChanges = 
    localSettings.apiRootUrl !== settings.apiRootUrl ||
    localSettings.authorizationKey !== settings.authorizationKey ||
    localSettings.authorizationType !== settings.authorizationType ||
    localSettings.customAuthPrefix !== settings.customAuthPrefix ||
    localSettings.testEndpoint !== settings.testEndpoint ||
    localSettings.csrfToken !== settings.csrfToken ||
    localSettings.useProxy !== settings.useProxy ||
    localSettings.proxyUrl !== settings.proxyUrl

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          API Endpoint Configuration
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Root URL
            </label>
            <input
              type="url"
              value={localSettings.apiRootUrl}
              onChange={(e) => setLocalSettings(prev => ({ ...prev, apiRootUrl: e.target.value }))}
              placeholder="https://infraonpoc.sd.everest-ims.com"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Base URL for all API requests (e.g., https://infraonpoc.sd.everest-ims.com or http://localhost:8000)
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Authorization Type
              </label>
              <select
                value={localSettings.authorizationType}
                onChange={(e) => setLocalSettings(prev => ({ ...prev, authorizationType: e.target.value as AuthorizationType }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              >
                <option value="bearer">Bearer Token</option>
                <option value="infraonDNS">Infraon DNS</option>
                <option value="custom">Custom</option>
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {localSettings.authorizationType === 'bearer' && 'Standard Bearer token authentication'}
                {localSettings.authorizationType === 'infraonDNS' && 'Infraon DNS authentication scheme'}
                {localSettings.authorizationType === 'custom' && 'Custom authorization prefix'}
              </p>
            </div>

            {localSettings.authorizationType === 'custom' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Custom Auth Prefix
                </label>
                <input
                  type="text"
                  value={localSettings.customAuthPrefix}
                  onChange={(e) => setLocalSettings(prev => ({ ...prev, customAuthPrefix: e.target.value }))}
                  placeholder="Basic, API-Key, etc."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Prefix used before the authorization key
                </p>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Authorization Key (Optional)
            </label>
            <input
              type="password"
              value={localSettings.authorizationKey}
              onChange={(e) => setLocalSettings(prev => ({ ...prev, authorizationKey: e.target.value }))}
              placeholder={localSettings.authorizationType === 'infraonDNS' ? 'Infraon DNS token' : 'Authorization token'}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {localSettings.authorizationType === 'bearer' && 'JWT token or API key for Bearer authentication'}
              {localSettings.authorizationType === 'infraonDNS' && 'Encoded Infraon DNS authentication token'}
              {localSettings.authorizationType === 'custom' && 'Token for custom authentication scheme'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Test Endpoint
              </label>
              <input
                type="text"
                value={localSettings.testEndpoint}
                onChange={(e) => setLocalSettings(prev => ({ ...prev, testEndpoint: e.target.value }))}
                placeholder="/ux/common/announcement/announcements/"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Endpoint path for connection testing (e.g., /ux/common/announcement/announcements/ for Infraon)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                CSRF Token (Optional)
              </label>
              <input
                type="password"
                value={localSettings.csrfToken}
                onChange={(e) => setLocalSettings(prev => ({ ...prev, csrfToken: e.target.value }))}
                placeholder="CSRF protection token"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                X-CSRFToken header value if required
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Proxy Configuration
        </h3>
        
        <div className="space-y-4">
          <label className="flex items-start">
            <input
              type="checkbox"
              checked={localSettings.useProxy}
              onChange={(e) => setLocalSettings(prev => ({ ...prev, useProxy: e.target.checked }))}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 mt-1"
            />
            <div className="ml-3">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Enable Proxy Mode
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Route requests through the backend proxy to bypass CORS restrictions when testing external APIs
              </p>
            </div>
          </label>

          {localSettings.useProxy && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Proxy Server URL
              </label>
              <input
                type="url"
                value={localSettings.proxyUrl}
                onChange={(e) => setLocalSettings(prev => ({ ...prev, proxyUrl: e.target.value }))}
                placeholder="http://localhost:8000"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                URL of your backend server that will proxy requests to external APIs
              </p>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <ConnectionStatusIndicator status={connectionStatus} />
            {connectionStatus.lastChecked && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Last checked: {connectionStatus.lastChecked.toLocaleTimeString()}
              </span>
            )}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handleTestConnection}
              disabled={isTestingConnection}
              className="flex items-center space-x-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 ${isTestingConnection ? 'animate-spin' : ''}`} />
              <span>Test Connection</span>
            </button>
            
            <button
              onClick={handleSave}
              disabled={!hasChanges}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircleIcon className="h-4 w-4" />
              <span>Save Changes</span>
            </button>
          </div>
        </div>

        {connectionStatus.errorMessage && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <div className="flex items-start space-x-2">
              <div className="flex-shrink-0">
                {settings.useProxy ? (
                  <span className="text-sm font-medium text-red-800 dark:text-red-300">🔄 Proxy Mode:</span>
                ) : (
                  <span className="text-sm font-medium text-red-800 dark:text-red-300">🌐 Direct Mode:</span>
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm text-red-800 dark:text-red-300">
                  {connectionStatus.errorMessage}
                </p>
              </div>
            </div>
            
            {connectionStatus.errorMessage.includes('CORS') && (
              <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-sm text-blue-800 dark:text-blue-300 font-medium mb-2">
                  💡 CORS Solution Available:
                </p>
                <ul className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                  <li>• <strong>Enable Proxy Mode</strong> above to bypass CORS restrictions</li>
                  <li>• The proxy routes requests through your backend server</li>
                  <li>• This allows testing external APIs without CORS issues</li>
                  <li>• Make sure your backend server (Man-O-Man) is running</li>
                  <li>• Alternative: Test endpoints directly using tools like Postman or curl</li>
                </ul>
              </div>
            )}
            
            {connectionStatus.errorMessage.includes('Proxy connection failed') && (
              <div className="mt-3 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm text-yellow-800 dark:text-yellow-300 font-medium mb-2">
                  ⚠️ Proxy Server Issue:
                </p>
                <ul className="text-xs text-yellow-700 dark:text-yellow-300 space-y-1">
                  <li>• Make sure your backend server is running on the configured proxy URL</li>
                  <li>• Default: <code>cd backend && uvicorn app.main:app --reload</code></li>
                  <li>• Check that the proxy URL matches your backend server address</li>
                  <li>• Verify the backend has the proxy endpoint enabled</li>
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function TestingOptionsTab() {
  const { settings, updateSettings } = useSettingsStore()
  
  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Default Testing Configuration
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Request Timeout (ms)
            </label>
            <input
              type="number"
              min="1000"
              max="300000"
              step="1000"
              value={settings.defaultTimeout}
              onChange={(e) => updateSettings({ defaultTimeout: parseInt(e.target.value) || 30000 })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Max Retries
            </label>
            <input
              type="number"
              min="0"
              max="10"
              value={settings.maxRetries}
              onChange={(e) => updateSettings({ maxRetries: parseInt(e.target.value) || 3 })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Default Request Format
            </label>
            <select
              value={settings.defaultRequestFormat}
              onChange={(e) => updateSettings({ defaultRequestFormat: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="json">JSON</option>
              <option value="form">Form Data</option>
              <option value="raw">Raw</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Workspace Mode
            </label>
            <select
              value={settings.workspaceMode}
              onChange={(e) => updateSettings({ workspaceMode: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="single">Single Workspace</option>
              <option value="tabs">Tabbed Workspace</option>
            </select>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.autoRetryEnabled}
              onChange={(e) => updateSettings({ autoRetryEnabled: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Enable automatic retries for failed requests
            </span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.showResponseHeaders}
              onChange={(e) => updateSettings({ showResponseHeaders: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Show response headers by default
            </span>
          </label>

          <label className="flex items-center">
            <input
              type="checkbox"
              checked={settings.enableSyntaxHighlighting}
              onChange={(e) => updateSettings({ enableSyntaxHighlighting: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600"
            />
            <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">
              Enable syntax highlighting for JSON responses
            </span>
          </label>
        </div>
      </div>
    </div>
  )
}

function AiFeaturesTab() {
  const { settings, updateSettings } = useSettingsStore()
  
  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          AI Assistant Configuration
        </h3>
        
        <div className="space-y-4">
          <label className="flex items-start">
            <input
              type="checkbox"
              checked={settings.aiAssistanceEnabled}
              onChange={(e) => updateSettings({ aiAssistanceEnabled: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 mt-1"
            />
            <div className="ml-3">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Enable AI Assistant
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Show AI-powered suggestions and help throughout the application
              </p>
            </div>
          </label>

          <label className="flex items-start">
            <input
              type="checkbox"
              checked={settings.autoGenerateTestData}
              onChange={(e) => updateSettings({ autoGenerateTestData: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 mt-1"
            />
            <div className="ml-3">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Auto-generate Test Data
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Automatically generate realistic test data for API parameters
              </p>
            </div>
          </label>

          <label className="flex items-start">
            <input
              type="checkbox"
              checked={settings.aiSuggestionsEnabled}
              onChange={(e) => updateSettings({ aiSuggestionsEnabled: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 mt-1"
            />
            <div className="ml-3">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Smart Suggestions
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Get intelligent suggestions for API testing and workflow optimization
              </p>
            </div>
          </label>
        </div>
      </div>
    </div>
  )
}

function AdvancedTab() {
  const { settings, updateSettings, resetToDefaults, exportSettings, importSettings } = useSettingsStore()
  const [importText, setImportText] = useState('')
  const [showImport, setShowImport] = useState(false)
  
  const handleExport = () => {
    const settingsJson = exportSettings()
    const blob = new Blob([settingsJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'man-o-man-settings.json'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }
  
  const handleImport = async () => {
    const success = await importSettings(importText)
    if (success) {
      setImportText('')
      setShowImport(false)
      alert('Settings imported successfully!')
    } else {
      alert('Failed to import settings. Please check the format.')
    }
  }
  
  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Advanced Options
        </h3>
        
        <div className="space-y-4">
          <label className="flex items-start">
            <input
              type="checkbox"
              checked={settings.enableRequestLogging}
              onChange={(e) => updateSettings({ enableRequestLogging: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 mt-1"
            />
            <div className="ml-3">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Enable Request Logging
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Log all API requests to browser console for debugging
              </p>
            </div>
          </label>

          <label className="flex items-start">
            <input
              type="checkbox"
              checked={settings.preserveHistory}
              onChange={(e) => updateSettings({ preserveHistory: e.target.checked })}
              className="rounded border-gray-300 dark:border-gray-600 text-blue-600 mt-1"
            />
            <div className="ml-3">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Preserve Testing History
              </span>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Keep history of API tests and conversations across sessions
              </p>
            </div>
          </label>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Settings Management
        </h3>
        
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleExport}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <DocumentArrowDownIcon className="h-4 w-4" />
            <span>Export Settings</span>
          </button>
          
          <button
            onClick={() => setShowImport(!showImport)}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <DocumentArrowUpIcon className="h-4 w-4" />
            <span>Import Settings</span>
          </button>
          
          <button
            onClick={() => {
              if (confirm('Are you sure you want to reset all settings to defaults?')) {
                resetToDefaults()
              }
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Reset to Defaults</span>
          </button>
        </div>
        
        <AnimatePresence>
          {showImport && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 space-y-3"
            >
              <textarea
                value={importText}
                onChange={(e) => setImportText(e.target.value)}
                placeholder="Paste settings JSON here..."
                className="w-full h-32 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <div className="flex space-x-2">
                <button
                  onClick={handleImport}
                  disabled={!importText.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Import
                </button>
                <button
                  onClick={() => {
                    setImportText('')
                    setShowImport(false)
                  }}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('api')
  
  const renderTabContent = () => {
    switch (activeTab) {
      case 'api': return <ApiConfigurationTab />
      case 'testing': return <TestingOptionsTab />
      case 'ai': return <AiFeaturesTab />
      case 'advanced': return <AdvancedTab />
      default: return <ApiConfigurationTab />
    }
  }
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex items-center space-x-3">
        <Cog6ToothIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Application Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Configure your Man-O-Man testing environment and preferences
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-1">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-1">
          {settingsTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center justify-center space-x-3 p-4 rounded-lg font-medium transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <div className="text-left hidden lg:block">
                <div className="font-semibold">{tab.label}</div>
                <div className="text-xs opacity-75">{tab.description}</div>
              </div>
              <div className="lg:hidden">
                <div className="font-semibold text-sm">{tab.label}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
        >
          {renderTabContent()}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  )
}