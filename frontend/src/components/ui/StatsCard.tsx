import { motion } from 'framer-motion'
import { cn } from '@/utils/cn'

interface StatsCardProps {
  label: string
  value: string
  change: string
  changeType: 'positive' | 'negative' | 'neutral'
  icon: React.ComponentType<{ className?: string }>
}

export default function StatsCard({ 
  label, 
  value, 
  change, 
  changeType, 
  icon: Icon 
}: StatsCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="card p-6"
    >
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/20 rounded-xl flex items-center justify-center">
            <Icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          </div>
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {label}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {value}
          </p>
        </div>
      </div>
      <div className="mt-4">
        <span
          className={cn(
            'inline-flex items-center text-sm font-medium',
            {
              'text-green-600 dark:text-green-400': changeType === 'positive',
              'text-red-600 dark:text-red-400': changeType === 'negative',
              'text-gray-600 dark:text-gray-400': changeType === 'neutral',
            }
          )}
        >
          {change}
        </span>
      </div>
    </motion.div>
  )
}