import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChatStore } from '../stores/chatStore'
import { useConversationStore } from '../stores/conversationStore'
import { useModelConfigStore } from '../stores/modelConfigStore'
import { useAuthStore } from '../stores/authStore'
import { sendMessage, getUploadPresignedUrl, generateTitle, Message } from '../services/chat'
import { createConversation, updateConversation } from '../services/conversation'
import { deleteModelConfigs } from '../services/modelConfig'
import { showToast } from './Toast'

// 全局错误消息，用于重试
// let lastErrorMessage = ''

interface ChatInputProps {
  onShowLogin: () => void
}

// 全局锁，防止并发创建对话
let isCreatingConversation = false

// 将base64转换为Blob
function base64ToBlob(base64: string, mimeType = 'image/jpeg'): Blob {
  const byteCharacters = atob(base64)
      const byteArrays: BlobPart[] = []
      
      for (let offset = 0; offset < byteCharacters.length; offset += 512) {
        const slice = byteCharacters.slice(offset, offset + 512)
        const byteNumbers = new Array(slice.length)
        for (let i = 0; i < slice.length; i++) {
          byteNumbers[i] = slice.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        byteArrays.push(byteArray)
      }
      
      return new Blob(byteArrays, { type: mimeType })}

// 将消息中的 base64 图片转换为 COS URL
async function convertImagesToCos(messages: any[], conversationId: number) {
  const convertedMessages: any[] = []
  
  for (const message of messages) {
    if (Array.isArray(message.content)) {
      const items: any[] = []
      let hasImage = false
      
      for (const item of message.content) {
        if (item.type === 'image_url' && typeof item.image_url === 'string' && item.image_url.startsWith('data:')) {
          // base64 图片，需要上传到 COS
          hasImage = true
          // 提取文件类型
          const match = item.image_url.match(/data:image\/(\w+);/)
          const mimeType = match ? `image/${match[1]}` : 'image/jpeg'
          const suffix = match ? match[1] : 'jpg'
          
          try {
            // 获取预签名上传 URL
            const uploadUrls = await getUploadPresignedUrl({ conversation_id: conversationId, suffixes: [suffix] })
            const uploadUrl = uploadUrls[0]
            const cosUrl = uploadUrl.split('?')[0]
            
            // 上传图片
            const base64Data = item.image_url.split(',')[1]
            const blob = base64ToBlob(base64Data, mimeType)
            
            await fetch(uploadUrl, {
              method: 'PUT',
              body: blob,
              headers: {
                'Content-Type': blob.type,
              },
            })
            
            items.push({ type: 'image_url', image_url: cosUrl })
          } catch (error) {
            console.error('Failed to upload image:', error)
            // 上传失败，保留原始图片 URL
            items.push(item)
          }
        } else {
          items.push(item)
        }
      }
      
      if (hasImage) {
        convertedMessages.push({
          ...message,
          content: items,
        })
        console.log('[convertImagesToCos] Converted message with image, message_id:', message.message_id)
      } else {
        convertedMessages.push(message)
        console.log('[convertImagesToCos] Kept original message, message_id:', message.message_id)
      }
    } else {
      convertedMessages.push(message)
    }
  }
  
  return convertedMessages
}

export default function ChatInput({ onShowLogin }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [isAborting, setIsAborting] = useState(false)
  const [showConfigPopup, setShowConfigPopup] = useState(false)
  // const [lastSentMessage, setLastSentMessage] = useState('')
  const [attachedImages, setAttachedImages] = useState<Array<{ displayUrl: string; cosUrl: string }>>([])
  const abortControllerRef = useRef<AbortController | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const configPopupRef = useRef<HTMLDivElement>(null)
  const configButtonContainerRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { messages, setMessages, appendToAssistantMessage, completeCurrentAssistantMessage, resetCurrentAssistantMessage, setHasError, setErrorMessage } = useChatStore()
  const { currentConversationId, setCurrentConversationId, setIsNewConversation } = useConversationStore()
  const { selectedConfigId, configs, setSelectedConfigId } = useModelConfigStore()
  const { accessToken } = useAuthStore()

  const selectedConfig = configs.find((c) => c.config_id === selectedConfigId)

  // Close model config popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node
      if (configPopupRef.current && !configPopupRef.current.contains(target) &&
          configButtonContainerRef.current && !configButtonContainerRef.current.contains(target)) {
        setShowConfigPopup(false)
      }
    }

    if (showConfigPopup) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => {
        document.removeEventListener('mousedown', handleClickOutside)
      }
    }
  }, [showConfigPopup])

  // 当切换对话时，清空附件图片
  useEffect(() => {
    setAttachedImages([])
  }, [currentConversationId])

  const handleSend = async () => {
    if (!message.trim() || loading) return

    if (!accessToken) {
      onShowLogin()
      return
    }

    if (configs.length === 0) {
      showToast('请先创建模型配置', 'info')
      return
    }

    // Auto-select first config if none selected
    if (!selectedConfig) {
      setSelectedConfigId(configs[0].config_id)
    }

    setLoading(true)
    setIsAborting(false)
    setHasError(false)

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController()

    try {
      let conversationId = currentConversationId
      let isNewConversationCreated = false

      // If no conversation is selected or it's a new conversation, create one
      if (conversationId === null) {
        if (isCreatingConversation) {
          console.log('[handleSend] Conversation creation in progress, waiting...')
          // 等待创建完成
          while (isCreatingConversation) {
            await new Promise(resolve => setTimeout(resolve, 100))
          }
          conversationId = currentConversationId
          console.log('[handleSend] Using conversation ID after waiting:', conversationId)
        } else {
          console.log('[handleSend] Creating new conversation...')
          isCreatingConversation = true
          try {
            const newConversation = await createConversation({ model_config_id: selectedConfigId! })
            console.log('[handleSend] createConversation returned:', newConversation)
            console.log('[handleSend] conversation_id field:', newConversation.conversation_id)
            console.log('[handleSend] id field:', (newConversation as any).id)
            // 兼容处理：如果 conversation_id 为 undefined，尝试使用 id
            conversationId = newConversation.conversation_id || (newConversation as any).id
            isNewConversationCreated = true
            console.log('[handleSend] New conversation created with ID:', conversationId)
            if (!conversationId) {
              throw new Error('Failed to get conversation ID from response')
            }
            setCurrentConversationId(conversationId)
            setIsNewConversation(false)
          } finally {
            isCreatingConversation = false
          }
        }
      } else {
        console.log('[handleSend] Using existing conversation ID:', conversationId)
      }

      // 如果有附件图片，上传到COS
      if (attachedImages.length > 0) {
        if (!conversationId) {
          throw new Error('No conversation ID available for image upload')
        }
        console.log('[handleSend] Uploading images to COS for conversation:', conversationId)
        const suffixes = attachedImages.map((_, index) => {
          // 从base64 URL中提取文件扩展名
          const match = attachedImages[index].displayUrl.match(/data:image\/(\w+);/)
          return match ? match[1] : 'png'
        })
        
        const uploadUrls = await getUploadPresignedUrl({ conversation_id: conversationId!, suffixes })
        
        // 上传每个图片
        for (let i = 0; i < attachedImages.length; i++) {
          const uploadUrl = uploadUrls[i]
          const cosUrl = uploadUrl.split('?')[0]
          
          // 从base64 URL中提取原始数据
          const base64Data = attachedImages[i].displayUrl.split(',')[1]
          const blob = base64ToBlob(base64Data)
          
          await fetch(uploadUrl, {
            method: 'PUT',
            body: blob,
            headers: {
              'Content-Type': blob.type,
            },
          })
          
          // 更新attachedImages中的cosUrl
          attachedImages[i].cosUrl = cosUrl
          console.log('[handleSend] Image uploaded:', cosUrl)
        }
      }

      // 构建用户消息内容
      let messageContent: string | Array<{ type: string; text?: string; image_url?: string }> = ''
      let displayMessageContent: string | Array<{ type: string; text?: string; image_url?: string }> = ''
      
      if (attachedImages.length > 0) {
        // 如果有图片，使用字典列表格式，使用 cosUrl 发送到后端
        messageContent = [
          { type: 'text', text: message },
          ...attachedImages.map((img: { displayUrl: string; cosUrl: string }) => ({ type: 'image_url', image_url: img.cosUrl }))
        ]
        // 用于显示的消息内容，使用 displayUrl
        displayMessageContent = [
          { type: 'text', text: message },
          ...attachedImages.map((img: { displayUrl: string; cosUrl: string }) => ({ type: 'image_url', image_url: img.displayUrl }))
        ]
      } else {
        // 没有图片，使用纯文本格式
        messageContent = message
        displayMessageContent = message
      }

      const userMessage = {
        role: 'user',
        content: displayMessageContent, // 使用显示版本（包含 base64）
      }

      setMessages([...messages, userMessage])
      // setLastSentMessage(message)
      setMessage('')
      setAttachedImages([]) // 清空附件图片

      // 创建发送到后端的消息（使用 COS URL）
      const userMessageForBackend = {
        role: 'user',
        content: messageContent, // 使用后端版本（包含 COS URL）
      }

      const messagesWithoutTimestamp = messages.map((m) => ({
        message_id: m.message_id,
        role: m.role,
        content: m.content,
      }))

      const currentConfig = configs.find((c) => c.config_id === selectedConfigId) || configs[0]

      // 同时发送消息和生成标题（如果是新对话）
      const [sendMessagePromise] = isNewConversationCreated
        ? [
            sendMessage(
              {
                conversation_id: conversationId!,
                messages: [...messagesWithoutTimestamp, userMessageForBackend], // 使用后端版本的消息
                base_url: currentConfig.base_url || '',
                model_name: currentConfig.model_name,
                api_key: currentConfig.api_key ?? null,
                params: null,
              },
              (chunk) => {
                console.log('Received chunk:', chunk)
                appendToAssistantMessage(chunk)
              },
              () => {
                completeCurrentAssistantMessage()
                setLoading(false)
                setIsAborting(false)
                abortControllerRef.current = null
              },
              (error) => {
                console.error('Failed to send message:', error)
                if (error.name !== 'AbortError') {
                  setHasError(true)
                  setErrorMessage(error.message || '发送消息失败')
                  
                  showToast(error.message || '发送消息失败', 'error', 5000)
                }
                setLoading(false)
                setIsAborting(false)
                abortControllerRef.current = null
              },
              (userMessageId) => {
                console.log('[handleSend] Received user_message_id:', userMessageId)
                // 更新最后一条用户消息的 message_id
                setMessages((prevMessages: Message[]) => {
                  const updatedMessages = [...prevMessages]
                  if (updatedMessages.length > 0) {
                    updatedMessages[updatedMessages.length - 1] = {
                      ...updatedMessages[updatedMessages.length - 1],
                      message_id: userMessageId,
                    }
                  }
                  return updatedMessages
                })
              },
              abortControllerRef.current.signal
            ),
            generateTitle({
              conversation_id: conversationId!,
              messages: [...messagesWithoutTimestamp, userMessageForBackend],
              base_url: currentConfig.base_url || '',
              model_name: currentConfig.model_name,
              api_key: currentConfig.api_key ?? null,
              params: null,
            }).then((titleResult) => {
              console.log('[chat/generate_title] Title generated:', titleResult.title)
              // 第二步：调用conversation/update更新标题
              return updateConversation({
                conversation_id: conversationId!,
                title: titleResult.title
              }).then(() => {
                console.log('[conversation/update] Title updated successfully')
                // 更新对话列表中的标题，或添加新对话
                const { conversations, updateConversation: updateConversationStore } = useConversationStore.getState()
                const updatedConversation = conversations.find(c => c.conversation_id === conversationId)
                if (updatedConversation) {
                  console.log('[generateTitle] Updating existing conversation')
                  updateConversationStore({ ...updatedConversation, title: titleResult.title })
                } else {
                  console.log('[generateTitle] Adding new conversation to list')
                  // 如果对话不在列表中，添加新对话
                  useConversationStore.getState().addConversation({
                    conversation_id: conversationId!,
                    title: titleResult.title,
                    update_at: titleResult.update_at,
                    model_config_id: selectedConfigId!,
                  })
                }
              })
            }).catch((err) => {
              console.error('Failed to generate or update title:', err)
            })
          ]
        : [
            sendMessage(
              {
                conversation_id: conversationId!,
                messages: [...messagesWithoutTimestamp, userMessageForBackend], // 使用后端版本的消息
                base_url: currentConfig.base_url || '',
                model_name: currentConfig.model_name,
                api_key: currentConfig.api_key ?? null,
                params: null,
              },
              (chunk) => {
                console.log('Received chunk:', chunk)
                appendToAssistantMessage(chunk)
              },
              () => {
                completeCurrentAssistantMessage()
                setLoading(false)
                setIsAborting(false)
                abortControllerRef.current = null
              },
              (error) => {
                console.error('Failed to send message:', error)
                if (error.name !== 'AbortError') {
                  setHasError(true)
                  setErrorMessage(error.message || '发送消息失败')
                  
                  showToast(error.message || '发送消息失败', 'error', 5000)
                }
                setLoading(false)
                setIsAborting(false)
                abortControllerRef.current = null
              },
              (userMessageId) => {
                console.log('[handleSend] Received user_message_id (existing conversation):', userMessageId)
                // 更新最后一条用户消息的 message_id
                setMessages((prevMessages: Message[]) => {
                  const updatedMessages = [...prevMessages]
                  if (updatedMessages.length > 0) {
                    updatedMessages[updatedMessages.length - 1] = {
                      ...updatedMessages[updatedMessages.length - 1],
                      message_id: userMessageId,
                    }
                  }
                  return updatedMessages
                })
              },
              abortControllerRef.current.signal
            )
          ]

      await sendMessagePromise
    } catch (err: any) {
      console.error('Failed to send message:', err)
      if (err.name !== 'AbortError') {
        const errorDetail = err.response?.data?.detail
        let errorMessage = 'Failed to send message'
        if (Array.isArray(errorDetail)) {
          const firstError = errorDetail[0]
          if (firstError && firstError.msg) {
            errorMessage = firstError.msg.replace('Value error, ', '')
          }
        } else if (typeof errorDetail === 'object' && errorDetail.msg) {
          errorMessage = errorDetail.msg.replace('Value error, ', '')
        } else if (typeof errorDetail === 'string') {
          errorMessage = errorDetail.replace('Value error, ', '')
        }
        appendToAssistantMessage(`Error: ${errorMessage}`)
      }
      setLoading(false)
      setIsAborting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!accessToken) {
      onShowLogin()
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    if (configs.length === 0) {
      showToast('请先创建模型配置', 'info')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    // Auto-select first config if none selected
    if (!selectedConfig) {
      setSelectedConfigId(configs[0].config_id)
    }

    try {
      console.log('[handleFileSelect] Processing image file...')
      
      // 将文件转换为 base64 用于前端显示
      const reader = new FileReader()
      reader.onload = () => {
        const base64Url = reader.result as string
        console.log('[handleFileSelect] Image converted to base64, storing locally')
        
        // 只保存base64 URL，等发送消息时再上传到COS
        setAttachedImages(prev => [...prev, { displayUrl: base64Url, cosUrl: '' }])
      }
      reader.readAsDataURL(file)
    } catch (err) {
      console.error('Failed to process image:', err)
      showToast('图片处理失败', 'error')
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Handle retry when error button is clicked
  useEffect(() => {
    const handleRetry = () => {
      // 直接使用消息列表重试
      retryCurrentConversation()
    }

    window.addEventListener('retryMessage', handleRetry)

    return () => {
      window.removeEventListener('retryMessage', handleRetry)
    }
  }, [])

  // 重试当前对话
  const retryCurrentConversation = async () => {
    // 从 store 获取最新值
    const currentConversationId = useConversationStore.getState().currentConversationId
    const accessToken = useAuthStore.getState().accessToken
    const selectedConfigId = useModelConfigStore.getState().selectedConfigId
    const configs = useModelConfigStore.getState().configs
    const messages = useChatStore.getState().messages

    if (!currentConversationId || !accessToken) return

    setLoading(true)
    setIsAborting(false)
    setHasError(false)
    // setLastSentMessage('')

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController()

    try {
      const currentConfig = configs.find((c) => c.config_id === selectedConfigId) || configs[0]

      // 获取消息列表，排除最后一条失败的 AI 消息
      // 检查最后一条消息的角色，只有当是 assistant 时才移除
      let messagesWithoutLastAI = [...messages]
      if (messages.length > 0 && messages[messages.length - 1].role === 'assistant') {
        messagesWithoutLastAI = messages.slice(0, -1)
      }

      // 过滤掉没有 message_id 的用户消息（这些是发送失败后重复添加的）
      messagesWithoutLastAI = messagesWithoutLastAI.filter(m => m.message_id !== undefined)

      // 更新消息列表，移除无效消息
      setMessages(messagesWithoutLastAI)

      // 将消息中的 base64 图片转换为 COS URL
      const messagesWithCosUrls = await convertImagesToCos(messagesWithoutLastAI, currentConversationId)

      const messagesWithoutTimestamp = messagesWithCosUrls.map((m) => ({
        message_id: m.message_id,
        role: m.role,
        content: m.content,
      }))

      // 重新发送消息
      await sendMessage(
        {
          conversation_id: currentConversationId,
          messages: messagesWithoutTimestamp,
          base_url: currentConfig.base_url || '',
          model_name: currentConfig.model_name,
          api_key: currentConfig.api_key ?? null,
          params: null,
        },
        (chunk) => {
          console.log('Received chunk:', chunk)
          appendToAssistantMessage(chunk)
        },
        () => {
          completeCurrentAssistantMessage()
          setLoading(false)
          setIsAborting(false)
          abortControllerRef.current = null
        },
        (error) => {
          console.error('Failed to retry message:', error)
          if (error.name !== 'AbortError') {
            setHasError(true)
            showToast(error.message || '重试失败', 'error', 5000)
          }
          setLoading(false)
          setIsAborting(false)
          abortControllerRef.current = null
        },
        (userMessageId) => {
          console.log('[retryCurrentConversation] Received user_message_id:', userMessageId)
          // 更新最后一条用户消息的 message_id
          setMessages((prevMessages: Message[]) => {
            const updatedMessages = [...prevMessages]
            if (updatedMessages.length > 0) {
              updatedMessages[updatedMessages.length - 1] = {
                ...updatedMessages[updatedMessages.length - 1],
                message_id: userMessageId,
              }
            }
            return updatedMessages
          })
        },
        abortControllerRef.current.signal
      )
    } catch (err: any) {
      console.error('Failed to retry:', err)
      showToast(err.message || '重试失败', 'error', 5000)
      setLoading(false)
      setIsAborting(false)
    }
  }

  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsAborting(true)
    resetCurrentAssistantMessage()
    setLoading(false)
  }

  const handleConfigSelect = async (configId: number) => {
    if (!accessToken) {
      onShowLogin()
      return
    }
    setSelectedConfigId(configId)
    setShowConfigPopup(false)

    // 如果有选中的对话，更新对话的 model_config_id
    if (currentConversationId) {
      try {
        await updateConversation({
          conversation_id: currentConversationId,
          model_config_id: configId,
        })
        // 更新前端 store 中的 model_config_id
        const { conversations, updateConversation: updateConversationStore } = useConversationStore.getState()
        const updatedConversation = conversations.find(c => c.conversation_id === currentConversationId)
        if (updatedConversation) {
          updateConversationStore({ ...updatedConversation, model_config_id: configId })
        }
      } catch (err) {
        console.error('Failed to update conversation model config:', err)
      }
    }
  }

  const handleEditConfig = (config: any) => {
    if (!accessToken) {
      onShowLogin()
      return
    }
    setShowConfigPopup(false)
    navigate('/model-config', {
      state: {
        editingConfig: config,
        conversationId: currentConversationId
      }
    })
  }

  const handleConfigDelete = async (configId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!accessToken) {
      onShowLogin()
      return
    }
    try {
      await deleteModelConfigs({ ids: [configId] })
      const newConfigs = configs.filter((c) => c.config_id !== configId)
      useModelConfigStore.getState().setConfigs(newConfigs)
      if (selectedConfigId === configId && newConfigs.length > 0) {
        setSelectedConfigId(newConfigs[0].config_id)
      }
    } catch (err) {
      console.error('Failed to delete config:', err)
      showToast('删除配置失败', 'error')
    }
  }

  const handleCreateConfig = () => {
    if (!accessToken) {
      onShowLogin()
      return
    }
    setShowConfigPopup(false)
    navigate('/model-config', {
      state: {
        conversationId: currentConversationId
      }
    })
  }

  return (
    <div className="p-4">
      {/* 输入框 */}
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full p-3 resize-none border border-mono"
        rows={3}
        disabled={loading}
      />

      {/* 已上传的图片预览 */}
      {attachedImages.length > 0 && (
        <div className="flex gap-2 mt-2 flex-wrap">
          {attachedImages.map((image, index) => (
            <div key={index} className="relative inline-block">
              <img
                src={image.displayUrl}
                alt={`Uploaded ${index + 1}`}
                className="h-16 w-16 object-cover rounded border border-mono"
              />
              <button
                onClick={() => setAttachedImages(prev => prev.filter((_, i) => i !== index))}
                className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-700"
                disabled={loading}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* 底部按钮栏 */}
      <div className="flex items-center justify-between mt-2">
        <div className="flex items-center gap-2 relative">
          {/* 模型配置按钮 */}
          <div className="relative" ref={configButtonContainerRef}>
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowConfigPopup(!showConfigPopup)
              }}
              className="py-1 px-3 transition-colors text-sm flex items-center gap-2 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)]"
            >
              <span className="truncate max-w-48">{selectedConfig?.name || selectedConfig?.model_name || 'Select Model'}</span>
            </button>

            {/* 配置列表弹窗 */}
            {showConfigPopup && (
              <div
                ref={configPopupRef}
                className="absolute bottom-full left-0 mb-2 min-w-fit max-w-xs border border-mono bg-[var(--color-bg)] max-h-96 overflow-y-auto"
                onMouseDown={(e) => e.stopPropagation()}
              >
                {configs.map((config) => (
                  <div
                    key={config.config_id}
                    onClick={() => handleConfigSelect(config.config_id)}
                    className="p-2 cursor-pointer flex items-center justify-between hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors group whitespace-nowrap"
                  >
                    <span className="truncate flex-1 max-w-48">{config.name || config.model_name}</span>
                    <div className="flex items-center gap-1 ml-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleEditConfig(config)
                        }}
                        className="p-1 hover:bg-[var(--color-bg)] hover:text-[var(--color-text)] transition-colors"
                        title="Edit"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => handleConfigDelete(config.config_id, e)}
                        className="p-1 text-red-700 hover:bg-red-700 hover:text-white transition-colors"
                        title="Delete"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
                <button
                  onClick={handleCreateConfig}
                  className="w-full p-2 text-center flex items-center justify-center gap-2 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors whitespace-nowrap"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  <span>Create New Config</span>
                </button>
              </div>
            )}
          </div>

          {/* 上传图片按钮 */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="py-1 px-2 border-0 transition-colors"
            disabled={loading}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* 发送/终止按钮 */}
        <button
          onClick={loading && !isAborting ? handleAbort : handleSend}
          disabled={!loading && !message.trim()}
          className="w-fit py-1 px-3 border-0 transition-colors disabled:opacity-50"
        >
          {loading && !isAborting ? 'Abort' : 'Send'}
        </button>
      </div>
    </div>
  )
}