import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  BeakerIcon, 
  CommandLineIcon, 
  SparklesIcon,
  PlayIcon,
  DocumentTextIcon,
  CpuChipIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline'
import { useServices } from '../hooks/useServices'
import { ApiTestingWorkspace } from '../components/testing/ApiTestingWorkspace'
import { ServiceSelector } from '../components/testing/ServiceSelector'

export default function ApiTesting() {
  const [selectedService, setSelectedService] = useState<string | null>(null)
  const { data: services = [], isLoading } = useServices()

  const testingFeatures = [
    {
      icon: PlayIcon,
      title: 'Live API Testing',
      description: 'Execute real API calls with interactive forms and instant feedback'
    },
    {
      icon: SparklesIcon,
      title: 'AI Test Assistant',
      description: 'Get intelligent test data generation and debugging guidance'
    },
    {
      icon: DocumentTextIcon,
      title: 'Response Analysis',
      description: 'Syntax highlighting, schema validation, and response inspection'
    },
    {
      icon: RocketLaunchIcon,
      title: 'Test Scenarios',
      description: 'Pre-built test scenarios for common operations and edge cases'
    }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
            <BeakerIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            <span>API Testing Studio</span>
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Test and explore API operations with intelligent assistance
          </p>
        </div>
      </div>

      {!selectedService ? (
        <>
          {/* Features Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {testingFeatures.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
              >
                <div className="flex items-center space-x-3 mb-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <feature.icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h3 className="font-semibold text-gray-900 dark:text-white text-sm">
                    {feature.title}
                  </h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>

          {/* Service Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center space-x-3 mb-6">
              <CpuChipIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Select a Service to Test
              </h2>
            </div>
            
            {isLoading ? (
              <div className="text-center py-12">
                <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent"></div>
                <p className="mt-4 text-gray-600 dark:text-gray-400">Loading services...</p>
              </div>
            ) : (
              <ServiceSelector 
                services={services} 
                onServiceSelect={setSelectedService} 
              />
            )}
          </div>

          {/* Getting Started */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-8">
            <div className="flex items-center space-x-3 mb-4">
              <CommandLineIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                Getting Started with API Testing
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">Choose Service</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 ml-8">
                  Select a service from the grid to explore its API operations
                </p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">Configure Test</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 ml-8">
                  Set parameters, headers, and request body with AI assistance
                </p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <div className="w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center text-sm font-bold">3</div>
                  <h3 className="font-semibold text-gray-900 dark:text-white">Execute & Analyze</h3>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 ml-8">
                  Run tests and analyze responses with detailed insights
                </p>
              </div>
            </div>
          </div>
        </>
      ) : (
        <ApiTestingWorkspace 
          serviceName={selectedService} 
          onBack={() => setSelectedService(null)} 
        />
      )}
    </motion.div>
  )
}