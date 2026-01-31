import { useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { useConversationStore } from '../stores/conversationStore'
import { useModelConfigStore } from '../stores/modelConfigStore'
import { useChatStore } from '../stores/chatStore'
import { getCurrentUser, updateUsername, updateEmail, updatePassword, logout as logoutApi } from '../services/user'
import { useErrorHandler } from '../hooks/useErrorHandler'

/**
 * User profile modal component
 * Displays and allows editing of user information (username, email, password)
 */
export default function UserProfileModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { userInfo, setUserInfo, setTokens, logout } = useAuthStore()
  const { error, handleError, clearError } = useErrorHandler()
  const [success, setSuccess] = useState('')

  // Editing state
  const [editingField, setEditingField] = useState<'username' | 'email' | 'password' | null>(null)
  const [editValue, setEditValue] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  /**
   * Start editing a user field
   */
  const handleStartEdit = (field: 'username' | 'email' | 'password') => {
    setEditingField(field)
    setEditValue('')
    setConfirmPassword('')
    clearError()
    setSuccess('')
  }

  /**
   * Cancel editing
   */
  const handleCancelEdit = () => {
    setEditingField(null)
    setEditValue('')
    setConfirmPassword('')
    clearError()
    setSuccess('')
  }

  /**
   * Save user information changes
   */
  const handleSaveEdit = async () => {
    clearError()
    setSuccess('')

    try {
      if (editingField === 'username') {
        await updateUsername({ username: editValue })
        setSuccess('用户名更新成功')
      } else if (editingField === 'email') {
        const data = await updateEmail({ email: editValue })
        setTokens(data.access_token, data.refresh_token)
        setSuccess('邮箱更新成功')
      } else if (editingField === 'password') {
        if (editValue !== confirmPassword) {
          handleError({ response: { data: { detail: '两次输入的密码不一致' } } })
          return
        }
        const data = await updatePassword({ password: editValue })
        setTokens(data.access_token, data.refresh_token)
        setSuccess('密码更新成功')
      }
      const updatedUser = await getCurrentUser()
      setUserInfo(updatedUser)
      setEditingField(null)
      // Auto-clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000)
    } catch (err: any) {
      handleError(err)
    }
  }

  /**
   * Handle logout
   */
  const handleLogout = async () => {
    const setConversations = useConversationStore.getState().setConversations
    const setConfigs = useModelConfigStore.getState().setConfigs
    const clearMessages = useChatStore.getState().clearMessages

    try {
      await logoutApi()
    } catch (err) {
      console.error('Logout failed:', err)
    } finally {
      // Clear frontend state
      logout()
      setConversations([])
      setConfigs([])
      clearMessages()
      onClose()
    }
  }

  /**
   * Close modal and clear all states
   */
  const handleClose = () => {
    setSuccess('')
    clearError()
    onClose()
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onMouseDown={handleClose}
    >
      <div
        className="border border-mono p-6 w-full max-w-md mx-4"
        style={{ backgroundColor: 'var(--color-bg)' }}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold">Profile</h2>
          <button
            onClick={handleClose}
            className="text-sm opacity-70 hover:opacity-100"
          >
            ✕
          </button>
        </div>

        {error && (
          <div className="mb-4 p-2 border-2 border-red-700 text-red-700 text-sm font-bold">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-2 border-2 border-green-700 text-green-700 text-sm font-bold">
            {success}
          </div>
        )}

        <div className="space-y-4">
          {/* Username field */}
          <div>
            <div className="flex justify-between items-center">
              <span className="font-bold">Username:</span>
              {editingField !== 'username' && (
                <button
                  onClick={() => handleStartEdit('username')}
                  className="text-sm opacity-70 hover:opacity-100"
                >
                  Edit
                </button>
              )}
            </div>
            {editingField === 'username' ? (
              <form onSubmit={(e) => { e.preventDefault(); handleSaveEdit(); }} className="mt-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="flex-1 p-2 border border-mono focus:outline-none text-sm"
                    required
                  />
                  <button
                    type="submit"
                    className="px-2 py-1 border border-mono text-xs"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="px-2 py-1 border border-mono text-xs"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <p className="mt-1 break-all">{userInfo?.username}</p>
            )}
          </div>

          {/* Email field */}
          <div>
            <div className="flex justify-between items-center">
              <span className="font-bold">Email:</span>
              {editingField !== 'email' && (
                <button
                  onClick={() => handleStartEdit('email')}
                  className="text-sm opacity-70 hover:opacity-100"
                >
                  Edit
                </button>
              )}
            </div>
            {editingField === 'email' ? (
              <form onSubmit={(e) => { e.preventDefault(); handleSaveEdit(); }} className="mt-2">
                <div className="flex gap-2">
                  <input
                    type="email"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value)}
                    className="flex-1 p-2 border border-mono focus:outline-none text-sm"
                    required
                  />
                  <button
                    type="submit"
                    className="px-2 py-1 border border-mono text-xs"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="px-2 py-1 border border-mono text-xs"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <p className="mt-1 break-all">{userInfo?.email}</p>
            )}
          </div>

          {/* Password field */}
          <div>
            <div className="flex justify-between items-center">
              <span className="font-bold">Password:</span>
              {editingField !== 'password' && (
                <button
                  onClick={() => handleStartEdit('password')}
                  className="text-sm opacity-70 hover:opacity-100"
                >
                  Change
                </button>
              )}
            </div>
            {editingField === 'password' && (
              <form onSubmit={(e) => { e.preventDefault(); handleSaveEdit(); }} className="mt-2 space-y-2">
                <input
                  type="password"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none text-sm"
                  placeholder="New Password"
                  required
                />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none text-sm"
                  placeholder="Confirm Password"
                  required
                />
                <div className="flex gap-2 justify-end">
                  <button
                    type="submit"
                    className="px-2 py-1 border border-mono text-xs"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="px-2 py-1 border border-mono text-xs"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-center">
          <button
            onClick={handleLogout}
            className="py-2 px-6 text-red-700 hover:bg-red-700 hover:text-white"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  )
}