import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiService, type Service } from '../services/api'

export const useServices = () => {
  return useQuery({
    queryKey: ['services'],
    queryFn: () => apiService.getServices(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  })
}

export const useService = (serviceName: string) => {
  return useQuery({
    queryKey: ['service', serviceName],
    queryFn: () => apiService.getService(serviceName),
    enabled: !!serviceName,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })
}

export const useUploadApiSpec = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (file: File) => apiService.uploadApiSpec(file),
    onSuccess: () => {
      // Invalidate and refetch services after successful upload
      queryClient.invalidateQueries({ queryKey: ['services'] })
    },
  })
}

export const useUploadStatus = (uploadId: string | null) => {
  return useQuery({
    queryKey: ['upload-status', uploadId],
    queryFn: () => uploadId ? apiService.getUploadStatus(uploadId) : null,
    enabled: !!uploadId,
    refetchInterval: 2000, // Poll every 2 seconds
    refetchOnWindowFocus: false,
  })
}