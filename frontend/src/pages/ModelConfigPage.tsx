import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  getModelConfigs,
  canCreateConfig,
  createModelConfig,
  updateModelConfig,
  deleteModelConfigs,
  type ModelConfig,
} from '../services/modelConfig'
import { useModelConfigStore } from '../stores/modelConfigStore'
import { useAuthStore } from '../stores/authStore'
import { showToast } from '../components/Toast'

export default function ModelConfigPage() {
  const [configs, setConfigs] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    base_url: '',
    model_name: '',
    api_key: '',
  })
  const [showApiKey, setShowApiKey] = useState(false)
  const [fromConversationId, setFromConversationId] = useState<number | null>(null)
  const navigate = useNavigate()
  const location = useLocation()
  const { setConfigs: setStoreConfigs } = useModelConfigStore()
  const { accessToken } = useAuthStore()

  useEffect(() => {
    if (!accessToken) {
      navigate('/')
      return
    }
    loadConfigs()
  }, [accessToken, navigate])

  // 处理从 ChatInput 传来的编辑状态
  useEffect(() => {
    if (location.state?.editingConfig) {
      setEditingConfig(location.state.editingConfig)
      setFormData({
        name: location.state.editingConfig.name || '',
        base_url: location.state.editingConfig.base_url,
        model_name: location.state.editingConfig.model_name || '',
        api_key: location.state.editingConfig.api_key || '',
      })
    }
    // 保存从对话页面跳转过来的 conversation_id
    if (location.state?.conversationId) {
      setFromConversationId(location.state.conversationId)
    }
  }, [location.state])

  const loadConfigs = async () => {
    try {
      const data = await getModelConfigs()
      setConfigs(data)
      setStoreConfigs(data)
    } catch (err) {
      console.error('Failed to load configs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingConfig) {
        // Only send api_key if user entered a new one
        const updateData: any = {
          config_id: editingConfig.config_id,
          name: formData.name || null,
          base_url: formData.base_url,
          model_name: formData.model_name || null,
          params: null,
        }
        if (formData.api_key) {
          updateData.api_key = formData.api_key
        }
        await updateModelConfig(updateData)
        // Update local state
        const updatedConfigs = configs.map((c) =>
          c.config_id === editingConfig.config_id
            ? {
                ...c,
                name: formData.name || null,
                base_url: formData.base_url,
                model_name: formData.model_name || null,
                api_key: formData.api_key || c.api_key,
              }
            : c
        )
        setConfigs(updatedConfigs)
        setStoreConfigs(updatedConfigs)
        setEditingConfig(null)
      } else {
        // Check if user can create new config
        const canCreateResult = await canCreateConfig({ config_count: configs.length })
        if (!canCreateResult.can_create) {
          showToast(`无法创建新配置，您最多只能创建 ${canCreateResult.limit} 个模型配置`, 'error')
          return
        }

        // Create new config and get response with config_id and name
        const response = await createModelConfig({
          name: formData.name || null,
          base_url: formData.base_url,
          model_name: formData.model_name || null,
          api_key: formData.api_key || null,
          params: null,
        })
        // Add new config to list, preserving user-entered model_name and api_key (backend returns None)
        const newConfig: ModelConfig = {
          config_id: response.config_id,
          name: response.name,
          base_url: response.base_url || formData.base_url,
          model_name: formData.model_name || null,
          api_key: formData.api_key || null,
        }
        const updatedConfigs = [...configs, newConfig]
        setConfigs(updatedConfigs)
        setStoreConfigs(updatedConfigs)
      }
      setFormData({ name: '', base_url: '', model_name: '', api_key: '' })
    } catch (err) {
      console.error('Failed to save config:', err)
      alert('Failed to save config')
    }
  }

  const handleEdit = (config: ModelConfig) => {
    setEditingConfig(config)
    setFormData({
      name: config.name || '',
      base_url: config.base_url,
      model_name: config.model_name || '',
      api_key: config.api_key || '',
    })
    setShowApiKey(false)
  }

  const handleDelete = async (configId: number) => {
    if (confirm('Delete this configuration?')) {
      try {
        await deleteModelConfigs({ ids: [configId] })
        // Update local state directly
        const updatedConfigs = configs.filter((c) => c.config_id !== configId)
        setConfigs(updatedConfigs)
        setStoreConfigs(updatedConfigs)
      } catch (err) {
        console.error('Failed to delete config:', err)
        alert('Failed to delete config')
      }
    }
  }

  const handleCancelEdit = () => {
    setEditingConfig(null)
    setFormData({ name: '', base_url: '', model_name: '', api_key: '' })
    setShowApiKey(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div>Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Model Configurations</h1>
          <button
            onClick={() => {
              if (fromConversationId) {
                window.dispatchEvent(new CustomEvent('restoreConversation', { detail: fromConversationId }))
              }
              navigate('/')
            }}
            className="py-1 px-2 border-0 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors inline-block"
          >
            Back to Chat
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mb-8 border border-mono p-6">
          <h2 className="text-lg font-bold mb-4">
            {editingConfig ? 'Edit Configuration' : 'Add New Configuration'}
          </h2>
          <div className="grid gap-4">
            <div>
              <label className="block text-sm mb-2">Name (optional)</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full p-2 border border-mono focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm mb-2">Base URL *</label>
              <input
                type="text"
                value={formData.base_url}
                onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                className="w-full p-2 border border-mono focus:outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-sm mb-2">Model Name (optional)</label>
              <input
                type="text"
                value={formData.model_name}
                onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                className="w-full p-2 border border-mono focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm mb-2">API Key (optional)</label>
              <div className="relative">
                <input
                  type={showApiKey ? 'text' : 'password'}
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full p-2 pr-10 border border-mono focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors"
                  title={showApiKey ? 'Hide' : 'Show'}
                >
                  {showApiKey ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              type="submit"
              className="py-1 px-2 border-0 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors inline-block"
            >
              {editingConfig ? 'Update' : 'Create'}
            </button>
            {editingConfig && (
              <button
                type="button"
                onClick={handleCancelEdit}
                className="py-1 px-2 border-0 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors inline-block"
              >
                Cancel
              </button>
            )}
          </div>
        </form>

        <div className="">
          <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,2fr)_minmax(0,1.5fr)_auto] gap-4 p-4 border-b font-bold" style={{ borderBottomColor: '#666' }}>
            <div>Name</div>
            <div>Base URL</div>
            <div>Model</div>
            <div className="text-right">Actions</div>
          </div>
          {configs.map((config) => (
            <div key={config.config_id} className="grid grid-cols-[minmax(0,1fr)_minmax(0,2fr)_minmax(0,1.5fr)_auto] gap-4 p-4 border-b" style={{ borderBottomColor: '#666' }}>
              <div className="truncate">{config.name || '-'}</div>
              <div className="truncate">{config.base_url}</div>
              <div className="truncate">{config.model_name || '-'}</div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => handleEdit(config)}
                  className="p-1 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors"
                  title="Edit"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  onClick={() => handleDelete(config.config_id)}
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
          {configs.length === 0 && (
            <div className="border-b" style={{ borderBottomColor: '#666' }}>
              <div className="p-8 text-center opacity-60">
                No configurations yet. Create one above.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
