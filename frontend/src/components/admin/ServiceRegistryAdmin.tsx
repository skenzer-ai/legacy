import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CogIcon,
  DocumentTextIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  EyeSlashIcon,
  CloudArrowUpIcon,
  ClockIcon,
  UserIcon,
  TagIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import { ServiceSummary } from '../../types/service'

interface ServiceRegistryAdminProps {
  services: ServiceSummary[]
}

interface ServiceEdit {
  id: string
  field: keyof ServiceSummary
  oldValue: any
  newValue: any
  status: 'pending' | 'approved' | 'rejected'
  author: string
  timestamp: Date
  reason?: string
}

interface RegistryAction {
  id: string
  type: 'create' | 'update' | 'delete' | 'merge' | 'split'
  serviceName: string
  description: string
  status: 'pending' | 'completed' | 'failed'
  author: string
  timestamp: Date
}

const mockPendingEdits: ServiceEdit[] = [
  {
    id: '1',
    field: 'suggested_description',
    oldValue: 'Manage incident tickets and workflows',
    newValue: 'Comprehensive incident management system with automated workflows and SLA tracking',
    status: 'pending',
    author: 'Sarah Chen',
    timestamp: new Date('2024-01-20T10:30:00Z'),
  },
  {
    id: '2',
    field: 'keywords',
    oldValue: ['incident', 'ticket', 'workflow'],
    newValue: ['incident', 'ticket', 'workflow', 'sla', 'automation', 'escalation'],
    status: 'pending',
    author: 'Mike Rodriguez',
    timestamp: new Date('2024-01-19T14:15:00Z'),
  },
]

const mockRecentActions: RegistryAction[] = [
  {
    id: '1',
    type: 'update',
    serviceName: 'user-management',
    description: 'Updated service classification from Tier 1 to Tier 2',
    status: 'completed',
    author: 'Admin',
    timestamp: new Date('2024-01-20T09:15:00Z'),
  },
  {
    id: '2',
    type: 'merge',
    serviceName: 'auth-service',
    description: 'Merged authentication and authorization endpoints',
    status: 'completed',
    author: 'System',
    timestamp: new Date('2024-01-19T16:45:00Z'),
  },
]

