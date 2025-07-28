import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Squares2X2Icon,
  ListBulletIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import { Menu, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import ServiceCard from './ServiceCard'
import ServiceCardWithChat from './ServiceCardWithChat'
import ServiceListItem from './ServiceListItem'
import { cn } from '../../utils/cn'
import { useServices } from '../../hooks/useServices'

interface ServiceGridProps {
  view: 'grid' | 'list'
  onViewChange: (view: 'grid' | 'list') => void
}

const sortOptions = [
  { label: 'Name (A-Z)', value: 'name_asc' },
  { label: 'Name (Z-A)', value: 'name_desc' },
  { label: 'Endpoints (High to Low)', value: 'endpoints_desc' },
  { label: 'Endpoints (Low to High)', value: 'endpoints_asc' },
  { label: 'Confidence Score', value: 'confidence_desc' },
]

const filterOptions = [
  { label: 'All Services', value: 'all' },
  { label: 'High Confidence', value: 'high_confidence' },
  { label: 'Needs Review', value: 'needs_review' },
  { label: 'Large Services (20+ endpoints)', value: 'large' },
  { label: 'Simple Services (<10 endpoints)', value: 'simple' },
]

export default function ServiceGrid({ view, onViewChange }: ServiceGridProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('name_asc')
  const [filterBy, setFilterBy] = useState('all')
  
  const { data: services = [], isLoading, error, isError } = useServices()

  const filteredAndSortedServices = useMemo(() => {
    let filtered = services

    // Apply search filter
    if (searchQuery) {
      filtered = filtered.filter(service =>
        service.service_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.suggested_description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        service.keywords.some(keyword => 
          keyword.toLowerCase().includes(searchQuery.toLowerCase())
        )
      )
    }

    // Apply category filter
    switch (filterBy) {
      case 'high_confidence':
        filtered = filtered.filter(service => service.confidence_score >= 0.9)
        break
      case 'needs_review':
        filtered = filtered.filter(service => service.needs_review)
        break
      case 'large':
        filtered = filtered.filter(service => service.endpoint_count >= 20)
        break
      case 'simple':
        filtered = filtered.filter(service => service.endpoint_count < 10)
        break
    }

    // Apply sorting
    switch (sortBy) {
      case 'name_asc':
        filtered.sort((a, b) => a.service_name.localeCompare(b.service_name))
        break
      case 'name_desc':
        filtered.sort((a, b) => b.service_name.localeCompare(a.service_name))
        break
      case 'endpoints_desc':
        filtered.sort((a, b) => b.endpoint_count - a.endpoint_count)
        break
      case 'endpoints_asc':
        filtered.sort((a, b) => a.endpoint_count - b.endpoint_count)
        break
      case 'confidence_desc':
        filtered.sort((a, b) => b.confidence_score - a.confidence_score)
        break
    }

    return filtered
  }, [services, searchQuery, sortBy, filterBy])

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              API Services
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Loading services...
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-full mb-4"></div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (isError) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              API Services
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Error loading services
            </p>
          </div>
        </div>
        <div className="text-center py-12">
          <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-500 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Failed to load services
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {error?.message || 'Unable to connect to the backend API'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            API Services
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            {filteredAndSortedServices.length} services discovered
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-3">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search services..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-9 pr-4 w-64"
            />
          </div>

          {/* Filter */}
          <Menu as="div" className="relative">
            <Menu.Button className="btn-secondary">
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filter
              <ChevronDownIcon className="h-4 w-4 ml-2" />
            </Menu.Button>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 mt-2 w-56 card shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <div className="py-1">
                  {filterOptions.map((option) => (
                    <Menu.Item key={option.value}>
                      {({ active }) => (
                        <button
                          onClick={() => setFilterBy(option.value)}
                          className={cn(
                            'block w-full text-left px-4 py-2 text-sm transition-colors',
                            active
                              ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                              : 'text-gray-700 dark:text-gray-300',
                            filterBy === option.value && 'font-medium text-primary-600 dark:text-primary-400'
                          )}
                        >
                          {option.label}
                        </button>
                      )}
                    </Menu.Item>
                  ))}
                </div>
              </Menu.Items>
            </Transition>
          </Menu>

          {/* Sort */}
          <Menu as="div" className="relative">
            <Menu.Button className="btn-secondary">
              Sort
              <ChevronDownIcon className="h-4 w-4 ml-2" />
            </Menu.Button>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 mt-2 w-56 card shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                <div className="py-1">
                  {sortOptions.map((option) => (
                    <Menu.Item key={option.value}>
                      {({ active }) => (
                        <button
                          onClick={() => setSortBy(option.value)}
                          className={cn(
                            'block w-full text-left px-4 py-2 text-sm transition-colors',
                            active
                              ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white'
                              : 'text-gray-700 dark:text-gray-300',
                            sortBy === option.value && 'font-medium text-primary-600 dark:text-primary-400'
                          )}
                        >
                          {option.label}
                        </button>
                      )}
                    </Menu.Item>
                  ))}
                </div>
              </Menu.Items>
            </Transition>
          </Menu>

          {/* View Toggle */}
          <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => onViewChange('grid')}
              className={cn(
                'p-2 rounded transition-colors',
                view === 'grid'
                  ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              )}
            >
              <Squares2X2Icon className="h-4 w-4" />
            </button>
            <button
              onClick={() => onViewChange('list')}
              className={cn(
                'p-2 rounded transition-colors',
                view === 'list'
                  ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              )}
            >
              <ListBulletIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Services */}
      <AnimatePresence mode="wait">
        {view === 'grid' ? (
          <motion.div
            key="grid"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {filteredAndSortedServices.map((service, index) => (
              <motion.div
                key={service.service_name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <ServiceCardWithChat service={service} />
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="list"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-3"
          >
            {filteredAndSortedServices.map((service, index) => (
              <motion.div
                key={service.service_name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <ServiceListItem service={service} />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty State */}
      {filteredAndSortedServices.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <MagnifyingGlassIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No services found
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Try adjusting your search or filter criteria
          </p>
        </motion.div>
      )}
    </div>
  )
}