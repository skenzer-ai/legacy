import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import {
  CloudArrowUpIcon,
  DocumentIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'
import { cn } from '@/utils/cn'
import toast from 'react-hot-toast'

interface UploadSectionProps {
  onUploadComplete?: (uploadId: string) => void
}

export default function UploadSection({ onUploadComplete }: UploadSectionProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileUpload(files[0])
    }
  }

  const handleFileUpload = async (file: File) => {
    // Validate file type
    if (!file.name.endsWith('.json') && !file.name.endsWith('.yaml') && !file.name.endsWith('.yml')) {
      toast.error('Please upload a JSON or YAML file')
      return
    }

    setUploadStatus('uploading')
    setUploadProgress(0)

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + Math.random() * 20
        })
      }, 200)

      // TODO: Replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      clearInterval(progressInterval)
      setUploadProgress(100)
      setUploadStatus('success')
      
      toast.success('API specification uploaded successfully!')
      
      // Mock upload ID for demo
      const mockUploadId = `upload_${Date.now()}`
      onUploadComplete?.(mockUploadId)
      
    } catch (error) {
      setUploadStatus('error')
      toast.error('Upload failed. Please try again.')
    }
  }

  const openFileDialog = () => {
    fileInputRef.current?.click()
  }

  return (
    <div className="card p-8">
      <div className="text-center mb-6">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          Upload API Specification
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Upload your OpenAPI specification to start discovering and testing services
        </p>
      </div>

      <div
        className={cn(
          'relative border-2 border-dashed rounded-xl p-12 transition-all duration-200',
          isDragging
            ? 'border-primary-400 bg-primary-50 dark:bg-primary-900/10'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500',
          uploadStatus === 'uploading' && 'pointer-events-none',
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".json,.yaml,.yml"
          onChange={handleFileSelect}
        />

        <div className="text-center">
          {uploadStatus === 'idle' && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Drop your API specification here
              </p>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                or{' '}
                <button
                  onClick={openFileDialog}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  browse to upload
                </button>
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-500">
                Supports JSON and YAML formats
              </p>
            </motion.div>
          )}

          {uploadStatus === 'uploading' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <div className="loading-spinner w-12 h-12 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Uploading and processing...
              </p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {Math.round(uploadProgress)}% complete
              </p>
            </motion.div>
          )}

          {uploadStatus === 'success' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <CheckCircleIcon className="mx-auto h-12 w-12 text-green-500 mb-4" />
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Upload successful!
              </p>
              <p className="text-gray-600 dark:text-gray-400">
                Your API specification has been processed and services are being classified
              </p>
            </motion.div>
          )}

          {uploadStatus === 'error' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <ExclamationCircleIcon className="mx-auto h-12 w-12 text-red-500 mb-4" />
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Upload failed
              </p>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Something went wrong. Please try again.
              </p>
              <button
                onClick={() => setUploadStatus('idle')}
                className="btn-primary"
              >
                Try Again
              </button>
            </motion.div>
          )}
        </div>
      </div>

      {uploadStatus === 'idle' && (
        <div className="mt-6 flex items-center justify-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
          <div className="flex items-center">
            <DocumentIcon className="w-4 h-4 mr-1" />
            OpenAPI 3.0+
          </div>
          <div className="flex items-center">
            <DocumentIcon className="w-4 h-4 mr-1" />
            JSON/YAML
          </div>
          <div className="flex items-center">
            <CloudArrowUpIcon className="w-4 h-4 mr-1" />
            Max 50MB
          </div>
        </div>
      )}
    </div>
  )
}