export const ServiceRegistryAdmin: React.FC<ServiceRegistryAdminProps> = ({ services }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'pending' | 'actions' | 'settings'>('overview')
  const [selectedServices, setSelectedServices] = useState<string[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all')
  const [pendingEdits, setPendingEdits] = useState<ServiceEdit[]>(mockPendingEdits)
  const [recentActions] = useState<RegistryAction[]>(mockRecentActions)

  const filteredServices = services.filter(service => {
    const matchesSearch = service.service_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         service.suggested_description.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesFilter = filterStatus === 'all' ||
                         (filterStatus === 'active' && service.confidence_score >= 0.8) ||
                         (filterStatus === 'inactive' && service.confidence_score < 0.8)
    
    return matchesSearch && matchesFilter
  })

  const approveEdit = (editId: string) => {
    setPendingEdits(prev => prev.map(edit => 
      edit.id === editId ? { ...edit, status: 'approved' as const } : edit
    ))
  }

  const rejectEdit = (editId: string, reason: string) => {
    setPendingEdits(prev => prev.map(edit => 
      edit.id === editId ? { ...edit, status: 'rejected' as const, reason } : edit
    ))
  }

  const toggleServiceSelection = (serviceName: string) => {
    setSelectedServices(prev => 
      prev.includes(serviceName) 
        ? prev.filter(name => name !== serviceName)
        : [...prev, serviceName]
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'approved': case 'completed': return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400'
      case 'rejected': case 'failed': return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30 dark:text-gray-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
            <CogIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            <span>Service Registry Admin</span>
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage service definitions, approvals, and registry operations
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            <CloudArrowUpIcon className="h-4 w-4" />
            <span>Import Services</span>
          </button>
          <button className="flex items-center space-x-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
            <DocumentTextIcon className="h-4 w-4" />
            <span>Export Registry</span>
          </button>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Services</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{services.length}</p>
            </div>
            <TagIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Pending Edits</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{pendingEdits.filter(e => e.status === 'pending').length}</p>
            </div>
            <ClockIcon className="h-8 w-8 text-yellow-600 dark:text-yellow-400" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">High Confidence</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {services.filter(s => s.confidence_score >= 0.9).length}
              </p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-green-600 dark:text-green-400" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Need Review</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {services.filter(s => s.confidence_score < 0.8).length}
              </p>
            </div>
            <ExclamationTriangleIcon className="h-8 w-8 text-red-600 dark:text-red-400" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
        {[
          { key: 'overview', label: 'Services Overview' },
          { key: 'pending', label: `Pending (${pendingEdits.filter(e => e.status === 'pending').length})` },
          { key: 'actions', label: 'Recent Actions' },
          { key: 'settings', label: 'Settings' },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Filters */}
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
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="all">All Services</option>
              <option value="active">High Confidence</option>
              <option value="inactive">Needs Review</option>
            </select>
          </div>

          {/* Bulk Actions */}
          {selectedServices.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 flex items-center justify-between"
            >
              <span className="text-blue-700 dark:text-blue-300">
                {selectedServices.length} service(s) selected
              </span>
              <div className="flex space-x-2">
                <button className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition-colors">
                  Bulk Edit
                </button>
                <button className="px-3 py-1.5 border border-blue-300 text-blue-700 dark:text-blue-300 rounded text-sm hover:bg-blue-100 dark:hover:bg-blue-900/30 transition-colors">
                  Export Selected
                </button>
                <button
                  onClick={() => setSelectedServices([])}
                  className="px-3 py-1.5 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 text-sm"
                >
                  Clear
                </button>
              </div>
            </motion.div>
          )}

          {/* Services Table */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left">
                      <input
                        type="checkbox"
                        checked={selectedServices.length === filteredServices.length && filteredServices.length > 0}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedServices(filteredServices.map(s => s.service_name))
                          } else {
                            setSelectedServices([])
                          }
                        }}
                        className="rounded border-gray-300 dark:border-gray-600"
                      />
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Service
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Endpoints
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Confidence
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredServices.map((service) => (
                    <tr key={service.service_name} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4">
                        <input
                          type="checkbox"
                          checked={selectedServices.includes(service.service_name)}
                          onChange={() => toggleServiceSelection(service.service_name)}
                          className="rounded border-gray-300 dark:border-gray-600"
                        />
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {service.service_name}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400 truncate max-w-xs">
                            {service.suggested_description}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                        {service.endpoint_count}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full transition-all duration-500 ${
                                service.confidence_score >= 0.9 ? 'bg-green-500' :
                                service.confidence_score >= 0.8 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${service.confidence_score * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-600 dark:text-gray-400">
                            {(service.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex space-x-2">
                          <button className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button className="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300">
                            <EyeIcon className="h-4 w-4" />
                          </button>
                          <button className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300">
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Pending Tab */}
      {activeTab === 'pending' && (
        <div className="space-y-4">
          {pendingEdits.filter(edit => edit.status === 'pending').length === 0 ? (
            <div className="text-center py-12">
              <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                All caught up!
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                No pending edits require your attention.
              </p>
            </div>
          ) : (
            pendingEdits.filter(edit => edit.status === 'pending').map((edit) => (
              <motion.div
                key={edit.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <UserIcon className="h-5 w-5 text-gray-500" />
                    <div>
                      <span className="font-medium text-gray-900 dark:text-white">{edit.author}</span>
                      <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                        proposed changes to <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">{edit.field}</code>
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {edit.timestamp.toLocaleDateString()}
                  </span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Current Value</h4>
                    <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                      <pre className="text-sm text-red-800 dark:text-red-300 whitespace-pre-wrap">
                        {Array.isArray(edit.oldValue) ? edit.oldValue.join(', ') : edit.oldValue}
                      </pre>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Proposed Value</h4>
                    <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                      <pre className="text-sm text-green-800 dark:text-green-300 whitespace-pre-wrap">
                        {Array.isArray(edit.newValue) ? edit.newValue.join(', ') : edit.newValue}
                      </pre>
                    </div>
                  </div>
                </div>
                
                <div className="flex space-x-3">
                  <button
                    onClick={() => approveEdit(edit.id)}
                    className="flex items-center space-x-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    <CheckCircleIcon className="h-4 w-4" />
                    <span>Approve</span>
                  </button>
                  <button
                    onClick={() => rejectEdit(edit.id, 'Insufficient justification')}
                    className="flex items-center space-x-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <ExclamationTriangleIcon className="h-4 w-4" />
                    <span>Reject</span>
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </div>
      )}

      {/* Actions Tab */}
      {activeTab === 'actions' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Registry Actions</h3>
          {recentActions.map((action) => (
            <div
              key={action.id}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(action.status)}`}>
                    {action.type}
                  </span>
                  <span className="font-medium text-gray-900 dark:text-white">{action.serviceName}</span>
                  <span className="text-gray-600 dark:text-gray-400">—</span>
                  <span className="text-gray-600 dark:text-gray-400">{action.description}</span>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500 dark:text-gray-400">{action.author}</div>
                  <div className="text-xs text-gray-400 dark:text-gray-500">
                    {action.timestamp.toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Registry Settings</h3>
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <p className="text-gray-600 dark:text-gray-400">
              Registry configuration and settings panel would be implemented here, including:
            </p>
            <ul className="mt-3 space-y-1 text-sm text-gray-600 dark:text-gray-400">
              <li>• Auto-approval thresholds</li>
              <li>• Notification preferences</li>
              <li>• User permissions and roles</li>
              <li>• Registry backup and versioning</li>
              <li>• Integration settings</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}