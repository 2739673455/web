import api from './api'

export interface Conversation {
  conversation_id: number
  title: string | null
  update_at: string
  model_config_id: number | null
}

export interface ConversationListResponse {
  conversations: Conversation[]
}

export interface CreateConversationRequest {
  model_config_id: number
}

export interface UpdateConversationRequest {
  conversation_id: number
  model_config_id?: number
  title?: string
}

export interface GenerateTitleRequest {
  conversation_id: number
  messages: Message[]
  base_url: string
  model_name: string | null
  encrypted_api_key: string | null
  params: object | null
}

export interface GenerateTitleResponse {
  conversation_id: number
  title: string
  update_at: string
}

export interface DeleteConversationsRequest {
  ids: number[]
}

export interface Message {
  message_id: number | null
  role: string
  content: string | Record<string, unknown>[]
  timestamp?: string | null
}

// Get conversation list
export const getConversations = async (): Promise<Conversation[]> => {
  const response = await api.get<ConversationListResponse>('/api/v1/conversation')
  return response.data.conversations
}

// Create new conversation
export const createConversation = async (
  data: CreateConversationRequest,
): Promise<Conversation> => {
  const response = await api.post<Conversation>('/api/v1/conversation/create', data)
  return response.data
}

// Update conversation model config
export const updateConversation = async (
  data: UpdateConversationRequest,
): Promise<void> => {
  await api.post('/api/v1/conversation/update', data)
}

// Generate conversation title - now handled by chat service
// export const generateTitle = async (data: GenerateTitleRequest): Promise<Conversation> => {
//   const response = await api.post<GenerateTitleResponse>(
//     '/api/v1/conversation/generate_title',
//     data,
//   )
//   return response.data
// }

// Batch delete conversations
export const deleteConversations = async (data: DeleteConversationsRequest): Promise<void> => {
  await api.post('/api/v1/conversation/delete', data)
}