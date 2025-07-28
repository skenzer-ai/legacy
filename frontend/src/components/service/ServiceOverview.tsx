import React from 'react'
import { motion } from 'framer-motion'
import {
  InformationCircleIcon,
  TagIcon,
  LinkIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import { ServiceSummary } from '../../types/service'

interface ServiceOverviewProps {
  service: ServiceSummary
}

export const ServiceOverview: React.FC<ServiceOverviewProps> = ({ service }) => {
  // Mock business context data
  const businessContext = {
    purpose: `The ${service.service_name} service is a core component of the Infraon platform that handles ${service.suggested_description.toLowerCase()}. This service provides essential functionality for managing and maintaining system operations.`,
    useCases: [
      `Creating and managing ${service.service_name} records`,
      `Automated ${service.service_name} workflow processing`,
      `Integration with third-party ${service.service_name} systems`,
      `Reporting and analytics for ${service.service_name} data`,
    ],
    dependencies: [
      'authentication',
      'user_profile',
      'audit_log',
      'notification'
    ].filter(dep => dep !== service.service_name).slice(0, 3),
    businessValue: `Critical service that enables ${service.service_name} management workflows, supporting operational efficiency and compliance requirements.`,
  }

  const healthMetrics = {
    uptime: '99.9%',
    avgResponse: '145ms',
    successRate: '99.2%',
    lastUpdated: '2 hours ago',
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Main Overview */}
      <div className="lg:col-span-2 space-y-6">
        {/* Business Context */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Business Context
            </h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Purpose</h4>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {businessContext.purpose}
              </p>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Common Use Cases</h4>
              <ul className="space-y-2">
                {businessContext.useCases.map((useCase, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-600 dark:text-gray-400">{useCase}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">Business Value</h4>
              <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                {businessContext.businessValue}
              </p>
            </div>
          </div>
        </div>

        {/* Keywords & Synonyms */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <TagIcon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Keywords & Classification
            </h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-3">Primary Keywords</h4>
              <div className="flex flex-wrap gap-2">
                {service.keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="px-3 py-1.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm font-medium"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 dark:text-white mb-3">Synonyms & Aliases</h4>
              <div className="flex flex-wrap gap-2">
                {service.synonyms.map((synonym) => (
                  <span
                    key={synonym}
                    className="px-3 py-1.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg text-sm"
                  >
                    {synonym}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Service Dependencies */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <LinkIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Service Dependencies
            </h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {businessContext.dependencies.map((dependency) => (
              <div
                key={dependency}
                className="flex items-center space-x-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:border-gray-300 dark:hover:border-gray-500 transition-colors cursor-pointer"
              >
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="font-mono text-sm text-gray-900 dark:text-gray-100">
                  {dependency}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400 ml-auto">
                  Connected
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div className="space-y-6">
        {/* Health Metrics */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <ChartBarIcon className="h-5 w-5 text-green-600 dark:text-green-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Health Metrics
            </h3>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Uptime</span>
              <span className="font-medium text-green-600 dark:text-green-400">
                {healthMetrics.uptime}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Avg Response</span>
              <span className="font-medium text-blue-600 dark:text-blue-400">
                {healthMetrics.avgResponse}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Success Rate</span>
              <span className="font-medium text-green-600 dark:text-green-400">
                {healthMetrics.successRate}
              </span>
            </div>
            
            <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                <ClockIcon className="h-3 w-3" />
                <span>Updated {healthMetrics.lastUpdated}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Classification Status */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <CheckCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Classification
            </h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600 dark:text-gray-400">Confidence</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {(service.confidence_score * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${service.confidence_score * 100}%` }}
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {service.needs_review ? (
                <>
                  <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
                  <span className="text-sm text-yellow-600 dark:text-yellow-400">
                    Needs Review
                  </span>
                </>
              ) : (
                <>
                  <CheckCircleIcon className="h-4 w-4 text-green-500" />
                  <span className="text-sm text-green-600 dark:text-green-400">
                    Verified
                  </span>
                </>
              )}
            </div>
            
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Automatically classified using AI service detection
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h3>
          
          <div className="space-y-3">
            <button className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors">
              <div className="font-medium text-gray-900 dark:text-white">Test API</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Try operations in testing studio
              </div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-green-300 dark:hover:border-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors">
              <div className="font-medium text-gray-900 dark:text-white">View Documentation</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Complete API reference
              </div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors">
              <div className="font-medium text-gray-900 dark:text-white">Export Schema</div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Download OpenAPI spec
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}