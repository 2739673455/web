import { useState } from 'react'
import { useAuthStore } from '../stores/authStore'
import { login, register } from '../services/user'
import { useErrorHandler } from '../hooks/useErrorHandler'

/**
 * Authentication modal component
 * Includes login and registration functionality with mode switching
 */
export default function AuthModal({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const { setTokens } = useAuthStore()
  const { handleError } = useErrorHandler()
  const [isLoginMode, setIsLoginMode] = useState(true)

  // Login form state
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginError, setLoginError] = useState('')

  // Registration form state
  const [registerUsername, setRegisterUsername] = useState('')
  const [registerEmail, setRegisterEmail] = useState('')
  const [registerPassword, setRegisterPassword] = useState('')
  const [registerConfirmPassword, setRegisterConfirmPassword] = useState('')
  const [registerError, setRegisterError] = useState('')

  /**
   * Switch between login and registration modes
   */
  const handleSwitchMode = () => {
    setIsLoginMode(!isLoginMode)
    setLoginError('')
    setRegisterError('')
  }

  /**
   * Handle login submission
   */
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoginError('')
    try {
      const data = await login({ email: loginEmail, password: loginPassword })
      setTokens(data.access_token, data.refresh_token)
      onClose()
      setLoginEmail('')
      setLoginPassword('')
    } catch (err: any) {
      handleError(err, setLoginError)
    }
  }

  /**
   * Handle registration submission
   */
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setRegisterError('')

    if (registerPassword !== registerConfirmPassword) {
      setRegisterError('两次输入的密码不一致')
      return
    }

    try {
      const data = await register({
        email: registerEmail,
        username: registerUsername,
        password: registerPassword,
      })
      setTokens(data.access_token, data.refresh_token)
      onClose()
      setRegisterUsername('')
      setRegisterEmail('')
      setRegisterPassword('')
      setRegisterConfirmPassword('')
    } catch (err: any) {
      handleError(err, setRegisterError)
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onMouseDown={onClose}
    >
      <div
        className="border border-mono p-6 w-full max-w-md mx-4"
        style={{ backgroundColor: 'var(--color-bg)' }}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-bold">{isLoginMode ? 'Login' : 'Register'}</h2>
          <button
            onClick={onClose}
            className="text-sm opacity-70 hover:opacity-100"
          >
            ✕
          </button>
        </div>

        {isLoginMode ? (
          // 登录表单
          <>
            {loginError && (
              <div className="mb-4 p-2 border-2 border-red-700 text-red-700 text-sm font-bold">
                {loginError}
              </div>
            )}
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <input
                  type="email"
                  placeholder="Email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                  required
                />
              </div>
              <div>
                <input
                  type="password"
                  placeholder="Password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                  required
                />
              </div>
              <div className="flex justify-between items-center">
                <button
                  type="button"
                  onClick={handleSwitchMode}
                  className="text-sm hover:underline opacity-70"
                >
                  No account? Register
                </button>
              </div>
              <div className="flex justify-center">
                <button
                  type="submit"
                  className="py-2 px-4"
                >
                  Login
                </button>
              </div>
            </form>
          </>
        ) : (
          // 注册表单
          <>
            {registerError && (
              <div className="mb-4 p-2 border-2 border-red-700 text-red-700 text-sm font-bold">
                {registerError}
              </div>
            )}
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <input
                  type="text"
                  placeholder="Username"
                  value={registerUsername}
                  onChange={(e) => setRegisterUsername(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                  required
                />
              </div>
              <div>
                <input
                  type="email"
                  placeholder="Email"
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                  required
                />
              </div>
              <div>
                <input
                  type="password"
                  placeholder="Password"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                  required
                />
              </div>
              <div>
                <input
                  type="password"
                  placeholder="Confirm Password"
                  value={registerConfirmPassword}
                  onChange={(e) => setRegisterConfirmPassword(e.target.value)}
                  className="w-full p-2 border border-mono focus:outline-none"
                  required
                />
              </div>
              <div className="flex justify-between items-center">
                <button
                  type="button"
                  onClick={handleSwitchMode}
                  className="text-sm hover:underline opacity-70"
                >
                  Already have an account? Login
                </button>
              </div>
              <div className="flex justify-center">
                <button
                  type="submit"
                  className="py-2 px-4"
                >
                  Register
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  )
}