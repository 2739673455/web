import React, { useRef } from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'
import { useAuthStore } from './stores/authStore'
import { getCurrentUser } from './services/user'

const InitApp = () => {
  const { accessToken, setUserInfo } = useAuthStore()
  const previousAccessToken = useRef('')

  React.useEffect(() => {
    // Load user info when access token becomes available
    if (accessToken && !previousAccessToken.current) {
      previousAccessToken.current = accessToken
      getCurrentUser()
        .then((userInfo) => {
          setUserInfo(userInfo)
        })
        .catch((err) => {
          console.error('Failed to get user info:', err)
        })
    }
    // Reset tracking when access token is cleared (logout)
    if (!accessToken) {
      previousAccessToken.current = ''
    }
  }, [accessToken])

  return <App />
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <InitApp />
)