import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  BookOpenIcon,
  ChartBarIcon,
  CogIcon,
} from '@heroicons/react/24/outline'
import { useServices, useService } from '../hooks/useServices'
import { ServiceAnnotations } from '../components/knowledge/ServiceAnnotations'
import { UsageAnalytics } from '../components/analytics/UsageAnalytics'
import { ServiceRegistryAdmin } from '../components/admin/ServiceRegistryAdmin'

export default function Knowledge() {
  const [activeTab, setActiveTab] = useState<'annotations' | 'analytics' | 'admin'>('annotations')
  const [selectedService, setSelectedService] = useState<string>('incident-management')
  const { data: services = [] } = useServices()
  const { data: service } = useService(selectedService)

  const tabs = [
    { 
      key: 'annotations', 
      label: 'Knowledge Base', 
      icon: BookOpenIcon,
      description: 'Community annotations and insights'
    },
    { 
      key: 'analytics', 
      label: 'Usage Analytics', 
      icon: ChartBarIcon,
      description: 'Service usage patterns and metrics'
    },
    { 
      key: 'admin', 
      label: 'Admin Panel', 
      icon: CogIcon,
      description: 'Registry management and approvals'
    },
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
            <BookOpenIcon className="h-8 w-8 text-purple-600 dark:text-purple-400" />
            <span>Collaborative Knowledge</span>
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Build and share knowledge about API services through annotations, analytics, and collaborative editing
          </p>
        </div>
        
        {/* Service Selector for annotations and analytics */}
        {(activeTab === 'annotations' || activeTab === 'analytics') && (
          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            {services.map((service) => (
              <option key={service.service_name} value={service.service_name}>
                {service.service_name}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-1">
        <div className="grid grid-cols-3 gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center justify-center space-x-3 p-4 rounded-lg font-medium transition-all duration-200 ${
                activeTab === tab.key
                  ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <div className="text-left">
                <div className="font-semibold">{tab.label}</div>
                <div className="text-xs opacity-75">{tab.description}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="min-h-screen">
        {activeTab === 'annotations' && service && (
          <ServiceAnnotations service={service} />
        )}
        
        {activeTab === 'analytics' && (
          <UsageAnalytics serviceName={selectedService} />
        )}
        
        {activeTab === 'admin' && (
          <ServiceRegistryAdmin services={services} />
        )}
      </div>

      {/* Features Overview (shown when no service selected for annotations/analytics) */}
      {(activeTab === 'annotations' || activeTab === 'analytics') && !service && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl p-8">
          <div className="text-center">
            <BookOpenIcon className="h-12 w-12 text-purple-600 dark:text-purple-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Loading Service Data
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Please wait while we load the service information...
            </p>
          </div>
        </div>
      )}

      {/* Collaboration Features Info */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <BookOpenIcon className="h-8 w-8 text-blue-600 dark:text-blue-400 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Knowledge Sharing</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Add notes, tips, and insights to help others understand and use services effectively
            </p>
          </div>
          <div className="text-center">
            <ChartBarIcon className="h-8 w-8 text-purple-600 dark:text-purple-400 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Usage Insights</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Track how services are being used and identify optimization opportunities
            </p>
          </div>
          <div className="text-center">
            <CogIcon className="h-8 w-8 text-green-600 dark:text-green-400 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Collaborative Editing</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Propose improvements to service definitions through community contributions
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}