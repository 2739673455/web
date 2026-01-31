import api from './api'

export interface ModelConfig {
  config_id: number
  name: string | null
  base_url: string
  model_name: string | null
  api_key: string | null
}

export interface ModelConfigListResponse {
  configs: ModelConfig[]
}

export interface CanCreateRequest {
  config_count: number
}

export interface CanCreateResponse {
  can_create: boolean
  limit: number
}

export interface CreateConfigRequest {
  name: string | null
  base_url: string
  model_name: string | null
  api_key: string | null
  params: object | null
}

export interface UpdateConfigRequest {
  config_id: number
  name: string | null
  base_url: string
  model_name: string | null
  api_key: string | null
  params: object | null
}

export interface DeleteConfigsRequest {
  ids: number[]
}

// Get model config list
export const getModelConfigs = async (): Promise<ModelConfig[]> => {
  const response = await api.get<ModelConfigListResponse>('/api/v1/model_config')
  return response.data.configs
}

// Check if new config can be created
export const canCreateConfig = async (
  data: CanCreateRequest,
): Promise<CanCreateResponse> => {
  const response = await api.post<CanCreateResponse>('/api/v1/model_config/can_create', data)
  return response.data
}

// Create model config
export const createModelConfig = async (data: CreateConfigRequest): Promise<ModelConfig> => {
  const response = await api.post<ModelConfig>('/api/v1/model_config/create', data)
  // Backend returns api_key as null, use user input api_key
  return {
    ...response.data,
    api_key: data.api_key,
  }
}

// Update model config
export const updateModelConfig = async (data: UpdateConfigRequest): Promise<void> => {
  await api.post('/api/v1/model_config/update', data)
}

// Batch delete model configs
export const deleteModelConfigs = async (data: DeleteConfigsRequest): Promise<void> => {
  await api.post('/api/v1/model_config/delete', data)
}