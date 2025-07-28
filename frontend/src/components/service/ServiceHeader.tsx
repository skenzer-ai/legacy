import React, { useState } from 'react'
import { motion } from 'framer-motion'
import {
  ArrowLeftIcon,
  StarIcon,
  ExclamationTriangleIcon,
  CpuChipIcon,
  BeakerIcon,
  ChatBubbleLeftRightIcon,
  ShareIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import { ServiceSummary } from '../../types/service'
import { cn } from '../../utils/cn'
import { ChatInterface } from '../chat/ChatInterface'
import { ServiceContext } from '../../types/chat'

interface ServiceHeaderProps {
  service: ServiceSummary
}

export const ServiceHeader: React.FC<ServiceHeaderProps> = ({ service }) => {
  const [isChatOpen, setIsChatOpen] = useState(false)

  const serviceContext: ServiceContext = {
    service_name: service.service_name
  }

  return (
    <>
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Breadcrumb */}
          <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400 mb-6">
            <Link to="/" className="hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
              Dashboard
            </Link>
            <span>/</span>
            <span className="text-gray-900 dark:text-gray-100">{service.service_name}</span>
          </div>

          <div className="flex items-start justify-between">
            <div className="flex-1">
              {/* Service Title */}
              <div className="flex items-center space-x-4 mb-4">
                <Link
                  to="/"
                  className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <ArrowLeftIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                </Link>
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
                    <span>{service.service_name}</span>
                    {service.needs_review && (
                      <ExclamationTriangleIcon className="h-6 w-6 text-yellow-500" />
                    )}
                  </h1>
                  <p className="text-lg text-gray-600 dark:text-gray-400 mt-2">
                    {service.suggested_description}
                  </p>
                </div>
              </div>

              {/* Service Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                      <CpuChipIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                        {service.endpoint_count}
                      </p>
                      <p className="text-sm text-blue-700 dark:text-blue-300">
                        Total Endpoints
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                      <BeakerIcon className="h-6 w-6 text-green-600 dark:text-green-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                        {service.tier1_operations}
                      </p>
                      <p className="text-sm text-green-700 dark:text-green-300">
                        CRUD Operations
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-xl p-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                      <BeakerIcon className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                        {service.tier2_operations}
                      </p>
                      <p className="text-sm text-purple-700 dark:text-purple-300">
                        Advanced Ops
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
                      <StarIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-yellow-900 dark:text-yellow-100">
                        {(service.confidence_score * 100).toFixed(0)}%
                      </p>
                      <p className="text-sm text-yellow-700 dark:text-yellow-300">
                        Confidence
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Keywords */}
              <div className="flex flex-wrap gap-2">
                {service.keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-3 py-1 rounded-full text-sm"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-3 ml-8">
              <button
                onClick={() => setIsChatOpen(true)}
                className="flex items-center space-x-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl"
              >
                <ChatBubbleLeftRightIcon className="h-5 w-5" />
                <span>Ask AI about this service</span>
              </button>

              <button className="p-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <ShareIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>

              <button className="p-3 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                <BookmarkIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>
          </div>

          {/* Confidence Bar */}
          <div className="mt-6 flex items-center space-x-3">
            <span className="text-sm text-gray-600 dark:text-gray-400 min-w-0">
              Classification Confidence:
            </span>
            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className={cn(
                  'h-2 rounded-full transition-all duration-500',
                  service.confidence_score >= 0.9
                    ? 'bg-green-500'
                    : service.confidence_score >= 0.7
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
                )}
                style={{ width: `${service.confidence_score * 100}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 min-w-0">
              {(service.confidence_score * 100).toFixed(1)}%
            </span>
          </div>
        </div>
      </div>

      {/* Chat Interface */}
      {isChatOpen && (
        <ChatInterface
          isOpen={isChatOpen}
          onClose={() => setIsChatOpen(false)}
          serviceContext={serviceContext}
        />
      )}
    </>
  )
}