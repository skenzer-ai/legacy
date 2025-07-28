import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ChevronRightIcon,
  StarIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline'
import { ServiceSummary } from '@/types/service'
import { cn } from '@/utils/cn'

interface ServiceListItemProps {
  service: ServiceSummary
}

export default function ServiceListItem({ service }: ServiceListItemProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="card-hover"
    >
      <Link
        to={`/services/${service.service_name}`}
        className="block p-6"
      >
        <div className="flex items-center">
          {/* Main content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                {service.service_name}
              </h3>
              
              {/* Status indicators */}
              <div className="flex items-center ml-3 space-x-2">
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
            
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-1">
              {service.suggested_description}
            </p>
            
            {/* Keywords */}
            <div className="flex flex-wrap gap-1 mt-2">
              {service.keywords.slice(0, 4).map((keyword) => (
                <span
                  key={keyword}
                  className="badge badge-info text-xs px-2 py-1"
                >
                  {keyword}
                </span>
              ))}
              {service.keywords.length > 4 && (
                <span className="text-xs text-gray-500 dark:text-gray-400 px-2 py-1">
                  +{service.keywords.length - 4} more
                </span>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="flex items-center space-x-6 ml-6">
            <div className="flex items-center">
              <CpuChipIcon className="h-4 w-4 text-primary-600 dark:text-primary-400 mr-2" />
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {service.endpoint_count}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Endpoints
                </p>
              </div>
            </div>
            
            <div className="flex items-center">
              <BeakerIcon className="h-4 w-4 text-green-600 dark:text-green-400 mr-2" />
              <div className="text-right">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {service.tier1_operations}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  CRUD Ops
                </p>
              </div>
            </div>

            {/* Confidence bar */}
            <div className="w-20">
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                <span>Confidence</span>
                <span>{(service.confidence_score * 100).toFixed(0)}%</span>
              </div>
              <div className="bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
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
            </div>

            {/* Arrow */}
            <ChevronRightIcon className="h-5 w-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
          </div>
        </div>
      </Link>
    </motion.div>
  )
}