import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  ChartBarIcon,
  CalendarDaysIcon,
  UserGroupIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon,
  PlayIcon,
  DocumentTextIcon,
  CpuChipIcon,
} from '@heroicons/react/24/outline'

interface UsageAnalyticsProps {
  serviceName: string
}

interface AnalyticsData {
  period: string
  views: number
  tests: number
  downloads: number
  users: number
}

interface PopularEndpoint {
  path: string
  method: string
  calls: number
  avgResponseTime: number
  successRate: number
}

const mockAnalyticsData: AnalyticsData[] = [
  { period: 'Last 7 days', views: 156, tests: 89, downloads: 23, users: 42 },
  { period: 'Last 30 days', views: 678, tests: 234, downloads: 67, users: 128 },
  { period: 'Last 90 days', views: 1543, tests: 892, downloads: 189, users: 287 },
  { period: 'All time', views: 4321, tests: 2156, downloads: 445, users: 523 },
]

const mockPopularEndpoints: PopularEndpoint[] = [
  { path: '/incidents', method: 'GET', calls: 1234, avgResponseTime: 120, successRate: 98.5 },
  { path: '/incidents/{id}', method: 'GET', calls: 987, avgResponseTime: 85, successRate: 99.2 },
  { path: '/incidents', method: 'POST', calls: 456, avgResponseTime: 250, successRate: 96.8 },
  { path: '/incidents/{id}', method: 'PUT', calls: 234, avgResponseTime: 180, successRate: 97.4 },
  { path: '/incidents/search', method: 'GET', calls: 189, avgResponseTime: 340, successRate: 94.7 },
]

export const UsageAnalytics: React.FC<UsageAnalyticsProps> = ({ serviceName }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('Last 30 days')
  const [activeTab, setActiveTab] = useState<'overview' | 'endpoints' | 'users'>('overview')

  const currentData = mockAnalyticsData.find(d => d.period === selectedPeriod) || mockAnalyticsData[1]
  const previousData = mockAnalyticsData[mockAnalyticsData.indexOf(currentData) - 1] || currentData

  const getGrowthRate = (current: number, previous: number) => {
    if (previous === 0) return 0
    return ((current - previous) / previous) * 100
  }

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400'
      case 'POST': return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400'
      case 'PUT': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'DELETE': return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30 dark:text-gray-400'
    }
  }

  const StatCard = ({ title, value, icon: Icon, growth, color = 'blue' }: {
    title: string
    value: number
    icon: any
    growth: number
    color?: string
  }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {value.toLocaleString()}
          </p>
        </div>
        <div className={`p-3 rounded-lg bg-${color}-100 dark:bg-${color}-900/30`}>
          <Icon className={`h-6 w-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
      </div>
      <div className="flex items-center mt-3">
        {growth >= 0 ? (
          <ArrowTrendingUpIcon className="h-4 w-4 text-green-500 mr-1" />
        ) : (
          <ArrowTrendingDownIcon className="h-4 w-4 text-red-500 mr-1" />
        )}
        <span className={`text-sm font-medium ${growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {Math.abs(growth).toFixed(1)}%
        </span>
        <span className="text-sm text-gray-500 dark:text-gray-400 ml-1">
          vs previous period
        </span>
      </div>
    </motion.div>
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Usage Analytics</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Track usage patterns and performance for {serviceName}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          >
            {mockAnalyticsData.map((data) => (
              <option key={data.period} value={data.period}>
                {data.period}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
        {[
          { key: 'overview', label: 'Overview', icon: ChartBarIcon },
          { key: 'endpoints', label: 'Endpoints', icon: CpuChipIcon },
          { key: 'users', label: 'Users', icon: UserGroupIcon },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors flex-1 justify-center ${
              activeTab === tab.key
                ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Service Views"
              value={currentData.views}
              icon={EyeIcon}
              growth={getGrowthRate(currentData.views, previousData.views)}
              color="blue"
            />
            <StatCard
              title="API Tests"
              value={currentData.tests}
              icon={PlayIcon}
              growth={getGrowthRate(currentData.tests, previousData.tests)}
              color="green"
            />
            <StatCard
              title="Downloads"
              value={currentData.downloads}
              icon={DocumentTextIcon}
              growth={getGrowthRate(currentData.downloads, previousData.downloads)}
              color="purple"
            />
            <StatCard
              title="Active Users"
              value={currentData.users}
              icon={UserGroupIcon}
              growth={getGrowthRate(currentData.users, previousData.users)}
              color="orange"
            />
          </div>

          {/* Usage Trends Chart Placeholder */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Usage Trends
            </h3>
            <div className="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-center">
              <div className="text-center">
                <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                <p className="text-gray-500 dark:text-gray-400">
                  Interactive usage trends chart would be displayed here
                </p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                  (Chart.js or similar visualization library integration)
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Endpoints Tab */}
      {activeTab === 'endpoints' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Most Popular Endpoints
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Ranked by total API calls in {selectedPeriod.toLowerCase()}
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Endpoint
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Calls
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Avg Response
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Success Rate
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {mockPopularEndpoints.map((endpoint, index) => (
                    <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-3">
                          <span className={`px-2 py-1 rounded text-xs font-mono font-bold ${getMethodColor(endpoint.method)}`}>
                            {endpoint.method}
                          </span>
                          <code className="text-sm font-mono text-gray-900 dark:text-gray-100">
                            {endpoint.path}
                          </code>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {endpoint.calls.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                        {endpoint.avgResponseTime}ms
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          endpoint.successRate >= 98 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                            : endpoint.successRate >= 95
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                        }`}>
                          {endpoint.successRate}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* User Activity */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                User Activity Distribution
              </h3>
              <div className="space-y-4">
                {[
                  { role: 'Developers', count: 45, percentage: 65 },
                  { role: 'QA Engineers', count: 18, percentage: 26 },
                  { role: 'System Admins', count: 6, percentage: 9 },
                ].map((group) => (
                  <div key={group.role}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-400">{group.role}</span>
                      <span className="font-medium text-gray-900 dark:text-white">{group.count} users</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${group.percentage}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Peak Usage Times */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Peak Usage Times
              </h3>
              <div className="space-y-3">
                {[
                  { time: '9:00 AM - 11:00 AM', usage: 85, label: 'Morning Peak' },
                  { time: '1:00 PM - 3:00 PM', usage: 72, label: 'Afternoon' },
                  { time: '7:00 PM - 9:00 PM', usage: 34, label: 'Evening' },
                  { time: '11:00 PM - 1:00 AM', usage: 12, label: 'Night' },
                ].map((period) => (
                  <div key={period.time} className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {period.time}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {period.label}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-gray-900 dark:text-white">
                        {period.usage}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}