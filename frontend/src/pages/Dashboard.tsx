import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  CpuChipIcon, 
  BeakerIcon, 
  ClockIcon,
  CheckCircleIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline'
import ServiceGrid from '@/components/ui/ServiceGrid'
import UploadSection from '@/components/ui/UploadSection'
import StatsCard from '@/components/ui/StatsCard'
import { ChatInterface } from '../components/chat/ChatInterface'

const mockStats = [
  {
    label: 'Total Services',
    value: '96',
    change: '+12%',
    changeType: 'positive' as const,
    icon: CpuChipIcon,
  },
  {
    label: 'API Endpoints',
    value: '1,288',
    change: '+156',
    changeType: 'positive' as const,
    icon: BeakerIcon,
  },
  {
    label: 'Tests Passed',
    value: '87%',
    change: '+5%',
    changeType: 'positive' as const,
    icon: CheckCircleIcon,
  },
  {
    label: 'Last Updated',
    value: '2 min ago',
    change: 'Active',
    changeType: 'neutral' as const,
    icon: ClockIcon,
  },
]

export default function Dashboard() {
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [isChatOpen, setIsChatOpen] = useState(false)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Service Discovery Dashboard
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Explore, test, and collaborate on API services with intelligent assistance
          </p>
        </div>
        
        {/* Chat Button */}
        <button
          onClick={() => setIsChatOpen(true)}
          className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          <ChatBubbleLeftRightIcon className="h-5 w-5" />
          <span>Ask AI Assistant</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {mockStats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <StatsCard {...stat} />
          </motion.div>
        ))}
      </div>

      {/* Upload Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <UploadSection />
      </motion.div>

      {/* Services Grid */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <ServiceGrid view={view} onViewChange={setView} />
      </motion.div>

      {/* Chat Interface */}
      <AnimatePresence>
        {isChatOpen && (
          <ChatInterface
            isOpen={isChatOpen}
            onClose={() => setIsChatOpen(false)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}