import api from './api'
import { apiClient } from './api'
import { useAuthStore } from '../stores/authStore'

export interface GetUploadPresignedUrlRequest {
  conversation_id: number
  suffixes: string[]
}

export interface GetUploadPresignedUrlResponse {
  urls: string[]
}

export interface Message {
  message_id?: number | null
  role: string
  content: string | Record<string, unknown>[]
  timestamp?: string | null
}

export interface MessageListResponse {
  messages: Message[]
}

export interface SendMessageRequest {
  conversation_id: number
  messages: Message[]
  base_url: string
  model_name: string | null
  api_key: string | null
  params: object | null
}

export interface GenerateTitleRequest {
  conversation_id: number
  messages: Message[]
  base_url: string
  model_name: string | null
  api_key: string | null
  params: object | null
}

export interface GenerateTitleResponse {
  conversation_id: number
  title: string
  update_at: string
}

export interface ChatWebSocketRequest {
  type: string
  messages: Message[]
  base_url: string
  model_name: string | null
  encrypted_api_key: string | null
  params: object | null
}

// Get image upload presigned URL
export const getUploadPresignedUrl = async (
  data: GetUploadPresignedUrlRequest,
): Promise<string[]> => {
  const response = await api.post<GetUploadPresignedUrlResponse>(
    '/api/v1/chat/get_upload_presigned_url',
    data,
  )
  return response.data.urls
}

// Upload image to presigned URL
export const uploadImage = async (url: string, file: File): Promise<void> => {
  await api.put(url, file, {
    headers: {
      'Content-Type': file.type,
    },
  })
}

// Get message history
export const getMessages = async (conversationId: number): Promise<Message[]> => {
  const response = await api.get<MessageListResponse>(`/api/v1/chat/${conversationId}`)
  return response.data.messages
}

// Send message (streaming response)
export const sendMessage = async (
  data: SendMessageRequest,
  onChunk: (chunk: string) => void,
  onComplete: () => void,
  onError: (error: Error) => void,
  onUserMessageId?: (userMessageId: number) => void,
  signal?: AbortSignal,
): Promise<void> => {
  let token = useAuthStore.getState().accessToken
  
  const doSend = async (retryCount = 0): Promise<void> => {
    try {
      console.log('Sending message to:', '/api/v1/chat/send')
      console.log('Request data:', data)

      const response = await fetch('/api/api/v1/chat/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
        signal: signal,
      })

      if (response.status === 401 && retryCount === 0) {
        // Token expired, try to refresh
        console.log('Token expired, attempting to refresh...')
        try {
          const refreshToken = useAuthStore.getState().refreshToken
          if (!refreshToken) {
            throw new Error('No refresh token available')
          }
          
          const refreshResponse = await fetch('/api/api/v1/user/refresh', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          })
          
          if (!refreshResponse.ok) {
            throw new Error('Failed to refresh token')
          }
          
          const refreshData = await refreshResponse.json()
          useAuthStore.getState().setTokens(refreshData.access_token, refreshData.refresh_token)
          token = refreshData.access_token
          
          // Retry the request with new token
          return doSend(retryCount + 1)
        } catch (refreshError) {
          console.error('Failed to refresh token:', refreshError)
          useAuthStore.getState().logout()
          window.location.href = '/'
          throw new Error('Authentication failed')
        }
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      console.log('Response received, reading stream...')
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          console.log('Stream completed')
          onComplete()
          break
        }
        
        const chunk = decoder.decode(value, { stream: true })
        console.log('Chunk content:', chunk)
        buffer += chunk
        
        // Process lines (each line is a JSON object)
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep the last incomplete line in buffer
        
        for (const line of lines) {
          if (line.trim()) {
            try {
              const data = JSON.parse(line)
              console.log('Parsed data:', data)

              if (data.type === 'user_message_id' && data.user_message_id) {
                console.log('Received user message id:', data.user_message_id)
                // 通知调用者更新消息ID
                onUserMessageId?.(data.user_message_id)
              } else if (data.type === 'ai_chunk' && data.content) {
                console.log('Emitting chunk:', data.content)
                onChunk(data.content)
              } else if (data.type === 'complete') {
                console.log('Received complete signal, ai_message_id:', data.ai_message_id)
                onComplete()
                return
              } else if (data.type === 'error') {
                console.error('Received error from server:', data.detail)
                onError(new Error(data.detail || 'Server error'))
                return
              }
            } catch (e) {
              console.error('Failed to parse JSON:', line, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in sendMessage:', error)
      onError(error as Error)
    }
  }
  
  await doSend()
}

// Generate conversation title via chat service
export const generateTitle = async (
  data: GenerateTitleRequest,
): Promise<GenerateTitleResponse> => {
  const response = await api.post<GenerateTitleResponse>(
    '/api/v1/chat/generate_title',
    data,
  )
  return response.data
}

// WebSocket chat connection
export class ChatWebSocket {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3
  private reconnectDelay = 1000

  connect(
    conversationId: number,
    request: ChatWebSocketRequest,
    onMessage: (chunk: string) => void,
    onError: (error: Event) => void,
    onClose: () => void,
  ) {
    const url = apiClient.getWebSocketUrl(`/api/api/v1/chat/ws/chat?conversation_id=${conversationId}`)
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      // Send chat request
      this.ws?.send(JSON.stringify(request))
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chunk') {
          onMessage(data.content)
        } else if (data.type === 'done') {
          onClose()
        }
      } catch (error) {
        // If not JSON, treat as text directly
        onMessage(event.data)
      }
    }

    this.ws.onerror = (error) => {
      onError(error)
    }

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        setTimeout(() => {
          this.connect(conversationId, request, onMessage, onError, onClose)
        }, this.reconnectDelay * this.reconnectAttempts)
      } else {
        onClose()
      }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  abort() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
}