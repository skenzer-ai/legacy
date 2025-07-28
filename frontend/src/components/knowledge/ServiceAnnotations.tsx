import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChatBubbleLeftEllipsisIcon,
  TagIcon,
  BookmarkIcon,
  PlusIcon,
  UserIcon,
  ClockIcon,
  PencilIcon,
  TrashIcon,
  CheckIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { ServiceSummary } from '../../types/service'

interface ServiceAnnotationsProps {
  service: ServiceSummary
}

interface Annotation {
  id: string
  type: 'note' | 'tag' | 'bookmark' | 'improvement'
  content: string
  author: string
  timestamp: Date
  likes: number
  replies?: Annotation[]
  category?: string
}

const mockAnnotations: Annotation[] = [
  {
    id: '1',
    type: 'note',
    content: 'This service handles all incident management operations. The bulk import endpoint is particularly useful for migrating from legacy systems.',
    author: 'Sarah Chen',
    timestamp: new Date('2024-01-20T10:30:00Z'),
    likes: 8,
    category: 'Usage Guidelines'
  },
  {
    id: '2',
    type: 'improvement',
    content: 'Consider adding pagination to the list endpoint - currently returns all records which can be slow for large datasets.',
    author: 'Mike Rodriguez',
    timestamp: new Date('2024-01-19T14:15:00Z'),
    likes: 12,
    category: 'Performance'
  },
  {
    id: '3',
    type: 'tag',
    content: 'frequently-used, critical, migration-ready',
    author: 'Admin',
    timestamp: new Date('2024-01-18T09:00:00Z'),
    likes: 5,
    category: 'Classification'
  }
]

export const ServiceAnnotations: React.FC<ServiceAnnotationsProps> = ({ service }) => {
  const [annotations, setAnnotations] = useState<Annotation[]>(mockAnnotations)
  const [isAdding, setIsAdding] = useState(false)
  const [newAnnotation, setNewAnnotation] = useState({
    type: 'note' as const,
    content: '',
    category: ''
  })
  const [editingId, setEditingId] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>('all')

  const getTypeIcon = (type: Annotation['type']) => {
    switch (type) {
      case 'note': return ChatBubbleLeftEllipsisIcon
      case 'tag': return TagIcon
      case 'bookmark': return BookmarkIcon
      case 'improvement': return PencilIcon
      default: return ChatBubbleLeftEllipsisIcon
    }
  }

  const getTypeColor = (type: Annotation['type']) => {
    switch (type) {
      case 'note': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400'
      case 'tag': return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400'
      case 'bookmark': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400'
      case 'improvement': return 'text-purple-600 bg-purple-100 dark:bg-purple-900/30 dark:text-purple-400'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30 dark:text-gray-400'
    }
  }

  const filteredAnnotations = annotations.filter(annotation => 
    filter === 'all' || annotation.type === filter
  )

  const addAnnotation = () => {
    if (!newAnnotation.content.trim()) return

    const annotation: Annotation = {
      id: Date.now().toString(),
      type: newAnnotation.type,
      content: newAnnotation.content,
      author: 'Current User',
      timestamp: new Date(),
      likes: 0,
      category: newAnnotation.category || 'General'
    }

    setAnnotations(prev => [annotation, ...prev])
    setNewAnnotation({ type: 'note', content: '', category: '' })
    setIsAdding(false)
  }

  const deleteAnnotation = (id: string) => {
    setAnnotations(prev => prev.filter(ann => ann.id !== id))
  }

  const likeAnnotation = (id: string) => {
    setAnnotations(prev => prev.map(ann => 
      ann.id === id ? { ...ann, likes: ann.likes + 1 } : ann
    ))
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Knowledge Base</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Community annotations and insights for {service.service_name}
          </p>
        </div>
        <button
          onClick={() => setIsAdding(true)}
          className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          <span>Add Annotation</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-2">
        {['all', 'note', 'tag', 'bookmark', 'improvement'].map((filterType) => (
          <button
            key={filterType}
            onClick={() => setFilter(filterType)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              filter === filterType
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            {filterType === 'all' ? 'All' : filterType.charAt(0).toUpperCase() + filterType.slice(1)}
          </button>
        ))}
      </div>

      {/* Add New Annotation */}
      <AnimatePresence>
        {isAdding && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
          >
            <div className="space-y-4">
              <div className="flex items-center space-x-4">
                <select
                  value={newAnnotation.type}
                  onChange={(e) => setNewAnnotation(prev => ({ ...prev, type: e.target.value as any }))}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                  <option value="note">Note</option>
                  <option value="tag">Tag</option>
                  <option value="bookmark">Bookmark</option>
                  <option value="improvement">Improvement</option>
                </select>
                <input
                  type="text"
                  placeholder="Category (optional)"
                  value={newAnnotation.category}
                  onChange={(e) => setNewAnnotation(prev => ({ ...prev, category: e.target.value }))}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
              </div>
              <textarea
                placeholder="Add your annotation..."
                value={newAnnotation.content}
                onChange={(e) => setNewAnnotation(prev => ({ ...prev, content: e.target.value }))}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              />
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setIsAdding(false)}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  <XMarkIcon className="h-4 w-4 inline mr-1" />
                  Cancel
                </button>
                <button
                  onClick={addAnnotation}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <CheckIcon className="h-4 w-4 inline mr-1" />
                  Add
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Annotations List */}
      <div className="space-y-4">
        {filteredAnnotations.map((annotation, index) => {
          const TypeIcon = getTypeIcon(annotation.type)
          
          return (
            <motion.div
              key={annotation.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6"
            >
              <div className="flex items-start space-x-4">
                <div className={`p-2 rounded-lg ${getTypeColor(annotation.type)}`}>
                  <TypeIcon className="h-4 w-4" />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <span className="font-medium text-gray-900 dark:text-white">
                        {annotation.author}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center space-x-1">
                        <ClockIcon className="h-3 w-3" />
                        <span>{annotation.timestamp.toLocaleDateString()}</span>
                      </span>
                      {annotation.category && (
                        <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs">
                          {annotation.category}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => likeAnnotation(annotation.id)}
                        className="text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400 text-sm"
                      >
                        ❤️ {annotation.likes}
                      </button>
                      <button
                        onClick={() => deleteAnnotation(annotation.id)}
                        className="text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                    {annotation.content}
                  </p>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Empty State */}
      {filteredAnnotations.length === 0 && (
        <div className="text-center py-12">
          <ChatBubbleLeftEllipsisIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No annotations found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            {filter === 'all' 
              ? 'Be the first to add knowledge about this service!'
              : `No ${filter} annotations found. Try a different filter.`
            }
          </p>
          <button
            onClick={() => setIsAdding(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Add First Annotation
          </button>
        </div>
      )}

      {/* Summary Stats */}
      <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {annotations.length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Total Annotations</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {annotations.reduce((sum, ann) => sum + ann.likes, 0)}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Total Likes</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {new Set(annotations.map(ann => ann.author)).size}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Contributors</div>
          </div>
          <div>
            <div className="text-lg font-bold text-gray-900 dark:text-white">
              {annotations.filter(ann => ann.type === 'improvement').length}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Improvements</div>
          </div>
        </div>
      </div>
    </div>
  )
}