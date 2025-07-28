import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  CpuChipIcon,
  BeakerIcon,
  StarIcon,
  ExclamationTriangleIcon,
  TagIcon,
} from '@heroicons/react/24/outline'
import { ServiceSummary } from '../../types/service'
import { cn } from '../../utils/cn'

interface ServiceCardProps {
  service: ServiceSummary
}

export default function ServiceCard({ service }: ServiceCardProps) {
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="card-hover group"
    >
      <Link
        to={`/services/${service.service_name}`}
        className="block p-6 h-full"
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
              {service.service_name}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
              {service.suggested_description}
            </p>
          </div>
          
          {/* Status indicators */}
          <div className="flex items-center space-x-2 ml-4">
            {service.needs_review && (
              <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500" />
            )}
            <div className="flex items-center">
              <StarIcon className="h-3 w-3 text-yellow-400 mr-1" />
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {(service.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-primary-100 dark:bg-primary-900/20 rounded-lg flex items-center justify-center mr-3">
              <CpuChipIcon className="w-4 h-4 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {service.endpoint_count}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Endpoints
              </p>
            </div>
          </div>
          
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center mr-3">
              <BeakerIcon className="w-4 h-4 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {service.tier1_operations}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                CRUD Ops
              </p>
            </div>
          </div>
        </div>

        {/* Keywords */}
        <div className="mb-4">
          <div className="flex items-center mb-2">
            <TagIcon className="h-3 w-3 text-gray-400 mr-1" />
            <span className="text-xs text-gray-500 dark:text-gray-400">Keywords</span>
          </div>
          <div className="flex flex-wrap gap-1">
            {service.keywords.slice(0, 3).map((keyword) => (
              <span
                key={keyword}
                className="badge badge-info text-xs px-2 py-1"
              >
                {keyword}
              </span>
            ))}
            {service.keywords.length > 3 && (
              <span className="text-xs text-gray-500 dark:text-gray-400 px-2 py-1">
                +{service.keywords.length - 3} more
              </span>
            )}
          </div>
        </div>

        {/* Operations breakdown */}
        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Tier 1: {service.tier1_operations}</span>
          <span>Tier 2: {service.tier2_operations}</span>
        </div>

        {/* Progress bar for confidence */}
        <div className="mt-3 flex items-center">
          <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className={cn(
                'h-1.5 rounded-full transition-all duration-300',
                service.confidence_score >= 0.9
                  ? 'bg-green-500'
                  : service.confidence_score >= 0.7
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              )}
              style={{ width: `${service.confidence_score * 100}%` }}
            />
          </div>
          <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
            Confidence
          </span>
        </div>
      </Link>
    </motion.div>
  )
}