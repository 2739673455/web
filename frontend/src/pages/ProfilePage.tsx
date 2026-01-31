import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  getCurrentUser,
  updateUsername,
  updateEmail,
  updatePassword,
} from '../services/user'
import { useAuthStore } from '../stores/authStore'

export default function ProfilePage() {
  const [userInfo, setUserInfo] = useState<{ username: string; email: string; groups: string[] } | null>(null)
  const [loading, setLoading] = useState(true)
  const [editingField, setEditingField] = useState<'username' | 'email' | 'password' | null>(null)
  const [editValue, setEditValue] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()
  const { accessToken, setTokens, logout } = useAuthStore()

  useEffect(() => {
    if (!accessToken) {
      navigate('/')
      return
    }
    loadUserInfo()
  }, [accessToken, navigate])

  const loadUserInfo = async () => {
    try {
      const data = await getCurrentUser()
      setUserInfo(data)
    } catch (err) {
      console.error('Failed to load user info:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStartEdit = (field: 'username' | 'email' | 'password') => {
    setEditingField(field)
    setEditValue('')
    setConfirmPassword('')
    setError('')
    setSuccess('')
  }

  const handleSaveEdit = async () => {
    setError('')
    setSuccess('')

    if (!editValue.trim()) {
      setError('值不能为空')
      return
    }

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
          setError('两次输入的密码不一致')
          return
        }
        const data = await updatePassword({ password: editValue })
        setTokens(data.access_token, data.refresh_token)
        setSuccess('密码更新成功')
      }
      loadUserInfo()
      setEditingField(null)
    } catch (err: any) {
      const errorDetail = err.response?.data?.detail
      if (Array.isArray(errorDetail)) {
        // 查找第一个不是 "Field required" 的错误
        const meaningfulError = errorDetail.find((err: any) => err.msg !== 'Field required');
        if (meaningfulError) {
          const errorMsg = meaningfulError.msg || meaningfulError.type || JSON.stringify(meaningfulError);
          setError(errorMsg.replace('Value error, ', ''))
        } else if (errorDetail.length > 0) {
          // 如果都是 "Field required"，检查是否是 cookie 缺失
          const lastError = errorDetail[errorDetail.length - 1];
          if (lastError.loc && lastError.loc.includes('cookie') && lastError.loc.includes('refresh_token')) {
            setError('认证失败，请重新登录')
          } else {
            const errorMsg = lastError.msg || lastError.type || JSON.stringify(lastError);
            setError(errorMsg.replace('Value error, ', ''))
          }
        } else {
          setError(`更新失败`)
        }
      } else if (typeof errorDetail === 'object' && errorDetail.msg) {
        setError(errorDetail.msg.replace('Value error, ', ''))
      } else if (typeof errorDetail === 'string') {
        setError(errorDetail.replace('Value error, ', ''))
      } else {
        setError(`更新失败`)
      }
    }
  }

  const handleCancelEdit = () => {
    setEditingField(null)
    setEditValue('')
    setConfirmPassword('')
    setError('')
    setSuccess('')
  }

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/')
    } catch (err) {
      console.error('Logout failed:', err)
      navigate('/')
    }
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
      <div className="max-w-2xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Profile</h1>
          <Link to="/" className="py-2 px-4 border border-mono transition-colors">
            Back to Chat
          </Link>
        </div>

        {error && (
          <div className="mb-4 p-3 border border-red-500 text-red-500 text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 border border-green-500 text-green-500 text-sm">
            {success}
          </div>
        )}

        <div className="border border-mono">
          <div className="p-4 border-b border-mono">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm opacity-60">Username</p>
                <p className="text-lg">{userInfo?.username}</p>
              </div>
              <button
                onClick={() => handleStartEdit('username')}
                className="py-1 px-3 border border-mono transition-colors text-sm"
              >
                Edit
              </button>
            </div>
            {editingField === 'username' && (
              <div className="mt-4 flex gap-2">
                <input
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="flex-1 p-2 border border-mono focus:outline-none"
                />
                <button
                  onClick={handleSaveEdit}
                  className="py-2 px-4 border border-mono transition-colors"
                >
                  Save
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="py-2 px-4 border border-mono transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          <div className="p-4 border-b border-mono">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm opacity-60">Email</p>
                <p className="text-lg">{userInfo?.email}</p>
              </div>
              <button
                onClick={() => handleStartEdit('email')}
                className="py-1 px-3 border border-mono transition-colors text-sm"
              >
                Edit
              </button>
            </div>
            {editingField === 'email' && (
              <div className="mt-4 flex gap-2">
                <input
                  type="email"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="flex-1 p-2 border border-mono focus:outline-none"
                />
                <button
                  onClick={handleSaveEdit}
                  className="py-2 px-4 border border-mono transition-colors"
                >
                  Save
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="py-2 px-4 border border-mono transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          <div className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm opacity-60">Password</p>
                <p className="text-lg">******</p>
              </div>
              <button
                onClick={() => handleStartEdit('password')}
                className="py-1 px-3 border border-mono transition-colors text-sm"
              >
                Change
              </button>
            </div>
            {editingField === 'password' && (
              <div className="mt-4 space-y-2">
                <input
                  type="password"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                />
                <div className="flex gap-2">
                  <button
                    onClick={handleSaveEdit}
                    className="py-2 px-4 border border-mono transition-colors"
                  >
                    Save
                  </button>
                  <button
                    onClick={handleCancelEdit}
                    className="py-2 px-4 border border-mono transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleLogout}
            className="w-full py-3 border border-red-900 text-red-500 hover:bg-red-900/20 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  )
}