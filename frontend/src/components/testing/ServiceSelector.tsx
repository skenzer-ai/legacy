import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  CpuChipIcon,
  BeakerIcon,
  RocketLaunchIcon,
} from '@heroicons/react/24/outline'
import { ServiceSummary } from '../../types/service'

interface ServiceSelectorProps {
  services: ServiceSummary[]
  onServiceSelect: (serviceName: string) => void
}

export const ServiceSelector: React.FC<ServiceSelectorProps> = ({ services, onServiceSelect }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterBy, setFilterBy] = useState<'all' | 'high_endpoints' | 'high_confidence'>('all')

  const filteredServices = services.filter(service => {
    const matchesSearch = 
      service.service_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.suggested_description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.keywords.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()))

    const matchesFilter = 
      filterBy === 'all' ||
      (filterBy === 'high_endpoints' && service.endpoint_count >= 10) ||
      (filterBy === 'high_confidence' && service.confidence_score >= 0.9)

    return matchesSearch && matchesFilter
  })

  const getTestingComplexity = (service: ServiceSummary) => {
    if (service.endpoint_count >= 20) return { label: 'Complex', color: 'red', icon: RocketLaunchIcon }
    if (service.endpoint_count >= 10) return { label: 'Moderate', color: 'yellow', icon: BeakerIcon }
    return { label: 'Simple', color: 'green', icon: CpuChipIcon }
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search services..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
        </div>
        <select
          value={filterBy}
          onChange={(e) => setFilterBy(e.target.value as any)}
          className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        >
          <option value="all">All Services</option>
          <option value="high_endpoints">10+ Endpoints</option>
          <option value="high_confidence">High Confidence</option>
        </select>
      </div>

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredServices.map((service, index) => {
          const complexity = getTestingComplexity(service)
          
          return (
            <motion.button
              key={service.service_name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              onClick={() => onServiceSelect(service.service_name)}
              className="text-left p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-lg transition-all duration-200 bg-white dark:bg-gray-800"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900 dark:text-white truncate flex-1">
                  {service.service_name}
                </h3>
                <div className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium ${
                  complexity.color === 'green' 
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                    : complexity.color === 'yellow'
                    ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                }`}>
                  <complexity.icon className="h-3 w-3" />
                  <span>{complexity.label}</span>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                {service.suggested_description}
              </p>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-3 mb-3">
                <div className="text-center">
                  <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                    {service.endpoint_count}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Endpoints</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600 dark:text-green-400">
                    {service.tier1_operations}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">CRUD</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold text-purple-600 dark:text-purple-400">
                    {service.tier2_operations}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Advanced</div>
                </div>
              </div>

              {/* Confidence */}
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 dark:text-gray-400">Confidence</span>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                    <div
                      className="bg-blue-600 h-1.5 rounded-full transition-all duration-500"
                      style={{ width: `${service.confidence_score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
                    {(service.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Keywords Preview */}
              <div className="mt-3 flex flex-wrap gap-1">
                {service.keywords.slice(0, 3).map((keyword) => (
                  <span
                    key={keyword}
                    className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs"
                  >
                    {keyword}
                  </span>
                ))}
                {service.keywords.length > 3 && (
                  <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-500 rounded text-xs">
                    +{service.keywords.length - 3}
                  </span>
                )}
              </div>
            </motion.button>
          )
        })}
      </div>

      {/* Empty State */}
      {filteredServices.length === 0 && (
        <div className="text-center py-12">
          <MagnifyingGlassIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No services found
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}

      {/* Summary */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
          <span>Showing {filteredServices.length} of {services.length} services</span>
          <span>Ready for testing</span>
        </div>
      </div>
    </div>
  )
}