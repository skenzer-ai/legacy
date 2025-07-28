export interface ServiceOperation {
  operation_id: string
  path: string
  method: string
  summary?: string
  description?: string
  parameters?: Parameter[]
  request_body?: RequestBody
  responses?: Record<string, Response>
  tags?: string[]
}

export interface Parameter {
  name: string
  in: 'query' | 'path' | 'header' | 'cookie'
  required?: boolean
  schema?: Schema
  description?: string
}

export interface RequestBody {
  description?: string
  content?: Record<string, MediaType>
  required?: boolean
}

export interface Response {
  description: string
  content?: Record<string, MediaType>
}

export interface MediaType {
  schema?: Schema
}

export interface Schema {
  type?: string
  format?: string
  properties?: Record<string, Schema>
  items?: Schema
  required?: string[]
  example?: any
  enum?: any[]
}

export interface ServiceDefinition {
  service_name: string
  description?: string
  keywords: string[]
  synonyms: string[]
  business_context?: string
  tier1_operations: Record<string, ServiceOperation>
  tier2_operations: Record<string, ServiceOperation>
  validation_results?: ValidationResults
  last_updated?: string
  confidence_score: number
  needs_review: boolean
}

export interface ValidationResults {
  tested_operations: number
  successful_operations: number
  failed_operations: number
  schema_accuracy: number
  test_entities_created: number
  test_entities_cleaned: number
  last_validation: string
}

export interface ServiceSummary {
  service_name: string
  endpoint_count: number
  suggested_description: string
  tier1_operations: number
  tier2_operations: number
  confidence_score: number
  needs_review: boolean
  keywords: string[]
  synonyms: string[]
}

export interface ClassificationResponse {
  upload_id: string
  total_services: number
  services: ServiceSummary[]
  processing_time_ms: number
  classification_accuracy: number
}