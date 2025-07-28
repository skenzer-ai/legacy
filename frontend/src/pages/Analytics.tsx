import { motion } from 'framer-motion'

export default function Analytics() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="card p-8 text-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          Usage Analytics
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Analytics dashboard will be implemented in Milestone 4
        </p>
      </div>
    </motion.div>
  )
}